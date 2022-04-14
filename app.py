"""
https://www.mockaroo.com/
https://pyjwt.readthedocs.io/en/stable/usage.html#encoding-decoding-tokens-with-hs256
https://stackoverflow.com/questions/34894170/difficulty-serializing-geography-column-type-using-sqlalchemy-marshmallow
https://geoalchemy-2.readthedocs.io/en/0.2.6/spatial_operators.html
https://gis.stackexchange.com/questions/77072/return-all-results-within-a-30km-radius-of-a-specific-lat-long-point
https://github.com/lixxu/flask-paginate
https://github.com/davidaurelio/hashids-python
https://stackoverflow.com/questions/21474075/show-distinct-tuples-regardless-of-column-order
https://gist.github.com/gearbox/c4c82d959c06beb3f4eead854995e369
!! https://gis.stackexchange.com/questions/247113/setting-up-indexes-for-postgis-distance-queries/247131#247131
https://stackoverflow.com/questions/23981056/geoalchemy-st-dwithin-implementation

"""
UNSAFE = True
PAGINATION_PAGE = 0
PAGINATION_SIZE = 10
LOCATION_LATITUDE = 42.90168922195973
LOCATION_LONGITUDE = -78.67070653228602
LOCATION_RADIUS = 25  # miles
SRID = 4326
METERS_IN_MILE = 1609.344

import logging
from logging.config import dictConfig
import math
import base64
import hashlib
import sys
import datetime
from pdb import set_trace
import time
import json
import random
from tqdm import tqdm
from pprint import pprint
from functools import wraps
from types import SimpleNamespace
from io import BytesIO
import itertools


import numpy as np
from PIL import Image
import jwt
from sqlalchemy import and_, func
from flask_cors import CORS
from sqlalchemy.orm import relationship
from flask import Flask, current_app, request, jsonify, session, make_response
from flask_restful import reqparse
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy import or_
from marshmallow import (
    ValidationError,
    EXCLUDE,
    fields,
    validate,
    validates,
    pre_dump,
    post_dump,
    pre_load,
)
from hashids import Hashids as _Hashids
import geojson
from passlib.apps import custom_app_context as password_context
from marshmallow_sqlalchemy import ModelConverter
from geoalchemy2 import Geography
from geoalchemy2.elements import WKTElement
from geoalchemy2.functions import ST_DWithin
from vincenty import vincenty

# from geoalchemy2.functions import ST_AsGeoJSON

# from hashids import Hashids as _Hashids
import shapely
from shapely.geometry import shape

# utils
def timestamp():
    return int(time.time() * 1000)


def checksum(data):
    packet = json.dumps(data, sort_keys=True).encode("utf-8")
    digest = hashlib.md5(packet).hexdigest()
    return digest


def load_date(string):
    return datetime.datetime.strptime(string, "%Y-%m-%d")


def dump_date(dt):
    return datetime.datetime.strftime(dt, "%Y-%m-%d")


LOCALHOST = "http://192.168.1.114:4000"
SVC = SimpleNamespace(
    **{
        "auth": True,
        "user": True,
        "profile": True,
        "location": False,
        "image": False,
        "message": False,
        "event": False,
    }
)

log = logging.getLogger(__name__)
app = Flask(__name__)
CORS(app)
# api = Api()
db = SQLAlchemy()
ma = Marshmallow()

# fmt: off
auth_parser = reqparse.RequestParser()
auth_parser.add_argument("TOKEN", location="headers", dest="token", type=str, default=None)
auth_parser.add_argument("PK", location="headers", dest="pk", type=int, default=None)

pagination_parser = reqparse.RequestParser()
pagination_parser.add_argument("page", location="args", type=int, default=PAGINATION_PAGE)
pagination_parser.add_argument("size", location="args", type=int, default=PAGINATION_SIZE)

location_parser = reqparse.RequestParser()
location_parser.add_argument("latitude", type=float, default=LOCATION_LATITUDE)
location_parser.add_argument("longitude", type=float, default=LOCATION_LONGITUDE)
location_parser.add_argument("radius", type=float, default=LOCATION_RADIUS)

calendar_parser = reqparse.RequestParser()
calendar_parser.add_argument("date", location="args", type=load_date, default=load_date(dump_date(datetime.datetime.now())))
calendar_parser.add_argument("days", location="args", type=int, default=7)
calendar_parser.add_argument("fk", location="args", type=int, required=True)
# fmt: on


class Hashids:
    def __init__(self, app=None, *args, **kwargs):
        if app:
            self.init_app(app)
        self._hashids = None

    def init_app(self, app):
        self.app = app
        self.app.extensions["hashids"] = self
        self.salt = app.config["SECRET_KEY"]
        self.min_length = app.config["TOKEN_MIN_LENGTH"]
        self.alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
        self._hashids = _Hashids(
            salt=self.salt, min_length=self.min_length, alphabet=self.alphabet
        )

    def encode(self, key):
        return self._hashids.encode(key)

    def decode(self, value):
        hid, *_ = self._hashids.decode(value) or (None, None)
        return hid


hashids = Hashids()


class HashidField(fields.Field):
    def _deserialize(self, value, attr, data, **kwargs):
        if value is None:
            return None
        return hashids.decode(value)

    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return None
        return hashids.encode(value)


def auth(*args, **kwargs):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session or UNSAFE:
                return f(*args, **kwargs)
            return Reply.unauthorized(error="Unauthorized")

        return decorated_function

    return decorator


# POJO
class Token:
    """
    Reserved Claims

    - iss (issuer): Issuer of the JWT
    - sub (subject): Subject of the JWT (the user)
    - aud (audience): Recipient for which the JWT is intended
    - exp (expiration time): Time after which the JWT expires
    - nbf (not before time): Time before which the JWT must not be accepted for processing
    - iat (issued at time): Time at which the JWT was issued; can be used to determine age of the JWT
    - jti (JWT ID): Unique identifier; can be used to prevent the JWT from being replayed (allows a token to be used only once)
        - this does undermine the stateless nature of JWT's, but can be optionally used in a rolling blacklist key-value store for revocation+ttl

    You can see a full list of reserved claims at the [IANA JSON Web Token Claims Registry](https://www.iana.org/assignments/jwt/jwt.xhtml#claims)
    """

    def __init__(self, sub: int, exp=None, ttl: int = 60 * 60 * 1):
        self.sub = sub
        self.exp = exp if exp is not None else timestamp() + (ttl * 1000)

    @property
    def valid(self):
        if self.exp is None:
            return False
        return timestamp() <= self.exp

    def serialize(self):
        return dict(sub=self.sub, exp=self.exp)

    @classmethod
    def deserialize(
        cls,
        sub,
        exp=None,
    ):
        return cls(sub, exp=exp)


