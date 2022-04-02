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

"""
UNSAFE = True
PAGINATION_PAGE = 0
PAGINATION_SIZE = 10
LOCATION_LATITUDE = 42.90168922195973
LOCATION_LONGITUDE = -78.67070653228602
LOCATION_RADIUS = 25  # miles

import sys
import pdb
import time
import json
from tqdm import tqdm
from pprint import pprint

# import jwt
from flask import Flask, current_app, request, jsonify
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
    post_dump,
    pre_load,
)
import geojson
from passlib.apps import custom_app_context as password_context
from marshmallow_sqlalchemy import ModelConverter
from geoalchemy2 import Geography
from geoalchemy2.elements import WKTElement
from geoalchemy2.functions import ST_AsGeoJSON
from hashids import Hashids as _Hashids
import shapely
from shapely.geometry import shape

# utils
def timestamp():
    return int(time.time() * 1000)


app = Flask(__name__)
# api = Api()
db = SQLAlchemy()
ma = Marshmallow()

pagination_parser = reqparse.RequestParser()
pagination_parser.add_argument(
    "page", location="args", type=int, default=PAGINATION_PAGE
)
pagination_parser.add_argument(
    "size", location="args", type=int, default=PAGINATION_SIZE
)

location_parser = reqparse.RequestParser()
location_parser.add_argument("latitude", type=float, default=LOCATION_LATITUDE)
location_parser.add_argument("longitude", type=float, default=LOCATION_LONGITUDE)
location_parser.add_argument("radius", type=float, default=LOCATION_RADIUS)
# class Hashids:
#     def __init__(self, app=None, *args, **kwargs):
#         if app:
#             self.init_app(app)
#         self._hashids = None

#     def init_app(self, app):
#         self.app = app
#         self.app.extensions["hashids"] = self
#         self.salt = app.config["SECRET_KEY"]
#         self.min_length = app.config["TOKEN_MIN_LENGTH"]
#         self.alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
#         self._hashids = _Hashids(salt=self.salt, min_length=self.min_length, alphabet=self.alphabet)

#     def encode(self, *args, **kwargs):
#         return self._hashids.encode(*args, **kwargs)

#     def decode(self, *args, **kwargs):
#         hid, *_ = self._hashids.decode(*args, **kwargs) or (None, None)
#         return hid

# class HashidField(fields.Field):
#     def _deserialize(self, value, attr, data, **kwargs):
#         if value is None:
#             return None
#         return hashids.decode(value)

#     def _serialize(self, value, attr, obj, **kwargs):
#         if value is None:
#             return None
#         return hashids.encode(value)

# hashids = Hashids()


class Reply:
    @staticmethod
    def success(data=None, error=None, status=200):
        return (
            jsonify(dict(data=data, error=error, timestamp=timestamp(), status=status)),
            status,
        )

    @staticmethod
    def error(data=None, error=None, status=400):
        return (
            jsonify(dict(data=data, error=error, timestamp=timestamp(), status=status)),
            status,
        )

    @staticmethod
    def unauthorized(data=None, error=None, status=401):
        return (
            jsonify(dict(data=data, error=error, timestamp=timestamp(), status=status)),
            status,
        )


class Config:
    SECRET_KEY = "be gay do crime"
    TOKEN_MIN_LENGTH = 8
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:postgres@localhost:5432"


class BaseModel(db.Model):
    __abstract__ = True
    pk = db.Column(db.Integer(), primary_key=True, unique=True)
    created_at = db.Column(db.BigInteger(), default=timestamp, nullable=False)
    updated_at = db.Column(
        db.BigInteger(), default=None, onupdate=timestamp, nullable=True
    )


class BaseSchema(ma.SQLAlchemyAutoSchema):
    """
    missing     used for deserialization (dump)
    default     used for serialization (load)
    https://github.com/marshmallow-code/marshmallow/issues/588#issuecomment-283544372
    """

    # pk = HashidField(dump_only=True)
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


class EventModel(BaseModel):
    __tablename__ = "events"
    stale = db.Column(db.Boolean(), unique=False, default=False)
    event = db.Column(db.String(), unique=False, nullable=False)
    source = db.Column(db.String(), unique=False, nullable=True)
    payload = db.Column(db.String(), unique=False, nullable=True)


class EventSchema(BaseSchema):
    class Meta(BaseSchema.Meta):
        model = EventModel
        editable = ("stale",)

    stale = fields.Bool(dump_only=True)
    event = fields.Str(allow_none=False)
    source = fields.Str(allow_none=True)
    payload = fields.Str(allow_none=True)


class EventManager:
    def __init__(self, *args, **kwargs):
        pass

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
        pages = total // size + 1
        content = q.limit(size).offset(page * size)
        pags = {
            "content": EventSchema(many=True).dump(content),
            "metadata": {"page": page, "size": size, "pages": pages, "total": total},
        }
        return pags


class UserModel(BaseModel):
    __tablename__ = "users"
    verified = db.Column(db.Boolean(), unique=False, default=False)
    email = db.Column(db.String(), unique=True, nullable=False)
    username = db.Column(db.String(), unique=True, nullable=False)
    password = db.Column(db.String(), unique=False, nullable=False)

    def hash_password(self, password):
        if UNSAFE:
            return
        self.password = password_context.encrypt(password)

    def verify_password(self, password):
        if UNSAFE:
            return password == self.password
        return password_context.verify(password, self.password)

    def generate_auth_token(self, ttl=600):
        pass

    @staticmethod
    def validate_auth_token(token):
        pass


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
        required=True, allow_none=False, validate=validate.Length(min=3, max=32)
    )
    password = fields.Str(
        load_only=True,
        required=True,
        allow_none=False,
        validate=validate.Length(max=128),
    )

    @validates("username")
    def validate_username(self, data, **kwargs):
        ALLOWABLE_CHARACTERS = set(
            "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789"
        )
        if not set(data).issubset(ALLOWABLE_CHARACTERS):
            raise ValidationError(
                f"Username contains non-allowable characters: {set(data).difference(ALLOWABLE_CHARACTERS)}"
            )


class UserManager:
    def __init__(self, *args, **kwargs):
        pass

    def create_user(self, data):
        user = UserSchema().load(data)
        user.hash_password(user.password)
        db.session.add(user)
        db.session.commit()
        # TODO: create profile for new user
        # TODO: create location for new user
        return UserSchema().dump(user)

    def read_user(self, pk):
        user = db.session.query(UserModel).filter_by(pk=pk).first()
        return UserSchema().dump(user)

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


class ProfileModel(BaseModel):
    __tablename__ = "profiles"
    fk = db.Column(db.Integer(), db.ForeignKey("users.pk"), nullable=False)
    alias = db.Column(
        db.String(), nullable=True, unique=False
    )  # initial default: username
    bio = db.Column(db.String(), nullable=True, unique=False)
    age = db.Column(db.Integer(), nullable=True, unique=False)
    handicap = db.Column(db.Float(), nullable=True, unique=False)
    drinking = db.Column(db.Boolean(), nullable=True, unique=False)
    ridewalk = db.Column(db.Integer(), nullable=True, unique=False)  # external enum


class ProfileSchema(BaseSchema):
    class Meta(BaseSchema.Meta):
        model = ProfileModel
        editable = (
            "alias",
            "bio",
            "age",
            "handicap",
            "drinking",
            "ridewalk",
        )

    fk = fields.Int(required=True, allow_none=False)
    alias = fields.Str(
        required=False, allow_none=True, validate=validate.Length(max=32)
    )
    bio = fields.Str(required=False, allow_none=True, validate=validate.Length(max=250))
    age = fields.Int(
        required=False, allow_none=True, validate=validate.Range(min=1, max=100)
    )
    handicap = fields.Float(required=False, allow_none=True)
    drinking = fields.Boolean(required=False, allow_none=True)
    ridewalk = fields.Integer(required=False, allow_none=True)  # enum


class ProfileManager:
    def __init__(self, *args, **kwargs):
        pass

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


class GeoField(fields.Field):
    def _serialize(self, value, attr, obj, **kwargs):
        return json.loads(geojson.dumps(shapely.wkb.loads(str(value), True)))

    def _deserialize(self, value, attr, data, **kwargs):
        return str(shape(value))


class GeoConverter(ModelConverter):
    SQLA_TYPE_MAPPING = ModelConverter.SQLA_TYPE_MAPPING.copy()
    SQLA_TYPE_MAPPING.update({Geography: GeoField})


class LocationModel(BaseModel):
    __tablename__ = "locations"
    fk = db.Column(db.Integer(), db.ForeignKey("users.pk"), nullable=False, unique=True)
    location = db.Column(
        Geography(geometry_type="POINT", srid=4326), nullable=False, unique=False
    )


class LocationSchema(BaseSchema):
    class Meta(BaseSchema.Meta):
        model = LocationModel
        model_coverter = GeoConverter
        editable = ("point",)

    fk = fields.Integer(required=True, allow_none=False)
    location = GeoField(required=True, allow_none=False)


class LocationManager:
    def __init__(self, *args, **kwargs):
        pass

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
        # do we want to accept a lat/lon or just an arbitrary geojson?
        p = WKTElement("POINT({0} {1})".format(latitude, longitude), srid=4326)
        # FIXME
        # q = db.session.query(LocationModel.location.ST_AsGeoJSON()).order_by(
        #     LocationModel.location.distance_box(p)
        # )
        q = db.session.query(LocationModel)
        total = q.count()
        pages = total // size + 1
        content = q.limit(size).offset(page * size)
        pags = {
            "content": LocationSchema(many=True).dump(content),
            "metadata": {"page": page, "size": size, "pages": pages, "total": total},
        }
        return pags


class MessageModel(BaseModel):
    __tablename__ = "messages"
    src_fk = db.Column(
        db.Integer(), db.ForeignKey("users.pk"), nullable=False, unique=False
    )
    dst_fk = db.Column(
        db.Integer(), db.ForeignKey("users.pk"), nullable=False, unique=False
    )
    body = db.Column(db.String(), nullable=False, unique=False)
    read = db.Column(db.Boolean(), nullable=False, unique=False, default=False)


class MessageSchema(BaseSchema):
    class Meta(BaseSchema.Meta):
        model = MessageModel
        editable = ("read",)

    src_fk = fields.Int(required=True, allow_none=False)
    dst_fk = fields.Int(required=True, allow_none=False)
    body = fields.Str(required=True, allow_none=False)
    read = fields.Bool(required=False, allow_none=False)


class MessageManager:
    def __init__(self, *args, **kwargs):
        pass

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
        # return the most recent message from each conversation
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
        messages = list()
        for (a, b) in records:
            message = (
                db.session.query(MessageModel)
                .filter(
                    or_(
                        (MessageModel.src_fk == a) | (MessageModel.dst_fk == b),
                        (MessageModel.src_fk == b) | (MessageModel.dst_fk == a),
                    )
                )
                .order_by(MessageModel.created_at.desc())
                .first()
            )
            messages.append(message)
        # TODO: guarantee sort messages by timestamp
        total = len(messages)
        pages = total // size + 1
        # messages = q.limit(size).offset(page * size)
        messages = messages[page * size : (page * size) + size]
        pags = {
            "content": MessageSchema(many=True).dump(messages),
            "metadata": {"page": page, "size": size, "pages": pages, "total": total},
        }
        return pags

    def get_conversation(self, src_fk, dst_fk, page=0, size=10):
        # return an ordered message history of one conversation
        q = (
            db.session.query(MessageModel)
            .filter(
                or_(
                    ((MessageModel.src_fk == src_fk) | (MessageModel.dst_fk == dst_fk)),
                    ((MessageModel.src_fk == dst_fk) | (MessageModel.dst_fk == src_fk)),
                )
            )
            .order_by(MessageModel.created_at.desc())
        )
        total = q.count()
        pages = q.count() // size + 1
        messages = q.limit(size).offset(page * size)
        pags = {
            "content": MessageSchema(many=True).dump(messages),
            "metadata": {"page": page, "size": size, "pages": pages, "total": total},
        }
        return pags


# ----------------------------------- #
@app.route("/auth/generate", methods=["POST"])
def generate_token():
    token = "asdf"
    return Reply.success(data=dict(token=token))


@app.route("/auth/validate", methods=["POST"])
def validate_token():
    token = request.args.get("token") or request.get_json().get("token")
    token = True
    return Reply.success(data=token)


# ----------------------------------- #
@app.route("/events", methods=["POST"])
def create_event():
    return Reply.success(data=event_manager.create_event(request.get_json()))


@app.route("/events/<int:pk>", methods=["GET"])
def read_event(pk=None):
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
def read_user(pk=None):
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
    # TODO: validate ownership of pk
    # TODO: optional reverse url param
    pags = pagination_parser.parse_args()
    return Reply.success(data=message_manager.get_conversations(pk, **pags))


@app.route("/conversations/<int:src_fk>/<int:dst_fk>", methods=["GET"])
def get_conversation(src_fk, dst_fk):
    # TODO: validate ownership of src_fk
    # TODO: optional reverse url param
    pags = pagination_parser.parse_args()
    return Reply.success(data=message_manager.get_conversation(src_fk, dst_fk, **pags))


# ----------------------------------- #
if __name__ == "__main__":
    config = Config()
    app.config.from_object(config)
    # api.init_app(app)
    db.init_app(app)
    ma.init_app(app)

    # hashids.init_app(app)
    user_manager = UserManager()
    profile_manager = ProfileManager()
    location_manager = LocationManager()
    event_manager = EventManager()
    message_manager = MessageManager()

    RESET = True
    N = 15

    with app.app_context() as ctx:
        if RESET:
            db.drop_all()
            db.create_all()

            with open("./data/users.json", "r") as file:
                users = json.load(file)
                users = users[:N]
            for i, user in tqdm(enumerate(users)):
                user_manager.create_user(user)

            with open("./data/profiles.json", "r") as file:
                profiles = json.load(file)
                profiles = profiles[:N]
            for i, profile in tqdm(enumerate(profiles)):
                profile_manager.create_profile({**profile, "fk": i + 1})

            with open("./data/messages.json", "r") as file:
                messages = json.load(file)
                messages = messages[:N]
            for i, message in tqdm(enumerate(messages)):
                message_manager.create_message(message)

            with open("./data/locations.json", "r") as file:
                locations = json.load(file)
                locations = locations[:N]
            for i, location in tqdm(enumerate(locations)):
                location_manager.create_location({**location, "fk": i + 1})
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

    # interactive mode
    if bool(getattr(sys, "ps1", sys.flags.interactive)):
        print("🟢 Interactive Mode")
    else:
        print("🔴 Non-interactive Mode")
        app.run(host="0.0.0.0", port=4000, debug=True, use_reloader=False)
