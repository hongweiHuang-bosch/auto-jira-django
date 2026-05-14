# Geely2 前后端功能合并设计

- 文档日期：2026-05-14
- 主题：把 `feature/geely2-minimal-backend` worktree 上的 Geely2 + 平台账号能力，最小并入主仓 `feature/filter-snapshot-single-issue`
- 范围标签：**最小并入**（不动现有 `analyzer` API 鉴权策略、不重构任务执行模型、不收口 settings 安全项）

## 1. 背景与现状

### 1.1 仓库布局

- 主后端：`django_jira_analyzer/`，当前在分支 `feature/filter-snapshot-single-issue`（HEAD `da273d4`）
- 前端 SPA：`jira-analyzer-web/`，已实现登录页、Geely2 首页、Geely2 结果页，并已经在调用 `/api/platform/*` 与 `/api/geely2/*`
- Geely2 后端实现：位于 worktree `django_jira_analyzer/.worktrees/geely2-minimal-backend/`，分支 `feature/geely2-minimal-backend`（HEAD `f98b890`）

### 1.2 主仓 vs worktree 的差异

| 维度 | 主仓现状 | worktree 已实现 |
|---|---|---|
| `INSTALLED_APPS` | 仅 `analyzer` | 多 `platform_accounts`、`geely2_analyzer` |
| URL 路由 | 仅 `api/` → `analyzer.urls` | 多 `api/platform/*`、`api/geely2/*` |
| DRF 鉴权 | 无（默认开放） | Session 登录 + `IsAuthenticated`，新增 `SessionStatusCodeAuthentication` 让未登录返回 401 而非 403 |
| Jira 凭据 | 全局 `config.yaml` | 用户级绑定，Fernet 加密落库 |
| 模型 | `AnalysisTask`、`IssueAnalysisResult`、`FilterTask`、`FilteredIssueSnapshot`、`IssueProcessTask`、`IssueProcessResult` | 新增 5 张：`JiraCredentialBinding`、`Geely2SyncTask`、`Geely2IssueSnapshot`、`Geely2AnalysisTask`、`Geely2AnalysisResult`，含 `0001_initial` migration |
| Worker | `run_task_worker`（筛票/单票） | 多一个 `run_geely2_worker`（同步 + 单票分析） |
| SSE | `tasks/stream/`、`rule-groups/stream/`（全局） | 多 `geely2/stream/`（按用户 ID 隔离） |
| settings 关键项 | 无 `JIRA_CREDENTIAL_ENCRYPTION_KEY`、无 `CSRF_TRUSTED_ORIGINS`、无 `CORS_ALLOW_CREDENTIALS` | 三项均已就位（`JIRA_CREDENTIAL_ENCRYPTION_KEY` 默认空字符串，未配置时报 `ImproperlyConfigured`） |
| 测试 | `analyzer/tests/*` 7 个 | 新增 `geely2_analyzer/tests/*` 7 个 + `platform_accounts/tests/*` 1 个 |

### 1.3 分支祖先关系

- `merge-base` = `889dd56`
- 主分支自 merge-base 起领先 1 个 commit（`da273d4` "fix connect bug and opt frontend"）
- Geely2 分支自 merge-base 起领先 17 个 commit（凭据 → 同步接口 → 同步 Worker → 流水线 → 分析接口，递进式提交）

### 1.4 共享文件冲突预扫

主分支与 Geely2 分支自 merge-base 起，**同时改动过的代码文件仅 3 个**，且全部为零交叠（单边新增）：

| 文件 | 主分支改动 | Geely2 分支改动 | 合并预期 |
|---|---|---|---|
| `config/settings.py` | 无 | 新增 `JIRA_CREDENTIAL_ENCRYPTION_KEY` 一行；`INSTALLED_APPS` 末尾追加 2 项 | 自动合并通过 |
| `config/urls.py` | 无 | `urlpatterns` 末尾追加 2 条 `include(...)` | 自动合并通过 |
| `analyzer/views.py` | 主分支改动 1 行 | 无 | 自动合并通过 |

主分支自 merge-base 后还修改了大量 `config——chery/...` 配置文件，与 Geely2 完全无交叠，不进入冲突分析。

### 1.5 工作区未提交修改