class Reply:
    @staticmethod
    def reply(data, error, status, headers, isjson=True):
        content = (
            jsonify(dict(data=data, error=error, timestamp=timestamp(), status=status))
            if isjson
            else data
        )
        response = make_response(
            content,
            status,
        )
        if headers:
            response.headers = headers
        return response

    # plain response: manually set content-type
    @classmethod
    def plain(cls, data=None, error=None, status=200, headers=None, dtype="text/plain"):
        headers = {**(headers or {}), "Content-Type": dtype}
        return cls.reply(
            data=data, error=error, status=status, headers=headers, isjson=False
        )

    # 200: Ok
    @classmethod
    def success(cls, data=None, error=None, status=200, headers=None):
        return cls.reply(data=data, error=error, status=status, headers=headers)

    # 400: Client Error
    @classmethod
    def error(cls, data=None, error=None, status=400, headers=None):
        return cls.reply(data=data, error=error, status=status, headers=headers)

    # 401: Unauthorized
    @classmethod
    def unauthorized(cls, data=None, error=None, status=401, headers=None):
        return cls.reply(data=data, error=error, status=status, headers=headers)


class Config:
    SECRET_KEY = "helloworld"
    TOKEN_MIN_LENGTH = 8
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:postgres@localhost:5432"


# MODELS
class BaseModel(db.Model):
    __abstract__ = True
    pk = db.Column(db.Integer(), primary_key=True, unique=True)
    created_at = db.Column(db.BigInteger(), default=timestamp, nullable=False)
    updated_at = db.Column(
        db.BigInteger(), default=None, onupdate=timestamp, nullable=True
    )


class EventModel(BaseModel):
    __tablename__ = "events"
    stale = db.Column(db.Boolean(), unique=False, default=False)
    action = db.Column(db.String(), unique=False, nullable=False)
    source = db.Column(db.String(), unique=False, nullable=True)
    payload = db.Column(db.String(), unique=False, nullable=True)


class NetworkModel(BaseModel):
    __tablename__ = "networks"
    src_fk = db.Column(
        db.Integer(), db.ForeignKey("users.pk"), nullable=False, unique=False
    )
    dst_fk = db.Column(
        db.Integer(), db.ForeignKey("users.pk"), nullable=False, unique=False
    )
    src = relationship("UserModel", foreign_keys=[src_fk], uselist=False, lazy="select")
    dst = relationship("UserModel", foreign_keys=[dst_fk], uselist=False, lazy="select")


class ProfileModel(BaseModel):
    __tablename__ = "profiles"
    alias = db.Column(db.String(), nullable=True, unique=False)
    bio = db.Column(db.String(), nullable=True, unique=False)
    age = db.Column(db.Integer(), nullable=True, unique=False)
    handicap = db.Column(db.Float(), nullable=True, unique=False)
    drinking = db.Column(db.Integer(), nullable=True, unique=False)
    mobility = db.Column(db.Integer(), nullable=True, unique=False)
    weather = db.Column(db.Integer(), nullable=True, unique=False)

    fk = db.Column(db.Integer(), db.ForeignKey("users.pk"), nullable=False)
    user = relationship("UserModel", back_populates="profile")


class LocationModel(BaseModel):
    __tablename__ = "locations"
    geometry = db.Column(
        Geography(geometry_type="POINT", srid=SRID), nullable=False, unique=False
    )
    label = db.Column(db.String(), nullable=True, unique=False)
    fk = db.Column(db.Integer(), db.ForeignKey("users.pk"), nullable=False)
    user = relationship("UserModel", back_populates="location")


class ImageModel(BaseModel):
    __tablename__ = "images"
    fk = db.Column(db.Integer(), db.ForeignKey("users.pk"), nullable=False)
    img = db.Column(db.String(), nullable=False, unique=False)

    user = relationship("UserModel", back_populates="image")


class MessageModel(BaseModel):
    __tablename__ = "messages"
    body = db.Column(db.String(), nullable=False, unique=False)
    read = db.Column(db.Boolean(), nullable=False, unique=False, default=False)
    src_fk = db.Column(
        db.Integer(), db.ForeignKey("users.pk"), nullable=False, unique=False
    )
    dst_fk = db.Column(
        db.Integer(), db.ForeignKey("users.pk"), nullable=False, unique=False
    )

    src = relationship("UserModel", foreign_keys=[src_fk], uselist=False, lazy="select")
    dst = relationship("UserModel", foreign_keys=[dst_fk], uselist=False, lazy="select")


class CalendarModel(BaseModel):
    __tablename__ = "calenders"
    date = db.Column(db.Date(), nullable=False, unique=False)
    time = db.Column(db.Integer(), nullable=False, unique=False)  # enum[0:3]

    fk = db.Column(db.Integer(), db.ForeignKey("users.pk"), nullable=False)
    user = relationship("UserModel", back_populates="calendar")


class UserModel(BaseModel):
    __tablename__ = "users"
    verified = db.Column(db.Boolean(), unique=False, default=False)
    email = db.Column(db.String(), unique=True, nullable=False)
    username = db.Column(db.String(), unique=True, nullable=False)
    password = db.Column(db.String(), unique=False, nullable=False)

    profile = relationship("ProfileModel", uselist=False, back_populates="user")
    location = relationship("LocationModel", uselist=False, back_populates="user")
    calendar = relationship("CalendarModel", back_populates="user")
    image = relationship("ImageModel", uselist=False, back_populates="user")

    # following = relationship("NetworkModel", back_populates="src")
    # followers = relationship("NetworkModel", back_populates="dst")

    # src_messages = relationship(
    #     "MessageModel", back_populates="src", uselist=False, lazy="select"
    # )
    # dst_messages = relationship("MessageModel", back_populates="dst")

    def hash_password(self, password):
        self.password = password_context.encrypt(password)

    def verify_password(self, password):
        return password_context.verify(password, self.password)

    def generate_auth_token(self, ttl=600):
        pass

    @staticmethod
    def validate_auth_token(token):
        pass


