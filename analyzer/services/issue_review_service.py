from __future__ import annotations

from analyzer.models import IssueProcessResult, IssueReviewSample
from legacy_core.config_map import ISSUE_REVIEW_SYSTEM
from legacy_core.utils import load_config
from legacy_core.ai_client_by_langchain import safe_parse_json


def _format_review_samples(samples: list) -> str:
    if not samples:
        return "（暂无历史错例）"
    lines = []
    for i, s in enumerate(samples, 1):
        lines.append(
            f"【错例 {i}】\n"
            f"  Jira: {s.issue_key}\n"
            f"  错误结论: {s.incorrect_conclusion}\n"
            f"  正确结论: {s.correct_conclusion}\n"
            f"  原因: {s.error_reason}"
        )
    return "\n\n".join(lines)


def review_issue_result(result: IssueProcessResult, samples: list) -> dict:
    """
    调用 AI 复核单票结果。
    返回 dict，包含 review_status / review_reason / correct_conclusion / few_shot_count / review_model。
    """
    cfg = load_config('config.yaml')
    ai_cfg = cfg.get('ai', {})

    # 延迟导入避免循环
    from legacy_core.ai_client_by_langchain import AIClient

    ai = AIClient(
        base_url=ai_cfg.get('base_url', ''),
        api_key=ai_cfg.get('api_key', ''),
        model=ai_cfg.get('model', 'Qwen3-32B-FP16'),
    )

    prompt = ISSUE_REVIEW_SYSTEM + f"""

---
Jira 评论 / 信号摘要：
{result.raw_signals or '（无）'}

当前模型结论：
{result.reply_text or '（无）'}

历史错例（最多 3 条）：
{_format_review_samples(samples)}
"""

    raw = ai.ask(prompt) if hasattr(ai, 'ask') else ''
    payload = safe_parse_json(raw) if raw else {}

    review_status = payload.get('review_status', 'PASS')
    if review_status not in ('PASS', 'FAIL'):
        review_status = 'PASS'

    return {
        'review_status': review_status,
        'review_reason': payload.get('review_reason', ''),
        'correct_conclusion': payload.get('correct_conclusion', ''),
        'few_shot_count': len(samples),
        'review_model': ai_cfg.get('model', 'Qwen3-32B-FP16'),
    }
