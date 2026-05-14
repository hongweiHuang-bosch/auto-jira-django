EXTRACT_RELATED_SIGNALS_PROMPT = (
    '请从下面的 Jira 评论中提取与 Bosch 相关的信号、prop id 或关键词。'
    '若无法提取，输出"无法提取"。\n\n{comments}'
)

EXTRACT_UPPER_REQUIREMENTS_PROMPT = (
    '请从下面的 Jira 评论中提取上层希望 Bosch 侧确认的需求，直接输出一段简洁中文摘要。\n\n{comments}'
)

FINAL_ANALYSIS_PROMPT = (
    '你将收到上层需求摘要和按 cycle 分组的 Bosch 日志，请输出一个 JSON 对象，字段为 '
    'analysis_summary、reply_text、confidence、risk_notes。\n\n'
    '需求摘要：{requirements}\n\n日志：{grouped_logs}'
)
