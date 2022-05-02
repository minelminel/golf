import pytest

# from artifice.scraper.core.app import create_app
# from artifice.scraper.models import db as _db

from flask import json, Response
from werkzeug.utils import cached_property


class ApiTestingResponse(Response):
    @cached_property
    def json(self):
        assert self.mimetype == "application/json"
        return json.loads(self.data)


def pytest_addoption(parser):
    # Allow remote host IP for integration tests to be supplied
    # Option is only required when using `-k integration`
    parser.addoption("--testhost", action="store", default=None)


@pytest.yield_fixture(scope="session")
def app():
    app = create_app(config="testing")
    app.response_class = ApiTestingResponse
    ctx = app.app_context()
    ctx.push()

    yield app

    ctx.pop()


@pytest.yield_fixture(scope="session")
def db(app):
    _db.create_all()

    yield _db

    _db.drop_all()


@pytest.fixture(scope="session")
def client(app):
    return app.test_client()


@pytest.yield_fixture(scope="function")
def session(db):
    connection = db.engine.connect()
    transaction = connection.begin()

    options = dict(bind=connection)
    session = db.create_scoped_session(options=options)

    db.session = session

    yield session

    transaction.rollback()
    connection.close()
    session.remove()
