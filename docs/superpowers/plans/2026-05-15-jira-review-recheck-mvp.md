# Jira 详情页复核功能 MVP 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 在单票详情页增加一个最小可落地的复核闸门：复核失败后禁止 Jira 回填，只有人工修改并保存 `reply_text` 后才允许回填；失败样本自动沉淀为固定 3 条 few-shot 示例。

**架构：** 后端在 `IssueProcessResult` 上增加复核状态和错例样本表，通过一个新的复核接口写入状态，并在现有 Jira 回填接口上做闸门校验。前端不新增复杂页面，只在现有 [ProcessedIssueDetail.vue](/home/huo2wx/project/python/django/basic/jira-analyzer-web/src/views/GroupDetail/ProcessedIssueDetail.vue) 中增加复核状态、复核按钮和回填按钮状态控制。

**技术栈：** Django 5、Django REST Framework、Vue 3、现有 `node` 脚本式前端状态测试、现有 `Qwen3-32B-FP16` 调用链。

---

## 0. 范围和假设

本计划按最新确认的业务规则执行：

- 复核失败后，Jira 回填不可继续。
- 用户手动修改并保存 `reply_text` 后，允许直接回填 Jira。
- 这次 MVP **不要求人工保存后再次复核**。
- few-shot 样本固定取 3 条，优先按 `role_index` 过滤。
- 不做样本管理后台，不做向量检索，不新增独立“复核上下文预览”接口。

如果后续决定“人工保存后必须重新复核”，需要另起一个增量计划；不要在本计划中偷偷加入这条规则。

## 1. 文件结构

**后端**

- 修改：`django_jira_analyzer/analyzer/models.py`
  - 给 `IssueProcessResult` 增加复核状态字段。
  - 新增 `IssueReviewSample` 轻量错例样本表。
- 创建：`django_jira_analyzer/analyzer/migrations/0004_issueprocessresult_review_fields_and_reviewsample.py`
  - 持久化新增字段和新表。
- 修改：`django_jira_analyzer/analyzer/serializers.py`
  - 让详情接口直接携带复核字段。
- 创建：`django_jira_analyzer/analyzer/services/issue_review_service.py`
  - 负责组装复核 prompt、挑选 3 条样本、调用 AI、写入复核结果。
- 修改：`django_jira_analyzer/legacy_core/config_map.py`
  - 增加复核 prompt 模板常量。
- 修改：`django_jira_analyzer/analyzer/views.py`
  - 新增复核接口。
  - 修改保存回复接口：人工保存后清空失败复核态并重新放行回填。
  - 修改 Jira 回填接口：只允许 `PASS` 或“失败后已人工保存”的结果继续回填。
- 修改：`django_jira_analyzer/analyzer/urls.py`
  - 增加复核路由。
- 修改：`django_jira_analyzer/analyzer/tests/test_issue_process_api.py`
  - 覆盖复核、保存、回填闸门行为。
- 修改：`django_jira_analyzer/analyzer/tests/test_rule_group_payload.py`
  - 确认详情 payload 暴露复核字段。

**前端**

- 修改：`jira-analyzer-web/src/network/filterTasks.js`
  - 新增 `reviewProcessedIssue`。
- 修改：`jira-analyzer-web/src/network/results.js`
  - 复用现有保存 / 回填接口，不改 URL。
- 创建：`jira-analyzer-web/src/utils/processedIssueReviewState.mjs`
  - 把按钮启用规则做成纯函数，方便脚本测试。
- 创建：`jira-analyzer-web/scripts/processedIssueReviewState.spec.mjs`
  - 纯状态测试，验证最小交互规则。
- 修改：`jira-analyzer-web/src/views/GroupDetail/ProcessedIssueDetail.vue`
  - 增加复核状态展示、复核按钮、回填按钮状态和错误提示。

## 2. 任务 1：后端复核状态模型与迁移

**文件：**

- 修改：`django_jira_analyzer/analyzer/models.py`
- 创建：`django_jira_analyzer/analyzer/migrations/0004_issueprocessresult_review_fields_and_reviewsample.py`
- 测试：`django_jira_analyzer/analyzer/tests/test_issue_process_api.py`