- 主仓未提交（保留）：`analyzer/services/issue_process_pipeline.py`、`legacy_core/pipeline.py`
- 主仓未跟踪（保留）：`.worktrees/`、`config——chery/8255/config_D01.txt`、`config——chery/8255/config_D01_HW.txt`、`config——chery/CHERY/config_T1L_FL1.txt`
- worktree 内未提交（**全部丢弃，不带入集成分支**）

## 2. 集成目标状态

### 2.1 分支与 commit 形态

新建 `feature/integrate-geely2`，从 `feature/filter-snapshot-single-issue` 分出，merge `feature/geely2-minimal-backend` 进来：

```
feature/integrate-geely2
│
├─ M  merge: 集成 Geely2 用户级 Jira 凭据、同步、单票分析    ← --no-ff
│  │
│  ├─ feat(geely2分析): 添加分析任务与结果接口
│  ├─ feat(geely2流水线): 添加解压与日志筛选辅助函数
│  ├─ feat(geely2同步): 添加同步 Worker、Jira 客户端工厂和任务抢占
│  ├─ feat(geely2同步): 添加同步接口与SSE
│  ├─ feat(geely2凭据): 添加凭据绑定接口
│  └─ ... 共 17 个 geely2 子能力 commit
│
└─ da273d4 fix connect bug and opt frontend                  ← 主分支唯一新增 commit
```

`stash pop` 还原的工作区修改保持"未暂存"，不进 commit。

### 2.2 主仓最终目录形态

```
django_jira_analyzer/
├── analyzer/                ← 现有，零改动
├── legacy_core/             ← 现有，零改动
├── platform_accounts/       ← 新增
│   ├── __init__.py / apps.py / urls.py / views.py
│   └── tests/
│       ├── __init__.py
│       └── test_session_api.py
├── geely2_analyzer/         ← 新增
│   ├── __init__.py / apps.py / models.py / serializers.py
│   ├── urls.py / views.py
│   ├── migrations/
│   │   ├── __init__.py
│   │   └── 0001_initial.py
│   ├── services/
│   │   ├── __init__.py / credential_crypto.py / client_factory.py
│   │   ├── sync_runner.py / analysis_runner.py / analysis_prompts.py
│   │   ├── pipeline_helpers.py / payloads.py / stream.py / task_claims.py
│   ├── management/commands/
│   │   ├── __init__.py
│   │   └── run_geely2_worker.py
│   └── tests/
│       ├── __init__.py
│       ├── test_credential_api.py / test_sync_api.py / test_sync_worker.py
│       ├── test_analysis_api.py / test_analysis_worker.py
│       ├── test_pipeline_helpers.py / test_domain_models.py
└── config/
    ├── settings.py          ← 叠加 3 项配置
    └── urls.py              ← 叠加 2 条路由
```

### 2.3 集成后 URL 总览

| 路径前缀 | 提供者 | 鉴权 | 备注 |
|---|---|---|---|
| `/admin/` | Django admin | Session | 现有 |
| `/api/tasks/` `/api/rule-groups/` `/api/results/` 等 | `analyzer`（现有） | **保持开放** | 最小并入约定 |
| `/api/platform/csrf/` | `platform_accounts`（新增） | 公开 | 写入 csrftoken cookie |
| `/api/platform/login/` | `platform_accounts`（新增） | 公开 | Session 登录 |
| `/api/platform/logout/` | `platform_accounts`（新增） | 已登录 | |
| `/api/platform/session/` | `platform_accounts`（新增） | 已登录 | 前端路由守卫探活用 |
| `/api/geely2/credential/` | `geely2_analyzer`（新增） | Session + IsAuthenticated | GET/PUT |
| `/api/geely2/sync-tasks/` | 同上 | 同上 | POST 创建同步任务 |
| `/api/geely2/sync-tasks/<pk>/` | 同上 | 同上 | GET 详情 |
| `/api/geely2/issues/` | 同上 | 同上 | GET 当前用户 issue 列表 |
| `/api/geely2/issues/<key>/analysis-tasks/` | 同上 | 同上 | POST 触发单票分析 |
| `/api/geely2/analysis-tasks/<pk>/` | 同上 | 同上 | GET 任务进度 |
| `/api/geely2/analysis-results/<pk>/` | 同上 | 同上 | GET / PATCH |
| `/api/geely2/analysis-results/<pk>/comment/` | 同上 | 同上 | POST 回填 Jira |
| `/api/geely2/stream/` | 同上 | 已登录（视图内手动判定） | SSE，按用户 ID 隔离 |

