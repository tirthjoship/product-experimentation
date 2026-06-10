"""Serialize experiment results (dict or list) to JSON. Tuples -> arrays; numpy -> python scalars."""

import json
from pathlib import Path
from typing import Any

import numpy as np


def _default(o: Any) -> Any:
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, np.integer):
        return int(o)
    raise TypeError(f"not JSON-serializable: {type(o)!r}")


def results_to_json(results: Any) -> str:
    return json.dumps(results, indent=2, default=_default)


def write_results_json(results: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(results_to_json(results) + "\n")
