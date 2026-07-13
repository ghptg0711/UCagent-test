from __future__ import annotations

from .reference_model import CacheParams

# tools/RealCacheMain.scala fixes totalSize=32 KiB, ways=4. NutShell Cache.scala
# defines LineSize=XLEN bytes (64 for the generated RV64 configuration).
REAL_DUT_CACHE_PARAMS = CacheParams(sets=128, ways=4, line_bytes=64)
