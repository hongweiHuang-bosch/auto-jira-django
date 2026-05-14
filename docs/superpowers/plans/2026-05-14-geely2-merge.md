# Geely2 前后端功能合并 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 把 worktree `feature/geely2-minimal-backend` 上的 Geely2 + 平台账号能力，最小并入主仓 `feature/filter-snapshot-single-issue`，让前端已有的 `/login`、`/geely2`、`/geely2/results/:id` 三个页面能完整跑通。

**架构：** 通过标准 git merge 在新分支 `feature/integrate-geely2` 上集成 17 个 Geely2 子能力 commit；3 个共享文件（`config/settings.py`、`config/urls.py`、`analyzer/views.py`）经预扫确认零交叠，自动合并通过；新增 2 个 Django app（`platform_accounts`、`geely2_analyzer`）整体落入主仓；通过环境变量提供 Fernet 密钥；运行 `geely2_analyzer` 自带的 7 个测试 + `platform_accounts` 1 个测试做回归；通过前端走完整登录→同步→分析→回填 Jira 流程做端到端验证。

**技术栈：** Django 5、DRF 3.15、Django Session Auth、Fernet 加密（cryptography）、PyMySQL、Vue 3 / Vue Router 4 / Vuex 4 前端、SSE（Server-Sent Events）。

**前置上下文（执行前必读）：**
- 设计规格：`docs/superpowers/specs/2026-05-14-geely2-merge-design.md`（执行前完整阅读）
- 工作目录：`django_jira_analyzer/`（除非另行说明，所有 `git`/`python manage.py` 命令都在此目录执行）
- 当前分支：`feature/filter-snapshot-single-issue`，HEAD `da273d4`，工作区有 2 个未提交文件 + 若干未跟踪文件，本计划不动它们
- worktree 路径：`.worktrees/geely2-minimal-backend/`（验证全部通过后才下线）
- 前端目录：`../jira-analyzer-web/`（本计划不修改前端代码）

**执行约束：**
- 任何步骤"预期输出"不符合时，停下汇报，**不要打补丁式硬干**
- 整个计划完成前不要 push 到远端
- 任务 1～任务 4 完成前，前端验证环节（任务 7、8）会失败，按顺序推进

---

## 任务 1：在新分支上执行 git merge

**文件：**
- 修改：`config/settings.py`（merge 自动合并：新增 `JIRA_CREDENTIAL_ENCRYPTION_KEY`、`INSTALLED_APPS` 追加 2 项、`CSRF_TRUSTED_ORIGINS`、`CORS_ALLOW_CREDENTIALS=True`）
- 修改：`config/urls.py`（merge 自动合并：追加 2 条 `include`）
- 修改：`analyzer/views.py`（merge 自动合并）
- 创建：`platform_accounts/`（整目录从 worktree 分支带入）
- 创建：`geely2_analyzer/`（整目录从 worktree 分支带入，含 `migrations/0001_initial.py`、`management/commands/run_geely2_worker.py`、`services/*.py`、`tests/*.py`）

- [ ] **步骤 1：前置安全检查**

运行：

```bash
cd django_jira_analyzer
git status --short
git branch --show-current
git fetch
```

预期：
- `git status` 显示 `M analyzer/services/issue_process_pipeline.py`、`M legacy_core/pipeline.py` 加若干 `??` 未跟踪条目
- `git branch --show-current` 输出 `feature/filter-snapshot-single-issue`
- `git fetch` 无报错

如果当前不在 `feature/filter-snapshot-single-issue`，停下汇报；不要 `git switch`。

- [ ] **步骤 2：暂存主仓 WIP 文件**

运行：

```bash
git stash push -u -m "wip: pipeline 调试，待合并 geely2 后恢复" \
    analyzer/services/issue_process_pipeline.py \
    legacy_core/pipeline.py
git status --short
```

预期：`git status` 不再列出 `analyzer/services/issue_process_pipeline.py` 与 `legacy_core/pipeline.py`；`?? .worktrees/`、`?? "config——chery/...txt"` 等仍在（未跟踪文件本来就不被 stash）。

如果 stash 报错（例如本地无修改）：跳过此步，进入步骤 3。

- [ ] **步骤 3：创建集成分支**

运行：

```bash
git switch -c feature/integrate-geely2
git branch --show-current
```

预期：输出 `feature/integrate-geely2`。

