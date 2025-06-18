"""Observatory Dashboard Module"""

from .views import create_observatory_content
from .callbacks import register_callbacks

__all__ = ["create_observatory_content", "register_callbacks"] 