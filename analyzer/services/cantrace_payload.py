import json
import logging
import re

logger = logging.getLogger('jira_analyzer_worker')

CANTRACE_LINE_PATTERN = re.compile(
    r'^(?P<name>.+?)值为\s*(?P<to>\S+).*?从时间\s*(?:\d{4}-\d{2}-\d{2}\s+)?(?P<at>\d{2}:\d{2}:\d{2})'
)


def parse_cantrace_summary(text: str) -> list[dict]:
    if not text:
        logger.warning('parse_cantrace_summary received empty text')
        return []

    signals = []
    for line in (text or '').splitlines():
        match = CANTRACE_LINE_PATTERN.search(line.strip())
        if not match:
            continue
        signals.append({
            'name': match.group('name').strip(),
            'at': match.group('at'),
            'from': '',
            'to': match.group('to').strip(),
        })
    if signals:
        logger.info('parse_cantrace_summary parsed %s signals', len(signals))
    else:
        logger.warning('parse_cantrace_summary parsed no signals from text preview=%r', text[:200])
    return signals


def build_raw_signals_json(cantrace_summary: str) -> str:
    signals = parse_cantrace_summary(cantrace_summary)
    if not signals:
        logger.warning('build_raw_signals_json skipped because no structured signals were parsed')
        return ''
    payload = json.dumps({'signals': signals}, ensure_ascii=False)
    logger.info('build_raw_signals_json generated payload for %s signals', len(signals))
    return payload
