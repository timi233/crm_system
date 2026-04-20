"""
统一策略层上下文定义

定义 PrincipalContext，统一封装当前登录用户信息。
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass(slots=True)
class PrincipalContext:
    """
    当前登录用户上下文

    替代在各处传裸 dict，统一封装用户信息。
    现阶段保留和当前 get_current_user() 返回内容兼容。
    """

    user_id: int
    role: str
    email: Optional[str] = None
    name: Optional[str] = None

    # 扩展字段（预留）
    department_id: Optional[int] = field(default=None)
    region: Optional[str] = field(default=None)

    @classmethod
    def from_dict(cls, user_dict: dict) -> "PrincipalContext":
        """
        从 get_current_user() 返回的 dict 构建

        Args:
            user_dict: 包含 id, role, email, name 等字段的字典

        Returns:
            PrincipalContext 实例
        """
        return cls(
            user_id=user_dict.get("id", 0),
            role=user_dict.get("role", ""),
            email=user_dict.get("email"),
            name=user_dict.get("name"),
        )

    @property
    def is_admin(self) -> bool:
        """是否为管理员"""
        return self.role == "admin"

    @property
    def is_business(self) -> bool:
        """是否为准管理员（业务角色）"""
        return self.role == "business"

    @property
    def is_sales(self) -> bool:
        """是否为销售人员"""
        return self.role == "sales"

    @property
    def is_finance(self) -> bool:
        """是否为财务人员"""
        return self.role == "finance"

    @property
    def is_technician(self) -> bool:
        """是否为技术员"""
        return self.role == "technician"

    @property
    def has_full_access(self) -> bool:
        """是否有全量访问权限（admin 或 business）"""
        return self.role in ("admin", "business")

    @property
    def has_read_only_access(self) -> bool:
        """是否有只读全量权限（finance）"""
        return self.role == "finance"