- [ ] **步骤 1：在 API 测试里先写出复核字段的失败用例**

```python
def test_processed_issue_detail_includes_review_fields(self):
    process_task = IssueProcessTask.objects.create(
        filter_task=self.filter_task,
        snapshot=self.snapshot,
        issue_key=self.snapshot.issue_key,
        summary=self.snapshot.summary,
        status='SUCCESS',
    )
    IssueProcessResult.objects.create(
        process_task=process_task,
        issue_key=self.snapshot.issue_key,
        summary=self.snapshot.summary,
        reply_text='分析结论',
    )

    response = self.client.get(
        f'/api/rule-groups/{self.filter_task.role_index}/processed-issues/{self.snapshot.issue_key}/'
    )

    self.assertEqual(response.status_code, 200)
    latest = response.data['records'][0]['result']
    self.assertEqual(latest['review_status'], 'PENDING')
    self.assertEqual(latest['review_reason'], '')
    self.assertEqual(latest['manual_override_after_review'], False)
```

- [ ] **步骤 2：运行单测确认当前字段不存在**

运行：`python manage.py test analyzer.tests.test_issue_process_api.IssueProcessApiTests.test_processed_issue_detail_includes_review_fields -v 2`

预期：`FAIL`，报 `KeyError: 'review_status'` 或 serializer 缺字段。

- [ ] **步骤 3：在模型中增加最小状态字段，并创建错例样本表**

```python
class IssueProcessResult(models.Model):
    REVIEW_STATUS_CHOICES = [
        ('PENDING', 'PENDING'),
        ('PASS', 'PASS'),
        ('FAIL', 'FAIL'),
    ]

    review_status = models.CharField(max_length=20, choices=REVIEW_STATUS_CHOICES, default='PENDING')
    review_reason = models.TextField(blank=True, default='')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_model = models.CharField(max_length=100, blank=True, default='')
    manual_override_after_review = models.BooleanField(default=False)


class IssueReviewSample(models.Model):
    role_index = models.PositiveIntegerField(db_index=True)
    issue_key = models.CharField(max_length=64)
    incorrect_conclusion = models.TextField()
    correct_conclusion = models.TextField()
    error_reason = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at', '-id']
```

```python
class IssueProcessResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = IssueProcessResult
        fields = '__all__'
```

- [ ] **步骤 4：写迁移文件**

```python
class Migration(migrations.Migration):
    dependencies = [
        ('analyzer', '0003_filteredissuesnapshot_filtertask_issueprocesstask_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='issueprocessresult',
            name='review_status',
            field=models.CharField(
                choices=[('PENDING', 'PENDING'), ('PASS', 'PASS'), ('FAIL', 'FAIL')],
                default='PENDING',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='issueprocessresult',
            name='review_reason',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='issueprocessresult',
            name='reviewed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='issueprocessresult',
            name='review_model',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='issueprocessresult',
            name='manual_override_after_review',
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name='IssueReviewSample',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role_index', models.PositiveIntegerField(db_index=True)),
                ('issue_key', models.CharField(max_length=64)),
                ('incorrect_conclusion', models.TextField()),
                ('correct_conclusion', models.TextField()),
                ('error_reason', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ['-updated_at', '-id']},
        ),
    ]
```

- [ ] **步骤 5：运行单测验证字段已透出**

运行：`python manage.py test analyzer.tests.test_issue_process_api.IssueProcessApiTests.test_processed_issue_detail_includes_review_fields -v 2`

预期：`PASS`

- [ ] **步骤 6：Commit**

```bash
git -C /home/huo2wx/project/python/django/basic/django_jira_analyzer add analyzer/models.py analyzer/serializers.py analyzer/migrations/0004_issueprocessresult_review_fields_and_reviewsample.py analyzer/tests/test_issue_process_api.py
git -C /home/huo2wx/project/python/django/basic/django_jira_analyzer commit -m "feat: add issue review result fields"
```

## 3. 任务 2：后端复核接口与错例样本沉淀

**文件：**