- [ ] **步骤 4：执行 merge**

运行：

```bash
git merge --no-ff feature/geely2-minimal-backend \
    -m "merge: 集成 Geely2 用户级 Jira 凭据、同步、单票分析"
```

预期：
- 输出包含 `Merge made by the 'ort' strategy.`（或 `'recursive'`）
- 文件统计行至少包含 `30 files changed`、`platform_accounts/...`、`geely2_analyzer/...` 路径

**异常分支：** 如果 git 报告冲突（理论上不应发生），立即运行 `git merge --abort`，停下汇报冲突文件清单（`git status --short` 输出），不要硬解。

- [ ] **步骤 5：验证 merge 体完整性**

运行：

```bash
git ls-files platform_accounts geely2_analyzer | wc -l
ls platform_accounts/urls.py geely2_analyzer/migrations/0001_initial.py geely2_analyzer/management/commands/run_geely2_worker.py
```

预期：
- 第一条命令输出数字 ≥ 25
- 第二条命令三个路径都列出，无 `No such file` 报错

- [ ] **步骤 6：Django 配置自检**

运行：

```bash
python manage.py check
```

预期：输出 `System check identified no issues (0 silenced).`

如果输出 `JIRA_CREDENTIAL_ENCRYPTION_KEY` 相关 `ImproperlyConfigured` 错误：这是任务 2 的事，**此步骤不需要环境变量也应通过**（只是 import 时不会触发 Fernet 构建）；如果真的报错，停下汇报。

- [ ] **步骤 7：检查 migration 完整性**

运行：

```bash
python manage.py makemigrations --dry-run
```

预期：输出 `No changes detected`。如果提示要为 `geely2_analyzer` 或 `platform_accounts` 生成新 migration，说明 worktree 的 `0001_initial.py` 与模型不一致，停下汇报。

- [ ] **步骤 8：恢复主仓 WIP 文件**

运行：

```bash
git stash pop
git status --short
```

预期：
- `git status` 重新显示 `M analyzer/services/issue_process_pipeline.py`、`M legacy_core/pipeline.py`
- 无冲突标记（`UU`、`AA` 等）

如果 pop 报告冲突：停下汇报，**不要** `git checkout --theirs/--ours` 自动解决——这两文件与 Geely2 无路径交集，冲突意味着 stash 之前有意外状态。

如果步骤 2 跳过了 stash，本步骤同样跳过。

- [ ] **步骤 9：确认任务 1 完成态**

运行：

```bash
git log --oneline -3
git status --short
```

预期：
- `git log` 第一行是 merge commit（消息含"集成 Geely2"），第二行是 17 个 geely2 commit 中的最新一个，第三行是 `da273d4 fix connect bug and opt frontend`
- `git status` 显示 `M analyzer/services/issue_process_pipeline.py`、`M legacy_core/pipeline.py`，加上未跟踪文件

**任务 1 不产生新 commit**（除了 merge commit 本身，已在步骤 4 写入）。WIP 文件保持未暂存，按规格 §3.7。

---

## 任务 2：环境变量配置

**文件：**
- 创建：`.env.local`（开发本地用，**不入 git**；生产由部署侧设置）

- [ ] **步骤 1：生成 Fernet 密钥**

运行：

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

预期：输出一行 44 字符的 base64 串，例如 `mRPLK2gvtrQ73iUlN_X8IZ4LfVkDUBYDbV4wV_b0Zz8=`。**复制保存这串值**，下一步要用，且**不能丢**——丢失会导致已加密的 Jira 凭据全部无法解密。

- [ ] **步骤 2：导出环境变量到当前 shell**

运行（把 `<生成出的 base64 串>` 替换成步骤 1 的输出）：

```bash
export JIRA_CREDENTIAL_ENCRYPTION_KEY="<生成出的 base64 串>"
export DJANGO_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(64))')"
echo "JIRA_CREDENTIAL_ENCRYPTION_KEY length: ${#JIRA_CREDENTIAL_ENCRYPTION_KEY}"
echo "DJANGO_SECRET_KEY length: ${#DJANGO_SECRET_KEY}"
```

预期：第一行输出 `JIRA_CREDENTIAL_ENCRYPTION_KEY length: 44`；第二行输出 `DJANGO_SECRET_KEY length: 86`。

- [ ] **步骤 3：可选——写入 .env.local 方便后续 shell 复用**

运行：

