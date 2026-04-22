# 测试环境部署包说明

本说明面向本仓库导出的测试环境运行包。

## 1. 包内包含内容

- `docker-compose.yml`
- `docker-compose.env.example`
- `backend/` 运行时源码、Alembic 迁移、环境模板、初始化脚本
- `frontend/` 运行时源码、Nginx 配置、前端构建配置
- `docs/` 中与部署和排障直接相关的文档

## 2. 测试环境部署步骤

1. 进入部署包根目录。
2. 复制配置模板：

   ```bash
   cp docker-compose.env.example .env
   ```

3. 编辑 `.env`，至少替换以下变量：
   - `POSTGRES_USER`
   - `POSTGRES_PASSWORD`
   - `POSTGRES_DB`
   - `JWT_SECRET_KEY`
   - `FEISHU_APP_ID`
   - `FEISHU_APP_SECRET`
   - `FRONTEND_PUBLIC_URL`
   - `BACKEND_PUBLIC_URL`
   - `ALLOWED_ORIGINS`
   - `NGINX_SERVER_NAME`

4. 启动容器：

   ```bash
   docker compose up -d --build
   ```

5. 执行数据库迁移：

   ```bash
   docker compose run --rm backend alembic upgrade head
   ```

6. 如果测试库为空，初始化管理员账号：

   ```bash
   docker compose run --rm backend python create_test_user.py
   ```

7. 如需补充基础字典数据，可执行：

   ```bash
   docker compose run --rm backend python seed_dict_data.py
   ```

## 3. 验证项

- 前端：`https://crm-test.example.com`
- 后端健康检查：`https://crm-test.example.com/health`
- Swagger：`https://crm-test.example.com/docs`

## 4. 说明

- 当前部署包面向 Docker 测试环境，不依赖仓库开发态的 `venv/`、`node_modules/`、截图、测试文件和临时脚本。
- `backend/.env.test` 保留在包中作为后端单独运行时的参考模板；Docker 部署以根目录 `.env` 为准。
