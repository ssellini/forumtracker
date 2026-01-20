from dataclasses import dataclass, asdict
from typing import Literal

@dataclass
class Topic:
    id: str
    name: str
    url: str
    forum_type: Literal["vbulletin", "xenforo", "auto"]

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'Topic':
        return cls(**data)
