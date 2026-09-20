from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Settings:
    data_dir: Path = Path("data")
    host: str = "127.0.0.1"
    port: int = 8765
    refresh_hours: float = 6.0
    max_items: int = 100
    max_concurrency: int = 4

    def __post_init__(self) -> None:
        if self.refresh_hours <= 0:
            raise ValueError("refresh_hours must be positive")
        if not 1 <= self.port <= 65535:
            raise ValueError("port must be between 1 and 65535")
        if self.max_items < 1:
            raise ValueError("max_items must be positive")
        if self.max_concurrency < 1:
            raise ValueError("max_concurrency must be positive")

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            data_dir=Path(os.getenv("SCRAPIARY_DATA_DIR", "data")),
            host=os.getenv("SCRAPIARY_HOST", "127.0.0.1"),
            port=int(os.getenv("SCRAPIARY_PORT", "8765")),
            refresh_hours=float(os.getenv("SCRAPIARY_REFRESH_HOURS", "6")),
            max_items=int(os.getenv("SCRAPIARY_MAX_ITEMS", "100")),
            max_concurrency=int(os.getenv("SCRAPIARY_MAX_CONCURRENCY", "4")),
        )