### 2.4 集成后部署拓扑

3 个进程并存，本次合并不调整：

| 进程 | 命令 | 角色 |
|---|---|---|
| Web | `python manage.py runserver 0.0.0.0:8000` | API、SSE、`analyzer.task_executor` 内置线程池 |
| Worker A | `python manage.py run_task_worker` | `analyzer` 的筛票任务、单票处理任务 |
| Worker B | `python manage.py run_geely2_worker` | Geely2 同步任务、Geely2 单票分析任务 |

前端 `jira-analyzer-web` 不需任何改动，devServer proxy 仍指向 `http://127.0.0.1:8000`。

## 3. 集成执行步骤

操作目录：`django_jira_analyzer/`，当前分支 `feature/filter-snapshot-single-issue`。

### 3.1 前置安全检查

```bash
git status
git branch --show-current     # 期望：feature/filter-snapshot-single-issue
git fetch
```

### 3.2 暂存主仓未提交修改

```bash
git stash push -u -m "wip: pipeline 调试，待合并 geely2 后恢复" \
    analyzer/services/issue_process_pipeline.py \
    legacy_core/pipeline.py
```

仅 stash 这 2 个跟踪文件。`.worktrees/`、`config——chery/...txt` 等未跟踪文件不进 stash，本地保留。

### 3.3 创建集成分支

```bash
git switch -c feature/integrate-geely2
```

### 3.4 执行 merge

```bash
git merge --no-ff feature/geely2-minimal-backend \
  -m "merge: 集成 Geely2 用户级 Jira 凭据、同步、单票分析"
```

**异常分支**：若 git 报告冲突（理论上不应发生），立即 `git merge --abort`，停下汇报冲突文件，不要硬解。

### 3.5 合并体快速校验

```bash
git ls-files platform_accounts geely2_analyzer | wc -l    # 期望 ≥ 25
python manage.py check                                     # 配置/URL/模型自检
python manage.py makemigrations --dry-run                  # 期望不产生新 migration
```

### 3.6 恢复主仓未提交修改

```bash
git stash pop
git status                                                 # 2 个文件回到未暂存状态
```

### 3.7 WIP 文件保持未暂存

恢复后的 `analyzer/services/issue_process_pipeline.py` 与 `legacy_core/pipeline.py` 保持工作区"未暂存"状态，不进入集成分支历史。这两文件的改动与 Geely2 集成无关，混入会污染 commit 语义；后续由其他工作线独立处理。

### 3.8 回滚预案

| 阶段 | 回滚动作 |
|---|---|
| Step 3.4 失败 | `git merge --abort` |
| Step 3.6 pop 冲突 | `git checkout --theirs/--ours <path>` 或从 stash 备份手动还原 |
| Step 3.5 之后才发现问题 | `git switch feature/filter-snapshot-single-issue && git branch -D feature/integrate-geely2` |

## 4. 合并后环境与数据准备

