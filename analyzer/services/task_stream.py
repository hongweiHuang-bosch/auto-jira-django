from __future__ import annotations

import json
import queue
import threading
from typing import Iterator

from analyzer.models import AnalysisTask
from analyzer.serializers import AnalysisTaskSerializer
from .task_catalog import list_role_options

_subscribers: dict[int, queue.Queue] = {}
_subscribers_lock = threading.Lock()
_next_subscriber_id = 1

'''
group:
    {
        'role_index': 0, 'role_label': '规则组 1', 'jql': 'project in (CHER, CHYT28) AND assignee = currentUser() AND CHERY_PROJECT != T1L_FL1_8255 ORDER BY updated DESC', 
        'latest_task': 
        {
            'id': 34, 'results': [], 'name': 'Jira 自动分析任务 - 规则组 1', 'role_index': 0, 'role_label': '规则组 1', 'jql': 'project in (CHER, CHYT28) AND assignee = currentUser() AND CHERY_PROJECT != T1L_FL1_8255 ORDER BY updated DESC', 'status': 'PENDING', 'progress': 0, 'message': '任务已创建', 'total_groups': 0, 'finished_groups': 0, 'created_at': '2026-04-03T15: 53: 49.647818+08: 00', 'updated_at': '2026-04-03T15: 53: 49.647859+08: 00'
        }
    },
    {'role_index': 1, 'role_label': '规则组 2', 'jql': 'project in (CHER, CHYT28) AND assignee = currentUser() AND CHERY_PROJECT = T1L_FL1_8255 ORDER BY updated DESC', 'latest_task': {'id': 32, 'results': [], 'name': 'Jira 自动分析任务 - 规则组 2', 'role_index': 1, 'role_label': '规则组 2', 'jql': 'project in (CHER, CHYT28) AND assignee = currentUser() AND CHERY_PROJECT = T1L_FL1_8255 ORDER BY updated DESC', 'status': 'SUCCESS', 'progress': 100, 'message': '规则组 2 分析完成', 'total_groups': 1, 'finished_groups': 1, 'created_at': '2026-04-03T15: 43: 49.381386+08: 00', 'updated_at': '2026-04-03T15: 44: 01.631426+08: 00'
        }
    },
    {'role_index': 2, 'role_label': '规则组 3', 'jql': 'project in (CHERY-T1J-FL2-8255) AND assignee in (currentUser()) ORDER BY updated DESC', 'latest_task': {'id': 28, 'results': [], 'name': 'Jira 自动分析任务 - 规则组 3', 'role_index': 2, 'role_label': '规则组 3', 'jql': 'project in (CHERY-T1J-FL2-8255) AND assignee in (currentUser()) ORDER BY updated DESC', 'status': 'SUCCESS', 'progress': 100, 'message': '规则组 3 分析完成', 'total_groups': 1, 'finished_groups': 1, 'created_at': '2026-04-03T15: 41: 59.957333+08: 00', 'updated_at': '2026-04-03T15: 42: 11.905784+08: 00'
        }
    },
    {'role_index': 3, 'role_label': '规则组 4', 'jql': 'project in (D01, CHERY-D01_INT, CHERY-D01-P, CHERY-D01-P-INT, CHERY-D01_HWADS) AND issue =DPINT-2941', 'latest_task': {'id': 24, 'results': [
                {'id': 10, 'issue_key': 'DPINT-2941', 'summary': '【D01P国际】【中控】【仪表】【实车】【客户问题】【10/10】车辆上电，仪表报辅助驾驶故障指示灯，辅助驾驶页面的功能都置灰不可点击', 'model': 'D01P', 'result_status': 'SUCCESS', 'reply_text': '：  \n通过查看cantrace日志，信号ADS_3_ELKSTS_31A和信号ADS_3_LKSSTS_31A反馈值为3，信号RRCR_1_SYSST_4F3和信号RLCR_1_SYSST_447反馈值为3，但ADS_3_ELKSts/ADS_3_LKSSts初始值存在不一致（上层4→3 vs CAN持续3），RRCR_1_SysSt/RLCR_1_SysSt存在短暂异常值（1/0）后恢复3，vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢。', 'can_trace_image': 'comment/D01P/DPINT-2941/仪表报故障灯，辅助驾驶界面部分功能不可点击.png', 'can_trace_image_url': '/media/D01P/DPINT-2941/仪表报故障灯，辅助驾驶界面部分功能不可点击.png', 'raw_signals': '', 'has_commented_to_jira': False, 'commented_at': None, 'error_message': '', 'created_at': '2026-04-03T14: 06: 20.198091+08: 00', 'updated_at': '2026-04-03T14: 06: 20.198117+08: 00', 'task': 24
                }
            ], 'name': 'Jira 自动分析任务 - 规则组 4', 'role_index': 3, 'role_label': '规则组 4', 'jql': 'project in (D01, CHERY-D01_INT, CHERY-D01-P, CHERY-D01-P-INT, CHERY-D01_HWADS) AND issue =DPINT-2941', 'status': 'SUCCESS', 'progress': 100, 'message': '规则组 4 分析完成', 'total_groups': 1, 'finished_groups': 1, 'created_at': '2026-04-03T14: 00: 55.005756+08: 00', 'updated_at': '2026-04-03T14: 06: 20.239588+08: 00'
        }
    }
'''
def build_group_payload() -> list[dict]:
    latest_tasks: dict[int, AnalysisTask] = {}
    # role_index 取出每个role_index 最新的一条任务 -是倒叙
    for task in AnalysisTask.objects.all().order_by('role_index', '-created_at'):
        # role_index没出现过就保存当前任务
        latest_tasks.setdefault(task.role_index, task)
    # role_index 0123  每个jql都会列出， 对应的任务是处理过的最新任务列表
    groups = []
    for option in list_role_options():
        task = latest_tasks.get(option['role_index'])
        # options：
        # 规则组 1 == [role_index]
        # project in (CHER, CHYT28) AND assignee = currentUser() AND CHERY_PROJECT != T1L_FL1_8255 ORDER BY updated DESC

        # task: db analysistask

        groups.append({
            **option,
            'latest_task': AnalysisTaskSerializer(task).data if task else None,
        })
    return groups


