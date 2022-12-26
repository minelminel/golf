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

import uuid
from types import SimpleNamespace
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
from functools import wraps

from flask_redis import FlaskRedis
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
    validates_schema,
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

CREDS1 = SimpleNamespace(
    KEY=1,
    email="hello@world.com",
    username="hello",
    password="notverygood",
)

CREDS2 = SimpleNamespace(
    KEY=2,
    email="ipsum@lorem.com",
    username="world",
    password="badchoice",
)


class UnauthorizedRequest(Exception):
    """401: Unauthorized"""


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
    REDIS_URL = "redis://localhost:6379/0"

    def __init__(self, **overrides):
        for key, value in overrides.items():
            setattr(self, key, value)


# utils
def timestamp():
    return int(time.time() * 1000)


def uuidstamp():
    return str(uuid.uuid4())


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


bp = Blueprint("apiv1", __name__)
# api = Api()
db = SQLAlchemy()
ma = Marshmallow()
redis = FlaskRedis()


def app_factory(environment="develop", **overrides):
    print(f"app | environment: {environment}")
    app = Flask(__name__)
    config = Config(environment=environment, **overrides)
    app.config.from_object(config)
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
    # https://github.dev/pallets/flask/blob/a03719b01076a5bfdc2c8f4024eda7b874614bc1/src/flask/app.py#L474
    # app.url_map.converters["hashid"] = HashidConverter
    CORS(app)
    db.init_app(app)
    ma.init_app(app)
    redis.init_app(app)
    hashids.init_app(app)
    # managers.init_app(...)
    with app.app_context() as ctx:
        db.create_all()

    def handle_error(error):
        # if error.code != 404:
        #     print(traceback.format_exc())
        return Reply.error(
            error="{}:{}".format(error.__class__.__qualname__, str(error))
        )

    @app.errorhandler(Exception)
    def errorhandler(error):
        return handle_error(error)

    @bp.errorhandler(Exception)
    def errorhandler(error):
        return handle_error(error)

    url_prefix = os.path.join(app.config["ROOT"], app.config["VERSION"])
    app.register_blueprint(bp, url_prefix=url_prefix)

    return app


def RBAC(identity, qualifier):
    if identity:
        if identity.key != qualifier:
            raise UnauthorizedRequest("Invalid Scope")


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

    def __init__(self, key: int, exp=None, ttl: int = 60 * 60 * 1):
        self.key = key
        self.exp = exp if exp is not None else timestamp() + (ttl * 1000)

    @property
    def valid(self):
        if self.exp is None:
            return False
        return timestamp() < self.exp

    def serialize(self):
        return dict(key=self.key, exp=self.exp)

    @classmethod
    def deserialize(cls, key=None, exp=None, **kwargs):
        return cls(key=key, exp=exp)


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
    key = db.Column(
        db.Integer(),
        primary_key=True,
        unique=True,
    )
    created_at = db.Column(db.BigInteger(), default=timestamp, nullable=False)
    updated_at = db.Column(
        db.BigInteger(), default=None, onupdate=timestamp, nullable=True
    )


class NetworkModel(BaseModel):
    __tablename__ = "network"
    source = db.Column(
        db.Integer(), db.ForeignKey("user.key"), nullable=False, unique=False
    )
    target = db.Column(
        db.Integer(), db.ForeignKey("user.key"), nullable=False, unique=False
    )


class MessageModel(BaseModel):
    __tablename__ = "messages"
    body = db.Column(db.String(), nullable=False, unique=False)
    source = db.Column(
        db.Integer(), db.ForeignKey("user.key"), nullable=False, unique=False
    )
    target = db.Column(
        db.Integer(), db.ForeignKey("user.key"), nullable=False, unique=False
    )