### 4.1 必备环境变量

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
export JIRA_CREDENTIAL_ENCRYPTION_KEY="<上一行输出的 44 位 base64 串>"
export DJANGO_SECRET_KEY="<随机长串>"
```

`JIRA_CREDENTIAL_ENCRYPTION_KEY` 未配置时，`geely2_analyzer.services.credential_crypto._build_fernet()` 会抛 `ImproperlyConfigured`，凭据保存接口直接 500。

### 4.2 数据库迁移

```bash
python manage.py migrate geely2_analyzer
python manage.py migrate
```

`platform_accounts` 无新表，无需单独 migrate。`geely2_analyzer/0001_initial.py` 创建 5 张新表，对现有 `analyzer_*` 表零影响。

### 4.3 创建至少 1 个用户

```bash
python manage.py createsuperuser
```

前端登录页用 Django 内置 `django.contrib.auth.User` 校验。

### 4.4 settings 暂不变更项

`DEBUG`、`ALLOWED_HOSTS=*`、`CORS_ALLOW_ALL_ORIGINS=DEBUG`、`AUTH_PASSWORD_VALIDATORS=[]`、`SECRET_KEY` 默认值——**本次集成不动**，归口"安全上线"另一条工作线。

## 5. 验证清单

按顺序执行，每步通过才进入下一步。

### 5.1 配置自检

```bash
python manage.py check
```

期望：无 `ERRORS`，至多 `WARNINGS`。

### 5.2 全量测试

```bash
python manage.py test analyzer platform_accounts geely2_analyzer
```

期望：原 `analyzer/tests/*` 无回归；新增 7 个 `geely2_analyzer/tests/*` 与 1 个 `platform_accounts/tests/*` 全绿。

### 5.3 未登录访问验证

```bash
curl -i http://127.0.0.1:8000/api/geely2/issues/        # 期望：401
curl -i http://127.0.0.1:8000/api/tasks/groups/         # 期望：200（保持开放）
```

### 5.4 登录闭环验证（前端手工）

1. 浏览器访问 `/geely2` → 路由守卫跳转 `/login`
2. 用 5.0 步骤创建的账号登录 → 回到 `/geely2`
3. 在凭据表单中填写 Jira 账户与密码 → 保存成功（`/api/geely2/credential/` PUT 返回 `{configured: true}`）
4. 触发同步 → SSE 推送 `geely2` 事件 → issue 列表渲染
5. 任选一票点击"分析" → 进度条经历 `FETCH_COMMENTS` → `EXTRACT_RELATED_SIGNALS` → ... → `SAVE_RESULT`，最终拿到 reply_text
6. 编辑 reply_text → 保存 → 点击"回填 Jira" → Jira issue 上出现新 comment

### 5.5 SSE 用户隔离验证

- 两个不同浏览器（或一个浏览器 + 隐身窗口）登录两个不同账号
- 用户 A 触发同步，用户 B 的 `/geely2` 页面不应出现 A 的 issue 列表更新
- 验证依据：`geely2_analyzer/services/stream.py` 的 `_subscribers` 字典按 `user_id` 隔离

任意一步失败 → 停止打补丁，按 §3.8 回滚，把现场反馈给上游评估。

## 6. worktree 下线

验证 5.1 ~ 5.5 全部通过后：

```bash
git -C django_jira_analyzer worktree remove .worktrees/geely2-minimal-backend
git -C django_jira_analyzer branch -D feature/geely2-minimal-backend   # 可选，远端保留
```

主仓 `.gitignore` 追加：

```
.worktrees/
```

理由：当前 `.gitignore` 只忽略 `.worktrees/*.log`，目录本身未忽略；下线后避免后续新建 worktree 残留被误提交。

## 7. 完成定义（DoD）

集成视为完成需同时满足：

- `feature/integrate-geely2` 上 `python manage.py check` 通过
- `python manage.py test analyzer platform_accounts geely2_analyzer` 全绿，且总用例数 ≥ 合并前 + 8（geely2 7 个 + platform_accounts 1 个）
- 前端「未登录跳登录 → 登录 → 配置凭据 → 同步 → 单票分析 → 编辑回填 Jira」全流程跑通
- 合并 commit 历史保留，`git log --first-parent feature/integrate-geely2` 可看到清晰主线
- worktree `.worktrees/geely2-minimal-backend/` 已下线，`.gitignore` 已追加 `.worktrees/`
- 主仓工作区中 `analyzer/services/issue_process_pipeline.py` 与 `legacy_core/pipeline.py` 仍处于"未暂存"状态（本次集成显式不 commit，归口其他工作线）

## 8. 显式不做的事

为防止范围漂移，本次集成**不**做下列事项，全部归口其他工作线：

- 给现有 `analyzer/*` API 加鉴权 → "统一鉴权"工作线
- 重构 `analyzer.task_executor` 线程池、合并两个 worker 为统一队列 → "任务稳定性"工作线
- 收口 `SECRET_KEY` 默认值、`DEBUG`、`CORS_ALLOW_ALL_ORIGINS`、`AUTH_PASSWORD_VALIDATORS` → "安全上线"工作线
- push 集成分支到远端、创建 PR → 用户未要求
- 修改前端代码（前端已对齐 `/api/platform/*` 与 `/api/geely2/*`，无需改动）
- 把 `config.yaml` 里的全局 Jira 凭据迁移到 `JiraCredentialBinding` → 不在本次范围
