# 审计整改项目计划

制定日期：2026-05-12
依据文档：`docs/代码审计报告/ 全栈项目专业代码审计报告.md`、`contract_audit.json`、`backend_audit.json`、`frontend_audit.json`、`npm_audit_summary.json`、`TEST_REPORT.md`

## 目标

本轮整改目标是先处理影响上线稳定性和安全边界的 P0/P1 问题，使项目达到“核心链路可用、测试可通过、主要安全风险有明确处置”的状态。大型架构重构、全面 OpenAPI 生成和前端大页面拆分放入后续迭代。

## 执行原则

- 不回滚当前工作树中已有改动，先识别并保护现有未提交文件。
- 每个批次都要有可运行验证命令和明确验收标准。
- 优先修复实际运行路径，清理或标注未注册历史实现，避免继续出现“改了但没生效”的代码。
- 安全类问题优先采用默认拒绝、最小权限、显式例外的策略。

## 第 0 阶段：执行前基线确认

负责人：opencode
建议耗时：0.5 天

任务：

1. 记录当前 Git 状态，确认已有改动来源。
2. 确认审计报告中的路径与当前代码是否一致。
3. 跑一次最小基线测试，保存失败列表。

建议命令：

```bash
git status --short
APP_ENV=test pytest -q
cd frontend && npm audit --json > ../docs/npm-audit-current.json
cd frontend && npx tsc --noEmit
```

验收标准：

- 明确哪些文件是执行前已有改动。
- 明确当前 pytest 失败项是否仍为销售目标相关接口。
- 明确当前 npm audit high 漏洞数量。

## 第 1 阶段：P0 安全与可用性修复

负责人：opencode
建议耗时：1-3 天

### 1.1 处理环境文件入库风险

问题来源：主报告严重问题 3。

任务：

1. 将真实或准真实环境文件从 Git 索引移除，仅保留示例文件。
2. 更新 `.gitignore`，默认忽略 `.env` 和 `.env.*`，显式允许示例文件。
3. 检查 `backend/.env.production`、`backend/.env.test` 是否包含真实密钥；如包含，输出需要轮换的密钥清单。

建议实现：

```bash
git rm --cached backend/.env.production backend/.env.test
```

验收标准：

- `git ls-files | grep -E '(^|/)\\.env(\\.|$)'` 不再出现生产或测试密钥文件。
- `.env.example`、`backend/.env.example` 等示例文件仍可被跟踪。
- 文档或提交说明中列出是否需要轮换 JWT、飞书、Webhook、数据库密钥。

### 1.2 修复项目模块编辑/删除不可用

问题来源：主报告严重问题 1、严重问题 7；契约审计 `DELETE /projects/${id}` 不匹配。

任务：

1. 在实际注册的 `backend/app/routers/project.py` 中实现 `PUT /projects/{project_id}` 和 `DELETE /projects/{project_id}`。
2. 合并 `project.py` 与未注册 `projects.py` 中更完整的校验逻辑。
3. 确认前端 `frontend/src/hooks/useProjects.ts` 的更新和删除调用与后端一致。
4. 增加后端测试覆盖：更新成功、删除成功、无权限、资源不存在、非法外键或非法金额。

验收标准：

- 项目管理页编辑/删除不再因路由不存在返回 404。
- `ProjectUpdate` 仅更新显式传入字段。
- 创建/更新项目时校验客户、负责人、渠道、来源商机等外键存在性和金额范围。
- 项目相关测试通过。

### 1.3 修复销售目标年度更新/删除伪契约

问题来源：主报告严重问题 2；pytest 当前存在 3 个失败。

任务：

1. 明确当前产品语义：年度目标是否允许更新/删除。
2. 若允许，实现 `PUT /sales-targets/{target_id}` 和 `DELETE /sales-targets/{target_id}`。
3. 更新逻辑必须校验子目标合计不能超过父目标。
4. 删除逻辑必须校验存在子目标或实际值时的保护规则。
5. 若不允许，删除或改写前端入口和测试，避免保留伪契约。

