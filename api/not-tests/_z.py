__version__ = "v1"
import os
import traceback
from enum import Enum
from time import time as now
from uuid import uuid4
from pdb import set_trace as debug
from functools import wraps

from flask import Flask, Blueprint, session, request, jsonify, current_app
from flask_restful import reqparse
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy as sql
import marshmallow as mm
from flask_marshmallow import Marshmallow
from marshmallow_enum import EnumField
import jwt

# app = Flask(__name__)
API = f"/api/{__version__}"

AuthBlueprint = Blueprint("auth", __name__)
UserBlueprint = Blueprint("user", __name__)
NetworkBlueprint = Blueprint("network", __name__)
MessageBlueprint = Blueprint("message", __name__)
CalendarBlueprint = Blueprint("calendar", __name__)

db = SQLAlchemy()
ma = Marshmallow()

time = lambda: int(now() * 1000)
uuid = lambda: str(uuid4())


def get_token_from_headers(request):
    authorization = "authorization"
    parser = reqparse.RequestParser()
    parser.add_argument(authorization, type=str, location="headers")
    kwargs = parser.parse_args()
    try:
        prefix, token = kwargs.get(authorization).split(" ", 2)
        decoded = jwt.decode(
            token, current_app.config["SECRET_KEY"], algorithms=["HS256"]
        )
        return decoded
    except Exception as err:
        return None


def rbac(identity, parameter):
    # if identity.role == Role.ADMIN:
    #     return
    return True
    # if identity.key != parameter:
    #     raise Exception("Unauthorized")


# POJO
class ExtendedEnum(Enum):
    """
    MyEnum(0)
        -> raises ValueError if invalid
    MyEnum["KEY"], MyEnum.KEY
        -> raises AttributeError if invalid
    """

    @classmethod
    def names(cls):
        return list(map(lambda e: e.name, cls))

    @classmethod
    def values(cls):
        return list(map(lambda e: e.value, cls))

    @classmethod
    def items(cls):
        return list(map(lambda e: (e.name, e.value), cls))


class Role(ExtendedEnum):
    USER = 0
    ADMIN = 1


class BaseModel(db.Model):
    __abstract__ = True
    key = db.Column(db.Integer(), primary_key=True, unique=True)
    created_at = db.Column(db.BigInteger(), nullable=False, unique=False, default=time)
    updated_at = db.Column(db.BigInteger(), nullable=True, unique=False, onupdate=time)


class BaseSchema(ma.SQLAlchemyAutoSchema):
    """
    missing     used for deserialization (dump)
    default     used for serialization (load)
    https://github.com/marshmallow-code/marshmallow/issues/588#issuecomment-283544372
    """

    # pk = HashidField(dump_only=True)  # this does work
    key = mm.fields.Int(dump_only=True)
    created_at = mm.fields.Int(dump_only=True)
    updated_at = mm.fields.Int(dump_only=True)

    class Meta:
        """Alternate method of configuration which eliminates the need to
        subclass BaseSchema.Meta
        https://marshmallow-sqlalchemy.readthedocs.io/en/latest/recipes.html#base-schema-ii
        """

        sqla_session = db.session
        load_instance = True
        transient = True
        unknown = mm.EXCLUDE
        editable = ()  # external implementation

    @mm.pre_load
    def set_nested_session(self, data, **kwargs):
        """Allow nested schemas to use the parent schema's session. This is a
        longstanding bug with marshmallow-sqlalchemy.
        https://github.com/marshmallow-code/marshmallow-sqlalchemy/issues/67
        https://github.com/marshmallow-code/marshmallow/issues/658#issuecomment-328369199
        """
        nested_fields = {
            k: v for k, v in self.fields.items() if type(v) == mm.fields.Nested
        }
        for field in nested_fields.values():
            field.schema.session = self.session
        return data


class AuthModel(BaseModel):
    __tablename__ = "auth"
    role = db.Column(db.String(), nullable=False, unique=False, default="USER")
    renewed_at = db.Column(db.BigInteger(), nullable=True, unique=False)
    email = db.Column(db.String(), nullable=False, unique=True)
    username = db.Column(db.String(), nullable=False, unique=True)
    password = db.Column(db.String(), nullable=False, unique=False)

    def renew(self):
        self.renewed_at = time()

    def hash_password(self):
        print("auth | hashing password")
        self.password = "asdf"

    def check_password(self, password):
        print("auth | check password")
        return True