# SCHEMAS
class BaseSchema(ma.SQLAlchemyAutoSchema):
    """
    missing     used for deserialization (dump)
    default     used for serialization (load)
    https://github.com/marshmallow-code/marshmallow/issues/588#issuecomment-283544372
    """

    # pk = HashidField(dump_only=True) # this does work
    pk = fields.Int(dump_only=True)
    created_at = fields.Int(dump_only=True)
    updated_at = fields.Int(dump_only=True)

    class Meta:
        """Alternate method of configuration which eliminates the need to
        subclass BaseSchema.Meta
        https://marshmallow-sqlalchemy.readthedocs.io/en/latest/recipes.html#base-schema-ii
        """

        sqla_session = db.session
        load_instance = True
        transient = True
        unknown = EXCLUDE
        editable = ()

    @pre_load
    def set_nested_session(self, data, **kwargs):
        """Allow nested schemas to use the parent schema's session. This is a
        longstanding bug with marshmallow-sqlalchemy.
        https://github.com/marshmallow-code/marshmallow-sqlalchemy/issues/67
        https://github.com/marshmallow-code/marshmallow/issues/658#issuecomment-328369199
        """
        nested_fields = {
            k: v for k, v in self.fields.items() if type(v) == fields.Nested
        }
        for field in nested_fields.values():
            field.schema.session = self.session
        return data


class EventSchema(BaseSchema):
    class Meta(BaseSchema.Meta):
        model = EventModel
        editable = ("stale",)

    stale = fields.Bool(dump_only=True)
    action = fields.Str(allow_none=False)
    source = fields.Str(allow_none=True)
    payload = fields.Str(allow_none=True)


class ProfileSchema(BaseSchema):
    class Meta(BaseSchema.Meta):
        model = ProfileModel
        editable = (
            "alias",
            "bio",
            "age",
            "handicap",
            "drinking",
            "mobility",
        )

    # fk = fields.Int(required=True, allow_none=False)
    alias = fields.Str(
        required=False, allow_none=True, validate=validate.Length(max=32)
    )
    bio = fields.Str(required=False, allow_none=True, validate=validate.Length(max=250))
    age = fields.Int(
        required=False, allow_none=True, validate=validate.Range(min=1, max=100)
    )
    handicap = fields.Float(required=False, allow_none=True)
    drinking = fields.Integer(required=False, allow_none=True)
    mobility = fields.Integer(required=False, allow_none=True)
    weather = fields.Integer(required=False, allow_none=True)


class GeoField(fields.Field):
    def _serialize(self, value, attr, obj, **kwargs):
        return json.loads(geojson.dumps(shapely.wkb.loads(str(value), True)))

    def _deserialize(self, value, attr, data, **kwargs):
        # FIXME
        return str(shape(value))


class GeoConverter(ModelConverter):
    SQLA_TYPE_MAPPING = ModelConverter.SQLA_TYPE_MAPPING.copy()
    SQLA_TYPE_MAPPING.update({Geography: GeoField})


class LocationSchema(BaseSchema):
    class Meta(BaseSchema.Meta):
        model = LocationModel
        model_coverter = GeoConverter
        editable = (
            "geometry",
            "label",
        )

    geometry = GeoField(required=True, allow_none=False)
    lable = fields.Str(required=False, allow_none=True)
    distance = fields.Decimal(required=False, default=None)


class ImageSchema(BaseSchema):
    class Meta(BaseSchema.Meta):
        model = ImageModel

    fk = fields.Int(required=True, allow_none=False)
    img = fields.Str(allow_none=False, required=True)

    @post_dump
    def make_href(self, data, **kwargs):
        pk = data.get("pk")
        if pk is not None:
            href = f"{LOCALHOST}/images/img/{pk}"
            data.update(href=href)
        return data


class CalendarSchema(BaseSchema):
    class Meta(BaseSchema.Meta):
        model = CalendarModel
        editable = ("time",)

    fk = fields.Int(required=True, allow_none=False)


class UserSchema(BaseSchema):
    class Meta(BaseSchema.Meta):
        model = UserModel
        editable = (
            "username",
            "email",
        )

    verified = fields.Bool(required=False, allow_none=False)
    username = fields.Str(
        required=True, allow_none=False, validate=validate.Length(min=3, max=32)
    )
    email = fields.Str(
        required=True,
        load_only=True,
        allow_none=False,
        validate=validate.Length(min=3, max=32),
    )
    password = fields.Str(
        required=True,
        load_only=True,
        allow_none=False,
        validate=validate.Length(max=128),
    )
    profile = fields.Nested(ProfileSchema, many=False)
    location = fields.Nested(LocationSchema, many=False)
    calendar = fields.Nested(CalendarSchema, many=True)
    image = fields.Nested(ImageSchema, many=False)
    # network = fields.Nested(NetworkSchema, many=True)

    @validates("username")
    def validate_username(self, data, **kwargs):
        ALLOWABLE_CHARACTERS = set(
            "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789"
        )
        if not set(data).issubset(ALLOWABLE_CHARACTERS):
            raise ValidationError(
                f"Username contains non-allowable characters: {set(data).difference(ALLOWABLE_CHARACTERS)}"
            )


class MessageSchema(BaseSchema):
    class Meta(BaseSchema.Meta):
        model = MessageModel
        editable = ("read",)

    src_fk = fields.Int(required=True, allow_none=False)
    dst_fk = fields.Int(required=True, allow_none=False)
    body = fields.Str(required=True, allow_none=False)
    read = fields.Bool(required=False, allow_none=False)

    src = fields.Nested(
        UserSchema,
        exclude=(
            "calendar",
            "location",
            "profile",
        ),
        many=False,
    )
    dst = fields.Nested(
        UserSchema,
        exclude=(
            "calendar",
            "location",
            "profile",
        ),
        many=False,
    )


class NetworkSchema(BaseSchema):
    class Meta(BaseSchema.Meta):
        model = NetworkModel

    src_fk = fields.Int(required=True, allow_none=False)
    dst_fk = fields.Int(required=True, allow_none=False)
    src = fields.Nested(
        UserSchema,
        many=False,
    )
    dst = fields.Nested(
        UserSchema,
        many=False,
    )


# MANAGERS
class BaseManager:
    name = None

    def __init__(self, *args, **kwargs):
        pass


class AuthManager(BaseManager):
    name = "auth_manager"

    def parse_token(self):
        return auth_parser.parse_args().get("token")

    def issue_token(self, subject):
        token = Token(sub=subject)
        encoded = jwt.encode(token.serialize(), "mysecret", algorithm="HS256")
        return encoded

    def check_token(self, encoded):
        if not encoded:
            return False
        try:
            decoded = jwt.decode(encoded, "mysecret", algorithms=["HS256"])
        except jwt.exceptions.InvalidSignatureError:
            return False
        except jwt.exceptions.DecodeError:
            return False
        except Exception as exc:
            print(f"Unhandled authentication error: {exc}")
            return False
        token = Token(**decoded)
        return token.valid