- 创建：`django_jira_analyzer/analyzer/services/issue_review_service.py`
- 修改：`django_jira_analyzer/legacy_core/config_map.py`
- 修改：`django_jira_analyzer/analyzer/views.py`
- 修改：`django_jira_analyzer/analyzer/urls.py`
- 测试：`django_jira_analyzer/analyzer/tests/test_issue_process_api.py`

- [ ] **步骤 1：先写 3 个失败测试，锁定复核行为**

```python
@patch('analyzer.views.review_issue_result')
def test_review_endpoint_marks_result_pass(self, mock_review_issue_result):
    mock_review_issue_result.return_value = {
        'review_status': 'PASS',
        'review_reason': '结论一致',
        'few_shot_count': 3,
        'review_model': 'Qwen3-32B-FP16',
    }
    result = self._create_process_result(reply_text='分析结论')

    response = self.client.post(f'/api/process-results/{result.id}/review/', {}, format='json')

    self.assertEqual(response.status_code, 200)
    result.refresh_from_db()
    self.assertEqual(result.review_status, 'PASS')
    self.assertFalse(result.manual_override_after_review)
```

```python
@patch('analyzer.views.review_issue_result')
def test_review_endpoint_marks_result_fail_and_creates_sample(self, mock_review_issue_result):
    mock_review_issue_result.return_value = {
        'review_status': 'FAIL',
        'review_reason': '评论与结论冲突',
        'few_shot_count': 2,
        'review_model': 'Qwen3-32B-FP16',
        'correct_conclusion': '建议人工检查 FLZCU 反馈链路',
    }
    result = self._create_process_result(reply_text='错误结论')

    response = self.client.post(f'/api/process-results/{result.id}/review/', {}, format='json')

    self.assertEqual(response.status_code, 200)
    result.refresh_from_db()
    self.assertEqual(result.review_status, 'FAIL')
    self.assertEqual(IssueReviewSample.objects.count(), 1)
```

```python
@patch('analyzer.views.review_issue_result')
def test_review_endpoint_uses_at_most_three_samples(self, mock_review_issue_result):
    for index in range(5):
        IssueReviewSample.objects.create(
            role_index=self.filter_task.role_index,
            issue_key=f'CHER-{index}',
            incorrect_conclusion=f'错误结论 {index}',
            correct_conclusion=f'正确结论 {index}',
            error_reason='历史错例',
        )
    result = self._create_process_result(reply_text='待复核结论')

    self.client.post(f'/api/process-results/{result.id}/review/', {}, format='json')

    args, _ = mock_review_issue_result.call_args
    self.assertEqual(len(args[1]), 3)
```

- [ ] **步骤 2：运行复核测试确认缺路由 / 缺实现**

运行：`python manage.py test analyzer.tests.test_issue_process_api.IssueProcessApiTests.test_review_endpoint_marks_result_pass analyzer.tests.test_issue_process_api.IssueProcessApiTests.test_review_endpoint_marks_result_fail_and_creates_sample analyzer.tests.test_issue_process_api.IssueProcessApiTests.test_review_endpoint_uses_at_most_three_samples -v 2`

预期：`FAIL`，报 `404` 或 `ImportError: review_issue_result`.

- [ ] **步骤 3：加复核 prompt 常量和服务函数**

```python
# legacy_core/config_map.py
ISSUE_REVIEW_SYSTEM = """
你将收到 Jira 评论、信号摘要、QNX/Android 日志摘要、CAN Trace 解析结果、当前模型结论，以及 3 条历史错例。
请判断当前结论是否可信。
如果可信，输出 JSON: {"review_status":"PASS","review_reason":"..."}
如果不可信，输出 JSON: {"review_status":"FAIL","review_reason":"...","correct_conclusion":"..."}
"""
```

```python
# analyzer/services/issue_review_service.py
def review_issue_result(result: IssueProcessResult, samples: list[IssueReviewSample]) -> dict:
    cfg = load_config('config.yaml')
    ai = AIClient(
        base_url=cfg['ai']['base_url'],
        api_key=cfg['ai']['api_key'],
        model=cfg['ai'].get('model', 'Qwen3-32B-FP16'),
    )
    prompt = ISSUE_REVIEW_SYSTEM.format(
        jira_comments=_load_jira_comments(result.issue_key),
        raw_signals=result.raw_signals or '',
        reply_text=result.reply_text or '',
        few_shot_examples=_format_review_samples(samples),
    )
    payload = safe_parse_json(ai.ask(prompt))
    return {
        'review_status': payload['review_status'],
        'review_reason': payload.get('review_reason', ''),
        'correct_conclusion': payload.get('correct_conclusion', ''),
        'few_shot_count': len(samples),
        'review_model': ai.model,
    }
```

