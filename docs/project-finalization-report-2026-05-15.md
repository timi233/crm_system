# 项目联合审查收口报告

日期：2026-05-15

## 背景

本轮围绕 CRM 当前系统代码完成多 agent 联合审查与整改：

- agent2：后端审查、协调、最终集成与文档收口。
- agent4：前端与原型设计审查、前端构建修复、离职交接前端权限同步。
- agent1：需求澄清与方案设计审查。
- agent3：后端整改、格式门禁收口。

## 本轮已收口事项

### 前端

- 修复 TypeScript 构建错误，`npm run build` 已恢复通过。
- 修复 `FollowUpList` props、mutation 参数、Hook 解构、缺失导入等编译问题。
- 离职交接操作按钮按业务规则调整为：`admin` 或交接单 `team_manager_user_id` 对应的部门负责人可操作。
- 工作台移除硬编码完成率，改为依赖后端 `completion_rate` 指标；无数据时不展示占位进度条。
- 待办中心对无跳转链接的待办补充反馈。
- 清理前端行尾空格，`git diff --check` 通过。

### 后端

- 日报/周报团队视图权限收口：部门负责人可读取团队成员报告详情和评论，不能代为编辑、提交或撤回。
- `channel_ops` 能力补齐：渠道读取、渠道绩效、渠道培训入口能力与角色定位一致。
- 离职交接操作规则调整为：`admin` 可操作全部交接单；部门负责人可操作 `team_manager_user_id` 等于自己的交接单。
- 派工记录列表补有界分页。
- 待办中心派生来源增加查询上限，避免无界全量聚合。
- 产品装机记录接入统一策略层。
- 产品装机凭据完成字段级加密改造：
  - 新增 `PRODUCT_INSTALLATION_CREDENTIAL_KEY`。
  - 新增密文字段 `username_ciphertext`、`password_ciphertext`、`login_url_ciphertext`。
  - 新写入/更新只写密文字段并清空旧明文字段。
  - 列表只返回掩码，凭据接口在授权后解密返回。
  - 提供存量迁移脚本 `backend/scripts/encrypt_product_installation_credentials.py`。
- 金蝶/财务导出相关 capability 隐藏：
  - `kingdee_integration:read`
  - `financial_export:read`
  - `financial_export:summary`

### 文档

- README 标明金蝶/财务导出 router 存在但未注册，capability 已隐藏。
- AGENTS.md 标明金蝶/财务导出不能视为已启用线上能力。
- 部署文档补充 `PRODUCT_INSTALLATION_CREDENTIAL_KEY`。
- 项目 review 计划补充金蝶/财务导出隐藏状态。
- 本报告记录本轮审查、整改和验证结果。

## 部署注意事项

### 数据库迁移

当前 Alembic head：

```text
product_installation_credential_ciphertext_20260515
```

部署时先执行：

```bash
cd backend
./venv/bin/alembic upgrade head
```

### 产品装机凭据加密

生产环境必须配置至少 32 字符的随机密钥：

```env
PRODUCT_INSTALLATION_CREDENTIAL_KEY=<random-32-char-minimum-secret>
```

迁移表结构后，对存量明文凭据执行一次加密清理：

```bash
cd backend
./venv/bin/python scripts/encrypt_product_installation_credentials.py
```

脚本会把旧 `username/password/login_url` 明文加密写入对应 `*_ciphertext` 字段，并清空旧明文字段。

## 验证结果

后端：

```bash
cd backend
APP_ENV=test ./venv/bin/python -m pytest -q
# 317 passed, 10 warnings

./venv/bin/alembic heads
# product_installation_credential_ciphertext_20260515 (head)

./venv/bin/alembic upgrade head --sql
# passed
```

前端：

```bash
cd frontend
npm test
# 26 passed

npm run build
# passed
```

全仓库格式门禁：

```bash
git diff --check
# passed
```

## 后续建议

- 若要启用金蝶或财务导出，应作为独立需求重新评估：注册 router、补权限矩阵、分页/导出范围、测试和前端入口。
- 产品装机凭据后续可继续做密钥轮换、凭据查看操作日志入库、旧明文字段物理删除。
- 下一阶段新功能建议先建立“角色 x capability x 菜单 x API”矩阵，避免角色能力和页面入口再次脱节。