建议优先选择：实现接口并满足现有测试。

验收标准：

- `APP_ENV=test pytest -q` 全部通过，或只剩与本任务无关且已说明的失败。
- 年度目标更新/删除接口不再返回路由级 404。
- 错误响应为稳定的 400/403/404，而不是 500。

### 1.4 处理前端依赖高危漏洞

问题来源：主报告严重问题 5；`npm_audit_summary.json` 显示 high 14。

任务：

1. 执行非破坏性修复，评估 package-lock 变化。
2. 对 `react-scripts` 链路无法无损修复的漏洞，形成例外清单或迁移计划。
3. 不在本批次强行迁移 Vite，除非当前依赖已无法安全修复或构建失败。

建议命令：

```bash
cd frontend
npm audit fix
npm audit --json
npm run build
npx tsc --noEmit
```

验收标准：

- high 漏洞降为 0；或保留项有明确原因、影响面和后续迁移计划。
- 前端 TypeScript 检查和构建通过。

## 第 2 阶段：P1 权限、Webhook 与 API 边界

负责人：opencode
建议耗时：3-7 天

### 2.1 将默认权限策略改为默认拒绝

问题来源：主报告严重问题 4。

任务：

1. 修改 `DefaultPolicy`，未注册资源默认 403。
2. 补齐策略注册或显式白名单，避免现有合法页面被误伤。
3. 增加策略注册测试和至少一个未注册资源默认拒绝测试。

验收标准：

- 未注册资源读写默认拒绝。
- 已注册核心资源的现有权限测试通过。
- Capability 与后端对象级授权没有明显冲突。

### 2.2 为派工 Webhook 增加重放防护和幂等

问题来源：主报告严重问题 6。

任务：

1. 要求请求头包含 `X-Dispatch-Timestamp` 和 `X-Dispatch-Event-Id`。
2. 签名内容改为 `timestamp + "." + body`。
3. 限制时间窗口，建议 5 分钟。
4. 增加事件幂等记录表或复用可靠的幂等存储。
5. 增加测试：缺少头、过期时间戳、签名错误、重复事件、正常事件。

验收标准：

- 重放请求被拒绝或安全忽略。
- 重复事件不会重复修改业务状态。
- 外部系统集成文档同步更新。

### 2.3 修复端到端报告中的高优页面错误

问题来源：`TEST_REPORT.md`。

任务：

1. 修复 `/operation-logs` 认证失败或前端请求路径问题。
2. 修复 `/alert-rules` 500 错误。
3. 对两个页面增加后端或前端回归测试。

验收标准：

- 管理员登录后可访问操作日志。
- 预警中心不再弹出服务器内部错误。
- 相关接口返回稳定错误码和响应结构。

### 2.4 为关键列表接口增加分页上限

问题来源：主报告一般问题 2；后端扫描约 56 个列表接口缺分页。

任务：

1. 先覆盖客户、渠道、合同、项目、工单、销售目标、操作日志等高频列表。
2. 默认 `limit=20`，最大 `limit=100`。
3. 前端同步适配分页响应，避免一次性拉全量数据。

验收标准：

- 高流量列表接口有 `skip/limit` 或等价分页。
- 超过最大 limit 会被限制或返回 422。
- 前端列表分页行为正常。

## 第 3 阶段：工程化收敛

负责人：opencode
建议耗时：1-2 周

任务：

1. 清理未注册 Router 或迁移到 `deprecated`，重点处理 `projects.py`、`financials.py`、`kingdee_integration.py`。
2. 增加路由注册清单测试，防止 API inventory 漂移。
3. 增加前后端契约测试，至少覆盖报告中已发现的不匹配接口。
4. 逐步减少前端空 `catch`、重复错误提示和高风险 `any`。

验收标准：

