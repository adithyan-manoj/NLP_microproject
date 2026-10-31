import re
from typing import Optional, Tuple
from dataclasses import dataclass

@dataclass
class TemporalExtraction:
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    last_n_innings: Optional[int] = None
    last_n_matches: Optional[int] = None

class TemporalParser:
    """
    Interprets natural language time expressions and relative windows.
    Strictly separates:
    1. Calendar date ranges (start_date, end_date)
    2. Sequence-based innings windows (last_n_innings)
    3. Sequence-based match windows (last_n_matches)
    """

    @classmethod
    def parse(cls, query: str) -> TemporalExtraction:
        q = query.lower()
        res = TemporalExtraction()

        # 1. Innings window: "last 5 innings", "past 10 innings", "last five innings"
        innings_match = re.search(r"(?:last|past|recent)\s+(\d+|one|two|three|four|five|six|seven|eight|nine|ten|twenty)\s+innings", q)
        if innings_match:
            val_str = innings_match.group(1)
            res.last_n_innings = cls._convert_word_to_num(val_str)

        # 2. Match window: "last 5 matches", "recent 10 matches"
        matches_match = re.search(r"(?:last|past|recent)\s+(\d+|one|two|three|four|five|six|seven|eight|nine|ten|twenty)\s+matches", q)
        if matches_match:
            val_str = matches_match.group(1)
            res.last_n_matches = cls._convert_word_to_num(val_str)

        # 3. "since YYYY" -> start_date = YYYY-01-01
        since_match = re.search(r"since\s+(\d{4})", q)
        if since_match:
            year = since_match.group(1)
            res.start_date = f"{year}-01-01"

        # 4. "in YYYY" (e.g. "in 2023") -> start_date = YYYY-01-01, end_date = YYYY-12-31
        in_year_match = re.search(r"\bin\s+(\d{4})\b", q)
        if in_year_match and not since_match:
            year = in_year_match.group(1)
            res.start_date = f"{year}-01-01"
            res.end_date = f"{year}-12-31"

        # 5. "between YYYY and YYYY"
        between_match = re.search(r"between\s+(\d{4})\s+and\s+(\d{4})", q)
        if between_match:
            y1 = between_match.group(1)
            y2 = between_match.group(2)
            res.start_date = f"{y1}-01-01"
            res.end_date = f"{y2}-12-31"

        # 6. Default recent form if "recent form" mentioned without count
        if (res.last_n_innings is None and res.last_n_matches is None and
            res.start_date is None and ("recent form" in q or "recent innings" in q)):
            res.last_n_innings = 10

        return res

    @staticmethod
    def _convert_word_to_num(val: str) -> int:
        mapping = {
            "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
            "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
            "twenty": 20,
        }
        if val in mapping:
            return mapping[val]
        try:
            return int(val)
        except ValueError:
            return 10