```bash
cat > .env.local <<EOF
export JIRA_CREDENTIAL_ENCRYPTION_KEY="${JIRA_CREDENTIAL_ENCRYPTION_KEY}"
export DJANGO_SECRET_KEY="${DJANGO_SECRET_KEY}"
EOF
chmod 600 .env.local
grep -q "^.env.local$" .gitignore || echo ".env.local" >> .gitignore
git status --short .gitignore
```

预期：`.env.local` 创建成功；`.gitignore` 末尾追加一行 `.env.local`，`git status` 显示 `M .gitignore`。

后续新 shell 可用 `source .env.local` 恢复环境。

- [ ] **步骤 4：验证 settings 能正确加载密钥**

运行：

```bash
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from geely2_analyzer.services.credential_crypto import encrypt_secret, decrypt_secret
sample = 'verify-key-roundtrip'
encrypted = encrypt_secret(sample)
decrypted = decrypt_secret(encrypted)
print('encrypted prefix:', encrypted[:7])
print('round-trip ok:', decrypted == sample)
"
```

预期：
- `encrypted prefix: enc::g` 或类似 `enc::` 开头
- `round-trip ok: True`

如果抛 `ImproperlyConfigured`：步骤 2 的 export 没生效，重做。

---

## 任务 3：数据库迁移

**文件：**
- 数据库变更：MySQL `jira_analyzer` 库新增 5 张表（`geely2_analyzer_*`）

- [ ] **步骤 1：确认 MySQL 连接参数**

运行：

```bash
python manage.py dbshell -- -e "SELECT DATABASE(), VERSION();"
```

预期：输出当前数据库名（默认 `jira_analyzer`）和 MySQL 版本。

如果连接失败：检查 `MYSQL_HOST/PORT/USER/PASSWORD/DATABASE` 环境变量，参考 `README.md` "三、准备数据库环境变量"一节，修复后重试。

- [ ] **步骤 2：列出待执行的 migration**

运行：

```bash
python manage.py showmigrations geely2_analyzer
```

预期：输出包含一行 `[ ] 0001_initial`（未应用）。

- [ ] **步骤 3：执行迁移**

运行：

```bash
python manage.py migrate geely2_analyzer
python manage.py migrate
```

预期：
- 第一条命令输出 `Applying geely2_analyzer.0001_initial... OK`
- 第二条命令输出 `No migrations to apply.`（其他 app 都已最新）

- [ ] **步骤 4：验证 5 张新表创建成功**

运行：

```bash
python manage.py dbshell -- -e "SHOW TABLES LIKE 'geely2_analyzer_%';"
```

预期输出包含这 5 行（顺序可能不同）：
```
geely2_analyzer_geely2analysisresult
geely2_analyzer_geely2analysistask
geely2_analyzer_geely2issuesnapshot
geely2_analyzer_geely2synctask
geely2_analyzer_jiracredentialbinding
```

如果只列出部分表：检查 `migrate` 输出是否中途报错，回滚用 `python manage.py migrate geely2_analyzer zero` 然后重做。

---

## 任务 4：创建至少一个 Django 用户

- [ ] **步骤 1：创建超级用户**

运行：

```bash
python manage.py createsuperuser
```

按提示交互输入：
- Username（建议 `admin` 或你的用户名）
- Email（可留空回车）
- Password（输入两次，至少 8 位；当前 `AUTH_PASSWORD_VALIDATORS=[]` 不强制复杂度）

预期：输出 `Superuser created successfully.`

- [ ] **步骤 2：验证用户已落库**

运行：

```bash
python manage.py shell -c "from django.contrib.auth import get_user_model; print(get_user_model().objects.values_list('id', 'username'))"
```

预期：输出形如 `<QuerySet [(1, 'admin')]>`，至少 1 条记录。

---

## 任务 5：后端测试套件回归

**文件：**
- 测试范围：`analyzer/tests/*` 7 个（既有）+ `platform_accounts/tests/*` 1 个（新增）+ `geely2_analyzer/tests/*` 7 个（新增）

- [ ] **步骤 1：跑全量测试**

运行：

```bash
python manage.py test analyzer platform_accounts geely2_analyzer --verbosity=2
```

预期：
- 输出末尾包含 `OK`
- 测试用例总数 ≥ 15（具体数字以实际为准；新增了 8 个测试文件，每个文件至少 1 个用例）
- 不出现 `FAILED`、`ERROR`、`unexpected success`