class UserModel(BaseModel):
    __tablename__ = "user"
    # username = db.Column(db.String(), db.ForeignKey("auth.username"), nullable=False)
    username = db.Column(db.ForeignKey(AuthModel.username))
    my_name = db.Column(db.String(), nullable=True, unique=False)
    my_bio = db.Column(db.String(), nullable=True, unique=False)


class AuthSchema(BaseSchema):
    class Meta(BaseSchema.Meta):
        model = AuthModel

    # role = EnumField(Role)
    role = mm.fields.Str(dump_only=True)
    renewed_at = mm.fields.Int(dump_only=True)
    email = mm.fields.Str(required=True, allow_none=False)
    username = mm.fields.Str(required=True, allow_none=False)
    password = mm.fields.Str(required=True, allow_none=False, load_only=True)


class UserSchema(BaseSchema):
    class Meta(BaseSchema.Meta):
        model = UserModel

    # username = mm.fields.Str()


class AuthManager:
    def register(self, data) -> dict:
        print(f"auth | register")
        this = AuthSchema().load(data)
        this.hash_password()
        db.session.add(this)
        db.session.commit()
        # create user associated with this identity
        user_manager.create(key=this.key)
        return self.login(data)

    def login(self, data) -> dict:
        print(f"auth | login")
        this = AuthSchema().load(data)
        identity = db.session.query(AuthModel).filter_by(email=this.email).first()
        if not identity:
            raise Exception("NoRecord")
        if not identity.check_password(this.password):
            raise Exception("Unauthorized")
        return self.renew(identity)

    def logout(self) -> dict:
        print(f"auth | logout")
        # TODO: expire token
        return True

    def renew(self, identity):
        print("auth | renew")
        identity = (
            identity or db.session.query(AuthModel).filter_by(key=identity.key).first()
        )
        identity.renew()
        db.session.commit()
        token = jwt.encode(
            dict(
                key=identity.key,
                role="USER",
                exp=time() + current_app.config["SECRET_TTL"],
            ),
            current_app.config["SECRET_KEY"],
            "HS256",
        )
        return token

    def _set_session(self):
        print(f"auth | set session")
        session.update(id=uuid())
        print(session)

    def _del_session(self):
        print(f"auth | del session")
        session.clear()

    def authenticate(self, *args, **kwargs):
        def decorator(function):
            @wraps(function)
            def decorated(*args, **kwargs):
                print(f"auth | authenticate")
                if current_app.config["INSECURE"]:
                    print(f"❌ Bypassing Authentication")
                    default_identity = (
                        db.session.query(AuthModel).filter_by(key=1).first()
                    )
                    return function(default_identity, *args, **kwargs)
                token = get_token_from_headers(request)
                if not token:
                    raise Exception("Unauthorized:MissingToken")
                # Check expiring time
                # Check revoked tokens
                # if time() < token.get("exp", 0):
                #     raise Exception("Unauthorized:ExpiredToken")
                key = token["key"]
                # TODO: handle this error in an unambiguous manner
                identity = db.session.query(AuthModel).filter_by(key=key).one()
                # check scope
                return function(identity, *args, **kwargs)

            return decorated

        return decorator


class UserManager:
    def create(self, key, **kwargs) -> dict:
        print(f"user | create")
        this = UserSchema().load(kwargs)
        this.key = key
        db.session.add(this)
        db.session.commit()
        return UserSchema().dump(this)

    def read(self, key) -> dict:
        print(f"user | read")
        res = db.session.query(UserModel).filter_by(key=key).first()
        return UserSchema().dump(res) if res is not None else res

    def update(self, key, **kwargs) -> dict:
        print(f"user | update")
        pass

    def delete(self, key) -> bool:
        print(f"user | delete")
        pass

    def query(self, **kwargs) -> list:
        print(f"user | query")
        pass


class NetworkManager:
    def follow(self, src_key, dst_key) -> bool:
        print(f"network | follow")
        pass

    def unfollow(self, src_key, dst_key) -> bool:
        print(f"network | unfollow")
        pass

    def followers(self, dst_key) -> dict:
        print(f"network | followers")
        pass

    def following(self, src_key) -> dict:
        print(f"network | following")
        pass

    def follows(self, src_key, dst_key) -> bool:
        print(f"network | edges")
        pass


