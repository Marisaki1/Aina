# Import memory module for easier access
from . import memory

# Allow direct imports from core
from .memory.memory_manager import MemoryManager

__all__ = [
    'memory',
    'MemoryManager'
]