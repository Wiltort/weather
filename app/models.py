from datetime import datetime, timezone, timedelta
from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login
import base64
import os


class User(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    forecast_requests: so.WriteOnlyMapped["Forecast_request"] = so.relationship(
        back_populates="from_user"
    )
    token = db.Column(db.String(32), index=True, unique=True)
    token_expiration = db.Column(db.DateTime)

    def __repr__(self):
        return "<User {}>".format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_token(self, expires_in=3600):
        now = datetime.now(timezone.utc)
        if self.token and self.token_expiration.replace(
            tzinfo=timezone.utc
        ) > now + timedelta(seconds=60):
            return self.token
        self.token = base64.b64encode(os.urandom(24)).decode('utf-8')
        self.token_expiration = now + timedelta(seconds=expires_in)
        db.session.add(self)
        return self.token

    def revoke_token(self):
        self.token_expiration = datetime.now(timezone.utc) - timedelta(seconds=1)

    @staticmethod
    def check_token(token):
        user = db.session.scalar(sa.select(User).where(User.token == token))
        if user is None or user.token_expiration.replace(
            tzinfo=timezone.utc
        ) < datetime.now(timezone.utc):
            return None
        return user


class City(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    forecast_requests: so.WriteOnlyMapped["Forecast_request"] = so.relationship(
        back_populates="city"
    )

    def __repr__(self):
        return f"<City {self.name}>"

    def to_dict(self):
        data = {
            "id": self.id,
            "name": self.name,
            "number_of_requests": number_of_requests(self.id),
        }
        return data


class Forecast_request(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    timestamp: so.Mapped[datetime] = so.mapped_column(
        index=True, default=lambda: datetime.now(timezone.utc)
    )
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)
    from_user: so.Mapped[User] = so.relationship(back_populates="forecast_requests")
    city_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(City.id), index=True)
    city: so.Mapped[City] = so.relationship(back_populates="forecast_requests")

    def __repr__(self):
        return f"<Forecast_request from {self.from_user} at {self.city}. Created at {self.timestamp}"


@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))

def number_of_requests(c):
    query = Forecast_request.query.filter(Forecast_request.city_id==c).count()
    return query
