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
ROOT = "/api"
LOCALHOST = "http://192.168.1.114:4000" + ROOT
UNSAFE = True
PAGINATION_PAGE = 0
PAGINATION_SIZE = 10
LOCATION_LATITUDE = 42.90168922195973
LOCATION_LONGITUDE = -78.67070653228602
LOCATION_RADIUS = 25  # miles
SRID = 4326
METERS_IN_MILE = 1609.344


import traceback
import os
import logging
from logging.config import dictConfig
import math
import base64
import hashlib
import sys
import datetime
from pdb import set_trace as debug
import time
import json
import random
from tqdm import tqdm
from pprint import pprint
from functools import wraps
from types import SimpleNamespace
from io import BytesIO
import itertools
from abc import abstractmethod


from werkzeug.routing import BaseConverter
import numpy as np
from PIL import Image
import jwt
from sqlalchemy import and_, func
from flask_cors import CORS
from sqlalchemy.orm import relationship
from flask import (
    Flask,
    Blueprint,
    current_app,
    request,
    jsonify,
    session,
    make_response,
)
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
    post_load,
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

log = logging.getLogger(__name__)


class Config:
    ROOT = "/api"
    VERSION = "v1"
    TESTING = False
    ENVIRONMENT = "develop"
    FLASK_HOST = "0.0.0.0"
    FLASK_PORT = 4000
    FLASK_DEBUG_ENABLED = False
    FLASK_USE_RELOADER = False
    SECRET_KEY = "helloworld"
    TOKEN_MIN_LENGTH = 8
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:postgres@localhost:5432"

    def __init__(self, **overrides):
        for key, value in overrides.items():
            setattr(self, key, value)


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


def dedupe(array):
    # order-preserving deduplication
    return [element for i, element in enumerate(array) if element not in set(array[:i])]


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


class HashidConverter(BaseConverter):
    def to_python(self, value):
        return hashids.decode(value)

    def to_url(self, value):
        return hashids.encode(value) if value is not None else ""


# app = Flask(__name__)
bp = Blueprint("apiv1", __name__)
# api = Api()
db = SQLAlchemy()
ma = Marshmallow()


def app_factory(environment="develop"):
    print(f"app | environment: {environment}")
    app = Flask(__name__)
    config = Config()
    app.config.from_object(config)
    # https://github.dev/pallets/flask/blob/a03719b01076a5bfdc2c8f4024eda7b874614bc1/src/flask/app.py#L474
    # app.url_map.converters["hashid"] = HashidConverter
    CORS(app)
    db.init_app(app)
    ma.init_app(app)

    def handle_error(error):
        if error.code != 404:
            print(traceback.format_exc())
        return Reply.error(error=error.__class__.__qualname__)

    @app.errorhandler(Exception)
    def errorhandler(error):
        return handle_error(error)

    @bp.errorhandler(Exception)
    def errorhandler(error):
        return handle_error(error)

    url_prefix = os.path.join(app.config["ROOT"], app.config["VERSION"])
    app.register_blueprint(bp, url_prefix=url_prefix)

    return app


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


class HashidField(fields.Field):
    def _deserialize(self, value, attr, data, **kwargs):
        # we decode at service layer
        return value
        # if value is None:
        #     return None
        # return hashids.decode(value)

    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return None
        return hashids.encode(value)


def authenticated(*args, **kwargs):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # new request or keep-alice
            if UNSAFE:
                log.warning(f" * * @auth: running in UNSAFE mode * * ")
                return f(*args, **kwargs)
            if session:
                log.info(f"Connecting existing session")
                return f(*args, **kwargs)
            return Reply.unauthorized(error="Unauthorized")

        return decorated_function

    return decorator


def require(*args, **kwargs):
    for arg in args:
        if not bool(arg):
            raise Exception("required stuff!")
    for key, value in kwargs.items():
        if not bool(value):
            raise Exception("required stuff!")


### POJO ###
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
        return cls(hashids.decode(sub), exp=exp)


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


### MODELS ###
class BaseModel(db.Model):
    __abstract__ = True
    pk = db.Column(
        db.Integer(),
        primary_key=True,
        unique=True,
    )
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


