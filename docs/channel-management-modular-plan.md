# 渠道管理模块化与跟进域拆分方案

## 目标

将“跟进记录”拆分为两个明确业务域，并完成渠道管理模块化导航：

1. 业务管理：`业务跟进`
2. 渠道管理：`渠道档案`、`渠道跟进`、`渠道业绩`、`渠道培训`

核心要求：

- 跟进数据仍使用同一张 `follow_ups` 表；
- 通过 `follow_up_type` 做域隔离（`business` / `channel`）；
- 前端路由与菜单分开，避免“业务跟进页面看见渠道记录”的混淆。

## 信息架构

### 业务管理

- 终端客户
- 线索管理
- 商机管理
- 项目管理
- **业务跟进**（`/business-follow-ups`）

### 渠道管理

- 渠道档案（`/channels`）
- **渠道跟进**（`/channel-follow-ups`）
- 渠道业绩（`/channel-performance`）
- 渠道培训（`/channel-training`）

## 技术策略

### 1) 后端查询分流（必须）

- 在 `GET /follow-ups/` 增加可选过滤参数 `follow_up_type`；
- 前端业务页固定传 `follow_up_type=business`；
- 前端渠道页固定传 `follow_up_type=channel`。

### 2) 前端路由拆分（必须）

- 新增：
  - `/business-follow-ups`
  - `/channel-follow-ups`
  - `/channel-performance`
  - `/channel-training`
- 兼容旧入口：
  - `/follow-ups` -> 重定向到 `/business-follow-ups`。

### 3) 跟进表单按域展示（第一阶段）

- 业务跟进：
  - 关联对象：线索/商机/项目（至少一个）
  - 字段重点：跟进结论、下次行动
- 渠道跟进：
  - 关联对象：渠道（必选）
  - 字段重点：拜访目的、拜访地点、参与人员

### 4) 字典治理（第一阶段兼容）

- 渠道跟进优先读取：
  - `拜访方式`
  - `拜访目的`
- 若字典尚未初始化，兼容回退到：
  - `跟进方式`

## 分阶段实施

### P1（本轮实施）

- 路由/菜单拆分上线；
- `follow_up_type` 后端过滤与前端透传；
- `FollowUpList` 支持 `mode=business|channel`；
- 新增“渠道业绩/渠道培训”页面骨架；
- 旧路由兼容重定向。

### P2

- 渠道业绩页面接入渠道业绩指标接口；
- 渠道培训页面接入培训计划/签到/完成率。
- 执行计划新增结构化字段 `plan_category`（`general` / `training`）；
- 后端过滤接口支持：
  - `GET /execution-plans/?plan_category=training`
  - `GET /execution-plans/?plan_category=general`

### P3

- 将业务跟进与渠道跟进的策略授权进一步拆分（能力点、按钮级权限）。

### P4

- 增加端到端自动化用例（业务跟进/渠道跟进双域回归）。

## 验收标准

1. 进入“业务跟进”不再出现 `follow_up_type=channel` 数据；
2. 进入“渠道跟进”不再出现 `follow_up_type=business` 数据；
3. `/follow-ups` 旧链接可正常跳转到业务跟进；
4. 新菜单下可看到四个渠道模块入口；
5. `npm run build` 与 `npx tsc --noEmit` 通过。