class AuthModel(BaseModel):
    __tablename__ = "auth"
    renewed_at = db.Column(db.BigInteger(), unique=False, nullable=True)
    verified = db.Column(db.Boolean(), unique=False, default=False)
    email = db.Column(db.String(), unique=True, nullable=False)
    username = db.Column(db.String(), unique=True, nullable=False)
    password = db.Column(db.String(), unique=False, nullable=False)

    # profile = relationship("ProfileModel", uselist=False, back_populates="user")
    # location = relationship("LocationModel", uselist=False, back_populates="user")
    # calendar = relationship("CalendarModel", back_populates="user")
    # image = relationship("ImageModel", uselist=False, back_populates="user")

    # following = relationship("NetworkModel", back_populates="src")
    # followers = relationship("NetworkModel", back_populates="dst")

    # src_messages = relationship(
    #     "MessageModel", back_populates="src", uselist=False, lazy="select"
    # )
    # dst_messages = relationship("MessageModel", back_populates="dst")

    def hash_password(self):
        self.password = password_context.encrypt(self.password)

    def verify_password(self, password):
        return password_context.verify(password, self.password)

    def generate_auth_token(self, ttl=600):
        return dict()

    @staticmethod
    def validate_auth_token(token):
        return True


class UserModel(BaseModel):
    __tablename__ = "user"
    # TODO: FK to auth key
    # TODO: username backref
    auth_ref = relationship(
        "AuthModel", foreign_keys=[BaseModel.key], uselist=False, lazy="select"
    )
    name = db.Column(db.String(), unique=False, nullable=True)
    bio = db.Column(db.String(), unique=False, nullable=True)
    image = db.Column(db.String(), unique=False, nullable=True)
    location = db.Column(db.String(), unique=False, nullable=True)
    handicap_label = db.Column(db.String(), unique=False, nullable=True)
    handicap_value = db.Column(db.String(), unique=False, nullable=True)
    prefers_drinking = db.Column(db.String(), unique=False, nullable=True)
    prefers_gambling = db.Column(db.String(), unique=False, nullable=True)
    prefers_mobility = db.Column(db.String(), unique=False, nullable=True)
    prefers_weather = db.Column(db.String(), unique=False, nullable=True)


class CalendarModel(BaseModel):
    __tablename__ = "calendar"
    # TODO: username backref
    identity = db.Column(db.Integer(), nullable=False, unique=False)
    date = db.Column(db.Date(), nullable=False, unique=False)
    slot = db.Column(db.Integer(), nullable=False, unique=False)  # Slot enum
    available = db.Column(db.Boolean(), nullable=False, unique=False)


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


class AuthSchema(BaseSchema):
    class Meta(BaseSchema.Meta):
        model = AuthModel
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
    # profile = fields.Nested(ProfileSchema, many=False)
    # location = fields.Nested(LocationSchema, many=False)
    # calendar = fields.Nested(CalendarSchema, many=True)
    # image = fields.Nested(ImageSchema, many=False)
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

    @validates("email")
    def validate_email(self, data, **kwargs):
        return True

    @validates("password")
    def validate_password(self, data, **kwargs):
        return True


class UserSchema(BaseSchema):
    class Meta(BaseSchema.Meta):
        model = UserModel
        editable = (
            "name",
            "bio",
            "image",
            "location",
            "handicap_label",
            "handicap_value",
            "prefers_drinking",
            "prefers_gambling",
            "prefers_mobility",
            "prefers_weather",
        )
        name = fields.Str(required=False, allow_none=True)
        bio = fields.Str(required=False, allow_none=True)
        image = fields.Str(required=False, allow_none=True)
        location = fields.Str(required=False, allow_none=True)
        handicap_label = fields.Str(required=False, allow_none=True)
        handicap_value = fields.Str(required=False, allow_none=True)
        prefers_drinking = fields.Str(required=False, allow_none=True)
        prefers_gambling = fields.Str(required=False, allow_none=True)
        prefers_mobility = fields.Str(required=False, allow_none=True)
        prefers_weather = fields.Str(required=False, allow_none=True)


class MessageSchema(BaseSchema):
    class Meta(BaseSchema.Meta):
        model = MessageModel

    source = fields.Int(required=True, allow_none=False)
    target = fields.Int(required=True, allow_none=False)
    body = fields.Str(required=True, allow_none=False)

    @validates_schema
    def mututally_exclusive_parties(self, data, **kwargs):
        if data.get("source") == data.get("target"):
            raise ValidationError("Message source and target cannot be the same")
        return True


