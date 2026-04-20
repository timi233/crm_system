"""
统一策略层注册表

维护资源到 Policy 的注册关系。
"""

from typing import Dict, Type, Optional
from .types import Resource


# 全局注册表：资源名 -> Policy 类
_policy_registry: Dict[Resource, Type] = {}


def register_policy(resource: Resource, policy_class: Type) -> None:
    """
    注册资源的 Policy 类

    Args:
        resource: 资源名
        policy_class: Policy 类（继承自 BasePolicy）
    """
    _policy_registry[resource] = policy_class


def get_policy_class(resource: Resource) -> Optional[Type]:
    """
    获取资源的 Policy 类

    Args:
        resource: 资源名

    Returns:
        Policy 类，未注册则返回 None
    """
    return _policy_registry.get(resource)


def is_registered(resource: Resource) -> bool:
    """
    检查资源是否已注册 Policy

    Args:
        resource: 资源名

    Returns:
        是否已注册
    """
    return resource in _policy_registry


def list_registered_resources() -> list[Resource]:
    """
    列出所有已注册的资源

    Returns:
        已注册资源名列表
    """
    return list(_policy_registry.keys())


def clear_registry() -> None:
    """
    清空注册表（仅用于测试）
    """
    _policy_registry.clear()
