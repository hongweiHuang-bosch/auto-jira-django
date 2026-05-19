import json
from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import TestCase, override_settings
from django.utils import timezone

from analyzer.models import FilterTask, IssueLearningMemory
from analyzer.services.learning_memory_service import (
    build_learning_memories_for_prompt,
    retrieve_learning_memories,
)


class LearningMemoryServiceTests(TestCase):
    def setUp(self):
        self.filter_task = FilterTask.objects.create(
            role_index=1,
            role_label='规则组 2',
            jql='project = GEELY',
            status='SUCCESS',
            expires_at=timezone.now(),
        )

    def _write_memory(self, root, *, issue_key, signal_summary, error_reason, correct_conclusion, review_status='FAIL'):
        payload = {
            'role_index': self.filter_task.role_index,
            'issue_key': issue_key,
            'requirements': '',
            'comment': '',
            'signal_summary': signal_summary,
            'qnx_android_logs': '',
            'cantrace_output': '',
            'incorrect_conclusion': f'{issue_key} 错误结论',
            'error_reason': error_reason,
            'correct_result': correct_conclusion,
            'review_status': review_status,
            'created_at': '2026-05-18T00:00:00+08:00',
            'updated_at': '2026-05-18T00:00:00+08:00',
        }
        role_dir = Path(root) / f'role_{self.filter_task.role_index}'
        role_dir.mkdir(parents=True, exist_ok=True)
        file_path = role_dir / f'{issue_key}.json'
        file_path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True), encoding='utf-8')
        return IssueLearningMemory.objects.create(
            role_index=self.filter_task.role_index,
            issue_key=issue_key,
            review_status=review_status,
            incorrect_conclusion=payload['incorrect_conclusion'],
            correct_conclusion=correct_conclusion,
            error_reason=error_reason,
            signal_summary=signal_summary,
            memory_file_path=str(file_path),
            memory_content_hash=f'hash-{issue_key}',
        )

    def test_retrieve_learning_memories_prefers_related_cases_and_limits_count(self):
        with TemporaryDirectory() as temp_dir:
            with override_settings(LEARNING_MEMORY_ROOT=temp_dir):
                self._write_memory(
                    temp_dir,
                    issue_key='CASE-1',
                    signal_summary='SIG_A SIG_B',
                    error_reason='忽略了 SIG_A 变化',
                    correct_conclusion='确认 SIG_A 链路',
                )
                self._write_memory(
                    temp_dir,
                    issue_key='CASE-2',
                    signal_summary='SIG_A only',
                    error_reason='漏看 SIG_A',
                    correct_conclusion='继续分析 SIG_A',
                )
                self._write_memory(
                    temp_dir,
                    issue_key='CASE-3',
                    signal_summary='SIG_B only',
                    error_reason='漏看 SIG_B',
                    correct_conclusion='继续分析 SIG_B',
                )
                self._write_memory(
                    temp_dir,
                    issue_key='CASE-4',
                    signal_summary='UNRELATED',
                    error_reason='无关案例',
                    correct_conclusion='无关结论',
                )

                memories = retrieve_learning_memories(
                    role_index=self.filter_task.role_index,
                    summary='问题涉及 SIG_A',
                    comment='评论提到 SIG_A 和 Bosch',
                    requirements='需求关注 SIG_A 和 SIG_B',
                    signal_summary='SIG_A',
                    max_count=3,
                )

        self.assertEqual(len(memories), 3)
        self.assertEqual(memories[0]['issue_key'], 'CASE-1')
        self.assertEqual(
            {item['issue_key'] for item in memories[1:]},
            {'CASE-2', 'CASE-3'},
        )
        self.assertNotIn('CASE-4', [item['issue_key'] for item in memories])

    def test_retrieve_learning_memories_skips_missing_or_broken_files(self):
        with TemporaryDirectory() as temp_dir:
            with override_settings(LEARNING_MEMORY_ROOT=temp_dir):
                missing_path = Path(temp_dir) / 'role_1' / 'missing.json'
                missing_path.parent.mkdir(parents=True, exist_ok=True)
                IssueLearningMemory.objects.create(
                    role_index=self.filter_task.role_index,
                    issue_key='CASE-MISSING',
                    review_status='FAIL',
                    incorrect_conclusion='错误',
                    correct_conclusion='正确',
                    error_reason='原因',
                    signal_summary='SIG_A',
                    memory_file_path=str(missing_path),
                    memory_content_hash='hash-missing',
                )
                broken = self._write_memory(
                    temp_dir,
                    issue_key='CASE-BROKEN',
                    signal_summary='SIG_A',
                    error_reason='损坏',
                    correct_conclusion='损坏结论',
                )
                Path(broken.memory_file_path).write_text('{bad json', encoding='utf-8')
                healthy = self._write_memory(
                    temp_dir,
                    issue_key='CASE-OK',
                    signal_summary='SIG_A',
                    error_reason='有效案例',
                    correct_conclusion='有效结论',
                )

                memories = retrieve_learning_memories(
                    role_index=self.filter_task.role_index,
                    summary='SIG_A',
                    comment='SIG_A',
                    requirements='SIG_A',
                    signal_summary='SIG_A',
                    max_count=3,
                )

                prompt_block = build_learning_memories_for_prompt(memories)

        self.assertEqual([item['issue_key'] for item in memories], [healthy.issue_key])
        self.assertIn('错误结论', prompt_block)
        self.assertIn('正确结论', prompt_block)
