# -*- coding: utf-8 -*-
# Author: huo2wx hongwei.huang@cn.bosch.com
# LastEditTime: 2025-11-07
# FilePath: aitool-restructure/gpt-restructure-map/ai_client_by_langchain.py
# Description: AI 客户端 - 导出三段系统提示 + 长超时 + 重试 + 可关系统代理

from __future__ import annotations
import re
import os
import time
import json
import logging
import requests
import yaml
import chromadb
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer, CrossEncoder
import chromadb
from langchain_openai import ChatOpenAI
import json
from pathlib import Path
from typing import Optional, Tuple, List
import base64
from langchain_core.messages import HumanMessage
logger = logging.getLogger("CAN-AI-JIRA")




# 提取上层评论中的信号
EXTRACT_SIGNALS_SYSTEM = (
    "我们将要进行CAN总线信号分析, 用户将输入{问题描述}, 我们将要从用户输入的{问题描述}提取需要分析的信号, "
    "例如: 'CEM_Abat_VentCMDSts, SET_Abat_VentCMD, IHU_17_GROUP_T1J_FL2'。"
    "不需要提取依据和分析要点。"
    "请提取{问题描述}中出现的所有信号，并且信号组也要提取。"
    "在一行中输出所有信号，并且信号间用', '隔开，如果没有提取到信号就输出“无法提取”。"
)

# 上层日志分析
LOG_SUMMARY_SYSTEM = (
    "我们将要进行CAN总线信号分析, 用户将输入{需求描述}、 {问题描述}、{信号映射关系}以及{信号组信息}, "
    "我们将要从用户输入的需求描述 问题描述, 选择与信号propid相关或者与信号组相关的日志, "
    "再根据信号映射关系和信号组信息以'时间戳 模块 信号名 信号值'的方式输出信号变化的日志摘要, "
    "例如, 对“2025-07-24 19:30:41.748 2631 29579 I ACM : canSetVehicleParam propertyId: 506 value 1 halPropertyId: 557843466 halAreaId 0”, "
    "输出“2025-07-24 19:30:41.748 Framework IHU_11_SCFSwtSet 1  (来自 2025-07-24 19:30:41.748 2631 29579 I ACM : canSetVehicleParam propertyId: 506 value 1 halPropertyId: 557843466 halAreaId 0)”; "
    "对“2025-09-05 15:23:00.269 2829 2851 I IALCarImpl: setGroupIHU8Property start 7 valOfGroup [0, 0, 1, 0, 0, 2, 0]”, "
    "结合信号组信息进行分析, 得知信号ESCOFF_ON_OFF在信号组IHU_8_GROUP中, 且信号值为1, "
    "则输出“2025-09-05 15:23:00.269 Framework ESCOFF_ON_OFF 1  (来自 2025-09-05 15:23:00.269 2829 2851 I IALCarImpl: setGroupIHU8Property start 7 valOfGroup [0, 0, 1, 0, 0, 2, 0])”; "
    "对“2025-07-17 20:03:49.317 484 583 D BoschVehicleHal: set prop: 557909787 / 0X2141071B, type: INT32_VEC, value:0 0 0 0 0 2 0 0 0 , car_type:14”, "
    "结合信号组信息进行分析, 得知信号IHU_ChbSterilization_Req在信号组IHU_CHB_42_GROUP_FL1中, 且信号值为2, "
    "则输出“2025-07-17 20:03:49.317 BoschVhal IHU_ChbSterilization_Req 2  (来自2025-07-17 20:03:49.317 484 583 D BoschVehicleHal: set prop: 557909787 / 0X2141071B, type: INT32_VEC, value:0 0 0 0 0 2 0 0 0 , car_type:14)”; "
    "不需要提取依据和分析要点。只对信号变化进行摘要。"
    "模块只有“Framework”、“BoschVhal”、“QNX”。"
    "日志中涉及“IALCarImpl”或者“ACM”, 则模块为“Framework”; "
    "日志中涉及“BoschVehicleHal”, 则模块为“BoshVhal”; "
    "日志中涉及“VehicleService”, 则模块为“QNX”。"
    "模块为“Framework”、“BoschVhal”、“QNX”的日志都需要进行输出。"
    "对于信号组, 请在信号组值中提取出<信号映射关系>中涉及的所有相关信号的信号值, 即使是0也要输出, 并且输出时不要带信号组名; 对于非信号组, 请提取出日志中的信号值。"
    "输出的日志摘要中的'信号名'不是信号的prop。"
    "如果日志中涉及'ACM', 只输出包含{信号映射关系}中propid的日志。"
    "如果日志中涉及'signalApi-CarOperation', 不要提取。"
)