- 新增接口变更能被契约测试发现。
- 未注册历史 Router 有明确处置。
- 前端错误处理策略统一，不吞掉关键异常。

## 第 4 阶段：剩余风险清零

负责人：opencode
建议耗时：1-2 周
状态：2026-05-12 追加，基于上一轮验收结果继续执行。

上一轮验收结果：

- 后端测试通过：`136 passed, 10 warnings`。
- 前端 TypeScript 通过：`npx tsc --noEmit` 无错误。
- 前端构建通过，但主包 gzip 后约 `803.05 kB`，仍显著偏大。
- `npm audit --json` 仍有 `high: 6`，主要来自 `react-scripts` 间接依赖链。
- 关键列表接口已加入 `skip/limit`，但缺少专门回归测试。

### 4.1 清零前端 npm 高危漏洞

问题来源：主报告严重问题 5；上一轮验收仍剩 `high: 6`。

目标：

- 不再接受只写例外清单作为最终状态。
- 优先通过迁移构建链或移除高危依赖链，使 `npm audit --json` 中 `metadata.vulnerabilities.high == 0`。

建议路线：

1. 评估当前 CRA/react-scripts 迁移成本。
2. 优先迁移到 Vite + React + TypeScript，保留现有 React 18、Ant Design、Redux Toolkit、TanStack Query、React Router 等业务代码。
3. 移除 `react-scripts`、CRA 专属配置和不再需要的依赖。
4. 迁移入口文件、HTML 模板、环境变量前缀、代理配置和构建脚本。
5. 确保开发、构建和类型检查脚本可用。

验收标准：

- `cd frontend && npm audit --json` 显示 `high: 0`。
- `cd frontend && npx tsc --noEmit` 通过。
- `cd frontend && npm run build` 通过。
- 构建产物无明显空白页风险，入口 HTML、root 挂载点和路由 basename 正常。
- 如必须保留某个非 high 漏洞，需说明影响范围和后续动作。

### 4.2 补齐分页上限回归测试

问题来源：主报告一般问题 2；上一轮已实现关键列表接口 `skip/limit`，但缺少测试。

任务：

1. 为关键列表接口补测试，至少覆盖：
   - 默认 `limit=20` 生效。
   - `skip` 生效。
   - `limit=100` 允许。
   - `limit=101` 返回 422。
   - `skip=-1` 返回 422。
2. 覆盖接口至少包括：
   - `/customers/`
   - `/contracts/`
   - `/leads/`
   - `/opportunities/`
   - `/projects/`
   - `/work-orders/`
3. 如测试夹具创建数据成本过高，可先做参数校验测试，再为至少一个核心列表补真实分页数据测试。

验收标准：

- 新增分页测试纳入 pytest。
- `APP_ENV=test ./venv/bin/python -m pytest -q` 通过。
- 测试能证明超过最大 limit 被 FastAPI 拒绝，而不是依赖人工检查。

### 4.3 治理前端主包过大风险

问题来源：主报告优化建议 3；上一轮构建主包 gzip 后约 `803.05 kB`。

任务：

1. 结合 Vite 迁移结果分析包体。
2. 对 ECharts、报表页、渠道绩效页、管理后台重页面采用路由级懒加载。
3. 避免为了降包体改动业务语义。
4. 输出构建后主要 chunk 尺寸。

验收标准：

- `npm run build` 通过。
- 首屏主入口 chunk 相比 `803.05 kB gzip` 有明显下降；如 Vite 输出口径不同，提供 gzip 后可比数据。
- 重页面通过动态 import 拆分，首屏不再一次性打入全部业务页面。

### 4.4 复核安全与契约修复

任务：

1. 复核 `.env.production`、`.env.test` 是否仍未被 Git 跟踪。
2. 复核项目 `PUT/DELETE`、销售目标 `PUT/DELETE`、Webhook 重放防护仍有测试覆盖。
3. 确认迁移前端构建链后 API baseURL、代理和生产构建部署路径没有回退。

