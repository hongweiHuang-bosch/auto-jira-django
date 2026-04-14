# Django Jira 自动分析工具（MySQL版）

这是一个基于 Django 封装的 Web 版 Jira 自动分析系统，默认数据库已改为 MySQL，并且已经附带 `analyzer_analysistask` 与 `analyzer_issueanalysisresult` 的建表 SQL。

## 已补齐的内容

- 默认数据库从 SQLite 改成 MySQL
- 新增 `PyMySQL` 驱动，无需本地编译 `mysqlclient`
- 新增 `.env.example`，可直接改成 `.env` 或导出为环境变量
- 新增 `sql/init_mysql.sql`，可直接创建数据库和两张业务表
- 保留 Django migration，后续仍可继续执行 `python manage.py migrate`

## 目录说明

- `legacy_core/`：原有分析核心代码
- `analyzer/`：Django 业务封装层
- `templates/index.html`：极简前端页面
- `comment/`：运行中生成的日志、分析文本、图片
- `sql/init_mysql.sql`：MySQL 初始化脚本
- `init_mysql_tables.sh`：Linux / WSL 下一键建表脚本

## 一、安装依赖

```bash
pip install -r requirements.txt
```

## 二、准备业务配置

把 `config.example.yaml` 复制为 `config.yaml`，并填写 Jira / AI 配置：

```bash
cp config.example.yaml config.yaml
```

## 三、准备数据库环境变量

方式一：直接导出

```bash
export DB_ENGINE=mysql
export MYSQL_HOST=127.0.0.1
export MYSQL_PORT=3306
export MYSQL_DATABASE=jira_analyzer
export MYSQL_USER=root
export MYSQL_PASSWORD=123456
```

方式二：参考 `.env.example` 自行加载。

## 四、创建 MySQL 数据库和表

### 方式 A：直接执行 SQL

```bash
mysql -h127.0.0.1 -P3306 -uroot -p < sql/init_mysql.sql
```

### 方式 B：执行脚本

```bash
bash init_mysql_tables.sh
```

执行后会创建：

- `jira_analyzer`
- `analyzer_analysistask`
- `analyzer_issueanalysisresult`

## 五、同步 Django migration

如果你已经手工执行了 SQL，仍然建议再跑一次迁移，让 Django 自己维护后续版本：

```bash
python manage.py migrate
```

如果你之前数据库里已经有旧表但没有 migration 记录，可先使用：

```bash
python manage.py migrate --fake-initial
```

## 六、启动服务

```bash
python manage.py runserver 0.0.0.0:8000
```

浏览器打开：

```text
http://127.0.0.1:8000/
```

## API

### 启动任务

```http
POST /api/tasks/start/
```

### 查询任务详情

```http
GET /api/tasks/<task_id>/
```

### 查询结果列表

```http
GET /api/results/?task_id=<task_id>
```

### 回填 Jira

```http
POST /api/results/<result_id>/comment/
```

## 说明

1. 这版已经补了 `analyzer_analysistask` 表对应的 migration 和 MySQL 建表 SQL。
2. 默认走 MySQL；如果你想临时切回 SQLite，可以设置 `DB_ENGINE=sqlite3`。
3. `legacy_core/config_map.py` 中的路径仍需要按你本地实际目录调整。
4. 如果你执行过旧版本但没有表，最直接就是先执行 `sql/init_mysql.sql`，再跑 `python manage.py migrate --fake-initial`。
