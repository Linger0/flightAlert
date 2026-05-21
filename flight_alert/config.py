import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .city_codes import normalize_city


@dataclass(frozen=True)
class MonitorConfig:
    mode: int
    place_from: str
    place_to: str
    target_price: int
    price_step: int
    ftqq_sckey: list[str]
    date_to_go: list[str]
    date_back: list[str]
    poll_time: str = "10:00:00"

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "MonitorConfig":
        tokens = raw.get("ftqq_SCKEY", [])
        if isinstance(tokens, str):
            tokens = [tokens]

        return cls(
            mode=int(raw.get("mode", 2)),
            place_from=normalize_city(str(raw["placeFrom"])),
            place_to=normalize_city(str(raw["placeTo"])),
            target_price=int(raw.get("targetPrice", 1000)),
            price_step=int(raw.get("priceStep", 20)),
            ftqq_sckey=list(tokens),
            date_to_go=[str(item) for item in raw.get("dateToGo", [])],
            date_back=[str(item) for item in raw.get("dateBack", [])],
            poll_time=str(raw.get("pollTime", "10:00:00")),
        )


def load_config(path: str | Path) -> MonitorConfig:
    with Path(path).open("r", encoding="utf-8") as fh:
        return MonitorConfig.from_dict(json.load(fh))