class EventManager(BaseManager):
    name = "event_manager"

    def create_event(self, data):
        event = EventSchema().load(data)
        db.session.add(event)
        db.session.commit()
        return EventSchema().dump(event)

    def read_event(self, pk):
        event = db.session.query(EventModel).filter_by(pk=pk).first()
        return EventSchema().dump(event)

    def update_event(self, pk, patches):
        event = db.session.query(EventModel).filter_by(pk=pk).first()
        [
            setattr(event, key, value)
            for key, value in patches.items()
            if key in EventSchema.Meta.editable
        ]
        return EventSchema().dump(event)

    def delete_event(self, pk):
        event = db.session.query(EventModel).filter_by(pk=pk).first()
        db.session.delete(event)
        db.session.commit()
        return True

    def query_events(self, params, page, size):
        q = (
            db.session.query(EventModel)
            .filter_by(**params)
            .order_by(EventModel.created_at.desc())
        )
        total = q.count()
        pages = total // size
        content = q.limit(size).offset(page * size)
        pags = {
            "content": EventSchema(many=True).dump(content),
            "metadata": {
                "page": page,
                "size": size,
                "pages": pages,
                "total": total,
            },
        }
        return pags


class ProfileManager(BaseManager):
    name = "profile_manager"

    def create_profile(self, data):
        profile = ProfileSchema().load(data)
        db.session.add(profile)
        db.session.commit()
        return ProfileSchema().dump(profile)

    def read_profile(self, pk):
        profile = db.session.query(ProfileModel).filter_by(pk=pk).first()
        return ProfileSchema().dump(profile)

    def update_profile(self, pk, patches):
        profile = db.session.query(ProfileModel).filter_by(pk=pk).first()
        [
            setattr(profile, key, value)
            for key, value in patches.items()
            if key in ProfileSchema.Meta.editable
        ]
        db.session.commit()
        return ProfileSchema().dump(profile)

    def delete_profile(self, pk):
        profile = db.session.query(ProfileModel).filter_by(pk=pk).first()
        db.session.delete(profile)
        db.session.commit()
        return True


class LocationManager(BaseManager):
    def create_location(self, data):
        location = LocationSchema().load(data)
        db.session.add(location)
        db.session.commit()
        return LocationSchema().dump(location)

    def read_location(self, pk):
        location = db.session.query(LocationModel).filter_by(pk=pk).first()
        return LocationSchema().dump(location)

    def update_location(self, pk, patches):
        location = db.session.query(LocationModel).filter_by(pk=pk).first()
        [
            setattr(location, key, value)
            for key, value in patches.items()
            if key in LocationSchema.Meta.editable
        ]
        db.session.commit()
        return LocationSchema().dump(location)

    def delete_location(self, pk):
        location = db.session.query(LocationModel).filter_by(pk=pk).first()
        db.session.delete(location)
        db.session.commit()
        return True

    def query_locations(self, latitude, longitude, radius, page, size):
        # radius is in miles, convert to meters for query
        meters = radius * METERS_IN_MILE
        p = WKTElement("POINT({0} {1})".format(latitude, longitude), srid=SRID)
        # TODO: order by distance, closest first
        q = db.session.query(LocationModel).filter(
            ST_DWithin(LocationModel.geometry, p, meters)
        )
        total = q.count()
        pages = total // size
        locations = q.limit(size).offset(page * size)
        content = LocationSchema(many=True).dump(locations)
        for location in content:
            lon, lat = location["location"]["coordinates"]
            distance = vincenty((lat, lon), (latitude, longitude)) / METERS_IN_MILE
            location.update(distance=distance)
        pags = {
            "content": content,
            "metadata": {
                "page": page,
                "size": size,
                "pages": pages,
                "total": total,
                "checksum": checksum(content),
            },
            "query": {
                "latitude": latitude,
                "longitude": longitude,
                "radius": radius,
            },
        }
        return pags


class ImageManager(BaseManager):
    name = "image_manager"

    def create_image(self, data):
        image = ImageSchema().load(data)
        db.session.add(image)
        db.session.commit()
        return ImageSchema().dump(image)

    def read_image(self, pk):
        image = db.session.query(ImageModel).filter_by(pk=pk).first()
        return ImageSchema().dump(image)

    def update_image(self, pk, patches):
        image = db.session.query(ImageModel).filter_by(pk=pk).first()
        [
            setattr(image, key, value)
            for key, value in patches.items()
            if key in ImageSchema.Meta.editable
        ]
        db.session.commit()
        return ImageSchema().dump(image)

    def delete_image(self, pk):
        image = db.session.query(ImageModel).filter_by(pk=pk).first()
        db.session.delete(image)
        db.session.commit()
        return True


