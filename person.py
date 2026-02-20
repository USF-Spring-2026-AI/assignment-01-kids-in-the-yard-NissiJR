from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

# Code pattern for using dataclasses (including slots=True in modern Python)
# from https://realpython.com/python-data-classes/ and
# https://stackoverflow.com/questions/75656549/dataclass-code-that-sets-slots-true-if-python-version-allows  # [web:7][web:19]
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