- [ ] **步骤 4：加复核接口和路由**

```python
class IssueProcessResultReviewView(APIView):
    def post(self, request, pk: int):
        result = get_object_or_404(IssueProcessResult, pk=pk)
        process_task = result.process_task
        samples = list(
            IssueReviewSample.objects.filter(role_index=process_task.filter_task.role_index)
            .order_by('-updated_at', '-id')[:3]
        )
        review = review_issue_result(result, samples)

        result.review_status = review['review_status']
        result.review_reason = review['review_reason']
        result.review_model = review['review_model']
        result.reviewed_at = timezone.now()
        result.manual_override_after_review = False
        result.save(update_fields=[
            'review_status', 'review_reason', 'review_model',
            'reviewed_at', 'manual_override_after_review', 'updated_at',
        ])

        if review['review_status'] == 'FAIL':
            IssueReviewSample.objects.create(
                role_index=process_task.filter_task.role_index,
                issue_key=result.issue_key,
                incorrect_conclusion=result.reply_text,
                correct_conclusion=review.get('correct_conclusion', ''),
                error_reason=review['review_reason'],
            )

        return Response(review)
```

```python
path('process-results/<int:pk>/review/', IssueProcessResultReviewView.as_view(), name='issue-process-result-review'),
```

- [ ] **步骤 5：运行复核测试验证通过**

运行：`python manage.py test analyzer.tests.test_issue_process_api.IssueProcessApiTests.test_review_endpoint_marks_result_pass analyzer.tests.test_issue_process_api.IssueProcessApiTests.test_review_endpoint_marks_result_fail_and_creates_sample analyzer.tests.test_issue_process_api.IssueProcessApiTests.test_review_endpoint_uses_at_most_three_samples -v 2`

预期：`PASS`

- [ ] **步骤 6：Commit**

```bash
git -C /home/huo2wx/project/python/django/basic/django_jira_analyzer add analyzer/services/issue_review_service.py legacy_core/config_map.py analyzer/views.py analyzer/urls.py analyzer/tests/test_issue_process_api.py
git -C /home/huo2wx/project/python/django/basic/django_jira_analyzer commit -m "feat: add process result review endpoint"
```

## 4. 任务 3：保存回复与 Jira 回填闸门

**文件：**

- 修改：`django_jira_analyzer/analyzer/views.py`
- 测试：`django_jira_analyzer/analyzer/tests/test_issue_process_api.py`

- [ ] **步骤 1：先写回填闸门测试**

```python
def test_comment_requires_review_pass_or_manual_save_after_fail(self):
    result = self._create_process_result(reply_text='原结论')
    result.review_status = 'FAIL'
    result.review_reason = '模型判断不可靠'
    result.save(update_fields=['review_status', 'review_reason', 'updated_at'])

    blocked = self.client.post(f'/api/process-results/{result.id}/comment/')
    self.assertEqual(blocked.status_code, 409)

    self.client.patch(
        f'/api/process-results/{result.id}/',
        {'reply_text': '人工修正后的结论'},
        format='json',
    )

    with patch('analyzer.views.load_config') as mock_load_config, patch('analyzer.views.JiraClient'):
        mock_load_config.return_value = {
            'jira': {'server': 'http://jira.example.com', 'username': 'tester', 'password': 'secret'}
        }
        allowed = self.client.post(f'/api/process-results/{result.id}/comment/')

    self.assertEqual(allowed.status_code, 200)
```