class MessageManager(BaseManager):
    name = "message_manager"

    @classmethod
    def get_conversation_pairs(cls, fk):
        # [(3, 1), (1, 2)]
        #   [(1, 2), (2, 1)]
        #   [(1, 3), (3, 1)]
        records = db.engine.execute(
            f"""
            SELECT t1.src_fk, t1.dst_fk
            FROM messages t1
            EXCEPT
            SELECT t1.src_fk, t1.dst_fk
            FROM messages t1
            INNER JOIN messages t2
            ON t1.src_fk = t2.dst_fk AND t1.dst_fk = t2.src_fk
            AND t1.src_fk > t1.dst_fk
            WHERE t1.src_fk = {fk}
            OR t1.dst_fk = {fk}
            OR t2.src_fk = {fk}
            OR t2.dst_fk = {fk};
            """.format(
                fk=fk
            )
        )
        # FIXME: until we can port this to native query, this blows up at scale
        return [(a, b) for a, b in records if fk in (a, b)]  # exhaustible iterable

    def create_message(self, data):
        message = MessageSchema().load(data)
        db.session.add(message)
        db.session.commit()
        return MessageSchema().dump(message)

    def read_message(self, pk):
        message = db.session.query(MessageModel).filter_by(pk=pk).first()
        return MessageSchema().dump(message)

    def update_message(self, pk, patches):
        message = db.session.query(MessageModel).filter_by(pk=pk).first()
        [
            setattr(message, key, value)
            for key, value in patches.items()
            if key in MessageSchema.Meta.editable
        ]
        return MessageSchema().dump(message)

    def delete_message(self, pk):
        message = db.session.query(MessageModel).filter_by(pk=pk).first()
        db.session.delete(message)
        db.session.commit()
        return True

    def get_conversations(self, fk, page=0, size=10):
        log.info(f"Getting conversations: fk={fk} page={page} size={size}")
        # return the most recent message from each conversation
        messages = list()
        for (a, b) in self.get_conversation_pairs(fk=fk):
            message = (
                db.session.query(MessageModel)
                .filter(
                    or_(
                        (MessageModel.src_fk == a) & (MessageModel.dst_fk == b),
                        (MessageModel.src_fk == b) & (MessageModel.dst_fk == a),
                    )
                )
                .order_by(MessageModel.created_at.desc())
                .first()
            )
            messages.append(message)
        # guarantee sort messages by timestamp
        messages.sort(key=lambda obj: obj.created_at, reverse=True)
        total = len(messages)
        pages = total // size
        # messages = q.limit(size).offset(page * size)
        messages = messages[page * size : (page * size) + size]
        # content = MessageSchema(many=True).dump(messages)
        content = MessageSchema(many=True).dump(messages)
        pags = {
            "content": content,
            "metadata": {
                "page": page,
                "size": size,
                "pages": pages,
                "total": total,
                "checksum": checksum(content),
            },
        }
        return pags

    def get_conversation(self, src_fk, dst_fk, page=0, size=10):
        log.info(
            f"Getting conversation: src_fk={src_fk} dst_fk={dst_fk} page={page} size={size}"
        )
        # return an ordered message history of one conversation
        q = (
            db.session.query(MessageModel)
            .filter(
                or_(
                    ((MessageModel.src_fk == src_fk) & (MessageModel.dst_fk == dst_fk)),
                    ((MessageModel.src_fk == dst_fk) & (MessageModel.dst_fk == src_fk)),
                )
            )
            .order_by(MessageModel.created_at.desc())
        )
        src = user_manager.read_user(
            src_fk, exclude=["calendar", "profile", "location"]
        )
        dst = user_manager.read_user(
            dst_fk, exclude=["calendar", "profile", "location"]
        )
        total = q.count()
        pages = q.count() // size
        messages = q.limit(size).offset(page * size)
        content = MessageSchema(many=True).dump(messages)
        pags = {
            "content": content,
            "context": {
                "src": src,
                "dst": dst,
            },
            "metadata": {
                "page": page,
                "size": size,
                "pages": pages,
                "total": total,
                "checksum": checksum(content),
            },
        }
        return pags

    def get_notifications(self, pk) -> int:
        log.info(f"Getting notifications: pk={pk}")
        notifications = 0
        for (a, b) in self.get_conversation_pairs(fk=pk):
            src_fk = [a, b][a == pk]
            dst_fk = [a, b][b == pk]
            notifs = (
                db.session.query(MessageModel)
                .filter(
                    (MessageModel.src_fk == src_fk) & (MessageModel.dst_fk == dst_fk)
                )
                .filter_by(read=False)
                .count()
            )
            notifications += 1 if notifs else 0
        return notifications

    def mark_read(self, src_fk, dst_fk):
        log.info(f"Updating chat notifications: src_fk={src_fk} dst_fk={dst_fk}")
        q = (
            db.session.query(MessageModel)
            .filter(((MessageModel.src_fk == dst_fk) & (MessageModel.dst_fk == src_fk)))
            .filter_by(read=False)
        )
        messages = q.all()
        for message in messages:
            self.update_message(pk=message.pk, patches=dict(read=True))
        return len(messages)


class CalendarManager(BaseManager):
    def create_calendar(self, data):
        calendar = CalendarSchema().load(data)
        # be nice to ui people, if the resource exists just return it
        result = (
            db.session.query(CalendarModel)
            .filter_by(fk=calendar.fk, date=calendar.date, time=calendar.time)
            .first()
        )
        if result:
            return self.read_calendar(result.pk)
        db.session.add(calendar)
        db.session.commit()
        return CalendarSchema().dump(calendar)

    def read_calendar(self, pk):
        calendar = db.session.query(CalendarModel).filter_by(pk=pk).first()
        return CalendarSchema().dump(calendar)

    def update_calendar(self, pk, patches):
        calendar = db.session.query(CalendarModel).filter_by(pk=pk).first()
        [
            setattr(calendar, key, value)
            for key, value in patches.items()
            if key in CalendarSchema.Meta.editable
        ]
        db.session.commit()
        return CalendarSchema().dump(calendar)

    def delete_calendar(self, pk):
        calendar = db.session.query(CalendarModel).filter_by(pk=pk).first()
        db.session.delete(calendar)
        db.session.commit()
        return True

    def query_calendar(self, fk, date, days):
        # TODO: accept bulk updates
        # set some empty column placeholders for days with no entries.
        # we typically only have max 28 entries per query (7*4)
        # which eliminates the need for gymnastics in the ui
        content = dict.fromkeys(
            [date + datetime.timedelta(days=d) for d in range(days)], {}
        )
        total = 0
        for key in content.keys():
            calendars = db.session.query(CalendarModel).filter_by(fk=fk, date=key).all()
            available = [
                cal["time"] for cal in CalendarSchema(many=True).dump(calendars)
            ]
            total += len(available)
            # don't use an update here, dumb pass-by-reference thing
            content[key] = dict(date=dump_date(key), available=available)
        pags = {
            "content": list(content.values()),
            "metadata": {
                "fk": fk,
                "date": dump_date(date),
                "days": days,
                "total": total,
            },
        }
        return pags

    def set_availability(self, data):
        available = data.get("available")  # true/false
        if available:
            # smart create a new entry
            return self.create_calendar(data)
        calendar = CalendarSchema().load(data)
        result = (
            db.session.query(CalendarModel)
            .filter_by(fk=calendar.fk, date=calendar.date, time=calendar.time)
            .first()
        )
        if result:
            return self.delete_calendar(result.pk)


class UserManager(BaseManager):
    name = "user_manager"

    def create_user(self, data):
        user = UserSchema().load(data)
        user.hash_password(user.password)
        db.session.add(user)
        db.session.commit()
        return UserSchema().dump(user)

    def read_user(self, pk, exclude=None, only=None):
        user = db.session.query(UserModel).filter_by(pk=pk).first()
        kwargs = dict(
            list(filter(lambda pair: pair[1], dict(only=only, exclude=exclude).items()))
        )
        return UserSchema(**kwargs).dump(user)

    def update_user(self, pk, patches):
        user = db.session.query(UserModel).filter_by(pk=pk).first()
        [
            setattr(user, key, value)
            for key, value in patches.items()
            if key in UserSchema.Meta.editable
        ]
        db.session.commit()
        return UserSchema().dump(user)

    def delete_user(self, pk):
        user = db.session.query(UserModel).filter_by(pk=pk).first()
        db.session.delete(user)
        db.session.commit()
        return True

    def query_users(self, params):
        users = db.session.query(UserModel).filter_by(**params).all()
        return UserSchema(many=True).dump(users)

    def login(self, payload):
        # creds are posted using json payload
        provider = UserSchema(
            only=(
                "username",
                "password",
            )
        ).load(payload)
        user = db.session.query(UserModel).filter_by(username=provider.username).first()
        if not user:
            return None
        if not user.verify_password(provider.password):
            return None
        session.update(UserSchema().dump(user))
        return user

    def logout(self, **kwargs):
        session.clear()
        return True


