"""
统一策略层类型定义

定义 Action、Resource、PolicyDecision 等核心类型。
"""

from typing import Literal, Union
from dataclasses import dataclass
from enum import Enum


# 标准动作集合
Action = Literal[
    "list",
    "read",
    "create",
    "update",
    "delete",
    "manage",
]

# 扩展动作（可选，用于特殊场景）
ExtendedAction = Literal[
    "export",
    "approve",
    "assign",
]

AllActions = Union[Action, ExtendedAction]


# 显式注册的资源名
Resource = Literal[
    "user",
    "customer",
    "lead",
    "opportunity",
    "project",
    "contract",
    "follow_up",
    "channel",
    "channel_assignment",
    "product",
    "work_order",
    "alert",
    "alert_rule",
    "sales_target",
    "operation_log",
    "knowledge",
    "evaluation",
    "dispatch_record",
    "product_installation",
    "execution_plan",
    "unified_target",
]


class PolicyDecision(Enum):
    """权限决策结果"""

    ALLOW = "allow"
    DENY = "deny"
    NOT_APPLICABLE = "not_applicable"


@dataclass(slots=True)
class PolicyResult:
    """
    权限检查结果

    用于 can() 等非强制场景，返回布尔值而不抛异常。
    """

    decision: PolicyDecision
    reason: str | None = None

    @property
    def allowed(self) -> bool:
        return self.decision == PolicyDecision.ALLOW
