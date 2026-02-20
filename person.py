from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(slots=True)
class Person:
    """Represents one person in the family tree."""

    person_id: int
    year_born: int
    year_died: int
    first_name: str
    last_name: str
    partner: Optional["Person"] = None
    children: List["Person"] = field(default_factory=list)

    def full_name(self) -> str:
        """Return full name for duplicate detection."""
        return f"{self.first_name} {self.last_name}"