class NetworkManager(BaseManager):
    def create_network(self, data):
        network = NetworkSchema().load(data)
        db.session.add(network)
        db.session.commit()
        return NetworkSchema().dump(network)

    def read_network(self, pk):
        network = db.session.query(NetworkModel).filter_by(pk=pk).first()
        return NetworkSchema().dump(network)

    def update_network(self, pk, patches):
        network = db.session.query(NetworkModel).filter_by(pk=pk).first()
        [
            setattr(network, key, value)
            for key, value in patches.items()
            if key in NetworkSchema.Meta.editable
        ]
        db.session.commit()
        return NetworkSchema().dump(network)

    def delete_network(self, pk):
        network = db.session.query(NetworkModel).filter_by(pk=pk).first()
        db.session.delete(network)
        db.session.commit()
        return True

    def get_followers(self, pk, page=0, size=10):
        q = db.session.query(NetworkModel).filter_by(dst_fk=pk)

        total = q.count()
        pages = total // size

        networks = q.limit(size).offset(page * size)
        content = NetworkSchema(many=True).dump(networks)
        pags = {
            "content": content,
            "metadata": {
                "page": page,
                "size": size,
                "pages": pages,
                "total": total,
                "checksum": checksum(content),
            },
        }
        return pags

    def get_following(self, pk, page=0, size=10):
        q = db.session.query(NetworkModel).filter_by(src_fk=pk)

        total = q.count()
        pages = total // size

        networks = q.limit(size).offset(page * size)
        content = NetworkSchema(many=True).dump(networks)
        pags = {
            "content": content,
            "metadata": {
                "page": page,
                "size": size,
                "pages": pages,
                "total": total,
                "checksum": checksum(content),
            },
        }
        return pags

    def follow(self, src_fk, dst_fk):
        network = (
            db.session.query(NetworkModel)
            .filter_by(src_fk=src_fk, dst_fk=dst_fk)
            .first()
        )
        if network:
            return NetworkSchema().dump(network)
        network = NetworkSchema().load(dict(src_fk=src_fk, dst_fk=dst_fk))
        db.session.add(network)
        db.session.commit()
        return NetworkSchema().dump(network)

    def unfollow(self, src_fk, dst_fk):
        network = (
            db.session.query(NetworkModel)
            .filter_by(src_fk=src_fk, dst_fk=dst_fk)
            .first()
        )
        if network:
            db.session.delete(network)
            db.session.commit()
            return True
        return False


class QueryManager(BaseManager):
    def query(self, size, page, **kwargs):
        # submodule queries should register parsers here and be able to
        # play nicely with unknown values. subqueries all run and we rank results
        user_query_params = dict()
        profile_query_params = dict()
        location_query_params = dict(distance=10000)
        calendar_query_params = dict()
        network_query_params = dict()

        # user_content = user_manager.query_users(**user_query_params)
        user_content = UserSchema(many=True).dump(db.session.query(UserModel).all())
        # profile_content = profile_manager.query_profiles()
        # location_content = location_manager.query_locations()
        # calendar_content = calendar_manager.query_calendar()
        # network_content = network_manager.query_network()

        concat = [*user_content]
        # concat = [*user_content, *profile_content, *location_content, *calendar_content, *network_content]
        # TODO: rank
        total = len(concat)
        pages = total // size
        content = concat[page * size : (page * size) + size]

        pags = {
            "content": content,
            "metadata": {
                "page": page,
                "pages": pages,
                "size": size,
                "total": total,
                "checksum": checksum(content),
                "links": {},
            },
        }
        return pags


# ----------------------------------- #
@app.errorhandler(Exception)
def error(e):
    print(e)
    return Reply.error(error=e.__class__.__qualname__)


# ----------------------------------- #
@app.route("/", methods=["GET"])
def index():
    omit = (
        "HEAD",
        "OPTIONS",
    )
    return {
        rule.rule: dict(
            methods=sorted(
                filter(
                    lambda r: r not in omit,
                    rule.methods,
                )
            ),
            endpoint=rule.endpoint,
        )
        for rule in current_app.url_map.iter_rules()
    }


@app.route("/favicon.ico")
def favicon():
    return Reply.plain(data=None)


# ----------------------------------- #
@app.route("/auth/register", methods=["POST"])
def auth_register():
    user = user_manager.create_user(request.get_json())
    return issue_token()


@app.route("/auth/login", methods=["POST"])
def issue_token():
    subject = user_manager.login(request.get_json())
    if subject is not None:
        return Reply.success(
            data=dict(pk=subject.pk, token=auth_manager.issue_token(subject=subject.pk))
        )
    return Reply.unauthorized(error="Unauthorized")


@app.route("/auth/logout", methods=["POST"])
def revoke_token():
    return Reply.success(data=user_manager.logout())


@app.route("/auth/validate", methods=["POST"])
def validate_token():
    token = auth_parser.parse_args().get("token")
    if auth_manager.check_token(token):
        return Reply.success(data=True)
    return Reply.unauthorized(data=False, error="Unauthorized")


# ----------------------------------- #
@app.route("/events", methods=["POST"])
def create_event():
    return Reply.success(data=event_manager.create_event(request.get_json()))


@app.route("/events/<int:pk>", methods=["GET"])
def read_event(pk):
    return Reply.success(data=event_manager.read_event(pk))


@app.route("/events/<int:pk>", methods=["PATCH"])
def update_event(pk):
    return Reply.success(data=event_manager.update_event(pk, request.get_json()))


@app.route("/events/<int:pk>", methods=["DELETE"])
def delete_event(pk):
    return Reply.success(data=event_manager.delete_event(pk))


@app.route("/events/query", methods=["POST"])
def query_events():
    pags = pagination_parser.parse_args()
    return Reply.success(
        data=event_manager.query_events(params=request.get_json(), **pags)
    )


# ----------------------------------- #
@app.route("/users", methods=["POST"])
def create_user():
    return Reply.success(data=user_manager.create_user(request.get_json()))


@app.route("/users/<int:pk>", methods=["GET"])
def read_user(pk):
    return Reply.success(data=user_manager.read_user(pk))


@app.route("/users/<int:pk>", methods=["PATCH"])
def update_user(pk):
    return Reply.success(data=user_manager.update_user(pk, request.get_json()))


@app.route("/users/<int:pk>", methods=["DELETE"])
def delete_user(pk):
    return Reply.success(data=user_manager.delete_user(pk))


