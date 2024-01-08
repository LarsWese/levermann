from dataclasses import dataclass
from datetime import date


@dataclass
class RawData:
    name: str
    value: str
    fetch_date: date
    note: str = None
    related_date: date = None

    def __repr__(self):
        return f'{self.name} = {self.value} from:{self.related_date} fetched:{self.fetch_date} note:{self.note}'


@dataclass
class BasicShare:
    isin: str
    name: str
    green: bool
    description: str