ANDROID_QNX_LOG_SUMMARY_SYSTEM = (
    "我们将要进行android和qnx日志信号分析, 用户将输入{信号映射关系}和{android_qnx日志}, "
    "我们将要从用户输入的{信号映射关系}, 选择与信号propid相关或者与信号组相关的日志, "
    "再根据{信号映射关系}和{android_qnx日志}以'时间戳 模块 信号名 信号值'的方式输出信号变化的日志摘要, "
    "例如, 对“2025-10-29 14:59:02.121  1088  1546 D BoschVehicleHal: set prop: 557891756 / 0X2140C0AC, type: INT32, value:1 , car_type:33 "
    "输出“2025-10-29 14:59:02.121 BoschVehicleHal 557891756 1"
    "对“2025-10-29 14:58:51.961    VehicleService.589896      VehicleServer   12848 11 D -28799472052906 VehicleService.cpp:PrintPropValue:2755 [7DD0] prop:FRZCU_FRMEMORYFB_4D2(557891757/0X2140C0AD:0), data[1]=0X1, (1234/0X4D2)FRZCU_11::FRZCU_FRMemoryFb, car:33 "
    "输出“2025-10-29 14:58:51.961 VehicleService 0X2140C0AD 0X1”"
    "对“2023-01-01 00:00:32.262    VehicleService.319558      VehicleServer   01149 03 N +0 statistics:214 [0B4D]0X214002D7(0)2|[0:00:04:680]lost|[0:00:09:189]0"
    "输出2023-01-01 00:00:32.262 VehicleService 0X214002D7 值变化了2次，第一次lost，[0:00:09:189 - 0:00:04:680 = 4.509秒]之后变为0"
    "不需要提取依据和分析要点。只对信号变化进行摘要。"
    "模块只有“BoschVehicleHal”、“VehicleService”、“VehicleClient”。"
    "如果日志中涉及'signalApi-CarOperation', 不要提取。"
)
# 一致性分析
CONSISTENCY_SYSTEM = (
    "我们将要进行CAN总线信号分析, 用户将输入{上层提供的信号日志}以及{CAN Trace日志}, "
    "请判断{CAN Trace日志}的变化趋势与{上层提供的信号日志}的变化趋势是否一致, "
    "如果不一致, 请指出不一致的时间点, 并且忽略时间差异，再按照信号值变化趋势进行判断, "
    "如果反馈信号没有根据请求信号改变, 则输出“转对手件分析”, "
    "不需要提取依据和分析要点。"
)

