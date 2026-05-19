import re
from typing import Any


CHECK_TYPE_AI_VS_CANTRACE = 'AI_RESULT_VS_CANTRACE'
CHECK_TITLE_AI_VS_CANTRACE = 'AI 结果 vs cantrace 一致性'
CHECK_SORT_ORDER_AI_VS_CANTRACE = 10
TIME_PATTERN = re.compile(r'\b\d{2}:\d{2}:\d{2}\b')


def build_validation_payload(
    *,
    reply_text: str,
    cantrace_payload: dict | None,
    upper_requirement_text: str,
) -> dict:
    signals = _extract_signals(cantrace_payload)
    if not signals:
        reason = '缺少可用 cantrace 数据，无法校验 AI 结果与信号证据的一致性'
        return _build_payload(
            system_verdict='UNKNOWN',
            summary_reason=reason,
            check_status='UNKNOWN',
            check_reason=reason,
            chart_payload={'series': []},
            table_rows=[],
            evidence={
                'ai_time': _extract_ai_time(reply_text),
                'cantrace_time': '',
                'upper_requirement_text': upper_requirement_text,
            },
        )

    first_signal = signals[0]
    ai_time = _extract_ai_time(reply_text)
    cantrace_time = str(first_signal.get('at') or '')

    if ai_time and cantrace_time and ai_time == cantrace_time:
        verdict = 'PASS'
        reason = '校验通过，AI 结果与 cantrace 时间点一致'
    else:
        verdict = 'FAIL'
        reason = '时间点不匹配'

    table_rows = [_build_signal_table_row(first_signal, ai_time, cantrace_time)]
    chart_payload = {
        'series': [
            {
                'name': str(first_signal.get('name') or ''),
                'points': [
                    {
                        'at': cantrace_time,
                        'from': str(first_signal.get('from') or ''),
                        'to': str(first_signal.get('to') or ''),
                    }
                ],
            }
        ]
    }

    return _build_payload(
        system_verdict=verdict,
        summary_reason=reason,
        check_status=verdict,
        check_reason=reason,
        chart_payload=chart_payload,
        table_rows=table_rows,
        evidence={
            'ai_time': ai_time,
            'cantrace_time': cantrace_time,
            'upper_requirement_text': upper_requirement_text,
            'signal': first_signal,
        },
    )


def _build_payload(
    *,
    system_verdict: str,
    summary_reason: str,
    check_status: str,
    check_reason: str,
    chart_payload: dict,
    table_rows: list[dict],
    evidence: dict,
) -> dict:
    return {
        'system_verdict': system_verdict,
        'summary_reason': summary_reason,
        'checks': [
            {
                'check_type': CHECK_TYPE_AI_VS_CANTRACE,
                'status': check_status,
                'title': CHECK_TITLE_AI_VS_CANTRACE,
                'reason': check_reason,
                'evidence_payload': evidence,
                'sort_order': CHECK_SORT_ORDER_AI_VS_CANTRACE,
            }
        ],
        'chart_payload': chart_payload,
        'table_rows': table_rows,
    }


def _extract_signals(cantrace_payload: dict | None) -> list[dict]:
    if not isinstance(cantrace_payload, dict):
        return []

    signals = cantrace_payload.get('signals')
    if not isinstance(signals, list):
        return []

    return [signal for signal in signals if isinstance(signal, dict)]


def _extract_ai_time(reply_text: str) -> str:
    match = TIME_PATTERN.search(reply_text or '')
    if not match:
        return ''
    return match.group(0)


def _build_signal_table_row(signal: dict[str, Any], ai_time: str, cantrace_time: str) -> dict:
    return {
        'signal_name': str(signal.get('name') or ''),
        'ai_time': ai_time,
        'cantrace_time': cantrace_time,
        'from': str(signal.get('from') or ''),
        'to': str(signal.get('to') or ''),
        'matched': bool(ai_time and cantrace_time and ai_time == cantrace_time),
    }