class NetworkSchema(BaseSchema):
    class Meta(BaseSchema.Meta):
        model = NetworkModel

    source = fields.Int(required=True, allow_none=False)
    target = fields.Int(required=True, allow_none=False)
    source_user = fields.Nested(
        UserSchema,
        many=False,
    )
    target_user = fields.Nested(
        UserSchema,
        many=False,
    )


class CalendarSchema(BaseSchema):
    class Meta(BaseSchema.Meta):
        model = CalendarModel

    key = fields.Int(required=True, allow_none=False)
    date = fields.Date(required=True, allow_none=False)
    slot = fields.Int(required=True, allow_none=False)
    available = fields.Bool(required=True, allow_none=False)


### MANAGERS ###
class BaseManager:
    def __init__(self, model=None, schema=None):
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

    def create(self, data, key=None):
        log.debug(f"Create: {data} (internal: {bool(key)})")
        identity = self.schema().load(data)
        if key is not None:
            identity.key = key
        db.session.add(identity)
        db.session.commit()
        return self.schema().dump(identity)

    def read(self, key, exclude=None, only=None):
        log.debug(f"Read: {key}")
        obj = self.lookup(key=key)
        if not obj:
            return None
        return self.schema(
            **{
                **({"exclude": exclude} if exclude else {}),
                **({"only": only} if only else {}),
            }
        ).dump(obj)

    def update(self, key, patches):
        log.debug(f"Update: {key}, {patches}")
        obj = self.lookup(key=key)
        wq = False
        for k, v in patches.items():
            if k not in self.schema.Meta.editable:
                log.debug(f"Skipping non-editable field update: {k}")
                continue
            log.debug(f"Rewriting field: {k}")
            par = self.schema(partial=True).load({k: v})
            setattr(obj, k, getattr(par, k))
            wq = True
        if wq:
            log.debug("Writing changes")
            db.session.commit()
        return self.schema().dump(obj)

    def delete(self, key):
        log.debug(f"Delete: {key}")
        obj = self.lookup(key=key)
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
    def __init__(self, model=AuthModel, schema=AuthSchema):
        super().__init__(model=model, schema=schema)

    def register(self, data, key=None):
        log.info(f"Creating new identity")
        identity = self.schema().load(data)
        if key is not None:
            identity.key = key
        identity.hash_password()
        db.session.add(identity)
        db.session.commit()
        log.info(f"Successfully registered identity")
        self.on_register(identity)
        return self.login(data)

    def login(self, payload):
        log.info(f"Logging in attempt")
        # allow either email or username from provider
        qualifier = (
            "username"
            if "username" in payload
            else "email"
            if "email" in payload
            else None
        )
        log.info(f"Using identity qualifier: {qualifier}")
        provider = AuthSchema(
            only=(
                qualifier,
                "password",
            )
        ).load(payload)
        identity = (
            db.session.query(AuthModel)
            .filter_by(**{qualifier: getattr(provider, qualifier)})
            .first()
        )
        if not identity:
            log.error(f"No identity registered")
            raise UnauthorizedRequest("Invalid Identity")
        if not identity.verify_password(provider.password):
            log.error(f"Invalid credentials provided")
            raise UnauthorizedRequest("Invalid Credentials")
        return self.renew(identity)

    def logout(self, identity):
        log.info(f"Logging out identity")
        return True

    def renew(self, identity):
        log.info(f"Renewing token for identity")
        identity.renewed_at = timestamp()
        db.session.commit()
        key = identity.key
        encoded = self.issue_token(key)
        return dict(key=key, token=encoded)

    # utils
    def issue_token(self, key):
        token = Token(key=key)
        encoded = jwt.encode(token.serialize(), "mysecret", algorithm="HS256")
        return encoded

    def parse_token(self, request):
        encoded = auth_parser.parse_args(request).get("token")
        if not encoded:
            log.error(f"No encoded token in request")
            return
        try:
            decoded = jwt.decode(encoded, "mysecret", algorithms=["HS256"])
        except jwt.exceptions.InvalidSignatureError as error:
            log.error(error)
            return
        except jwt.exceptions.DecodeError as error:
            log.error(error)
            return
        except Exception as exc:
            log.error(f"Unhandled authentication error: {exc}")
            return
        token = Token.deserialize(**decoded)
        return token

    # decorator
    def protect(self, f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            token = self.parse_token(request)
            if not token:
                return Reply.unauthorized(error="Invalid Token")
            if not token.valid:
                return Reply.unauthorized(error="Expired Token")
            identity = self.lookup(key=token.key)
            return f(identity, *args, **kwargs)

        return wrapped

    def on_register(self, identity):
        # register a new entry with the user manager
        fn = user_manager.create(self.schema().dump(identity), key=identity.key)
        log.info(f"hook result: {fn}")


class MessageManager(BaseManager):
    def __init__(self, model=MessageModel, schema=MessageSchema):
        super().__init__(model=model, schema=schema)

    def notify(self, message):
        log.info(f"Notifying for message")
        # set redis value for notification
        source = message["source"]
        target = message["target"]
        notification = "{}|{}".format(source, target)
        # include the key in the message
        message.update(notification=notification)
        data = json.dumps(message)
        # TODO: create acknowledgement link
        return redis.set(notification, data)

    def send(self, data):
        log.info(f"Sending message")
        message = self.create(data)
        # trigger notification
        self.notify(message)
        return message

    def get_inbox(self, key, page=PAGINATION_PAGE, size=PAGINATION_SIZE):
        # https://stackoverflow.com/questions/4378698/return-all-possible-combinations-of-values-on-columns-in-sql
        records = db.engine.execute(
            f"""
            SELECT DISTINCT m.target, m.source FROM messages m
            WHERE m.target = {key} OR  m.source = {key};
            """.format(
                key=key
            )
        )
        pairs = set([tuple(sorted(record)) for record in records])
        messages = []
        for a, b in pairs:
            message = (
                db.session.query(self.model)
                .filter(
                    or_(
                        (self.model.source == a) & (self.model.target == b),
                        (self.model.source == b) & (self.model.target == a),
                    )
                )
                .order_by(self.model.created_at.desc())
                .first()
            )
            messages.append(message)
        content = self.schema(many=True).dump(
            sorted(messages, key=lambda m: m.created_at)
        )
        pagination = {
            "content": content,
            "metadata": {
                "page": page,
                "size": size,
                "pages": None,
                "total": None,
                "checksum": checksum(content),
            },
        }
        return pagination

    def get_chat(self, source, target, page=PAGINATION_PAGE, size=PAGINATION_SIZE):
        q = (
            db.session.query(self.model)
            .filter(
                or_(
                    (self.model.source == source) & (self.model.target == target),
                    (self.model.source == target) & (self.model.target == source),
                )
            )
            .order_by(self.model.created_at.desc())
        )
        total = q.count()
        pages = total // size
        messages = q.limit(size).offset(page * size)
        content = self.schema(many=True).dump(messages)
        pagination = {
            "content": content,
            "metadata": {
                "page": page,
                "size": size,
                "pages": pages,
                "total": total,
                "checksum": checksum(content),
            },
        }
        return pagination

    def notifications(self, key):
        log.info(f"Getting notifications for: {key}")
        _, matches = redis.scan(match="*|{}".format(key))
        return [json.loads(redis.get(match)) for match in matches]

    def acknowledge(self, notification):
        log.info(f"Acknowledging notification: {notification}")
        return redis.delete(notification)


class UserManager(BaseManager):
    def __init__(self, model=UserModel, schema=UserSchema):
        super().__init__(model=model, schema=schema)

    def query(
        self, identity=None, page=PAGINATION_PAGE, size=PAGINATION_SIZE, **kwargs
    ):
        # if identity is provided, omit from the results
        # .filter(AuthModel.username.like("%{}%".format(username)))
        # name/bio
        # location/distance
        # handicap
        # preferences
        q = db.session.query(UserModel)
        if identity:
            q.filter(UserModel.key != identity.key)
        total = q.count()
        pages = total // size
        users = q.limit(size).offset(page * size)
        content = self.schema(many=True).dump(users)
        pagination = {
            "content": content,
            "metadata": {
                "page": page,
                "size": size,
                "pages": pages,
                "total": total,
                "checksum": checksum(content),
            },
        }
        return pagination


class NetworkManager(BaseManager):
    def __init__(self, model=NetworkModel, schema=NetworkSchema):
        super().__init__(model=model, schema=schema)

    def follow(self, source, target):
        network = self.lookup(source=source, target=target)
        if network:
            return None
        return self.create(dict(source=source, target=target))

    def unfollow(self, source, target):
        network = self.lookup(source=source, target=target)
        if not network:
            return None
        db.session.delete(network)
        db.session.commit()
        return True

    def get_edges(self, source, target):
        # source & target can be provided in any order
        edges = [
            self.lookup(source=source, target=target),
            self.lookup(source=target, target=source),
        ]
        return self.schema(many=True).dump([edge for edge in edges if edge])

    def get_followers(self, key, page=PAGINATION_PAGE, size=PAGINATION_SIZE):
        q = db.session.query(NetworkModel).filter_by(target=key)
        total = q.count()
        pages = total // size

        networks = q.limit(size).offset(page * size)
        content = NetworkSchema(many=True).dump(networks)
        # FIXME: reciprocity
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

    def get_following(self, key, page=PAGINATION_PAGE, size=PAGINATION_SIZE):
        q = db.session.query(NetworkModel).filter_by(source=key)

        total = q.count()
        pages = total // size

        networks = q.limit(size).offset(page * size)
        content = NetworkSchema(many=True).dump(networks)
        # FIXME: reciprocity
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


class CalendarManager(BaseManager):
    def __init__(self, model=CalendarModel, schema=CalendarSchema):
        super().__init__(model=model, schema=schema)

    def entry(self, data):
        this = self.schema().load(data)
        cursor = (
            db.session.query(CalendarModel)
            .filter_by(source=this.source, date=this.date, slot=this.slot)
            .first()
        )
        # create
        if this.available:
            if cursor:
                return True
            db.session.add(this)
            db.session.commit()
            return True
        # delete
        else:
            if cursor:
                db.session.delete(cursor)
                return False
            # nothing to do
            return False

    def query(self, *args, **kwargs):
        pass


auth_manager = AuthManager()
user_manager = UserManager()
network_manager = NetworkManager()
message_manager = MessageManager()
calendar_manager = CalendarManager()


### SERVICES ###
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
    return Reply.success(data=auth_manager.register(request.get_json()))


@bp.route("/auth/login", methods=["POST"])
def auth_token():
    return Reply.success(data=auth_manager.login(request.get_json()))


@bp.route("/auth/logout", methods=["POST"])
@auth_manager.protect
def auth_logout(identity):
    return Reply.success(data=auth_manager.logout(identity))


@bp.route("/auth/renew", methods=["POST"])
@auth_manager.protect
def auth_renew(identity):
    return Reply.success(data=auth_manager.renew(identity))


@bp.route("/auth/identity/<int:key>", methods=["GET"])
@auth_manager.protect
def auth_read(identity, key):
    RBAC(identity, key)
    return Reply.success(data=auth_manager.read(key=key))


@bp.route("/auth/identity/<int:key>", methods=["PATCH"])
@auth_manager.protect
def auth_update(identity, key):
    RBAC(identity, key)
    return Reply.success(data=auth_manager.update(request.get_json(), key=key))


# ----------------------------------- #
@bp.route("/user/<int:key>", methods=["POST"])
@auth_manager.protect
def user_create(identity, key):
    RBAC(identity, key)
    return Reply.success(data=user_manager.create(request.get_json(), key=key))


@bp.route("/user/<int:key>", methods=["GET"])
@auth_manager.protect
def user_read(identity, key):
    RBAC(identity, key)
    return Reply.success(data=user_manager.read(key))


@bp.route("/user/<int:key>", methods=["PATCH"])
@auth_manager.protect
def user_update(identity, key):
    RBAC(identity, key)
    return Reply.success(data=user_manager.update(key, request.get_json()))


@bp.route("/user/<int:key>", methods=["DELETE"])
@auth_manager.protect
def user_delete(identity, key):
    RBAC(identity, key)
    return Reply.success(data=user_manager.delete(key))


@bp.route("/user/query", methods=["POST"])
@auth_manager.protect
def user_query(identity):
    pagination = pagination_parser.parse_args()
    return Reply.success(
        data=user_manager.query(identity=identity, **request.get_json(), **pagination)
    )


# ----------------------------------- #
@bp.route("/message/send", methods=["POST"])
@auth_manager.protect
def message_send(identity):
    # TODO: validate sender from request model
    return Reply.success(data=message_manager.send(request.get_json()))


@bp.route("/message/inbox/<int:key>", methods=["GET"])
@auth_manager.protect
def message_inbox(identity, key):
    RBAC(identity, key)
    pagination = pagination_parser.parse_args()
    return Reply.success(data=message_manager.get_inbox(key, **pagination))


@bp.route("/message/chat/<int:source>/<int:target>", methods=["GET"])
@auth_manager.protect
def message_chat(identity, source, target):
    RBAC(identity, source)
    pagination = pagination_parser.parse_args()
    return Reply.success(data=message_manager.get_chat(source, target, **pagination))


@bp.route("/message/notifications/<int:key>", methods=["GET"])
@auth_manager.protect
def message_notifications(identity, key):
    RBAC(identity, key)
    return Reply.success(data=message_manager.notifications(key))


@bp.route("/message/acknowledge/<int:key>/<notification>", methods=["POST"])
@auth_manager.protect
def message_acknowledge(identity, key, notification):
    RBAC(identity, key)
    return Reply.success(data=message_manager.acknowledge(notification))


# ----------------------------------- #
@bp.route("/network/follow/<int:source>/<int:target>", methods=["POST"])
@auth_manager.protect
def network_follow(identity, source, target):
    RBAC(identity, source)
    return Reply.success(data=network_manager.follow(source, target))


@bp.route("/network/unfollow/<int:source>/<int:target>", methods=["POST"])
@auth_manager.protect
def network_unfollow(identity, source, target):
    RBAC(identity, source)
    return Reply.success(data=network_manager.unfollow(source, target))


@bp.route("/network/followers/<int:key>", methods=["GET"])
@auth_manager.protect
def network_followers(identity, key):
    pagination = pagination_parser.parse_args()
    return Reply.success(data=network_manager.get_followers(key, **pagination))


@bp.route("/network/following/<int:key>", methods=["GET"])
@auth_manager.protect
def network_following(identity, key):
    pagination = pagination_parser.parse_args()
    return Reply.success(data=network_manager.get_following(key, **pagination))


@bp.route("/network/edges/<int:source>/<int:target>", methods=["GET"])
@auth_manager.protect
def network_edges(identity, source, target):
    return Reply.success(data=network_manager.get_edges(source, target))


# ----------------------------------- #
@bp.route("/calendar/<int:key>", methods=["POST"])
@auth_manager.protect
def calendar_entry(identity, key):
    RBAC(identity, key)
    return Reply.success(calendar_manager.entry(request.get_json()))


@bp.route("/calendar/<int:key>", methods=["GET"])
@auth_manager.protect
def calendar_query(identity, key):
    return Reply.success(data=calendar_manager.query(request.get_json()))


def mock_factory(app):
    log.warning(f"Loading mock data")
    with app.app_context() as ctx:
        auth1 = auth_manager.register(vars(CREDS1), key=CREDS1.KEY)
        auth2 = auth_manager.register(vars(CREDS2), key=CREDS2.KEY)

        for i in range(100):
            try:
                message_manager.send(
                    dict(
                        source=random.randint(1, 10),
                        target=random.randint(1, 10),
                        body=uuidstamp(),
                    )
                )
            except Exception as error:
                pass

    # key, token
    return auth1


# ----------------------------------- #
if __name__ == "__main__":
    tic = datetime.datetime.now()
    app = app_factory(environment="develop")

    here = os.path.dirname(os.path.abspath(__file__))
    data = os.path.join(os.path.dirname(here), "data")

    RESET = True
    MOCK = True

    with app.app_context() as ctx:
        if RESET:
            db.drop_all()
            db.create_all()
        if MOCK:
            auth = mock_factory(app)
            print(f"---Token Authentication---\n{auth}")

        toc = datetime.datetime.now()
        print(f"Startup Time: {toc - tic}")

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
