"""A2IA tools package initialization.

We avoid eager imports to prevent circular dependencies.
Tools are registered dynamically by the MCP runtime.
"""

# Lazy initialization — do not import submodules here to avoid circular import issues.

__all__ = []
