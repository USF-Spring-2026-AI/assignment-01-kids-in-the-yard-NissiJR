from __future__ import annotations

import random
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

from person import Person


def decade_of(year: int) -> int:
    """Convert a year to its decade bucket (e.g., 1954 -> 1950)."""
    return (year // 10) * 10


def parse_decade(value: object) -> int:
    """
    Parse decade values that may appear as:
      - 1950
      - "1950"
      - "1950s"
      - "1950-1959"
      - "1950 – 1959" (with a fancy dash)
    Returns the starting year of the decade as an int.
    """
    s = str(value).strip()
    if not s:
        raise ValueError("Empty decade value")

    # Normalize common separators
    s = s.replace("–", "-").replace("—", "-")

    # "1950s" -> "1950"
    if s.lower().endswith("s") and len(s) >= 2:
        s = s[:-1].strip()

    # "1950-1959" -> "1950"
    if "-" in s:
        left = s.split("-", 1)[0].strip()
        if left.isdigit():
            return int(left)
        match = re.search(r"\d{4}", left)
        if match:
            return int(match.group(0))

    # plain digits
    if s.isdigit():
        return int(s)

    # last resort: find first 4-digit year anywhere in string
    match = re.search(r"\d{4}", s)
    if match:
        return int(match.group(0))

    raise ValueError(f"Could not parse decade from: {value!r}")


class PersonFactory:
    """
    CS 362 version.
    Loads CSV data with pandas and generates Person objects according to the spec.

    Required CSVs in current directory:
      - life_expectancy.csv                 (Year, Period life expectancy at birth)
      - first_names.csv                     (decade, gender, name, frequency)
      - last_names.csv                      (decade, rank, lastname)
      - rank_to_probability.csv             (either 'rank,probability' OR one-row list of probabilities)
      - birth_and_marriage_rates.csv        (decade, birth_rate, marriage_rate)

    NOTE: gender_name_probability.csv is not required for CS 362, so we ignore it.
    """

    def __init__(self, seed: Optional[int] = None) -> None:
        if seed is not None:
            random.seed(seed)

        self._next_id = 1

        self._life_expectancy: Dict[int, float] = {}
        self._birth_rate: Dict[int, float] = {}
        self._marriage_rate: Dict[int, float] = {}

        self._first_names_by_decade: Dict[int, Tuple[List[str], List[float]]] = {}
        self._last_names: List[str] = []
        self._last_name_weights: List[float] = []

    def read_files(self) -> None:
        """Load all required CSV files from current directory."""
        life_df = pd.read_csv(self._require("life_expectancy.csv"))
        first_df = pd.read_csv(self._require("first_names.csv"))
        last_df = pd.read_csv(self._require("last_names.csv"))

        # rank_to_probability.csv in your dataset is NOT a normal 2-column CSV.
        # We handle both formats inside _load_last_names().
        rank_path = self._require("rank_to_probability.csv")
        rates_df = pd.read_csv(self._require("birth_and_marriage_rates.csv"))

        self._load_life_expectancy(life_df)
        self._load_birth_and_marriage_rates(rates_df)
        self._load_first_names(first_df)
        self._load_last_names(last_df, rank_path)

    def get_person(self, year_born: int, *, last_name: Optional[str] = None) -> Person:
        """Generate a Person using decade-based rules."""
        decade = self._nearest_decade(decade_of(year_born))

        year_died = self._generate_year_died(year_born, decade)
        first_name = self._pick_first_name(decade)
        ln = last_name if last_name is not None else self._pick_last_name()

        person = Person(
            person_id=self._next_id,
            year_born=year_born,
            year_died=year_died,
            first_name=first_name,
            last_name=ln,
        )
        self._next_id += 1
        return person

    def marriage_probability(self, year_born: int) -> float:
        """Return marriage rate for person's birth decade."""
        decade = self._nearest_decade(decade_of(year_born))
        return self._marriage_rate[decade]

    def birth_rate(self, year_born: int) -> float:
        """Return birth rate for person's birth decade."""
        decade = self._nearest_decade(decade_of(year_born))
        return self._birth_rate[decade]

    # -------------------------
    # CSV Loading (matches YOUR headers)
    # -------------------------

    def _load_life_expectancy(self, df: pd.DataFrame) -> None:
        """
        life_expectancy.csv headers:
          - Year
          - Period life expectancy at birth

        We convert Year -> decade and store decade -> expectancy (averaged within decade).
        """
        cols = {c.lower(): c for c in df.columns}
        year_col = cols.get("year")
        exp_col = cols.get("period life expectancy at birth")

        if year_col is None or exp_col is None:
            raise ValueError(
                "life_expectancy.csv must have columns: "
                "'Year' and 'Period life expectancy at birth'"
            )

        temp: Dict[int, List[float]] = {}
        for _, row in df.iterrows():
            year = int(row[year_col])
            decade = decade_of(year)
            exp = float(row[exp_col])
            temp.setdefault(decade, []).append(exp)

        self._life_expectancy = {d: sum(vals) / len(vals) for d, vals in temp.items()}

        if not self._life_expectancy:
            raise ValueError("life_expectancy.csv loaded no usable rows.")

    def _load_birth_and_marriage_rates(self, df: pd.DataFrame) -> None:
        """
        birth_and_marriage_rates.csv headers:
          - decade  (e.g., '1950s')
          - birth_rate
          - marriage_rate
        """
        cols = {c.lower(): c for c in df.columns}
        required = {"decade", "birth_rate", "marriage_rate"}

        if not required.issubset(cols.keys()):
            raise ValueError(
                "birth_and_marriage_rates.csv must contain: "
                "decade, birth_rate, marriage_rate"
            )

        for _, row in df.iterrows():
            d = parse_decade(row[cols["decade"]])
            self._birth_rate[d] = max(0.0, float(row[cols["birth_rate"]]))
            self._marriage_rate[d] = max(
                0.0, min(1.0, float(row[cols["marriage_rate"]]))
            )

        if not self._birth_rate or not self._marriage_rate:
            raise ValueError("birth_and_marriage_rates.csv loaded no usable rows.")

    def _load_first_names(self, df: pd.DataFrame) -> None:
        """
        first_names.csv headers:
          - decade  (e.g., '1950s')
          - gender
          - name
          - frequency

        CS 362 doesn't require gender logic, so we ignore gender.
        If the same name appears multiple times in a decade (e.g., both genders),
        we sum frequencies.
        """
        cols = {c.lower(): c for c in df.columns}
        required = {"decade", "name", "frequency"}

        if not required.issubset(cols.keys()):
            raise ValueError(
                "first_names.csv must contain at least: decade, name, frequency"
            )

        grouped: Dict[int, Dict[str, float]] = {}
        for _, row in df.iterrows():
            d = parse_decade(row[cols["decade"]])
            name = str(row[cols["name"]]).strip()
            freq = float(row[cols["frequency"]])

            if not name:
                continue

            grouped.setdefault(d, {})
            grouped[d][name] = grouped[d].get(name, 0.0) + max(0.0, freq)

        if not grouped:
            raise ValueError("first_names.csv loaded no usable rows.")

        for d, name_map in grouped.items():
            names = list(name_map.keys())
            weights = list(name_map.values())
            if sum(weights) <= 0:
                weights = [1.0] * len(weights)
            self._first_names_by_decade[d] = (names, weights)

    def _load_last_names(self, last_df: pd.DataFrame, rank_path: Path) -> None:
        """
        last_names.csv headers:
          - decade (unused for weighting here)
          - rank
          - lastname

        rank_to_probability.csv in your dataset is a SINGLE ROW of probabilities like:
          0.1800,0.0900,0.0600,...
        where index = rank.

        We support BOTH:
          A) normal format: columns rank, probability
          B) your one-row format (no headers)
        """
        lcols = {c.lower(): c for c in last_df.columns}
        if "rank" not in lcols or "lastname" not in lcols:
            raise ValueError("last_names.csv must contain: rank, lastname")

        rank_to_prob = self._read_rank_probabilities(rank_path)

        names: List[str] = []
        weights: List[float] = []

        for _, row in last_df.iterrows():
            ln = str(row[lcols["lastname"]]).strip()
            if not ln:
                continue
            rk = int(row[lcols["rank"]])
            names.append(ln)
            weights.append(rank_to_prob.get(rk, 0.0))

        if not names:
            raise ValueError("last_names.csv loaded no usable rows.")

        if sum(weights) <= 0:
            weights = [1.0] * len(weights)

        self._last_names = names
        self._last_name_weights = weights

    def _read_rank_probabilities(self, path: Path) -> Dict[int, float]:
        """
        Read rank probabilities supporting:
          - columns: rank, probability
          - one-row CSV with probabilities only (rank = column index)
        """
        # First try normal 2-column format
        try:
            df = pd.read_csv(path)
            cols = {c.lower(): c for c in df.columns}
            if "rank" in cols and "probability" in cols and not df.empty:
                out: Dict[int, float] = {}
                for _, row in df.iterrows():
                    out[int(row[cols["rank"]])] = max(0.0, float(row[cols["probability"]]))
                if out:
                    return out
        except Exception:
            # Fall through to one-row parsing
            pass

        # One-row parsing: read with no header
        df_raw = pd.read_csv(path, header=None)
        if df_raw.empty or df_raw.shape[0] < 1:
            raise ValueError("rank_to_probability.csv is empty or unreadable.")

        first_row = df_raw.iloc[0].tolist()
        out = {i: max(0.0, float(p)) for i, p in enumerate(first_row)}
        return out

    # -------------------------
    # Sampling helpers
    # -------------------------

    def _generate_year_died(self, year_born: int, decade: int) -> int:
        base = self._life_expectancy[decade]
        life_len = max(1.0, base + random.uniform(-10, 10))
        return year_born + int(round(life_len))

    def _pick_first_name(self, decade: int) -> str:
        if decade not in self._first_names_by_decade:
            decade = self._nearest_decade(decade)
        names, weights = self._first_names_by_decade[decade]
        return random.choices(names, weights=weights, k=1)[0]

    def _pick_last_name(self) -> str:
        return random.choices(self._last_names, weights=self._last_name_weights, k=1)[0]

    def _nearest_decade(self, d: int) -> int:
        if d in self._life_expectancy:
            return d
        return min(self._life_expectancy.keys(), key=lambda x: abs(x - d))

    @staticmethod
    def _require(filename: str) -> Path:
        path = Path(filename)
        if not path.exists():
            raise FileNotFoundError(
                f"Missing required file: {filename}\n"
                "All CSV files must be in the current directory."
            )
        return path