# Rzplan-vercel 
**本项目是一个`Vercel`的`Python Runtime guide`运行示例**

------ 
- 上游项目 [https://github.com/fastapi/full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template)
- 当前项目是单独分离上游项目的 `backend` 端，在此基础上进行的二次开发。
- `master` 分支为发布分支， 用于发布到 `vercel`
- `sync-repo` 分支是同步分支，主要用于同步上游项目的修改
- `devement` 为开发分支
- `pre-dev` 为预发布分支
-------- 

# backend for the project
## How to run
```bash
$> python -m venv .venv
$> source .venv/bin/activate
$> pip install -r requirements.txt

$> uvicorn app.main:app --reload
```

## 系统后端初始化 -  初次部署使用 
```bash
# 包含初始化配置的默认用户 .env 中指定 
$> bash scripts/prestart.sh
```

## 数据库升级回滚 - 开发时使用
```bash
$> alembic revision --autogenerate -m  'commit message'
# 修改对应内容
$> alembic upgrade head

# 回滚一次，回滚后可以直接重新升级
$> alembic downgrade -1
```

## 测试数据生成
```bash
$> python app/tests/scripts/generate_test_performance_data.py
```