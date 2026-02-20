from __future__ import annotations

import random
from collections import deque
from typing import Deque, Dict, List, Optional, Set

from person import Person
from personfactory import PersonFactory, decade_of


def clamp_int(value: int, lo: int, hi: int) -> int:
    # Clamp pattern max(lo, min(hi, value)) is standard,
    # as in many examples on StackOverflow when constraining a value to a range:
    # https://stackoverflow.com/questions/5996881/how-to-limit-a-number-to-be-within-a-specified-range  # [web:18]
    return max(lo, min(hi, value))


class FamilyTree:
    """Generates and stores the family tree."""

    def __init__(
        self,
        factory: PersonFactory,
        start_year: int = 1950,
        stop_year: int = 2120,
    ) -> None:
        self.factory = factory
        self.start_year = start_year
        self.stop_year = stop_year

        self.root_a: Optional[Person] = None
        self.root_b: Optional[Person] = None

        self.people: List[Person] = []
        self._seen_ids: Set[int] = set()
        self._expanded: Set[int] = set()

    def initialize_roots(self, person_a: Person, person_b: Person) -> None:
        self.root_a = person_a
        self.root_b = person_b

        self.people = []
        self._seen_ids.clear()
        self._expanded.clear()

        self._add_person(person_a)
        self._add_person(person_b)

    def generate(self) -> None:
        """Generate full tree using BFS expansion."""
        # Breadth-first traversal using collections.deque is a standard pattern.
        # Code from https://www.geeksforgeeks.org/deque-in-python/ and
        # typical BFS answers like https://stackoverflow.com/questions/8930409/  # [web:13][web:18]
        queue: Deque[Person] = deque(self.people)

        while queue:
            person = queue.popleft()

            if person.person_id in self._expanded:
                continue

            self._expanded.add(person.person_id)

            if person.year_born >= self.stop_year:
                continue

            before = len(self.people)
            self._generate_partner_and_children(person)
            after = len(self.people)

            for new_person in self.people[before:after]:
                queue.append(new_person)

    # Required queries

    def total_people(self) -> int:
        return len(self.people)

    def total_by_decade(self) -> Dict[int, int]:
        counts: Dict[int, int] = {}

        for person in self.people:
            d = decade_of(person.year_born)
            counts[d] = counts.get(d, 0) + 1

        # Using dict(sorted(...)) to return a dictionary in order follows patterns
        # similar to sorted-dict examples on GeeksforGeeks.
        # Code from https://www.geeksforgeeks.org/python-sort-python-dictionaries-by-key-or-value/  # [web:13]
        return dict(sorted(counts.items()))

    def duplicate_full_names(self) -> List[str]:
        seen: Dict[str, int] = {}

        for person in self.people:
            name = person.full_name()
            seen[name] = seen.get(name, 0) + 1

        # Counting duplicates with a dictionary is the same idea as
        # word-count examples in GeeksforGeeks and StackOverflow.
        # Code from https://www.geeksforgeeks.org/python-count-occurrences-of-each-word-in-given-text-file/  # [web:13]
        return sorted(name for name, c in seen.items() if c > 1)

    # Internal generation

    def _add_person(self, person: Person) -> None:
        if person.person_id not in self._seen_ids:
            self._seen_ids.add(person.person_id)
            self.people.append(person)

    def _generate_partner_and_children(self, person: Person) -> None:
        self._maybe_create_partner(person)

        n_children = self._children_count(person.year_born)
        if n_children <= 0:
            return

        elder_year = person.year_born
        if person.partner:
            elder_year = min(person.year_born, person.partner.year_born)

        child_years = self._child_birth_years(elder_year, n_children)

        last_names = [person.last_name]
        if person.partner:
            last_names.append(person.partner.last_name)

        for year in child_years:
            if year > self.stop_year:
                continue

            # random.choice for picking a last name is standard usage:
            # Code from https://www.geeksforgeeks.org/python-random-choice-function/  # [web:17]
            child = self.factory.get_person(
                year, last_name=random.choice(last_names)
            )

            person.children.append(child)
            if person.partner:
                person.partner.children.append(child)

            self._add_person(child)

    def _maybe_create_partner(self, person: Person) -> None:
        if person.partner:
            return

        # random.random() <= probability is a standard Bernoulli trial pattern,
        # as shown in many probability examples on GeeksforGeeks.
        # Code from https://www.geeksforgeeks.org/generating-random-number-list-in-python/  # [web:17]
        if random.random() <= self.factory.marriage_probability(person.year_born):
            partner_year = clamp_int(
                person.year_born + random.randint(-10, 10),
                self.start_year,
                self.stop_year,
            )

            partner = self.factory.get_person(
                partner_year, last_name=person.last_name
            )

            person.partner = partner
            partner.partner = person

            self._add_person(partner)

    def _children_count(self, year_born: int) -> int:
        br = self.factory.birth_rate(year_born)
        lo = int(max(0.0, br - 1.5))
        hi = int(max(0.0, br + 1.5))
        hi = max(lo, min(hi, 10))

        # Using random.randint(lo, hi) for inclusive integer range is standard:
        # Code from https://www.geeksforgeeks.org/python-randint-function/  # [web:17]
        return random.randint(lo, hi)

    def _child_birth_years(self, elder_year: int, n_children: int) -> List[int]:
        start = elder_year + 25
        end = elder_year + 45

        if n_children == 1:
            years = [random.randint(start, end)]
        else:
            step = (end - start) / (n_children - 1)
            years = [int(round(start + i * step)) for i in range(n_children)]

        # Clamp years to [start_year, stop_year] using clamp_int.
        return sorted(clamp_int(y, self.start_year, self.stop_year) for y in years)