- [ ] **步骤 2：失败时排查指引**

如果出现失败，按以下顺序排查：

1. **`ImproperlyConfigured: JIRA_CREDENTIAL_ENCRYPTION_KEY ...`** → 任务 2 步骤 2 没在当前 shell 执行；重新 `source .env.local` 或重新 export。

2. **`OperationalError: ... access denied / unknown database`** → 任务 3 步骤 1 的数据库参数没对齐；检查环境变量。

3. **`relation "geely2_analyzer_..." does not exist`** → 任务 3 步骤 3 的 migrate 没执行成功；回到任务 3 重做。

4. **`AssertionError` in `test_credential_api.py`** → 检查 `JIRA_CREDENTIAL_ENCRYPTION_KEY` 是否变化；如果你重做过任务 2，加密的旧值无法用新 key 解密。开发环境可清表重测：`python manage.py migrate geely2_analyzer zero && python manage.py migrate geely2_analyzer`。

5. **其他失败** → 不要修测试源码，停下汇报失败用例名 + 关键报错。

- [ ] **步骤 3：单独跑 geely2 测试做二次确认**

运行：

```bash
python manage.py test geely2_analyzer --verbosity=2
```

预期：所有用例通过；用例总数 ≥ 7。

---

## 任务 6：未登录访问 curl 烟雾测试

**前置：** 任务 5 已通过。

- [ ] **步骤 1：启动 Django Web 进程**

打开**终端 A**，运行：

```bash
source .env.local 2>/dev/null || true
python manage.py runserver 0.0.0.0:8000
```

预期：终端 A 输出 `Starting development server at http://0.0.0.0:8000/`，并保持运行。

后续步骤在**新终端**执行。

- [ ] **步骤 2：验证 Geely2 接口拒绝未登录**

在新终端运行：

```bash
curl -s -o /dev/null -w "geely2 issues status: %{http_code}\n" \
  http://127.0.0.1:8000/api/geely2/issues/
```

预期：输出 `geely2 issues status: 401`。

如果是 403：worktree 实现里 `SessionStatusCodeAuthentication.authenticate_header` 应该让 DRF 返回 401；403 表示该类未生效。停下汇报。

- [ ] **步骤 3：验证 analyzer 接口仍开放**

运行：

```bash
curl -s -o /dev/null -w "analyzer task-groups status: %{http_code}\n" \
  http://127.0.0.1:8000/api/tasks/groups/
```

预期：输出 `analyzer task-groups status: 200`。

如果是 401/403：说明现有 `analyzer` API 被意外加上了鉴权，违反"最小并入"约定，停下汇报。

- [ ] **步骤 4：验证 platform 登录 API 公开访问**

运行：

```bash
curl -s -i http://127.0.0.1:8000/api/platform/csrf/ | head -n 5
```

预期：第一行 `HTTP/1.1 204 No Content`；响应头中含 `Set-Cookie: csrftoken=...`。

---

## 任务 7：前端登录闭环 + Geely2 全流程

**前置：** 任务 6 中终端 A 的 Web 进程仍在跑。

**前置说明：** 此任务需要真实 Jira 账号；如果暂无可用 Jira 凭据，跳过本任务并标记为"待补"，先完成任务 8、9，最后再补此任务。

- [ ] **步骤 1：启动 Geely2 Worker**

打开**终端 B**，运行：

```bash
cd django_jira_analyzer
source .env.local 2>/dev/null || true
python manage.py run_geely2_worker --poll-interval 2
```

预期：终端 B 进程启动后保持运行，无 import error。

- [ ] **步骤 2：启动前端开发服务器**

打开**终端 C**，运行：

```bash
cd ../jira-analyzer-web
npm install     # 仅首次需要
npm run serve
```

预期：终端 C 输出 `App running at: http://localhost:8080/`。

- [ ] **步骤 3：浏览器走未登录跳转**

操作：
1. 浏览器访问 `http://localhost:8080/geely2`
2. 观察 URL

预期：URL 自动跳转到 `http://localhost:8080/login?next=/geely2`，登录页正常渲染。

如果页面空白或控制台报跨域：检查任务 1 步骤 4 后 `config/settings.py` 是否含 `CORS_ALLOW_CREDENTIALS = True` 和 `CSRF_TRUSTED_ORIGINS = [..., "http://localhost:8080", ...]`。

