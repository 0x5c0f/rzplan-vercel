# PROJECT_HANDOFF.md

## 文档目的

这份文档用于帮助后续开发者或 AI 代理快速接手本仓库，建立对项目定位、运行方式、代码结构和扩展边界的基础认知。

它不是执行规范。执行规范请看根目录的 [AGENTS.md](AGENTS.md)。

本文档重点回答以下问题：

- 这个项目是什么
- 仓库是怎么组织的
- 技术栈和外部依赖是什么
- 本地如何启动、检查和测试
- 代码入口和主要调用链在哪里
- 哪些信息是已确认事实，哪些是基于代码和上下文的推断

## 项目定位

### 已确认

- 本仓库实际主体是一个 Python 后端服务，核心框架是 FastAPI。
- 数据层使用 SQLModel + PostgreSQL，数据库迁移使用 Alembic。
- 当前分支的主要 `rz` 业务扩展是字典模块。
- 当前分支中保留了一个最小化的 MCP 接入结构，但它不代表当前分支应继续扩展其他工具能力。
- 应用主入口在 [app/main.py](app/main.py)。
- API 聚合入口在 [app/api/main.py](app/api/main.py)。

### 已知背景

根据维护者说明，本仓库来源于 `fastapi/full-stack-fastapi-template` 的后端部分，并做了面向当前项目的演化：

- `rzplan` 表示“归零计划（Reset Zero Plan）”
- `vercel` 表示当前仓库对 Vercel 部署做过适配与简化

这里的 `vercel` 是当前仓库特征，不意味着后续任意扩展都仍适合部署到 Vercel。

### 推断

- 当前仓库更像“从模板提取并持续扩展的后端骨架”，而不是完整产品仓库。
- 它的长期维护思路不是脱离上游独立发展，而是尽量保持与上游模板低耦合，再通过 `rz` 命名空间承载业务扩展。

推断依据：

- 模板原生结构仍保留明显痕迹
- `rz` 目录与 `app/api/routes/rz` 形成了稳定的扩展接缝
- 维护者明确强调后续要尽量少动模板原生区域，方便同步上游

## 仓库结构

### 顶层

- [app](app)
  - 主应用代码
- [scripts](scripts)
  - 当前仅保留预启动脚本
- [.vscode/launch.json](.vscode/launch.json)
  - VSCode 本地调试配置
- [requirements.txt](requirements.txt)
  - Python 依赖清单
- [alembic.ini](alembic.ini)
  - Alembic 配置入口
- [env.example](env.example)
  - 环境变量示例
- [vercel.json](vercel.json)
  - Vercel Python Runtime 配置
- [.vercelignore](.vercelignore)
  - Vercel 打包忽略规则
- [.dockerignore](.dockerignore)
  - Docker 构建上下文忽略规则
- [README.md](README.md)
  - 当前仓库的简要说明、启动方式与部署背景
- [AGENTS.md](AGENTS.md)
  - 项目执行规范

### `app/` 目录

- [app/main.py](app/main.py)
  - FastAPI 应用入口，负责 CORS、路由挂载、MCP 注册
- [app/api/main.py](app/api/main.py)
  - API 路由聚合入口
- [app/api/routes](app/api/routes)
  - 模板原生路由和 `rz` 路由入口
- [app/core](app/core)
  - 配置、数据库、安全相关基础设施
- [app/models.py](app/models.py)
  - 模板原生用户/条目模型
- [app/crud.py](app/crud.py)
  - 模板原生 CRUD
- [app/alembic](app/alembic)
  - 数据库迁移脚本
- [app/tests](app/tests)
  - 测试
- [app/rz](app/rz)
  - 项目自定义扩展命名空间

### `app/rz/` 目录

当前已经存在以下子结构：

- [app/rz/models](app/rz/models)
  - `rz` 领域模型，例如字典类型、字典项
- [app/rz/crud](app/rz/crud)
  - `rz` 领域数据库操作
- [app/rz/subsystem](app/rz/subsystem)
  - 当前主要用于保留最小化 MCP 接入结构
- [app/rz/utils](app/rz/utils)
  - `rz` 工具函数与日志工具

### `app/api/routes/rz`

- [app/api/routes/rz/dict.py](app/api/routes/rz/dict.py)
  - 字典模块 API

这是当前 `rz` 业务路由的实际挂载位置，也是后续最应优先参考的新增 API 落点。

