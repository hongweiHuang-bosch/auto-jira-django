from __future__ import annotations

from legacy_core.jira_utils import JiraClient
from legacy_core.utils import load_config


def build_jira_url(issue_key: str) -> str:
    try:
        cfg = load_config('config.yaml')
    except Exception:
        return ''
    server = cfg.get('jira', {}).get('server', '').rstrip('/')
    return f'{server}/browse/{issue_key}' if server else ''


def _build_jira_client():
    cfg = load_config('config.yaml')
    jira_cfg = cfg['jira']
    return JiraClient(
        server=jira_cfg['server'],
        username=jira_cfg['username'],
        password=jira_cfg['password'],
        use_system_proxy=jira_cfg.get('use_system_proxy', True),
        proxies=jira_cfg.get('proxies'),
    )


def _serialize_user(user):
    if not user:
        return None
    return {
        'account_id': getattr(user, 'accountId', '') or '',
        'name': getattr(user, 'name', '') or '',
        'display_name': getattr(user, 'displayName', '') or '',
    }


def _candidate_key(user):
    return user.get('account_id') or user.get('name') or user.get('display_name')


def _append_candidate(candidates, user):
    if not user:
        return
    key = _candidate_key(user)
    if not key:
        return
    if any(_candidate_key(item) == key for item in candidates):
        return
    candidates.append(user)


def _build_user_candidates(issue, comments):
    fields = getattr(issue, 'fields', None)
    candidates = []
    _append_candidate(candidates, _serialize_user(getattr(fields, 'assignee', None)))
    _append_candidate(candidates, _serialize_user(getattr(fields, 'reporter', None)))
    for comment in comments:
        _append_candidate(candidates, comment.get('author'))
    return candidates


def build_jira_issue_payload(issue_key: str):
    jira = _build_jira_client()
    issue = jira.get_issue(issue_key)
    comments = jira.get_comments(issue_key)
    transitions = jira.get_transitions(issue_key)
    return {
        'issue_key': issue_key,
        'jira_url': build_jira_url(issue_key),
        'comments': comments,
        'transition_candidates': transitions,
        'user_candidates': _build_user_candidates(issue, comments),
    }


def transition_jira_issue(issue_key: str, transition_id: str, target_user: str):
    jira = _build_jira_client()
    jira.assign_issue(issue_key, target_user)
    jira.transition_issue(issue_key, transition_id)
