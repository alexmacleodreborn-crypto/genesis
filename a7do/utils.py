from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict


def now_ts() -> float:
    return datetime.utcnow().timestamp()


def dataclass_to_dict(obj: Any) -> Dict:
    return asdict(obj)