## 技术栈与依赖

### 已确认

核心依赖来自 [requirements.txt](requirements.txt)：

- `fastapi[standard]`
- `sqlmodel`
- `psycopg[binary]`
- `alembic`
- `pydantic`
- `pydantic-settings`
- `pyjwt`
- `pwdlib[argon2,bcrypt]`
- `sentry-sdk[fastapi]`
- `emails`
- `jinja2`
- `httpx`
- `tenacity`
- `fastapi-mcp`

开发与检查相关依赖：

- `pytest`
- `coverage`
- `mypy`
- `ruff`

### 运行时前提

已确认当前仓库自带虚拟环境 Python 版本为：

- Python 3.12.12

这是通过执行 `./.venv/bin/python --version` 得到的结果。

### 推断

- 如果重新搭建环境，建议优先使用 Python 3.12。

推断依据：

- 仓库中已有 `.venv`
- 当前虚拟环境版本是 3.12.12
- 依赖组合与现代 FastAPI / Pydantic v2 / SQLAlchemy 2 系生态兼容

## 应用启动与运行

### 已确认的准备步骤

从脚本可以确认，应用启动前默认依赖 PostgreSQL 可用，并执行迁移和初始化数据：

- [scripts/prestart.sh](scripts/prestart.sh)
  - 先执行 `python app/backend_pre_start.py`
  - 再执行 `alembic upgrade head`
  - 最后执行 `python app/initial_data.py`

其中：

- [app/backend_pre_start.py](app/backend_pre_start.py)
  - 会循环探测数据库连通性
- [app/initial_data.py](app/initial_data.py)
  - 会初始化首个超级用户

### 已确认的外部依赖

从 [app/core/config.py](app/core/config.py) 和 [`.env`](.env) 可知，运行时主要依赖：

- PostgreSQL
- 可选 SMTP
- 可选 Sentry

核心环境变量包括：

- `PROJECT_NAME`
- `ENVIRONMENT`
- `SECRET_KEY`
- `FIRST_SUPERUSER`
- `FIRST_SUPERUSER_PASSWORD`
- `POSTGRES_SERVER`
- `POSTGRES_PORT`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `SMTP_*`

### 已确认的本地启动命令

仓库现在已经提供了明确的本地与部署入口信息：

- [README.md](README.md) 直接给出 `uvicorn app.main:app --reload`
- [vercel.json](vercel.json) 将 [app/main.py](app/main.py) 作为 Vercel 运行入口
- [.vscode/launch.json](.vscode/launch.json) 也使用 `uvicorn` 调试启动

因此当前最可靠的本地启动命令是：

```bash
uvicorn app.main:app --reload
```

如果使用项目自带虚拟环境，可以写成：

```bash
./.venv/bin/uvicorn app.main:app --reload
```

## 代码入口与主要调用链

### FastAPI 入口

- [app/main.py](app/main.py)
  - 创建 FastAPI 应用
  - 配置 OpenAPI 路径
  - 挂载 CORS
  - 通过 `app.include_router(api_router, prefix=settings.API_V1_STR)` 挂载主 API
  - 注册 MCP 服务器

### API 路由入口

- [app/api/main.py](app/api/main.py)
  - 注册模板原生路由：`login`、`users`、`utils`、`items`
  - 在本地环境额外挂载 `private`
  - 注册最小化的 `rz.subsystem.mcp`
  - 注册 `rz` 字典路由

### 数据库与配置

- [app/core/config.py](app/core/config.py)
  - 定义设置项与 `.env` 映射
- [app/core/db.py](app/core/db.py)
  - 创建 SQLModel engine
  - 初始化超级用户

### 模板原生业务

- [app/models.py](app/models.py)
  - 用户、条目、认证相关数据结构
- [app/crud.py](app/crud.py)
  - 用户和条目 CRUD
- [app/api/routes/login.py](app/api/routes/login.py)
  - 登录、密码恢复等模板接口
- [app/api/routes/users.py](app/api/routes/users.py)
  - 用户相关接口
- [app/api/routes/items.py](app/api/routes/items.py)
  - 条目相关接口

### `rz` 字典模块调用链

主要调用链如下：

1. [app/api/routes/rz/dict.py](app/api/routes/rz/dict.py)
   - 接收请求
   - 做参数校验与基础错误处理
