"""
[gmail with flask-mail](https://stackoverflow.com/a/37059417/12641958)

"""
import time
import textwrap

from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message

whoseaway = "whoseaway@gmail.com"

config = dict(
    SQLALCHEMY_DATABASE_URI="postgresql://postgres:postgres@localhost:5432",
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_PORT=465,
    MAIL_USE_SSL=True,
    MAIL_USERNAME=whoseaway,
    MAIL_PASSWORD="gvt^ojGVJ&zvmmsNuuk$JfL@h8T&mJA6N",
    MAIL_DEFAULT_SENDER=whoseaway,
    # MAIL_USE_TLS="default False",
    # MAIL_DEBUG="default app.debug",
    # MAIL_MAX_EMAILS="default None",
    # MAIL_SUPPRESS_SEND="default app.testing",
    # MAIL_ASCII_ATTACHMENTS="default False",
)

app = Flask(__name__)
app.config.update(config)
db = SQLAlchemy(app)
mail = Mail(app)


def timestamp():
    return int(time.time())


class Token:
    def __init__(self, sub=None, exp=None, ttl=60 * 60):
        self.sub = sub
        self.ttl = 60 * 60
        self.exp = None

    @property
    def valid(self):
        if not self.sub or not self.exp:
            return False
        return timestamp() < self.exp

    @classmethod
    def load(cls, **kwargs):
        pass

    def dump(self):
        pass


class IdentityModel:
    pass


class IdentitySchema:
    pass


class IdentityManager:
    def exists(self, email: str, username: str) -> bool:
        identity = self.lookup(email, username)
        return bool(identity)

    def lookup(self, pk: int, email: str, username: str) -> IdentityModel:
        filters = {
            key: value
            for key, value in dict(pk=pk, email=email, username=username)
            if value
        }
        result = db.sesssion.query(IdentityModel).filter_by(**filters)
        return result

    def register(self, email: str, username: str, password: str) -> dict:
        if self.exists(email, username):
            return {}, 409
        identity = IdentitySchema().load(
            dict(email=email, username=username, password=password)
        )
        identity.hash_password(identity.password)
        db.session.add(identity)
        db.session.commit()
        identity = IdentitySchema().dump(identity)
        # user_manager.create(identity)
        return identity

    def login(self, creds) -> Token:
        provided = IdentitySchema().load(creds)
        identity = im.lookup(provided.email)
        if not identity:
            return {}, 401
        elif not identity.verify_password(provided.password):
            return {}, 401
        return im.grant(identity)

    def grant(self, identity) -> Token:
        im.record_login(identity)
        token = jwt.serialize(identity, exp)
        return token

    def email_verify_account(self, identity) -> bool:
        # generate verification link
        # send email async
        pass

    def email_reset_password(self, identity) -> bool:
        # generate reset token link
        # send email async
        pass

    def handle_verify_account(self, token, **kwargs):
        pass

    def handle_reset_password(self, token, **kwargs):
        pass

    # unsafe: these assume preflight checks
    def _update_verified(self, pk, email) -> bool:
        identity = im.lookup(pk)
        identity.email = email
        db.session.commit()
        return True

    def _update_username(self, pk, username) -> bool:
        identity = im.lookup(pk)
        identity.username = username
        db.session.commit()
        return True

    def _update_email(self, pk, email) -> bool:
        identity = im.lookup(pk)
        identity.email = email
        db.session.commit()
        return True

    def _update_password(self, pk, password) -> bool:
        identity = im.lookup(pk)
        identity.hash_password(password)
        db.session.commit()
        return True


@app.route("/")
def index():
    """
    recipient(s)
    subject
    html
    # explore no-reply
    """
    msg = Message("Hello", recipients=[whoseaway])
    msg.html = textwrap.dedent(
        """
    <div>
        <h1>Hello There</h1>
        <a href="/">Click this link</a>
    </div>
    """
    )
    print(f"Sending: {msg}")
    mail.send(msg)
    return jsonify(success=True)


@app.route("/identity/register", methods=["POST"])
def register():
    pass


@app.route("/identity/login", methods=["POST"])
def login():
    pass


@app.route("/user/read/<key>", methods=["GET"])
def user_read():
    pass


@app.route("/user/edit/<key>", methods=["POST"])
def user_edit():
    pass


@app.route("/user/query", methods=["GET", "POST"])
def user_query():
    pass


@app.route("/calendar/read/<key>/<date>", methods=["GET"])
def calendar_read():
    pass


@app.route("/calendar/edit/key/<date>", methods=["POST"])
def calendar_edit():
    pass


@app.route("/calendar/query", methods=["GET", "POST"])
def calendar_query():
    pass


@app.route("/network/follow/<src>/<dst>", methods=["POST"])
def network_follow():
    pass


@app.route("/network/unfollow/<src>/<dst>", methods=["POST"])
def network_unfollow():
    pass


@app.route("/network/followers/<src>/<dst>", methods=["POST"])
def network_followers():
    # if not nm.is_follower():
    pass


@app.route("/network/following/<src>/<dst>", methods=["POST"])
def network_following():
    # if not nm.is_following():
    pass


@app.route("/network/notifications/<key>", methods=["GET"])
def network_notifications():
    pass


@app.route("/network/notifications/ack/<key>", methods=["POST"])
def network_acknowledge():
    pass


@app.route("/message/inbox/<key>", methods=["GET"])
def message_inbox():
    pass


@app.route("/message/chat/<src>/<dst>", methods=["GET"])
def message_chat():
    pass


@app.route("/message/chat/<src>/<dst>", methods=["POST"])
def message_send():
    pass


@app.route("/message/notifications/<key>", methods=["GET"])
def message_notifications():
    pass


@app.route("/message/notifications/ack/<key>", methods=["POST"])
def message_acknowledge():
    pass


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4000, debug=True)