### SCHEMAS ###
class BaseSchema(ma.SQLAlchemyAutoSchema):
    """
    load_default     used for deserialization (dump)
    dump_default     used for serialization (load)
    https://github.com/marshmallow-code/marshmallow/issues/588#issuecomment-283544372
    """

    # pk = HashidField(dump_only=True)  # this does work
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

    fk = HashidField(required=True, allow_none=False)
    alias = fields.Str(
        required=False, allow_none=True, validate=validate.Length(max=32)
    )
    bio = fields.Str(required=False, allow_none=True, validate=validate.Length(max=250))
    age = fields.Int(
        required=False, allow_none=True, validate=validate.Range(min=1, max=100)
    )
    handicap = fields.Float(required=False, allow_none=True)
    drinking = fields.Integer(required=False, allow_none=True, load_default=0)
    mobility = fields.Integer(required=False, allow_none=True, load_default=0)
    weather = fields.Integer(required=False, allow_none=True, load_default=0)


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
    distance = fields.Decimal(required=False)


class ImageSchema(BaseSchema):
    class Meta(BaseSchema.Meta):
        model = ImageModel

    fk = HashidField(required=True, allow_none=False)
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

    fk = HashidField(required=True, allow_none=False)


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

    src_fk = HashidField(required=True, allow_none=False)
    dst_fk = HashidField(required=True, allow_none=False)
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

    src_fk = HashidField(required=True, allow_none=False)
    dst_fk = HashidField(required=True, allow_none=False)
    src = fields.Nested(
        UserSchema,
        many=False,
    )
    dst = fields.Nested(
        UserSchema,
        many=False,
    )


### MANAGERS ###
class BaseManager:
    def __init__(self, name="Base", model=None, schema=None):
        self.name = name
        self.model = model
        self.schema = schema
        log.info(f"Created: {self}")

    def __repr__(self):
        return "<{} model={} schema={}>".format(
            self.__class__.__qualname__,
            self.model,
            self.schema,
        )

    def lookup(self, **kwargs):
        return db.session.query(self.model).filter_by(**kwargs).first()

    def create(self, data):
        log.debug(f"Create: {data}")
        obj = self.schema().load(data)
        db.session.add(obj)
        db.session.commit()
        return self.schema().dump(obj)

    def read(self, pk, exclude=None, only=None):
        log.debug(f"Read: {pk}")
        obj = self.lookup(pk=pk)
        if not obj:
            return None
        return self.schema(
            **{
                **({"exclude": exclude} if exclude else {}),
                **({"only": only} if only else {}),
            }
        ).dump(obj)

    def update(self, pk, patches):
        log.debug(f"Update: {pk}, {patches}")
        obj = self.lookup(pk=pk)
        [
            setattr(obj, key, value)
            for key, value in patches.items()
            if key in self.schema.Meta.editable
        ]
        db.session.commit()
        return self.schema().dump(obj)

    def delete(self, pk):
        log.debug(f"Delete: {pk}")
        obj = self.lookup(pk=pk)
        db.session.delete(obj)
        db.session.commit()
        return True

    def bulk_read(self, **params):
        log.debug(f"Bulk read: {params}")
        objs = (
            db.session.query(self.model)
            .filter(
                *[
                    getattr(self.model, key).in_(dedupe(value))
                    for key, value in params.items()
                ]
            )
            .all()
        )
        return self.schema(many=True).dump(objs)

    @abstractmethod
    def query(self, page=PAGINATION_PAGE, size=PAGINATION_SIZE, **kwargs):
        pass


class AuthManager(BaseManager):
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
    def __init__(self, model=EventModel, schema=EventSchema):
        super().__init__(model=model, schema=schema)

    def query(self, params, page, size):
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
    def __init__(self, model=ProfileModel, schema=ProfileSchema):
        super().__init__(model=model, schema=schema)

    def query(self, page=PAGINATION_PAGE, size=PAGINATION_SIZE, **kwargs):
        alias = kwargs.get("alias")

        q = db.session.query(ProfileModel).filter(
            ProfileModel.alias.like("%{}%".format(alias))
        )
        total = q.count()
        pages = total // size
        profiles = q.limit(size).offset(page * size)
        content = ProfileSchema(many=True).dump(profiles)
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


class LocationManager(BaseManager):
    def __init__(self, model=LocationModel, schema=LocationSchema):
        super().__init__(model=model, schema=schema)

    def query(self, latitude, longitude, radius, page, size):
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
    def __init__(self, model=ImageModel, schema=ImageSchema):
        super().__init__(model=model, schema=schema)