class MessageManager:
    def send(self, src_key, dst_key, body) -> dict:
        print(f"message | send")
        pass

    def inbox(self, key) -> dict:
        print(f"message | inbox")
        pass

    def chat(self, src_key, dst_key) -> dict:
        print(f"message | chat")
        pass

    def notifications(self, src_key) -> dict:
        print(f"message | notifications")
        pass

    def acknowledge(self, notification) -> bool:
        print(f"message | acknowledge")
        pass


class CalendarManager:
    def create(self) -> dict:
        print(f"calendar | create")
        pass

    def read(self) -> dict:
        print(f"calendar | read")
        pass

    def delete(self) -> bool:
        print(f"calendar | delete")
        pass

    def query(self) -> list:
        print(f"calendar | query")
        pass


# instances
auth_manager = AuthManager()
user_manager = UserManager()
network_manager = NetworkManager()
message_manager = MessageManager()
calendar_manager = CalendarManager()

# auth
@AuthBlueprint.route("register", methods=["POST"])
def auth_register():
    response = auth_manager.register(request.get_json())
    return jsonify(response)


@AuthBlueprint.route("login", methods=["POST"])
def auth_login():
    response = auth_manager.login(request.get_json())
    return jsonify(response)


@AuthBlueprint.route("logout", methods=["POST"])
@auth_manager.authenticate()
def auth_logout(identity):
    response = auth_manager.logout(identity)
    return jsonify(response)


@AuthBlueprint.route("renew", methods=["POST"])
@auth_manager.authenticate()
def auth_renew(identity):
    response = auth_manager.renew(identity)
    return jsonify(response)


# user
@UserBlueprint.route("/<int:key>", methods=["POST"])
@auth_manager.authenticate()
def user_create(identity, key):
    rbac(identity, key)
    return jsonify(user_manager.create(key))


@UserBlueprint.route("/<int:key>", methods=["GET"])
@auth_manager.authenticate()
def user_read(identity, key):
    return jsonify(user_manager.read(key))


@UserBlueprint.route("/<int:key>", methods=["PATCH"])
@auth_manager.authenticate()
def user_update(identity, key):
    rbac(identity, key)
    return jsonify(user_manager.patch(key))


@UserBlueprint.route("/<int:key>", methods=["DELETE"])
@auth_manager.authenticate()
def user_delete(identity, key):
    rbac(identity, key)
    return jsonify(user_manager.delete(key))


@UserBlueprint.route("/query", methods=["POST"])
@auth_manager.authenticate()
def user_query(identity, key):
    return jsonify(key=key, query=request.get_json())


# network
@NetworkBlueprint.route("/follow/<int:source>/<int:target>", methods=["POST"])
@auth_manager.authenticate()
def network_follow(identity, source, target):
    rbac(identity, source)
    return jsonify(network="follow")


@NetworkBlueprint.route("/unfollow/<int:source>/<int:target>", methods=["POST"])
@auth_manager.authenticate()
def network_unfollow(identity, source, target):
    rbac(identity, source)
    return jsonify(network="unfollow")


@NetworkBlueprint.route("/followers/<int:key>", methods=["GET"])
@auth_manager.authenticate()
def network_followers(identity, key):
    return jsonify(network="followers")


@NetworkBlueprint.route("/following/<int:key>", methods=["GET"])
@auth_manager.authenticate()
def network_following(identity, key):
    return jsonify(network="following")


@NetworkBlueprint.route("/edges/<int:source>/<int:target>", methods=["GET"])
@auth_manager.authenticate()
def network_edges(identity, source, target):
    return jsonify(network="edges")


# message
@MessageBlueprint.route("/send/<int:source>/<int:target>", methods=["POST"])
@auth_manager.authenticate()
def message_send(identity, source, target):
    rbac(identity, source)
    return jsonify(message="send")


@MessageBlueprint.route("/inbox/<int:key>", methods=["GET"])
@auth_manager.authenticate()
def message_inbox(identity, key):
    rbac(identity, key)
    return jsonify(message="inbox")


@MessageBlueprint.route("/chat/<int:source>/<int:target>", methods=["GET"])
@auth_manager.authenticate()
def message_chat(identity, source, target):
    rbac(identity, source)
    return jsonify(message="chat")