COMPARE_CANTRACE = (
    "我们将要进行CAN总线信号分析, 用户将输入{信号及信号组关系},{上层评论}以及{CAN Trace日志}, "
    "梳理上层评论中关于信号的触发机制，比如信号A没有反馈1，信号A应该反馈2，没有收到信号B的反馈。"
    "请判断信号及信号组关系中的信号，在CAN Trace中随时间值变化的关系,"
    "比如正常信号的情况：信号A发送1且持续，信号B立即发送2持续；信号A发送1三帧有立即发送三帧0，同时信号B立即发送三帧2又立即发送三帧1；"
    "比如异常信号的情况：信号A发送1且持续，信号B的值没有变化，持续原来的值发送；信号A发送1三帧有立即发送三帧0，信号B的值没有变化，持续原来的值发送；（值没有变化，持续原来的值发送认为是不反馈）"
    "给出信号分析的结果，给出结论，比如：从CAN trace来看：ICC_ExhibitionModeSwitch 发1之后，FLZCU_CarMode 变成3，VCU_2_G_ExhibitionMod 变成1，请按照需求确认问题原因并转相关模块分析，谢谢。"
    "比如：通过查看cantrace日志，信号HCU_PowerCut多次上报1, vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢"
    "比如：通过查看cantrace日志，信号ICC_ModeAdjustDisplaySts已经正常下设，但是信号TMS_ModeAdjustDisplaySts一直是0没有变化，vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢"
    "比如：从cantace来看，信号FLZCU_UIROpenStas的值和信号FLZCU_WALOpenStas的值始终是1没有变化，请上层确认，谢谢。"
)
REQUIREMENT_EXTRACT_SYSTEM = (
    "我们将对日志中的需求进行提取,用户输入{问题描述}, 提取上层对本层的需求，"
    "比如：请求 IHU_3_DVD_Set_DOW  反馈 BSD_1_DOWSts 信号组 IHU_3_GROUP，应用下设打开门开预警0x1:ON，无反馈，请底层继续确认; 提取需求结果：上层下设信号IHU_3_DVD_Set_DOW值为1，反馈信号BSD_1_DOWSts值没有变化"
    "比如：从日志上看，掉电前，通过557909442 / 0X214105C2数组，设置 IHU_20_RgnSet 3 强档 底层反馈强， 557842985 / 0X21400229, type:INT32, value:0 , car_type:7 断电瓶后，重新上电反馈：557842985 / 0X21400229, type: INT32, value:2 请代工check一下can trace，期望反馈0 （强）;提取需求结果：上层下设信号557909442 值为1，反馈信号 557842985值反馈了0，重新上电后，信号557842985 反馈2，请下层检查这几个变化的信号是否变化趋势一致"
    "比如：主驾加热及通风设置请求  SET_FLSEATHEATVENTSWREQ_57F  557895861 主驾加热及通风设置反馈  CEM_IPM_FLSEATHEATVENTSWSTS_5C4  557895862 获取主驾加热及通风设置反馈为无效值； 下设主驾加热及通风 = 0x7后，获取主驾加热及通风还是无效值  请帮忙接续确认底层信号的状态位 aplog.001:277731:2025-12-05 15:03:09.413 2789 2839 D CarServiceImpl: getIntProperty propId 557895862 Name CEM_IPM_FLSEATHEATVENTSWSTS_5C4 result -2147483648； 提取需求结果：上层下设信号SET_FLSEATHEATVENTSWREQ_57F 获取反馈信号CEM_IPM_FLSEATHEATVENTSWSTS_5C4值是无效值，请下层确认信号SET_FLSEATHEATVENTSWREQ_57F下设之后，反馈信号值是不是无效值( -2147483648)"
)

__all__ = [
    "AIClient",
    "EXTRACT_SIGNALS_SYSTEM",
    "LOG_SUMMARY_SYSTEM",
    "CONSISTENCY_SYSTEM",
]

def split_into_chunks(doc_file: str) -> List[str]:
    """按空行分块，过滤空块。"""
    content = Path(doc_file).read_text(encoding="utf-8", errors="ignore")
    return [chunk for chunk in content.split("\n\n") if chunk.strip()]
def build_context(chunks: List[str], max_chars: int = 20000) -> str:
        """
        拼接上下文，按字符数粗略限长，避免超过模型 context。
        """
        parts: List[str] = []
        total_len = 0

        for ch in chunks:
            if not ch:
                continue

            length = len(ch)
            if total_len + length > max_chars:
                remain = max_chars - total_len
                if remain > 0:
                    parts.append(ch[:remain])
                break

            parts.append(ch)
            total_len += length

        return "\n\n".join(parts)