class MessageManager(BaseManager):
    def __init__(self, model=MessageModel, schema=MessageSchema):
        super().__init__(model=model, schema=schema)

    @classmethod
    def get_conversation_pairs(cls, fk):
        # [(3, 1), (1, 2)]
        #   [(1, 2), (2, 1)]
        #   [(1, 3), (3, 1)]
        if fk is None:
            return []
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

    def get_conversations(self, fk, page=PAGINATION_PAGE, size=PAGINATION_SIZE):
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

    def get_conversation(
        self, src_fk, dst_fk, page=PAGINATION_PAGE, size=PAGINATION_SIZE
    ):
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
        src = user_manager.read(src_fk, exclude=["calendar", "profile", "location"])
        dst = user_manager.read(dst_fk, exclude=["calendar", "profile", "location"])
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
            self.update(pk=message.pk, patches=dict(read=True))
        return len(messages)


class CalendarManager(BaseManager):
    def __init__(self, model=CalendarModel, schema=CalendarSchema):
        super().__init__(model=model, schema=schema)

    def query(self, fk, date, days):
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
            return self.create(data)
        calendar = CalendarSchema().load(data)
        result = (
            db.session.query(CalendarModel)
            .filter_by(fk=calendar.fk, date=calendar.date, time=calendar.time)
            .first()
        )
        if result:
            return self.delete(result.pk)


class UserManager(BaseManager):
    def __init__(self, model=UserModel, schema=UserSchema):
        super().__init__(model=model, schema=schema)

    # @override
    def create(self, data):
        user = self.schema().load(data)
        user.hash_password(user.password)
        db.session.add(user)
        db.session.commit()
        return self.schema().dump(user)

    def query(self, page=PAGINATION_PAGE, size=PAGINATION_SIZE, **kwargs):
        username = kwargs.get("username")

        q = db.session.query(UserModel).filter(
            UserModel.username.like("%{}%".format(username))
        )
        total = q.count()
        pages = total // size
        users = q.limit(size).offset(page * size)
        content = UserSchema(many=True).dump(users)
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
    def __init__(self, model=NetworkModel, schema=NetworkSchema):
        super().__init__(model=model, schema=schema)

    def is_reciprocal(self, src_fk, dst_fk):
        # given a->b, does b->a
        network = (
            db.session.query(NetworkModel)
            .filter_by(src_fk=dst_fk, dst_fk=src_fk)
            .first()
        )
        return bool(network)

    def get_followers(self, pk, page=PAGINATION_PAGE, size=PAGINATION_SIZE):
        # SRC: others
        # DST: us
        q = db.session.query(NetworkModel).filter_by(dst_fk=pk)
        total = q.count()
        pages = total // size

        networks = q.limit(size).offset(page * size)
        content = NetworkSchema(many=True).dump(networks)
        # FIXME: reciprocity
        [
            c["network"].update(reciprocal=self.is_reciprocal(c["src_fk"], c["dst_fk"]))
            if c.get("network")
            else c.update(
                network=dict(reciprocal=self.is_reciprocal(c["src_fk"], c["dst_fk"]))
            )
            for c in content
        ]
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

    def get_following(self, pk, page=PAGINATION_PAGE, size=PAGINATION_SIZE):
        # SRC: us
        # DST: others
        q = db.session.query(NetworkModel).filter_by(src_fk=pk)

        total = q.count()
        pages = total // size

        networks = q.limit(size).offset(page * size)
        content = NetworkSchema(many=True).dump(networks)
        # FIXME: reciprocity
        [
            c["network"].update(reciprocal=self.is_reciprocal(c["dst_fk"], c["src_fk"]))
            if c.get("network")
            else c.update(
                network=dict(reciprocal=self.is_reciprocal(c["dst_fk"], c["src_fk"]))
            )
            for c in content
        ]
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
    def __init__(self, model=None, schema=None):
        super().__init__(model=model, schema=schema)

    def query(self, page=PAGINATION_PAGE, size=PAGINATION_SIZE, **kwargs):
        # query multiple managers to grab the coresponding `users` pk's,
        # then do a bulk query & merge these results.

        # submodule queries should register parsers here and be able to
        # play nicely with unknown values. subqueries all run and we rank results
        user_query_params = dict(username=kwargs.get("username"))
        profile_query_params = dict(alias=kwargs.get("alias"))
        # ...

        users = user_manager.query(page=page, size=size, **user_query_params)
        profiles = profile_manager.query(page=page, size=size, **profile_query_params)
        # ...

        pks = list()
        pks.extend([obj["pk"] for obj in users["content"]])
        pks.extend([obj["fk"] for obj in profiles["content"]])
        # ...

        records = user_manager.bulk_read(pk=pks)
        # TODO: rank
        total = len(records)
        pages = total // size
        content = records[page * size : (page * size) + size]

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


