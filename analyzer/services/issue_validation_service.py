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
        chart_payload = {'series': []}
        table_rows: list[dict] = []
        return _build_payload(
            system_verdict='UNKNOWN',
            summary_reason=reason,
            check_status='UNKNOWN',
            check_reason=reason,
            chart_payload=chart_payload,
            table_rows=table_rows,
            evidence={
                'ai_time': _extract_ai_time(reply_text),
                'upper_requirement_text': upper_requirement_text,
                'signals': [],
            },
        )

    ai_time = _extract_ai_time(reply_text)
    table_rows = [_build_signal_table_row(signal, ai_time) for signal in signals]
    chart_payload = _build_chart_payload(signals)

    has_missing_time = any(not row['cantrace_time'] for row in table_rows)
    has_mismatch = any(row['status'] == 'FAIL' for row in table_rows)
    if has_missing_time:
        verdict = 'FAIL'
        reason = '缺少信号时间点'
    elif not ai_time:
        verdict = 'WARNING'
        reason = 'AI 结果缺少明确时间，已加载 cantrace 证据但无法做时间一致性校验'
    elif has_mismatch:
        verdict = 'FAIL'
        reason = '时间点不匹配'
    else:
        verdict = 'PASS'
        reason = '校验通过，AI 结果与 cantrace 时间点一致'

    return _build_payload(
        system_verdict=verdict,
        summary_reason=reason,
        check_status=verdict,
        check_reason=reason,
        chart_payload=chart_payload,
        table_rows=table_rows,
        evidence={
            'ai_time': ai_time,
            'upper_requirement_text': upper_requirement_text,
            'signals': signals,
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
    evidence_payload = {
        **evidence,
        'chart_payload': chart_payload,
        'table_rows': table_rows,
    }
    return {
        'system_verdict': system_verdict,
        'summary_reason': summary_reason,
        'checks': [
            {
                'check_type': CHECK_TYPE_AI_VS_CANTRACE,
                'status': check_status,
                'title': CHECK_TITLE_AI_VS_CANTRACE,
                'reason': check_reason,
                'evidence_payload': evidence_payload,
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


def _build_signal_table_row(signal: dict[str, Any], ai_time: str) -> dict:
    cantrace_time = str(signal.get('at') or '')
    matched = bool(ai_time and cantrace_time and ai_time == cantrace_time)
    if not cantrace_time:
        status = 'FAIL'
    elif not ai_time:
        status = 'WARNING'
    else:
        status = 'PASS' if matched else 'FAIL'
    return {
        'signal_name': str(signal.get('name') or ''),
        'ai_time': ai_time,
        'cantrace_time': cantrace_time,
        'from': str(signal.get('from') or ''),
        'to': str(signal.get('to') or ''),
        'matched': matched,
        'status': status,
    }


def _build_chart_payload(signals: list[dict]) -> dict:
    return {
        'series': [
            {
                'name': str(signal.get('name') or ''),
                'points': [
                    {
                        'at': str(signal.get('at') or ''),
                        'from': str(signal.get('from') or ''),
                        'to': str(signal.get('to') or ''),
                    }
                ],
            }
            for signal in signals
        ]
    }
