from datetime import datetime, date
from enum import IntEnum

from levermann_share_value import db


class ShareType(IntEnum):
    Large_Caps = 1
    Small_Mid_Caps = 2
    Finance_Caps = 3
    Unknown = 4

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class Share(db.Model):
    id: int = db.Column(db.Integer, primary_key=True)
    isin: str = db.Column(db.String, unique=True)
    wkn: str = db.Column(db.String, unique=True)
    symbol: str = db.Column(db.String)
    name: str = db.Column(db.String, nullable=False)
    website: str = db.Column(db.String)
    sector: str = db.Column(db.String)
    branch: str = db.Column(db.String)
    country: str = db.Column(db.String)
    street: str = db.Column(db.String)
    zip_code: str = db.Column(db.String)
    city: str = db.Column(db.String)
    last_fiscal_year: date = db.Column(db.Date)
    next_quarter: date = db.Column(db.Date)
    logo_url: str = db.Column(db.String)
    long_description_de: str = db.Column(db.String)
    long_description_en: str = db.Column(db.String)
    short_description_de: str = db.Column(db.String)
    green: bool = db.Column(db.Boolean)
    share_values = db.relationship('ShareValue', backref='shareValues', lazy='dynamic')

    def __repr__(self):
        return f'{self.name} {self.description} {self.isin}'


class ShareValue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String, nullable=False, index=True)
    related_date: date = db.Column(db.Date, index=True, nullable=False)
    value: str = db.Column(db.String, nullable=False)
    fetch_date: datetime = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    share_id = db.Column(db.Integer, db.ForeignKey('share.id'))
    db.UniqueConstraint(share_id, related_date, value)

    def __repr__(self):
        return f'{self.name} {self.value} {self.related_date}'
