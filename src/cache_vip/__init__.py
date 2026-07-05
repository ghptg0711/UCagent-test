"""Reusable verification components for NutShell-like cache DUTs."""

from .coverage import Coverage
from .generator import CacheGenerator
from .memory_agent import MemoryRequest, MemoryResponse, ScriptedMemoryAgent
from .reference_model import CacheParams, ReferenceCache
from .scoreboard import Scoreboard
from .transactions import CacheOp, CacheTxn

__all__ = [
    "CacheGenerator",
    "CacheOp",
    "CacheParams",
    "CacheTxn",
    "Coverage",
    "MemoryRequest",
    "MemoryResponse",
    "ReferenceCache",
    "Scoreboard",
    "ScriptedMemoryAgent",
]