- [ ] **步骤 4：登录**

用任务 4 创建的账号登录。

预期：成功后浏览器跳转到 `/geely2`，页面显示凭据配置入口。

- [ ] **步骤 5：保存 Jira 凭据**

在凭据表单中填写：
- Jira Base URL（默认 `https://boolbool.atlassian.net/`，按你实际环境修改）
- Jira Username（你的 Jira 账号）
- Jira Password（Jira API Token 或密码）

点击保存。

预期：
- 接口 `PUT /api/geely2/credential/` 返回 200，响应体包含 `{"configured": true, ...}`
- 数据库 `geely2_analyzer_jiracredentialbinding` 表新增一行；`encrypted_password` 字段以 `enc::` 开头（验证：`python manage.py shell -c "from geely2_analyzer.models import JiraCredentialBinding; print(JiraCredentialBinding.objects.values_list('encrypted_password', flat=True)[0][:7])"`，应输出 `enc::g` 或类似）

- [ ] **步骤 6：触发同步**

在前端点击"同步"按钮。

预期：
- 接口 `POST /api/geely2/sync-tasks/` 返回 201
- 终端 B（Worker）打印 `claimed sync task` 类似日志
- SSE 推送 `geely2` 事件，issue 列表渲染出当前用户的 Jira issue

如果 issue 列表为空：确认 Jira 账号确实有分配的 issue（`assignee = currentUser()`）。

- [ ] **步骤 7：触发单票分析**

任选一票，点击"分析"按钮。

预期：
- 接口 `POST /api/geely2/issues/<key>/analysis-tasks/` 返回 201
- 终端 B 打印 `claimed analysis task` 日志
- 前端进度条依次经历 `FETCH_COMMENTS` → `EXTRACT_RELATED_SIGNALS` → `DOWNLOAD_ARCHIVES` → `UNPACK_QNX_LOG` → `SELECT_TARGET_CYCLES` → `FILTER_BOSCH_LOGS` → `EXTRACT_UPPER_REQUIREMENTS` → `AI_ANALYZE` → `SAVE_RESULT`
- 最终状态 `SUCCESS`，结果页显示 `reply_text`

如果在 `DOWNLOAD_ARCHIVES` 卡住：该 issue 没有 `qnx_log.tgz` 附件，按 worktree `geely2_analyzer/services/analysis_runner.py:39-47` 的实现会抛 `FileNotFoundError`，换一票测试。

- [ ] **步骤 8：编辑回填 Jira**

操作：
1. 在结果页编辑 `reply_text`
2. 点击保存（`PATCH /api/geely2/analysis-results/<id>/`）
3. 点击"回填 Jira"（`POST /api/geely2/analysis-results/<id>/comment/`）

预期：
- 保存返回 200
- 回填返回 `{"detail": "已成功回填 Jira"}`
- 在 Jira 网页打开对应 issue，能看到刚才提交的 comment

如果回填失败 502：检查 Jira 凭据权限（API Token 是否有 comment 权限）、Jira Base URL 是否正确。

---

## 任务 8：SSE 用户隔离验证

**前置：** 任务 6 终端 A、任务 7 终端 B 仍在跑。

- [ ] **步骤 1：创建第二个测试用户**

运行：

```bash
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
u, created = User.objects.get_or_create(username='sse_tester')
u.set_password('sse_tester_pwd_2026')
u.save()
print('user_id:', u.id, 'created:', created)
"
```

预期：输出 `user_id: <int> created: True`（首次）或 `created: False`（已存在）。

- [ ] **步骤 2：双浏览器登录**

操作：
1. 浏览器窗口 A（普通模式）：用任务 4 的账号登录，访问 `/geely2`
2. 浏览器窗口 B（隐身模式或另一浏览器）：用 `sse_tester / sse_tester_pwd_2026` 登录，访问 `/geely2`

预期：两个窗口各自显示独立的 issue 列表（B 用户可能为空，因为还没配置凭据）。

- [ ] **步骤 3：A 用户触发同步**

在窗口 A 点击"同步"。

预期：
- 窗口 A：SSE 推送，issue 列表更新
- 窗口 B：**不应**收到任何 SSE 事件，issue 列表保持原样

如果窗口 B 收到 A 的数据：违反 `geely2_analyzer/services/stream.py` 的用户隔离设计，停下汇报。

