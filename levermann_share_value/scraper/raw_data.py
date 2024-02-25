from dataclasses import dataclass
from datetime import date


@dataclass
class RawData:
    name: str
    value: str
    fetch_date: date
    note: str = None
    related_date: date = None


@dataclass
class BasicShare:
    isin: str
    name: str
    green: bool
    description: str