### SERVICES ###
# ----------------------------------- #
# @app.errorhandler(Exception)
# def error(e):
#     if e.code != 404:
#         print(traceback.format_exc())
#     return Reply.error(error=e.__class__.__qualname__)


# ----------------------------------- #
@bp.route("/", methods=["GET"])
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


# ----------------------------------- #
@bp.route("/auth/register", methods=["POST"])
def auth_register():
    user = user_manager.create(request.get_json())
    return issue_token()


@bp.route("/auth/login", methods=["POST"])
def issue_token():
    subject = user_manager.login(request.get_json())
    if not subject:
        return Reply.unauthorized(error="Unauthorized")
    pk = UserSchema().dump(subject).get("pk")
    return Reply.success(data=dict(pk=pk, token=auth_manager.issue_token(subject=pk)))


@bp.route("/auth/logout", methods=["POST"])
def revoke_token():
    return Reply.success(data=user_manager.logout())


@bp.route("/auth/validate", methods=["POST"])
def validate_token():
    token = auth_parser.parse_args().get("token")
    if auth_manager.check_token(token):
        return Reply.success(data=True)
    return Reply.unauthorized(data=False, error="Unauthorized")


# ----------------------------------- #
@bp.route("/events", methods=["POST"])
@authenticated()
def create_event():
    return Reply.success(data=event_manager.create(request.get_json()))


@bp.route("/events/<int:pk>", methods=["GET"])
@authenticated()
def read_event(pk):
    return Reply.success(data=event_manager.read(pk))


@bp.route("/events/<int:pk>", methods=["PATCH"])
@authenticated()
def update_event(pk):
    return Reply.success(data=event_manager.update(pk, request.get_json()))


@bp.route("/events/<int:pk>", methods=["DELETE"])
@authenticated()
def delete_event(pk):
    return Reply.success(data=event_manager.delete(pk))


@bp.route("/events/query", methods=["POST"])
@authenticated()
def query_events():
    pags = pagination_parser.parse_args()
    return Reply.success(data=event_manager.query(params=request.get_json(), **pags))


# ----------------------------------- #
@bp.route("/users", methods=["POST"])
@authenticated()
def create_user():
    return Reply.success(data=user_manager.create(request.get_json()))


@bp.route("/users/<int:pk>", methods=["GET"])
@authenticated()
def read_user(pk):
    return Reply.success(data=user_manager.read(pk))


@bp.route("/users/<int:pk>", methods=["PATCH"])
@authenticated()
def update_user(pk):
    return Reply.success(data=user_manager.update(pk, request.get_json()))


@bp.route("/users/<int:pk>", methods=["DELETE"])
@authenticated()
def delete_user(pk):
    return Reply.success(data=user_manager.delete(pk))


@bp.route("/users/query", methods=["POST"])
@authenticated()
def query_users():
    pags = pagination_parser.parse_args()
    return Reply.success(data=user_manager.query(**request.get_json(), **pags))


# ----------------------------------- #
@bp.route("/profiles", methods=["POST"])
@authenticated()
def create_profile():
    return Reply.success(data=profile_manager.create(request.get_json()))


@bp.route("/profiles/<int:pk>", methods=["GET"])
@authenticated()
def read_profile(pk):
    return Reply.success(data=profile_manager.read(pk))


@bp.route("/profiles/<int:pk>", methods=["PATCH"])
@authenticated()
def update_profile(pk):
    return Reply.success(data=profile_manager.update(pk, request.get_json()))


@bp.route("/profiles/<int:pk>", methods=["DELETE"])
@authenticated()
def delete_profile(pk):
    return Reply.success(data=profile_manager.delete(pk))


# ----------------------------------- #
@bp.route("/locations", methods=["POST"])
@authenticated()
def create_location():
    return Reply.success(data=location_manager.create(request.get_json()))


@bp.route("/locations/<int:pk>", methods=["GET"])
@authenticated()
def read_location(pk):
    return Reply.success(data=location_manager.read(pk))


@bp.route("/locations/<int:pk>", methods=["PATCH"])
@authenticated()
def update_location(pk):
    return Reply.success(data=location_manager.update(pk, request.get_json()))


@bp.route("/locations/<int:pk>", methods=["DELETE"])
@authenticated()
def delete_location(pk):
    return Reply.success(data=location_manager.delete(pk))