```python
def test_save_reply_after_fail_sets_manual_override_flag(self):
    result = self._create_process_result(reply_text='原结论')
    result.review_status = 'FAIL'
    result.save(update_fields=['review_status', 'updated_at'])

    response = self.client.patch(
        f'/api/process-results/{result.id}/',
        {'reply_text': '人工修正后的结论'},
        format='json',
    )

    self.assertEqual(response.status_code, 200)
    result.refresh_from_db()
    self.assertEqual(result.review_status, 'PENDING')
    self.assertTrue(result.manual_override_after_review)
```

- [ ] **步骤 2：运行闸门测试确认当前会误放行**

运行：`python manage.py test analyzer.tests.test_issue_process_api.IssueProcessApiTests.test_comment_requires_review_pass_or_manual_save_after_fail analyzer.tests.test_issue_process_api.IssueProcessApiTests.test_save_reply_after_fail_sets_manual_override_flag -v 2`

预期：`FAIL`，当前 `comment/` 会直接成功，`PATCH` 不会清理复核态。

- [ ] **步骤 3：实现保存和回填的最小状态机**

```python
class IssueProcessResultUpdateView(APIView):
    def patch(self, request, pk: int):
        result = get_object_or_404(IssueProcessResult, pk=pk)
        reply_text = request.data.get('reply_text')
        if not isinstance(reply_text, str):
            return Response({'detail': 'reply_text 必须是字符串'}, status=status.HTTP_400_BAD_REQUEST)

        edited_after_fail = result.review_status == 'FAIL' and reply_text != result.reply_text
        result.reply_text = reply_text
        if edited_after_fail:
            result.review_status = 'PENDING'
            result.review_reason = ''
            result.manual_override_after_review = True
        result.save(update_fields=['reply_text', 'review_status', 'review_reason', 'manual_override_after_review', 'updated_at'])
        publish_rule_group_snapshot()
        return Response(IssueProcessResultSerializer(result).data)
```

```python
class IssueProcessResultCommentView(APIView):
    def post(self, request, pk: int):
        result = get_object_or_404(IssueProcessResult, pk=pk)
        if result.has_commented_to_jira:
            return Response({'detail': '该结果已回填 Jira'}, status=status.HTTP_200_OK)
        if result.review_status == 'FAIL' and not result.manual_override_after_review:
            return Response({'detail': '复核失败，请先人工修改分析结果并保存'}, status=status.HTTP_409_CONFLICT)
        if result.review_status == 'PENDING' and not result.manual_override_after_review:
            return Response({'detail': '请先完成复核'}, status=status.HTTP_409_CONFLICT)
        # 原有 Jira comment 逻辑保持不变
```

- [ ] **步骤 4：运行闸门测试验证通过**

运行：`python manage.py test analyzer.tests.test_issue_process_api.IssueProcessApiTests.test_comment_requires_review_pass_or_manual_save_after_fail analyzer.tests.test_issue_process_api.IssueProcessApiTests.test_save_reply_after_fail_sets_manual_override_flag -v 2`

预期：`PASS`

- [ ] **步骤 5：Commit**

```bash
git -C /home/huo2wx/project/python/django/basic/django_jira_analyzer add analyzer/views.py analyzer/tests/test_issue_process_api.py
git -C /home/huo2wx/project/python/django/basic/django_jira_analyzer commit -m "feat: gate jira comment by review status"
```

## 5. 任务 4：详情 payload 与前端状态控制

**文件：**

- 修改：`django_jira_analyzer/analyzer/tests/test_rule_group_payload.py`
- 修改：`jira-analyzer-web/src/network/filterTasks.js`
- 创建：`jira-analyzer-web/src/utils/processedIssueReviewState.mjs`
- 创建：`jira-analyzer-web/scripts/processedIssueReviewState.spec.mjs`
- 修改：`jira-analyzer-web/src/views/GroupDetail/ProcessedIssueDetail.vue`

- [ ] **步骤 1：先写后端 payload 测试，要求详情页能拿到复核字段**