@app.route("/users/query", methods=["GET"])
def query_users():
    return Reply.success(data=user_manager.query_users(request.args))


# ----------------------------------- #
@app.route("/profiles", methods=["POST"])
def create_profile():
    return Reply.success(data=profile_manager.create_profile(request.get_json()))


@app.route("/profiles/<int:pk>", methods=["GET"])
def read_profile(pk):
    return Reply.success(data=profile_manager.read_profile(pk))


@app.route("/profiles/<int:pk>", methods=["PATCH"])
def update_profile(pk):
    return Reply.success(data=profile_manager.update_profile(pk, request.get_json()))


@app.route("/profiles/<int:pk>", methods=["DELETE"])
def delete_profile(pk):
    return Reply.success(data=profile_manager.delete_profile(pk))


# ----------------------------------- #
@app.route("/locations", methods=["POST"])
def create_location():
    return Reply.success(data=location_manager.create_location(request.get_json()))


@app.route("/locations/<int:pk>", methods=["GET"])
def read_location(pk):
    return Reply.success(data=location_manager.read_location(pk))


@app.route("/locations/<int:pk>", methods=["PATCH"])
def update_location(pk):
    return Reply.success(data=location_manager.update_location(pk, request.get_json()))


@app.route("/locations/<int:pk>", methods=["DELETE"])
def delete_location(pk):
    return Reply.success(data=location_manager.delete_location(pk))


@app.route("/locations/query", methods=["POST"])
def query_locations():
    pags = pagination_parser.parse_args()
    locs = location_parser.parse_args()
    return Reply.success(data=location_manager.query_locations(**locs, **pags))


# ----------------------------------- #
@app.route("/messages", methods=["POST"])
def create_message():
    return Reply.success(data=message_manager.create_message(request.get_json()))


@app.route("/messages/<int:pk>", methods=["GET"])
def read_message(pk):
    return Reply.success(data=message_manager.read_message(pk))


@app.route("/messages/<int:pk>", methods=["PATCH"])
def update_message(pk):
    return Reply.success(data=message_manager.update_message(pk, request.get_json()))


@app.route("/messages/<int:pk>", methods=["DELETE"])
def delete_message(pk):
    return Reply.success(data=message_manager.delete_message(pk))


# ----------------------------------- #
@app.route("/conversations/<int:pk>", methods=["GET"])
def get_conversations(pk):
    pags = pagination_parser.parse_args()
    return Reply.success(data=message_manager.get_conversations(pk, **pags))


@app.route("/conversations/<int:src_fk>/<int:dst_fk>", methods=["GET"])
def get_conversation(src_fk, dst_fk):
    pags = pagination_parser.parse_args()
    return Reply.success(data=message_manager.get_conversation(src_fk, dst_fk, **pags))


@app.route("/chat/read/<int:src_fk>/<int:dst_fk>", methods=["POST"])
def mark_read(src_fk, dst_fk):
    return Reply.success(data=message_manager.mark_read(src_fk, dst_fk))


# ----------------------------------- #
@app.route("/notifications/<int:pk>", methods=["POST"])
def get_notifications(pk):
    return Reply.success(message_manager.get_notifications(pk))


# ----------------------------------- #
@app.route("/images", methods=["POST"])
def create_image():
    return Reply.success(data=image_manager.create_image(request.get_json()))


@app.route("/images/<int:pk>", methods=["GET"])
def read_image(pk):
    return Reply.success(data=image_manager.read_image(pk=pk))


@app.route("/images/<int:pk>", methods=["PATCH"])
def update_image(pk):
    return Reply.success(data=image_manager.update_image(pk, request.get_json()))


@app.route("/images/<int:pk>", methods=["DELETE"])
def delete_image(pk):
    return Reply.success(data=image_manager.delete_image(pk))


@app.route("/images/img/<int:pk>", methods=["GET"])
def serve_image(pk):
    image = image_manager.read_image(pk=pk)
    return Reply.plain(data=base64.b64decode(image.get("img")), dtype="image/png")


# ----------------------------------- #
@app.route("/calendar", methods=["POST"])
def create_calendar():
    return Reply.success(data=calendar_manager.create_calendar(request.get_json()))


@app.route("/calendar/<int:pk>", methods=["GET"])
def read_calendar(pk):
    return Reply.success(data=calendar_manager.read_calendar(pk))


@app.route("/calendar/<int:pk>", methods=["PATCH"])
def update_calendar(pk):
    return Reply.success(data=calendar_manager.update_calendar(pk, request.get_json()))


@app.route("/calendar/<int:pk>", methods=["DELETE"])
def delete_calendar(pk):
    return Reply.success(data=calendar_manager.delete_calendar(pk))


@app.route("/calendar/query", methods=["POST"])
def query_calendar():
    kwargs = calendar_parser.parse_args()
    return Reply.success(data=calendar_manager.query_calendar(**kwargs))


@app.route("/calendar/availability", methods=["POST"])
def set_availability():
    return Reply.success(data=calendar_manager.set_availability(request.get_json()))


# ----------------------------------- #
@app.route("/search/query", methods=["POST"])
def search_query():
    pags = pagination_parser.parse_args()
    # TODO: put back request.get_json()
    return Reply.success(data=query_manager.query(**pags))


# ----------------------------------- #
@app.route("/network", methods=["POST"])
def create_network():
    # TODO: fail if exists
    return Reply.success(data=network_manager.create_network(request.get_json()))


@app.route("/network/<int:pk>", methods=["GET"])
def read_network(pk):
    return Reply.success(data=network_manager.read_network(pk))


@app.route("/network/<int:pk>", methods=["PATCH"])
def update_network(pk):
    return Reply.success(data=network_manager.update_network(pk, request.get_json()))


@app.route("/network/<int:pk>", methods=["DELETE"])
def delete_network(pk):
    return Reply.success(data=network_manager.delete_network(pk))


@app.route("/network/followers/<int:pk>", methods=["POST"])
def network_followers(pk):
    pags = pagination_parser.parse_args()
    return Reply.success(data=network_manager.get_followers(pk, **pags))


@app.route("/network/following/<int:pk>", methods=["POST"])
def network_following(pk):
    return Reply.success(data=network_manager.get_following(pk))