def _subscribe() -> tuple[int, queue.Queue]:
    # subscriber_id 会话的意思，每次开一个网页 就会加一
    global _next_subscriber_id
    subscriber_queue: queue.Queue = queue.Queue()
    with _subscribers_lock:
        subscriber_id = _next_subscriber_id
        _next_subscriber_id += 1
        _subscribers[subscriber_id] = subscriber_queue
    return subscriber_id, subscriber_queue


def _unsubscribe(subscriber_id: int) -> None:
    with _subscribers_lock:
        _subscribers.pop(subscriber_id, None)

# 广播机制 通知所有订阅的客户端 分组数据更新了
def publish_groups_snapshot() -> None:
    payload = build_group_payload()
    with _subscribers_lock:
        # 获取所有的会话（client）拥有的队列
        # 比如 html1 拥有的队列1  html2 拥有的队列2
        subscribers = list(_subscribers.values())
    # 每个订阅者队列都放入相同的payload 
    # 队列1 put payload,队列2 put payload   就是让不同的client有相同的payload
    # 可以查看payload.json 了解过程
    for subscriber_queue in subscribers:
        subscriber_queue.put(payload)
        # print("payload"+str(payload))



def stream_group_events() -> Iterator[str]:
    # 先注册订阅者  当前客户端建立连接后 会拿到一个唯一订阅 ID 和一个属于自己的队列
    subscriber_id, subscriber_queue = _subscribe()
    try:
        # 立刻拿当前最新快照，先发一次。 推送初始数据
        initial_payload = build_group_payload()
        yield _format_sse(initial_payload)
        # 持续等待消息
        while True:
            try:
                # 如果这 15 秒内有人调用了 publish_groups_snapshot()，那这个订阅者队列里就会收到一个 payload
                payload = subscriber_queue.get(timeout=15)
                yield _format_sse(payload)
            except queue.Empty:
                # 15秒没有任何更新，会发送一个ping 防止断开
                yield ': ping\n\n'
    finally:
        # 连接结束自动取消订阅
        _unsubscribe(subscriber_id)


def _format_sse(payload: list[dict]) -> str:
    return f"event: groups\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"