@MessageBlueprint.route("/notifications/<int:key>", methods=["GET"])
@auth_manager.authenticate()
def message_notifications(identity, key):
    rbac(identity, key)
    return jsonify(message="notifications")


@MessageBlueprint.route("/acknowledge/<int:key>/<string:value>", methods=["POST"])
@auth_manager.authenticate()
def message_acknowledge(identity, key, value):
    rbac(identity, key)
    return jsonify(message="acknowledge")


# calendar
@CalendarBlueprint.route("/<int:key>/<string:date>", methods=["POST"])
@auth_manager.authenticate()
def calendar_create(identity, key, date):
    rbac(identity, key)
    return jsonify(message="create")


@CalendarBlueprint.route("/<int:key>/<string:date>", methods=["GET"])
@auth_manager.authenticate()
def calendar_read(identity, key, date):
    rbac(identity, key)
    return jsonify(message="read")


@CalendarBlueprint.route("/<int:key>/<string:date>/<string:slot>", methods=["DELETE"])
@auth_manager.authenticate()
def calendar_delete(identity, key, date, slot):
    rbac(identity, key)
    return jsonify(message="delete")


@CalendarBlueprint.route("/query", methods=["POST"])
@auth_manager.authenticate()
def calendar_query(identity):
    return jsonify(message="query")


# core
class BaseConfig:
    ENVIRONMENT = None
    INSECURE = False
    TESTING = False
    SECRET_KEY = "P@ssw0rd"
    SECRET_TTL = 1000 * 60 * 60  # 1h
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(BaseConfig):
    ENVIRONMENT = "development"
    INSECURE = True


class TestingConfig(BaseConfig):
    ENVIRONMENT = "testing"
    TESTING = True


class StagingConfig(BaseConfig):
    ENVIRONMENT = "staging"


class ProductionConfig(BaseConfig):
    ENVIRONMENT = "production"


def app_factory(environment="development", overrides=None):
    print(f"Creating app: environment={environment} overrides={overrides}")
    app = Flask(__name__)
    configs = {
        "development": DevelopmentConfig,
        "testing": TestingConfig,
        "staging": StagingConfig,
        "production": ProductionConfig,
    }
    config = configs[environment]
    app.config.from_object(config)
    if app.config.get("INSECURE"):
        print(f"❌ Running in INSECURE mode ❌")

    db.init_app(app)
    ma.init_app(app)

    with app.app_context() as ctx:
        db.create_all()

    def handle_error(error):
        print(traceback.format_exc())
        response = jsonify(error=str(error))
        response.status_code = 400
        return response

    blueprints = {
        "auth": {
            "blueprint": AuthBlueprint,
            "enabled": True,
            "url_prefix": f"{API}/auth",
        },
        "user": {
            "blueprint": UserBlueprint,
            "enabled": True,
            "url_prefix": f"{API}/user",
        },
        "network": {
            "blueprint": NetworkBlueprint,
            "enabled": True,
            "url_prefix": f"{API}/network",
        },
        "message": {
            "blueprint": MessageBlueprint,
            "enabled": True,
            "url_prefix": f"{API}/message",
        },
        "calendar": {
            "blueprint": CalendarBlueprint,
            "enabled": True,
            "url_prefix": f"{API}/calendar",
        },
    }
    for name, blueprint in blueprints.items():
        if not blueprint.get("enabled"):
            print(f"app | disabling blueprint: {name}")
            continue
        print(f"app | registering blueprint: {name}")
        bp = blueprint["blueprint"]
        url_prefix = blueprint["url_prefix"]

        @bp.errorhandler(Exception)
        def errorhandler(error):
            return handle_error(error)

        app.register_blueprint(bp, url_prefix=url_prefix)

    @app.before_request
    def before_request_func():
        auth_manager._set_session()

    @app.after_request
    def after_request_func(response):
        auth_manager._del_session()
        return response

    return app


def mock():
    print(f"mock | loading data")
    auth_manager.register(
        {"email": "hello@world.com", "username": "admin", "password": "password"}
    )
    pass


if __name__ == "__main__":
    app = app_factory()
    with app.app_context() as ctx:
        mock()
    app.run(host="0.0.0.0", port=4000, debug=True, use_reloader=True)