```python
def test_build_processed_issue_detail_exposes_review_fields(self):
    process_task = IssueProcessTask.objects.create(
        filter_task=self.filter_task,
        snapshot=self.snapshot,
        issue_key=self.snapshot.issue_key,
        summary=self.snapshot.summary,
        status='SUCCESS',
    )
    IssueProcessResult.objects.create(
        process_task=process_task,
        issue_key=self.snapshot.issue_key,
        summary=self.snapshot.summary,
        reply_text='处理正文',
        review_status='FAIL',
        review_reason='评论与结论冲突',
        manual_override_after_review=False,
    )

    payload = build_processed_issue_detail(role_index=0, issue_key='CHER-500')

    self.assertEqual(payload['records'][0]['result']['review_status'], 'FAIL')
    self.assertEqual(payload['records'][0]['result']['review_reason'], '评论与结论冲突')
```

- [ ] **步骤 2：写前端状态纯函数测试**

```javascript
assert.deepEqual(
  buildProcessedIssueReviewState({
    reviewStatus: 'FAIL',
    manualOverrideAfterReview: false,
    submittingReview: false,
    savingReply: false,
    commenting: false,
  }),
  {
    reviewLabel: '模型分析出现问题，建议手动分析',
    canReview: true,
    canComment: false,
    commentLabel: '请先人工修改并保存',
  }
);

assert.deepEqual(
  buildProcessedIssueReviewState({
    reviewStatus: 'PENDING',
    manualOverrideAfterReview: true,
    submittingReview: false,
    savingReply: false,
    commenting: false,
  }),
  {
    reviewLabel: '已人工修改，允许回填',
    canReview: true,
    canComment: true,
    commentLabel: '回填 Jira',
  }
);
```

- [ ] **步骤 3：运行测试确认前端状态文件尚不存在**

运行：`node jira-analyzer-web/scripts/processedIssueReviewState.spec.mjs`

预期：`FAIL`，报 `Cannot find module '../src/utils/processedIssueReviewState.mjs'`。

- [ ] **步骤 4：补网络层与状态纯函数**

```javascript
// src/network/filterTasks.js
export function reviewProcessedIssue(resultId) {
  return request({
    url: `/api/process-results/${resultId}/review/`,
    method: 'POST',
  });
}
```

```javascript
// src/utils/processedIssueReviewState.mjs
export function buildProcessedIssueReviewState({
  reviewStatus,
  manualOverrideAfterReview,
  submittingReview,
  savingReply,
  commenting,
}) {
  if (submittingReview) {
    return { reviewLabel: '复核中...', canReview: false, canComment: false, commentLabel: '处理中...' };
  }
  if (commenting) {
    return { reviewLabel: '准备回填', canReview: false, canComment: false, commentLabel: '回填中...' };
  }
  if (reviewStatus === 'PASS') {
    return { reviewLabel: '复核正确', canReview: true, canComment: true, commentLabel: '回填 Jira' };
  }
  if (reviewStatus === 'FAIL' && !manualOverrideAfterReview) {
    return { reviewLabel: '模型分析出现问题，建议手动分析', canReview: true, canComment: false, commentLabel: '请先人工修改并保存' };
  }
  if (manualOverrideAfterReview) {
    return { reviewLabel: '已人工修改，允许回填', canReview: true, canComment: true, commentLabel: '回填 Jira' };
  }
  return { reviewLabel: '未复核', canReview: true, canComment: false, commentLabel: '请先复核' };
}
```

- [ ] **步骤 5：在详情页接入复核和回填状态**

```vue
<section v-if="latestResult" class="review-panel">
  <div class="review-status">{{ reviewState.reviewLabel }}</div>
  <p v-if="latestResult.review_reason" class="review-reason">{{ latestResult.review_reason }}</p>
  <div class="review-actions">
    <button :disabled="!reviewState.canReview" @click="reviewLatestResult">复核</button>
    <button :disabled="!reviewState.canComment" @click="commentLatestResult">
      {{ reviewState.commentLabel }}
    </button>
  </div>
</section>
```

```javascript
const latestResult = computed(() => latestRecord.value && latestRecord.value.result);

const reviewState = computed(() => buildProcessedIssueReviewState({
  reviewStatus: latestResult.value?.review_status || 'PENDING',
  manualOverrideAfterReview: !!latestResult.value?.manual_override_after_review,
  submittingReview: reviewSubmitting.value,
  savingReply: false,
  commenting: commentSubmitting.value,
}));
```