@bp.route("/locations/query", methods=["POST"])
@authenticated()
def query_locations():
    pags = pagination_parser.parse_args()
    locs = location_parser.parse_args()
    return Reply.success(data=location_manager.query(**locs, **pags))


# ----------------------------------- #
@bp.route("/messages", methods=["POST"])
@authenticated()
def create_message():
    return Reply.success(data=message_manager.create(request.get_json()))


@bp.route("/messages/<int:pk>", methods=["GET"])
@authenticated()
def read_message(pk):
    return Reply.success(data=message_manager.read(pk))


@bp.route("/messages/<int:pk>", methods=["PATCH"])
@authenticated()
def update_message(pk):
    return Reply.success(data=message_manager.update(pk, request.get_json()))


@bp.route("/messages/<int:pk>", methods=["DELETE"])
@authenticated()
def delete_message(pk):
    return Reply.success(data=message_manager.delete(pk))


# ----------------------------------- #
@bp.route("/conversations/<int:pk>", methods=["GET"])
@authenticated()
def get_conversations(pk):
    pags = pagination_parser.parse_args()
    return Reply.success(data=message_manager.get_conversations(pk, **pags))


@bp.route("/conversations/<int:src_fk>/<int:dst_fk>", methods=["GET"])
@authenticated()
def get_conversation(src_fk, dst_fk):
    pags = pagination_parser.parse_args()
    return Reply.success(data=message_manager.get_conversation(src_fk, dst_fk, **pags))


@bp.route("/chat/read/<int:src_fk>/<int:dst_fk>", methods=["POST"])
@authenticated()
def mark_read(src_fk, dst_fk):
    return Reply.success(data=message_manager.mark_read(src_fk, dst_fk))


# ----------------------------------- #
@bp.route("/notifications/<int:pk>", methods=["GET"])
@authenticated()
def get_notifications(pk):
    return Reply.success(data=message_manager.get_notifications(pk))


# ----------------------------------- #
@bp.route("/images", methods=["POST"])
@authenticated()
def create_image():
    return Reply.success(data=image_manager.create(request.get_json()))


@bp.route("/images/<int:pk>", methods=["GET"])
@authenticated()
def read_image(pk):
    return Reply.success(data=image_manager.read(pk=pk))


@bp.route("/images/<int:pk>", methods=["PATCH"])
@authenticated()
def update_image(pk):
    return Reply.success(data=image_manager.update(pk, request.get_json()))


@bp.route("/images/<int:pk>", methods=["DELETE"])
@authenticated()
def delete_image(pk):
    return Reply.success(data=image_manager.delete(pk))


@bp.route("/images/img/<int:pk>", methods=["GET"])
def serve_image(pk):
    return Reply.plain(
        data=base64.b64decode(image_manager.read(pk=pk).get("img")), dtype="image/png"
    )


# ----------------------------------- #
@bp.route("/calendar", methods=["POST"])
@authenticated()
def create_calendar():
    return Reply.success(data=calendar_manager.create(request.get_json()))


@bp.route("/calendar/<int:pk>", methods=["GET"])
@authenticated()
def read_calendar(pk):
    return Reply.success(data=calendar_manager.read(pk))


@bp.route("/calendar/<int:pk>", methods=["PATCH"])
@authenticated()
def update_calendar(pk):
    return Reply.success(data=calendar_manager.update(pk, request.get_json()))


@bp.route("/calendar/<int:pk>", methods=["DELETE"])
@authenticated()
def delete_calendar(pk):
    return Reply.success(data=calendar_manager.delete(pk))


@bp.route("/calendar/query", methods=["POST"])
@authenticated()
def query_calendar():
    kwargs = calendar_parser.parse_args()
    return Reply.success(data=calendar_manager.query(**kwargs))


@bp.route("/calendar/availability", methods=["POST"])
@authenticated()
def set_availability():
    return Reply.success(data=calendar_manager.set_availability(request.get_json()))


# ----------------------------------- #
@bp.route("/search/query", methods=["POST"])
@authenticated()
def search_query():
    pags = pagination_parser.parse_args()
    return Reply.success(data=query_manager.query(**request.get_json(), **pags))


# ----------------------------------- #
@bp.route("/network", methods=["POST"])
@authenticated()
def create_network():
    # TODO: fail if exists
    return Reply.success(data=network_manager.create(request.get_json()))


@bp.route("/network/<int:pk>", methods=["GET"])
@authenticated()
def read_network(pk):
    return Reply.success(data=network_manager.read(pk))


