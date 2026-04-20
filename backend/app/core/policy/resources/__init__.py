"""
统一策略层资源 Policy 子包

每个资源的具体 Policy 实现放在此目录下。
Phase 1 阶段暂不实现具体 Policy，Phase 2 迁移时逐步添加。
"""

from ..registry import register_policy
from ..base import BasePolicy

# Phase 2 迁移时在此导入具体 Policy 并注册
# 示例：
# from .lead import LeadPolicy
# register_policy("lead", LeadPolicy)