- [ ] **步骤 4：清理测试用户（可选）**

运行：

```bash
python manage.py shell -c "
from django.contrib.auth import get_user_model
get_user_model().objects.filter(username='sse_tester').delete()
print('cleaned')
"
```

预期：输出 `cleaned`。

---

## 任务 9：worktree 下线与 .gitignore 更新

**前置：** 任务 5 ~ 任务 8 全部通过。

**文件：**
- 修改：`.gitignore`（追加 `.worktrees/`）
- 删除：worktree 目录 `.worktrees/geely2-minimal-backend/`

- [ ] **步骤 1：再次确认集成分支状态**

运行：

```bash
git branch --show-current
git log --oneline -5
```

预期：在 `feature/integrate-geely2`，最近 5 个 commit 含 merge commit 与若干 geely2 子能力 commit。

- [ ] **步骤 2：下线 worktree**

运行：

```bash
git worktree list
git worktree remove .worktrees/geely2-minimal-backend
git worktree list
```

预期：
- 第一条命令输出 2 行（主仓 + worktree）
- 第二条命令无输出
- 第三条命令只输出 1 行（仅主仓）

如果 `git worktree remove` 报错 `contains modified or untracked files`，先确认 worktree 内修改是否真的不需要保留（按规格 §1.5 已决定丢弃）；强制下线运行 `git worktree remove --force .worktrees/geely2-minimal-backend`。

- [ ] **步骤 3：删除残留远端分支引用（可选）**

```bash
git branch -D feature/geely2-minimal-backend
```

预期：输出 `Deleted branch feature/geely2-minimal-backend (was f98b890).`

如果不想删本地分支引用作为历史档案，跳过此步。

- [ ] **步骤 4：更新 .gitignore**

打开 `.gitignore` 查看现有内容：

```bash
cat .gitignore
```

当前内容应为：
```
.worktrees/*.log
.codex
.env.example
.venv/
__pycache__/
.gitignore
comment/
```

修改：把第 1 行 `.worktrees/*.log` 替换为 `.worktrees/`，并在末尾追加 `.env.local`（如果任务 2 步骤 3 没追加过）。

修改后预期内容：

```
.worktrees/
.codex
.env.example
.venv/
__pycache__/
.gitignore
comment/
.env.local
```

注：`.gitignore` 文件本身被 ignore 了一行（第 6 行 `.gitignore`）这是已有的"梗"，不动它。

- [ ] **步骤 5：commit .gitignore 修改**

运行：

```bash
git add -f .gitignore     # -f 因为 .gitignore 自身被 ignore
git status --short
git diff --cached .gitignore
```

预期：`git diff --cached` 显示 `.worktrees/*.log` → `.worktrees/`、追加 `.env.local`。

```bash
git commit -m "chore: 收紧 .gitignore，忽略 .worktrees 目录与 .env.local"
git log --oneline -2
```

预期：新 commit 进入 `feature/integrate-geely2`，HEAD 是这个 chore commit，前一个是 merge commit。

- [ ] **步骤 6：确认工作区终态**

运行：

```bash
git status --short
```

预期：仍显示
```
 M analyzer/services/issue_process_pipeline.py
 M legacy_core/pipeline.py
?? "config——chery/8255/config_D01.txt"
?? "config——chery/8255/config_D01_HW.txt"
?? "config——chery/CHERY/config_T1L_FL1.txt"
```

不应出现 `?? .worktrees/`（已下线）、不应出现 `?? .env.local`（已 ignore）。

---

## 任务 10：完成定义（DoD）终检

**前置：** 任务 1 ~ 任务 9 全部通过。

- [ ] **步骤 1：DoD 逐条核对**

按规格 §7 走一遍：

```bash
git branch --show-current                                        # 期望 feature/integrate-geely2
python manage.py check                                           # 期望 no issues
python manage.py test analyzer platform_accounts geely2_analyzer # 期望 OK
git log --first-parent --oneline -10                             # 期望主线清晰
git worktree list                                                # 期望仅主仓
grep -c "^.worktrees/" .gitignore                                # 期望 1
git status --short | grep -E "(issue_process_pipeline|legacy_core/pipeline)" | wc -l   # 期望 2
```

预期 DoD 7 项全部满足：