@bp.route("/network/<int:pk>", methods=["PATCH"])
@authenticated()
def update_network(pk):
    return Reply.success(data=network_manager.update(pk, request.get_json()))


@bp.route("/network/<int:pk>", methods=["DELETE"])
@authenticated()
def delete_network(pk):
    return Reply.success(data=network_manager.delete(pk))


@bp.route("/network/follow", methods=["POST"])
@authenticated()
def follow():
    return Reply.success(data=network_manager.follow(**request.get_json()))


@bp.route("/network/unfollow", methods=["POST"])
@authenticated()
def unfollow():
    return Reply.success(data=network_manager.unfollow(**request.get_json()))


@bp.route("/network/followers/<int:pk>", methods=["POST"])
@authenticated()
def network_followers(pk):
    pags = pagination_parser.parse_args()
    return Reply.success(data=network_manager.get_followers(pk, **pags))


@bp.route("/network/following/<int:pk>", methods=["POST"])
@authenticated()
def network_following(pk):
    return Reply.success(data=network_manager.get_following(pk))


# ----------------------------------- #
@bp.route("/hash/<int:pk>")
def hash_route(pk):
    return Reply.success(data=dict(pk=pk, type=str(type(pk))))


# ----------------------------------- #
if __name__ == "__main__":
    tic = datetime.datetime.now()
    here = os.path.dirname(os.path.abspath(__file__))
    data = os.path.join(os.path.dirname(here), "data")

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
                    "level": "INFO",
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
    app = app_factory(environment="develop")

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
    N = 5

    with app.app_context() as ctx:
        if RESET:
            db.drop_all()
            db.create_all()

            if N > 0:
                # USERS
                with open(os.path.join(data, "users.json"), "r") as file:
                    users = json.load(file)
                    users = users[:N]
                for i, user in tqdm(
                    enumerate(users), total=len(users), desc="Loading users"
                ):
                    trans = UserModel(**user)
                    db.session.add(trans)
                    db.session.commit()
                # pprint(user_manager.read(pk=1))

                # PROFILES
                with open(os.path.join(data, "profiles.json"), "r") as file:
                    profiles = json.load(file)
                    profiles = profiles[:N]
                for i, profile in tqdm(
                    enumerate(profiles), total=len(profiles), desc="Loading profiles"
                ):
                    trans = ProfileModel(**profile)
                    db.session.add(trans)
                    db.session.commit()
                # pprint(profile_manager.read(pk=1))

                # MESSAGES
                with open(os.path.join(data, "messages.json"), "r") as file:
                    messages = json.load(file)
                for i, message in tqdm(
                    enumerate(messages), total=len(messages), desc="Loading messages"
                ):
                    src_fk, dst_fk = random.sample(range(1, N + 1), 2)
                    message.update(src_fk=src_fk, dst_fk=dst_fk)
                    trans = MessageModel(**message)
                    db.session.add(trans)
                    db.session.commit()
                # pprint(message_manager.read(pk=1))

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
                with open(os.path.join(data, "locations.json"), "r") as file:
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
                # pprint(location_manager.read(pk=1))

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
                        network = network_manager.create(data)
                        networks.append(network)
                        data = dict(
                            src_fk=b,
                            dst_fk=a,
                        )
                        network = network_manager.create(data)
                        networks.append(network)
                    elif outcome == 2:
                        # ltr
                        data = dict(
                            src_fk=a,
                            dst_fk=b,
                        )
                        network = network_manager.create(data)
                        networks.append(network)
                    elif outcome == 1:
                        # rtl
                        data = dict(
                            src_fk=b,
                            dst_fk=a,
                        )
                        network = network_manager.create(data)
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
                            calendar = calendar_manager.create(
                                dict(date=dump_date(today), time=outcome, fk=i)
                            )
                            calendars.append(calendar)
                        today += datetime.timedelta(days=1)

        else:
            db.create_all()

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

    log.info(f"Hashid (1): {hashids.encode(1)}")
    # interactive mode
    if bool(getattr(sys, "ps1", sys.flags.interactive)):
        log.warning("🟢 Interactive Mode")
    else:
        log.warning("🔴 Non-interactive Mode")
        app.run(
            host=app.config["FLASK_HOST"],
            port=app.config["FLASK_PORT"],
            debug=app.config["FLASK_DEBUG_ENABLED"],
            use_reloader=app.config["FLASK_USE_RELOADER"],
        )
