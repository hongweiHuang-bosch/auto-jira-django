from __future__ import annotations

import os
from concurrent.futures import Future, ThreadPoolExecutor

from .analysis_runner import AnalysisRunner

_max_workers = int(os.getenv('ANALYSIS_MAX_WORKERS', '4'))
_executor = ThreadPoolExecutor(max_workers=max(1, _max_workers), thread_name_prefix='analysis-task')


def submit_analysis_task(task_id: int) -> Future:
    runner = AnalysisRunner(task_id)
    return _executor.submit(runner.run)