- [ ] **步骤 6：运行前端状态测试和后端 payload 测试**

运行：`python manage.py test analyzer.tests.test_rule_group_payload.RuleGroupPayloadTests.test_build_processed_issue_detail_exposes_review_fields -v 2`

预期：`PASS`

运行：`node jira-analyzer-web/scripts/processedIssueReviewState.spec.mjs`

预期：输出 `processedIssueReviewState ok`

- [ ] **步骤 7：Commit**

```bash
git -C /home/huo2wx/project/python/django/basic/django_jira_analyzer add analyzer/tests/test_rule_group_payload.py
git -C /home/huo2wx/project/python/django/basic/jira-analyzer-web add src/network/filterTasks.js src/utils/processedIssueReviewState.mjs scripts/processedIssueReviewState.spec.mjs src/views/GroupDetail/ProcessedIssueDetail.vue
git -C /home/huo2wx/project/python/django/basic/django_jira_analyzer commit -m "test: expose review fields in processed issue detail"
git -C /home/huo2wx/project/python/django/basic/jira-analyzer-web commit -m "feat: add processed issue review controls"
```

## 6. 任务 5：最小回归验证

**文件：**

- 测试：`django_jira_analyzer/analyzer/tests/test_issue_process_api.py`
- 测试：`django_jira_analyzer/analyzer/tests/test_rule_group_payload.py`
- 测试：`jira-analyzer-web/scripts/processedIssueReviewState.spec.mjs`
- 测试：`jira-analyzer-web/scripts/jiraIssuePanelState.spec.mjs`
- 测试：`jira-analyzer-web/scripts/processedIssueHistory.spec.mjs`

- [ ] **步骤 1：跑后端复核相关测试**

运行：`python manage.py test analyzer.tests.test_issue_process_api analyzer.tests.test_rule_group_payload -v 2`

预期：`PASS`

- [ ] **步骤 2：跑前端脚本测试**

运行：`node jira-analyzer-web/scripts/processedIssueReviewState.spec.mjs`

预期：输出 `processedIssueReviewState ok`

运行：`node jira-analyzer-web/scripts/jiraIssuePanelState.spec.mjs`

预期：输出 `jiraIssuePanelState ok`

运行：`node jira-analyzer-web/scripts/processedIssueHistory.spec.mjs`

预期：输出 `processedIssueHistory ok`

- [ ] **步骤 3：跑前端构建验证**

运行：`npm run build`

工作目录：`/home/huo2wx/project/python/django/basic/jira-analyzer-web`

预期：构建成功；若仅出现 bundle size warning，记录但不阻断。

- [ ] **步骤 4：人工验收清单**

1. 打开单票详情页。
2. 看到 `未复核` 状态，`回填 Jira` 按钮不可点。
3. 点击 `复核`，若返回 `PASS`，`回填 Jira` 按钮变可点。
4. 若返回 `FAIL`，页面显示“模型分析出现问题，建议手动分析”，`回填 Jira` 不可点。
5. 手工修改 `reply_text` 并保存后，状态变为“已人工修改，允许回填”，`回填 Jira` 按钮变可点。
6. 点击回填后，Jira comment 成功写入，`has_commented_to_jira` 变为 `true`。

## 7. 自检

### 7.1 规格覆盖

- 复核入口：任务 2、任务 4 覆盖。
- 失败样本持久化：任务 1、任务 2 覆盖。
- 固定 3 条 few-shot：任务 2 覆盖。
- 失败后禁止回填：任务 3 覆盖。
- 人工修改并保存后恢复回填：任务 3、任务 4 覆盖。
- 最小前端展示：任务 4 覆盖。

### 7.2 占位符扫描

- 没有使用“TODO”“后续实现”“适当处理”等占位语。
- 每个测试步骤都有命令和预期。
- 每个代码步骤都给了明确的新增字段、函数或分支。

### 7.3 类型一致性

- `review_status` 在模型、serializer、测试、前端状态机中统一使用。
- `manual_override_after_review` 在保存接口、回填接口、前端状态机中统一使用。
- 本计划只使用 `process-results/<pk>/review/` 这一条新路由，没有引入第二套复核接口路径。