| DoD 条目 | 验证命令 | 预期 |
|---|---|---|
| 在 `feature/integrate-geely2` | `git branch --show-current` | `feature/integrate-geely2` |
| `manage.py check` 通过 | `python manage.py check` | `no issues` |
| 测试全绿且数量 ≥ 既有 + 8 | `python manage.py test ...` | `OK`、`Ran <N> tests` 其中 `N ≥ 既有 + 8` |
| 前端全流程跑通 | 任务 7 已验证 | 6 步均成功 |
| 主线 commit 清晰 | `git log --first-parent` | 含 merge commit + chore commit |
| worktree 已下线 + .gitignore 更新 | `git worktree list`、`grep .gitignore` | worktree 仅主仓；`.gitignore` 含 `.worktrees/` |
| WIP 文件保持未暂存 | `git status --short` | 含 `M analyzer/services/issue_process_pipeline.py`、`M legacy_core/pipeline.py` |

- [ ] **步骤 2：交付总结**

向用户报告：

> Geely2 集成完成。
>
> - 集成分支：`feature/integrate-geely2`
> - 合入 commit：1 个 merge commit + 1 个 chore commit
> - 数据库：新增 5 张 `geely2_analyzer_*` 表
> - 测试：`analyzer + platform_accounts + geely2_analyzer` 全绿
> - 端到端：前端 `/login → /geely2 → 同步 → 单票分析 → 回填 Jira` 验证通过
> - worktree `.worktrees/geely2-minimal-backend/` 已下线
> - WIP 文件 `analyzer/services/issue_process_pipeline.py`、`legacy_core/pipeline.py` 保持未暂存
>
> 未做（按规格 §8 显式不做）：
> - 给 `analyzer/*` API 加鉴权
> - 重构 `task_executor` / 合并 worker
> - 收口 `SECRET_KEY`、`DEBUG`、`CORS_ALLOW_ALL_ORIGINS`、`AUTH_PASSWORD_VALIDATORS`
> - push 到远端、创建 PR
>
> 是否需要 push `feature/integrate-geely2` 到远端、或继续推进上述任一条线？

---

## 自检（计划编写者完成后填写）

**1. 规格覆盖度核对**：

| 规格章节 | 对应任务 |
|---|---|
| §2.1 分支与 commit 形态 | 任务 1 |
| §2.2 主仓最终目录形态 | 任务 1（merge 自动产生） |
| §2.3 集成后 URL 总览 | 任务 6（curl 验证）、任务 7（前端联通） |
| §2.4 部署拓扑 | 任务 6（Web）、任务 7（Worker B + 前端） |
| §3.1 ~ §3.7 集成执行步骤 | 任务 1 步骤 1 ~ 步骤 8 |
| §3.8 回滚预案 | 任务 1 各步骤"异常分支"段 |
| §4.1 必备环境变量 | 任务 2 |
| §4.2 数据库迁移 | 任务 3 |
| §4.3 创建用户 | 任务 4 |
| §5.1 配置自检 | 任务 1 步骤 6、任务 10 步骤 1 |
| §5.2 全量测试 | 任务 5 |
| §5.3 未登录访问验证 | 任务 6 |
| §5.4 登录闭环验证 | 任务 7 |
| §5.5 SSE 用户隔离验证 | 任务 8 |
| §6 worktree 下线 + .gitignore | 任务 9 |
| §7 DoD | 任务 10 |
| §8 显式不做的事 | 任务 10 步骤 2 报告中重申 |

无遗漏。

**2. 占位符扫描**：搜索 "TODO"、"待定"、"补充"、"类似任务"、"略" 关键词——无命中。所有代码块和命令都是完整可执行的具体内容。

**3. 类型一致性**：

- 分支名 `feature/integrate-geely2`、`feature/geely2-minimal-backend`、`feature/filter-snapshot-single-issue` 全文一致
- 路径 `geely2_analyzer/`、`platform_accounts/`、`.worktrees/geely2-minimal-backend/` 全文一致
- 环境变量名 `JIRA_CREDENTIAL_ENCRYPTION_KEY`、`DJANGO_SECRET_KEY`、`MYSQL_*` 全文一致
- 表名前缀 `geely2_analyzer_*` 全文一致
- 命令 `python manage.py {check, migrate, test, runserver, shell, dbshell, createsuperuser, makemigrations, run_geely2_worker}` 全文一致
- API 路径 `/api/geely2/*`、`/api/platform/*`、`/api/tasks/groups/` 全文一致

无类型/命名漂移。