def safe_parse_json(text: str) -> Any:
    """
    从模型输出中安全解析 JSON：
    - 支持 <think>...</think> 思维链包裹
    - 支持 JSON 前后有额外说明文字，只截取第一个 { 到最后一个 } 之间的内容
    """
    # 1) 去掉 <think>...</think> 块（跨行匹配）
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
    cleaned = cleaned.strip()

    # 2) 找到第一个 '{' 和最后一个 '}'，截取中间作为 JSON 字符串
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or start > end:
        raise ValueError(f"Cannot locate JSON object in model output:\n{cleaned}")

    json_str = cleaned[start:end + 1].strip()

    # 3) 真正解析 JSON
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Cannot parse JSON (after cleaning think-blocks): {e}\n"
            f"JSON candidate:\n{json_str}"
        )
    
def image_to_data_url(path: str) -> str:
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/jpeg;base64,{b64}"


class AIClient:
    def __init__(self,
                 base_url: str,
                 api_key: str,
                 model: str = "Qwen3-32B-FP16",
                 pic_model: str = "Qwen3-VL-8B",
                 connect_timeout: int = 10,
                 read_timeout: int = 300,
                 max_retries: int = 3,
                 use_system_proxy: bool = False,
                 proxies: Optional[dict] = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.pic_model = pic_model
        self.timeout: Tuple[int, int] = (connect_timeout, read_timeout)
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.trust_env = use_system_proxy
        self.proxies = proxies
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        
        # 微软研发的 MiniLM 架构进行微调 
        # 高效的轻量级语言模型，适合资源有限的环境，能够胜任多种 NLP 任务
        self.embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        self.embedding_model.max_seq_length = 512
        self.chromadb_client = chromadb.EphemeralClient()
        self.chromadb_collection = self.chromadb_client.get_or_create_collection(name="default")

        self.llm = ChatOpenAI(
            model = self.model,
            openai_api_base = f"{self.base_url}/llm/model/v1/",  # remote service URL  */v1/chat/completions
            openai_api_key = self.api_key,
            model_kwargs = {"tool_choice": "none"},  # disable auto tool mode
        )

    @staticmethod
    def clean_ai_response(s: str) -> str:
        s = re.sub(r'<think>.*?</think>', '', s, flags=re.DOTALL)
        s = re.sub(r'\n\s*\n', '\n', s)
        return s.strip()
    
    def read_img(self, image_path: str):
        # base_dir = Path(__file__).resolve().parent
        # image_path = base_dir / "image.png"
        img_data_url = image_to_data_url((image_path))

        message = HumanMessage(
            content=[
                {"type": "text", "text": "请识别这张图片的主要内容, 保留图片内容，不要添加任何解释和说明，只保留识别的结果"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": img_data_url
                    }
                },
            ]
        )
        self.pic_llm = ChatOpenAI(
            model = self.pic_model,
            openai_api_base = f"{self.base_url}/llm/model/v1/",  # remote service URL  */v1/chat/completions
            openai_api_key = self.api_key,
            model_kwargs = {"tool_choice": "none"},  # disable auto tool mode
        )
        resp = self.pic_llm.invoke([message])
        print(resp.content)
        return resp.content
    
    def embed_chunk(self, text: str) -> List[float]:
        """
        Encode a single text into a 1D embedding vector.
        """
        emb = self.embedding_model.encode(text)  # 一般返回 np.ndarray(shape=(dim,))
        # 转成 Python list
        if hasattr(emb, "tolist"):
            emb = emb.tolist()

        # 如果 encode 返回的是 [[...]]，这里做一下防御性处理
        if len(emb) > 0 and isinstance(emb[0], (list, tuple)):
            emb = emb[0]

        return list(emb)

    def save_embeddings(self,chunks: List[str], embeddings: List[List[float]]) -> None:
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            self.chromadb_collection.add(
                documents=[chunk],
                embeddings=[embedding],
                ids=[str(i)],
            )

    def retrieve(self, query: str, top_k: int = 5) -> List[str]:
        query_embedding = self.embed_chunk(query)  # -> [float]

        results = self.chromadb_collection.query(
            query_embeddings=[query_embedding],  # -> [[float]]
            n_results=top_k,
        )

        # Chroma 的 documents 形状是 List[List[str]]，外层是 query 数量
        docs = results.get("documents") or []
        if not docs:
            return []

        # docs[0] 就是当前 query 对应的 top_k 个文档字符串 List[str]
        chunks = docs[0]
        # 再做一层清洗，确保是 List[str]
        return [c for c in chunks if isinstance(c, str) and c.strip()]


    def rerank(self, query: str, retrieved_chunks: Any, top_k: int = 3) -> List[str]:
        """
        使用 CrossEncoder 对 retrieved_chunks 进行重排序，并返回得分最高的 top_k 个文本片段。

        - query: 用户问题（必须是 str）
        - retrieved_chunks: 可以是 str、List[str]、List[List[str]]、甚至是其他类型，统一在这里做清洗。
        """

        if not isinstance(query, str):
            query = "" if query is None else str(query)

        chunks: List[str] = []

        def _normalize_one(x: Any) -> None:
            """把单个元素 x 尽量转成 str，加入 chunks。"""
            if x is None:
                return
            if isinstance(x, str):
                chunks.append(x)
            elif isinstance(x, (list, tuple)):
                # 如果是 list/tuple，递归展开一层（防止 List[List[str]] 之类）
                for y in x:
                    _normalize_one(y)
            else:
                # 其它类型（dict / int / float），转成字符串（避免 tokenizer 报类型错）
                try:
                    chunks.append(json.dumps(x, ensure_ascii=False))
                except Exception:
                    chunks.append(str(x))

        _normalize_one(retrieved_chunks)

        # 去掉特别短的 / 空白的，防止浪费 cross-encoder 资源
        chunks = [c for c in chunks if isinstance(c, str) and c.strip()]

        if not chunks:
            # 没有有效文本，直接返回空
            return []

        # CrossEncoder 期望: List[Tuple[str, str]] 或 List[List[str]]
        pairs: List[Tuple[str, str]] = []
        for chunk in chunks:
            q = query
            c = chunk
            # 再兜一层类型保护
            if not isinstance(q, str):
                q = "" if q is None else str(q)
            if not isinstance(c, str):
                try:
                    c = json.dumps(c, ensure_ascii=False)
                except Exception:
                    c = str(c)
            pairs.append((q, c))

        if not pairs:
            return []

        cross_encoder = CrossEncoder("cross-encoder/mmarco-mMiniLMv2-L12-H384-v1")
        scores = cross_encoder.predict(pairs)  # len(scores) == len(pairs) == len(chunks)

        # 按得分排序，取前 top_k --------
        scored_chunks = list(zip(chunks, scores))
        scored_chunks.sort(key=lambda x: x[1], reverse=True)

        top_k = min(top_k, len(scored_chunks))
        reranked = [chunk for chunk, _ in scored_chunks[:top_k]]

        return reranked
    
    #  JSON结构输出
    def generate(self, query: str, chunks: List[str], top_k: int = 8) -> Dict[str, Any]:
        """
        使用 top_k 个 chunk，构造限长上下文，调用 LLM。
        输出为结构化 JSON（dict），schema 为：
        {
        "signals": string[],
        "analysis": string,
        "suggested_owner": string,
        "confidence": number
        }
        """
        # 1）限制 chunk 数量
        selected_chunks = chunks[:top_k]

        # 2）限制上下文长度
        context = build_context(selected_chunks, max_chars=20000)

        # 3）强约束 JSON 的 prompt（英文， 没有使用中文embedding模型）
        prompt = f"""
    You are a CAN / vehicle signal analysis assistant.

    You MUST answer strictly as a single valid JSON object.
    Do NOT output any extra text, comments, or markdown.

    The JSON schema is:
    {{
    "signals": string[],
    "analysis": string,
    "suggested_owner": string,
    "confidence": number
    }}

    - "signals": signals mentioned in the user question or relevant CAN/VHAL/CAN trace signals.
    - "analysis": detailed reasoning and findings based on the context.
    - "suggested_owner": which module/team should investigate (e.g. ABM, IHU, Gateway, Network).
    - "confidence": a number between 0 and 1.

    User question:
    {query}

    Context:
    {context}
    """

        resp = self.llm.invoke(prompt)

        # ChatOpenAI.invoke 返回的是 AIMessage，取 content
        raw_text = getattr(resp, "content", str(resp)).strip()
        logger.debug(f"[AI RAW] {raw_text}")
        result = safe_parse_json(raw_text)
        return result


    def query_signal_by_rag(self, query: str, car_type_json_path: str)->str:
        # 1）加载文档并分块
        doc_path = car_type_json_path  
        chunks = split_into_chunks(doc_path)

        # 2）构建向量并写入 Chroma
        embeddings = [self.embed_chunk(chunk) for chunk in chunks]
        self.save_embeddings(chunks, embeddings)

        # 3） query prompt写死
        # query = (
        #     "请从用户提供的{问题描述}中提取评论中出现的所有信号名称，比如：CEM_IPM_FrontOFFSts，Queen_bed_mode_Swt，若无匹配项则输出'无法提取'"
        #     f"{comment}"
        # )
        # 4）检索 + 重排
        retrieved_chunks = self.retrieve(query, top_k=3)
        reranked_chunks = self.rerank(query, retrieved_chunks, top_k=2)

        # 5）生成结构化 JSON 答案
        answer = self.generate(query, reranked_chunks)
        return answer

    def _post(self, url: str, payload: dict) -> requests.Response:
        last_err = None
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.session.post(
                    url, headers=self.headers, json=payload,
                    timeout=self.timeout, proxies=self.proxies
                )
                resp.raise_for_status()
                return resp
            except (requests.ReadTimeout, requests.ConnectionError) as e:
                last_err = e
                wait = min(2 ** attempt, 8)  # 指数退避
                logger.warning(f"[AIClient] 请求失败({type(e).__name__}) 第{attempt}/{self.max_retries}次，{wait}s后重试…")
                time.sleep(wait)
            except requests.HTTPError:
                # 4xx/5xx 是否重试可按需处理，这里先不重试
                raise
        assert last_err is not None
        raise last_err

    def chat_by_langchain(self, system_prompt: str, user_msg: str):
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg}
        ]

        resp = self.llm.invoke(messages)
        return self.clean_ai_response(resp.content)
    
    def chat_by_langchain_rag(self, system_prompt: str, user_msg: str):
        # user_msg comment中提取信号，
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg}
        ]

        resp = self.llm.invoke(messages)
        return self.clean_ai_response(resp.content)

    def chat(self, system_prompt: str, user_msg: str) -> str:
        url = f"{self.base_url}/llm/model/v1/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg}
            ],
            "stream": False
        }
        try:
            sz = len(json.dumps(payload, ensure_ascii=False))
            logger.debug(f"[AIClient] payload size = {sz} bytes")
        except Exception:
            pass

        resp = self._post(url, payload)
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        return self.clean_ai_response(content)

