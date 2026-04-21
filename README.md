# Rzplan-vercel

本项目基于上游 [fastapi/full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template) 的后端部分提取并演化而来。

当前仓库的维护目标是：

- 保留与上游模板的低耦合关系
- 在此基础上通过 `rz` 命名空间承载项目扩展
- 对 Vercel 部署保持友好，但不限制后续扩展只能运行在 Vercel 上

当前分支已经预置了两类 `rz` 扩展示例：

- 字典模块
- MCP 子系统

## 分支说明

- `sync-repo`
  - 用于和上游模板同步
- `release`
  - 当前项目的核心发布分支
- 其他分支
  - 可以基于同步分支继续初始化或扩展，但适合当前仓库的通用配置、说明和部署元信息可以按需从 `release` 吸收

## 文档

- [AGENTS.md](AGENTS.md)
  - 项目执行规范，约束后续开发应该如何扩展和修改
- [PROJECT_HANDOFF.md](PROJECT_HANDOFF.md)
  - 项目接手说明，帮助建立代码结构、启动方式和调用链认知

## 快速开始

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

应用启动后可访问：

- `http://127.0.0.1:8000/docs`

## 初始化

初次部署或首次准备数据库时，可以执行：

```bash
bash scripts/prestart.sh
```

该脚本会依次完成：

- 等待数据库可用
- 执行 Alembic 迁移
- 初始化默认超级用户

环境变量示例请参考 [env.example](env.example)。

## 本地检查与测试

当前仓库不再保留上游模板里的包装脚本，日常开发直接使用底层命令即可。

静态检查：

```bash
mypy app
ruff check app
ruff format app --check
```

格式化：

```bash
ruff check app --fix
ruff format app
```

测试：

```bash
coverage run --source=app -m pytest
coverage report --show-missing
```

## 数据库迁移

```bash
alembic revision --autogenerate -m "your message"
alembic upgrade head
```

如果需要回滚最近一次迁移：

```bash
alembic downgrade -1
```

## Vercel

仓库根目录包含 [vercel.json](vercel.json)，当前使用 `@vercel/python` 运行 [app/main.py](app/main.py)。

本地开发命令与 Vercel 的运行入口保持一致，默认仍然使用：

```bash
uvicorn app.main:app --reload
```

## 调试

仓库包含 [.vscode/launch.json](.vscode/launch.json)，可直接在 VSCode 中使用 Python 调试配置启动 FastAPI。
