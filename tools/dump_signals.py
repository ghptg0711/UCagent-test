from __future__ import annotations

import json
import sys
from pathlib import Path


def walk(node: object, prefix: str = "") -> None:
    if isinstance(node, dict) and "Pin" in node:
        high = int(node["High"])
        low = int(node["Low"])
        width = 1 if high == -1 else high - low + 1
        print(f"{prefix:55s} {str(node['Pin']):6s} {width}")
        return
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "_":
                continue
            name = f"{prefix}_{key}" if prefix else key
            walk(value, name)


if __name__ == "__main__":
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "rtl/generated_real/signals.json")
    walk(json.loads(path.read_text()))