# answer = generate(query, reranked_chunks)
# print(json.dumps(answer, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    config_path = "config.yaml"
    print("------")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"配置文件不存在")
    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)
        ai_config = cfg["ai"]
    print("------")

    ai = AIClient(
        base_url = ai_config["base_url"],
        api_key= ai_config["api_key"],
        model= ai_config.get("model", "Qwen3-32B-FP16"),
        connect_timeout=ai_config.get("connect_timeout", 10),
        read_timeout= ai_config.get("read_timeout", 300),
        max_retries=ai_config.get("max_retries", 3),
        use_system_proxy= ai_config.get("max_retries", False),
        proxies=ai_config.get("proxies")
    )
    response = ai.chat_by_langchain("你是一个评论总结大师", 
                                    """
评论11
作者: 博世-代云贵
时间: 2026-01-26T15:12:37.000+0800
内容:
主机发送的周期报文0x537没有抓到，现在只抓到了对手件反馈的周期报文0x49c，我们看了CAN trace里面没有主机的周期网管报文0x618,请确认正确抓取了ICC CAN，谢谢。



!image-2026-01-26-15-11-33-997.png|width=332,height=164!
----------------------------------------
评论12
作者: 王宇_光庭
时间: 2026-01-27T20:14:34.000+0800
内容:
!screenshot-3.png|thumbnail![^20260127-195816.mp4][^can_20260127195554.asc][^Logs_2026_01_27_19_59_38.7z.002][^Logs_2026_01_27_19_59_38.7z.001]
----------------------------------------
评论13
作者: 王宇_光庭
时间: 2026-01-27T20:14:51.000+0800
内容:
代总，麻烦再看看呢
----------------------------------------
评论14
作者: 博世-代云贵
时间: 2026-01-27T20:37:12.000+0800
内容:
通过查看cantrace日志，信号ICC_RolloverSetCmd已经正常下设，但是信号ABM_1_Rollover_Status一直是0没有变化，vehicle已经透传，请按需求确认原因并转对应模块分析，谢谢

 !screenshot-4.png|thumbnail! 
----------------------------------------
                                    """)
    print(response)
    # ai = AIClient(
    #     base_url = ai_config["base_url"],
    #     api_key= ai_config["api_key"],
    #     model= ai_config.get("model", "Qwen3-32B-FP16"),
    #     connect_timeout=ai_config.get("connect_timeout", 10),
    #     read_timeout= ai_config.get("read_timeout", 300),
    #     max_retries=ai_config.get("max_retries", 3),
    #     use_system_proxy= ai_config.get("max_retries", False),
    #     proxies=ai_config.get("proxies")
    # )

    # ai_extract = ai.chat("你是一个日志分析师, 帮我分析一下下面这段日志","2025-10-29 14:59:02.121 BoschVehicleHal 557891756 1   2025-10-29 14:58:51.961 VehicleService 0X2140C0AD 0X1    2023-01-01 00:00:32.262 VehicleService 0X214002D7 值变化了2次，第一次lost，[0:00:09:189 - 0:00:04:680 = 4.509秒]之后变为0")
    # print(f"ai_extract ： {ai_extract}")

    # resp = requests.Session().post(
    #     f"{ai_config['base_url']}/llm/model/v1/chat/completions",
    #     headers={
    #         "Content-Type": "application/json",
    #         "Authorization": f"Bearer {ai_config.get('api_key')}",
    #     },
    #     json={
    #         "model":ai_config.get("model", "Qwen3-32B-FP16"),
    #         "messages":[
    #             {"role" : "system", "content" : "你是一个日志分析师, 帮我分析一下下面这段日志"},
    #             {"role": "user", "content" : "2023-01-01 00:00:32.262 VehicleService 0X214002D7 值变化了2次，第一次lost，[0:00:04:680 - 0:00:09:189 = 4.509秒]之后变为0"}
    #         ],
    #         "stream" : False
    #     },
    #     timeout=300,
    #     proxies=ai_config.get("proxies"),
    # )
    # resp.raise_for_status()
    # data = resp.json()
    # content = data["choices"][0]["message"]["content"]
    # print(f"content: {content}")