# ----------------------------------- #
if __name__ == "__main__":
    dictConfig(
        {
            "version": 1,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(levelname)s - %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                }
            },
            "handlers": {
                "console": {
                    "level": "DEBUG",
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "stream": "ext://sys.stdout",
                },
                "file": {
                    "level": "DEBUG",
                    "class": "logging.handlers.RotatingFileHandler",
                    "formatter": "default",
                    "filename": "/dev/null",
                    "maxBytes": 1024,
                    "backupCount": 3,
                },
            },
            "loggers": {"": {"level": "DEBUG", "handlers": ["console", "file"]}},
            "disable_existing_loggers": False,
        }
    )
    config = Config()
    app.config.from_object(config)
    # api.init_app(app)
    db.init_app(app)
    ma.init_app(app)

    hashids.init_app(app)
    auth_manager = AuthManager()
    user_manager = UserManager()
    profile_manager = ProfileManager()
    location_manager = LocationManager()
    event_manager = EventManager()
    message_manager = MessageManager()
    image_manager = ImageManager()
    calendar_manager = CalendarManager()
    network_manager = NetworkManager()
    query_manager = QueryManager()

    RESET = True
    N = 10

    with app.app_context() as ctx:
        if RESET:
            db.drop_all()
            db.create_all()

            if N > 0:
                tic = datetime.datetime.now()
                # USERS
                with open("./data/users.json", "r") as file:
                    users = json.load(file)
                    users = users[:N]
                for i, user in tqdm(
                    enumerate(users), total=len(users), desc="Loading users"
                ):
                    trans = UserModel(**user)
                    db.session.add(trans)
                    db.session.commit()
                pprint(user_manager.read_user(pk=1))

                # PROFILES
                with open("./data/profiles.json", "r") as file:
                    profiles = json.load(file)
                    profiles = profiles[:N]
                for i, profile in tqdm(
                    enumerate(profiles), total=len(profiles), desc="Loading profiles"
                ):
                    trans = ProfileModel(**profile)
                    db.session.add(trans)
                    db.session.commit()
                # pprint(profile_manager.read_profile(pk=1))

                # MESSAGES
                with open("./data/messages.json", "r") as file:
                    messages = json.load(file)
                for i, message in tqdm(
                    enumerate(messages), total=len(messages), desc="Loading messages"
                ):
                    src_fk, dst_fk = random.sample(range(1, N + 1), 2)
                    message.update(src_fk=src_fk, dst_fk=dst_fk)
                    trans = MessageModel(**message)
                    db.session.add(trans)
                    db.session.commit()
                # pprint(message_manager.read_message(pk=1))

                # IMAGES
                for i in tqdm(range(N), desc="Loading images"):
                    array = np.stack(
                        [np.full((300, 300), random.randint(0, 255)) for _ in range(3)],
                        axis=2,
                    )
                    img = Image.fromarray(array.astype("uint8"))
                    # im.show()
                    buffer = BytesIO()
                    img.save(buffer, format="PNG")
                    myimage = buffer.getvalue()
                    image = dict(
                        fk=i + 1, img=base64.b64encode(myimage).decode("utf-8")
                    )
                    trans = ImageModel(**image)
                    db.session.add(trans)
                    db.session.commit()

                # LOCATIONS
                with open("./data/locations.json", "r") as file:
                    locations = json.load(file)
                    locations = locations[:N]
                for i, location in tqdm(
                    enumerate(locations), total=len(locations), desc="Loading locations"
                ):
                    lon, lat = location["geometry"]["coordinates"]
                    point = f"POINT({lon} {lat})"
                    label = random.choice(
                        [
                            "Small town",
                            "Big city",
                            "Metro region",
                            "Back country",
                            "Coastline",
                        ]
                    )
                    location.update(geometry=point, label=label)
                    trans = LocationModel(**location)
                    db.session.add(trans)
                    db.session.commit()
                # pprint(location_manager.read_location(pk=1))

                # NETWORKS
                networks = list()
                for a, b in tqdm(
                    itertools.combinations(range(1, N + 1), 2),
                    total=int(
                        # n choose k
                        math.factorial(N)
                        / (math.factorial(N - 2) * math.factorial(2))
                    ),
                    desc="Loading networks:",
                ):
                    outcome = random.randint(0, 3)
                    if outcome == 3:
                        # dual connection
                        data = dict(
                            src_fk=a,
                            dst_fk=b,
                        )
                        network = network_manager.create_network(data)
                        networks.append(network)
                        data = dict(
                            src_fk=b,
                            dst_fk=a,
                        )
                        network = network_manager.create_network(data)
                        networks.append(network)
                    elif outcome == 2:
                        # ltr
                        data = dict(
                            src_fk=a,
                            dst_fk=b,
                        )
                        network = network_manager.create_network(data)
                        networks.append(network)
                    elif outcome == 1:
                        # rtl
                        data = dict(
                            src_fk=b,
                            dst_fk=a,
                        )
                        network = network_manager.create_network(data)
                        networks.append(network)
                    else:
                        pass

                # CALENDARS
                calendars = list()
                for i in tqdm(range(1, N + 1), desc="Loading calendars:"):
                    today = load_date(dump_date(datetime.datetime.now()))
                    for d in range(7):
                        # do sample
                        outcome = random.choice([0, 1, 2, 3])
                        if outcome:
                            calendar = calendar_manager.create_calendar(
                                dict(date=dump_date(today), time=outcome, fk=i)
                            )
                            calendars.append(calendar)
                        today += datetime.timedelta(days=1)

        else:
            db.create_all()

        # search = "%{}%".format("er")
        # by_username = (
        #     db.session.query(UserModel).filter(UserModel.username.like(search)).all()
        # )
        # print([u["username"] for u in UserSchema(many=True).dump(by_username)])

        print("Users:", db.session.query(UserModel).count())
        # pprint(UserSchema(many=True).dump(db.session.query(UserModel).all()))
        print("Profiles:", db.session.query(ProfileModel).count())
        # pprint(ProfileSchema(many=True).dump(db.session.query(ProfileModel).all()))
        print("Messages:", db.session.query(MessageModel).count())
        # pprint(MessageSchema(many=True).dump(db.session.query(MessageModel).all()))
        print("Locations:", db.session.query(LocationModel).count())
        # pprint(LocationSchema(many=True).dump(db.session.query(LocationModel).all()))
        print("Networks:", db.session.query(NetworkModel).count())
        # pprint(NetworkSchema(many=True).dump(db.session.query(NetworkModel).all()))
        print("Calendars:", db.session.query(CalendarModel).count())

        toc = datetime.datetime.now()
        print(f"Startup Time: {toc - tic}")

    log.info("Done initializing data, starting server")
    # interactive mode
    if bool(getattr(sys, "ps1", sys.flags.interactive)):
        log.warning("🟢 Interactive Mode")
    else:
        log.warning("🔴 Non-interactive Mode")
        app.run(host="0.0.0.0", port=4000, debug=True, use_reloader=False)