验收标准：

- `git ls-files | grep -E '(^|/)\\.env(\\.|$)|(^|/)\\.env$'` 只允许 example 类文件。
- 后端测试仍为全绿。
- 前端类型检查、构建和 audit 全部通过。

### 4.5 最新验收状态

更新时间：2026-05-12
验收人：codex

独立验收结果：

- `cd backend && APP_ENV=test ./venv/bin/python -m pytest -q`：`142 passed, 10 warnings`。
- `cd frontend && npx tsc --noEmit`：通过。
- `cd frontend && npm audit --json`：`info=0, low=0, moderate=0, high=0, critical=0, total=0`。
- `cd frontend && npm run build`：通过。
- `git ls-files | grep -E '(^|/)\\.env(\\.|$)|(^|/)\\.env$'`：仅跟踪 `backend/.env.example` 与 `backend/.env.dispatch.example`。

构建结果摘要：

- 已迁移到 Vite，`react-scripts` 已移除。
- Vite circular chunk 警告已消失。
- 首屏入口 chunk gzip 约 `27.86 kB`，较 CRA 主包 `803.05 kB gzip` 显著下降。
- `antd` 与 `echarts` 已独立分块，gzip 分别约 `385.31 kB` 与 `370.66 kB`；仍有大 chunk 提示，但属于业务库独立分块后的非阻断优化项。

## 第 5 阶段：收尾与交付

负责人：opencode
状态：待执行。

目标：

把本轮审计整改从“代码已修复”推进到“可审阅、可交付、可回归”的状态，补齐收尾文档、烟测说明和剩余非阻断优化项。

任务：

1. 更新或新增整改完成报告，记录 P0/P1/P4 的最终修复内容、修改文件、验证命令和结果。
2. 复核 Vite 迁移后的开发体验：
   - `npm run dev` 是否可启动在 `3002`。
   - `/api` 代理是否仍转发到 `localhost:8000`。
   - 生产构建产物仍输出到 `frontend/build`。
3. 做一次前端 smoke 检查：
   - 启动 Vite 开发服务。
   - 至少打开登录页或根路由，确认不是空白页。
   - 如无法启动后端，记录原因，不阻塞前端静态验证。
4. 复核分页测试质量：
   - 现有 `test_pagination.py` 已覆盖非法参数和 `limit=100`。
   - 如成本可控，为至少一个核心列表补充真实数据分页测试，证明 `skip` 与默认 `limit` 实际生效。
5. 复核工作树中与本轮无关的文件：
   - `docker-compose.yml`
   - `backup_pg14_20260512_102837.sql`
   - `docs/代码审计报告/`
   不要回滚这些文件，只在交付说明中标注它们是既有或外部变更。

验收标准：

- 最终整改报告存在且内容包含验证结果。
- 不引入新的 `npm audit` 漏洞。
- 后端测试、前端类型检查、前端构建仍通过。
- smoke 检查结果明确记录。
- 当前 CCB/opencode 队列不再卡在 running 状态。

## 推荐执行顺序

1. 第 0 阶段基线确认。
2. 第 1 阶段中的环境文件、项目接口、销售目标接口。
3. 跑后端测试并修复阻断项。
4. 前端 npm audit 与构建验证。
5. 第 2 阶段权限默认拒绝、Webhook、页面高优错误。
6. 第 3 阶段工程化测试和清理。
7. 第 4 阶段剩余风险清零：先处理 `npm audit high=0`，再补分页测试和包体治理。
8. 第 5 阶段收尾交付：补最终报告、smoke 检查和交付说明。

## 交付物

- 代码改动。
- 测试结果摘要。
- 如保留安全例外，必须不包含 high 漏洞；否则本轮不算完成。
- 更新相关文档：环境变量、Webhook 签名、API 契约或测试说明。
- 最终整改完成报告与 smoke 检查记录。