2. [app/rz/crud/dict_crud.py](app/rz/crud/dict_crud.py)
   - 执行数据库操作
3. [app/rz/models/dict_type.py](app/rz/models/dict_type.py)
   - 定义字典类型模型
4. [app/rz/models/dict_item.py](app/rz/models/dict_item.py)
   - 定义字典项模型
5. [app/alembic/versions/5ac6edc32020_add_dictionary_and_sync_tables.py](app/alembic/versions/5ac6edc32020_add_dictionary_and_sync_tables.py)
   - 落地数据库表结构

### `rz` MCP 子系统调用链

1. [app/main.py](app/main.py)
   - 调用 `register_mcp_server(app)`
2. [app/rz/subsystem/main.py](app/rz/subsystem/main.py)
   - 用 `FastApiMCP` 注册 HTTP MCP 暴露
3. [app/rz/subsystem/mcp/main.py](app/rz/subsystem/mcp/main.py)
   - 暴露最小化的 MCP 工具清单查询接口

## 测试、格式化与检查

### 已确认命令

当前仓库没有保留额外的格式化、静态检查、测试包装脚本，直接使用底层命令。

格式化：

```bash
ruff check app --fix
ruff format app
```

静态检查：

```bash
mypy app
ruff check app
ruff format app --check
```

测试：

```bash
coverage run --source=app -m pytest
coverage report --show-missing
```

如果需要完整走初始化与数据库准备链路，则继续使用：

- [scripts/prestart.sh](scripts/prestart.sh)

### 测试行为特征

从 [app/tests/conftest.py](app/tests/conftest.py) 可确认：

- 测试不是基于内存数据库
- 测试会直接连接配置中的 PostgreSQL
- session 级 fixture 会调用 `init_db(session)`
- 测试结束后会删除模板原生 `Item` 和 `User`

### 已知注意事项

在当前工作环境中，我实际运行了：

```bash
./.venv/bin/pytest -q app/tests/api/routes/test_login.py app/tests/rz
```

结果全部在测试初始化阶段失败，原因是 PostgreSQL 认证失败，而不是业务断言失败。

这说明：

- 当前环境下，`.env` 中的数据库连接信息与实际本地数据库状态不一致
- 后续测试前应先确认 PostgreSQL 用户、密码、数据库已按当前配置就绪

## 预制模块说明

### 字典模块

字典模块不是临时示例，而是当前仓库中已经成型的 `rz` 扩展样板。

它体现了几个关键设计：

- 领域模型放在 `app/rz/models`
- 数据访问放在 `app/rz/crud`
- API 放在 `app/api/routes/rz`
- 通过模板接缝挂载到主应用
- 数据库通过 Alembic 迁移接入

后续新增业务时，优先参考这个结构。

### MCP 子系统

MCP 子系统在当前分支中仅用于保留最小接入结构。

它说明：

- 当前仓库具备一个可挂接子系统的接缝
- 但在当前分支内，不应据此继续扩展任何非字典类能力

## 当前仍不确定的点

以下内容目前还没有从仓库内完全确认，只能保留为未定项：

### 1. 当前 Vercel 部署所依赖的平台侧环境配置

仓库现在已经提供了 `vercel.json`，但平台侧环境变量、域名绑定和部署参数仍无法仅靠代码完全还原。

### 2. 未来是否会继续扩展更多 `rz` 子结构

当前已经形成 `models`、`crud`、`subsystem`、`utils` 的基本骨架。后续是否固定加入 `services` 等目录，仍取决于需求演化，但这不影响当前接手认知。

## 接手建议

后续接手本仓库时，建议按以下顺序进入：

1. 先读 [AGENTS.md](AGENTS.md)，理解执行边界与扩展规则
2. 再读本文件，建立项目结构和启动链路认知
3. 接着查看 [app/main.py](app/main.py)、[app/api/main.py](app/api/main.py)、[app/core/config.py](app/core/config.py)
4. 如果要开发业务能力，优先参考字典模块
5. 如果需求超出字典模块边界，先确认当前分支是否应该承载该能力

## 一句话总结

这是一个以 FastAPI 模板为基础、通过 `rz` 命名空间承载低耦合扩展的后端仓库。接手时最重要的不是“它有哪些文件”，而是先理解“哪些地方是模板基础、哪些地方是项目扩展、应该从哪里新增代码”。
