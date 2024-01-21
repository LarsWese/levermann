import enum
from datetime import datetime, date

from sqlalchemy import Enum
from sqlalchemy.orm import Mapped

from levermann_share_value import db


class ShareValue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String, nullable=False)
    related_date: date = db.Column(db.Date, nullable=False)
    value: str = db.Column(db.String, nullable=False)
    fetch_date: datetime = db.Column(db.DateTime, default=datetime.utcnow)
    note: str = db.Column(db.String)
    share_id = db.Column(db.Integer, db.ForeignKey('share.id'))
    db.UniqueConstraint(share_id, name, related_date, value)

    def __repr__(self):
        return f'{self.name} {self.value} {self.related_date}'


class ShareType(enum.Enum):
    None_Finance = 1
    Finance = 2


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
    market: str = db.Column(db.String)
    logo_url: str = db.Column(db.String)
    long_description_de: str = db.Column(db.String)
    long_description_en: str = db.Column(db.String)
    short_description_de: str = db.Column(db.String)
    green: bool = db.Column(db.Boolean, default=False)
    share_type: str = db.Column(Enum(ShareType), default=ShareType.None_Finance.value, nullable=False)
    share_values: Mapped[ShareValue] = db.relationship('ShareValue')
    index_id = db.Column(db.Integer, db.ForeignKey('indices.id'))

    def exists(self, share_value: ShareValue) -> bool:
        return ShareValue.query.filter(ShareValue.share_id == self.id, ShareValue.name == share_value.name,
                                       ShareValue.value == share_value.value).first() is not None

    def __repr__(self):
        return f'{self.name} {self.description} {self.isin}'

    def as_dict(self) -> {}:
        share_data = {'id': self.id,
                      'isin': self.isin,
                      'wkn': self.wkn,
                      'symbol': self.symbol,
                      'name': self.name,
                      'website': self.website,
                      'sector': self.sector,
                      'branch': self.branch,
                      'country': self.country,
                      'street': self.street,
                      'zip_code': self.zip_code,
                      'city': self.city,
                      'logo_url': self.logo_url,
                      'long_description_de': self.long_description_de,
                      'long_description_en': self.long_description_en,
                      'green': self.green,
                      'share_type': self.share_type,
                      'short_description_de': self.short_description_de}
        return share_data


class Indices(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String, nullable=False, index=True)
    wkn: str = db.Column(db.String)
    symbol: str = db.Column(db.String)
    isin: str = db.Column(db.String)
    ulr: str = db.Column(db.String, nullable=False)
    country: str = db.Column(db.String)
    shares: Mapped[Share] = db.relationship('Share')
    db.UniqueConstraint(name)
