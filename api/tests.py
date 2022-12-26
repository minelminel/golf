#!/usr/bin/env python3 -m pytest tests.py -k test_ -v
"""
TODO:
- implement fakeredis test fixture: https://github.com/jamesls/fakeredis
"""
#
# SHARED
#
import os
from pprint import pprint
from pdb import set_trace as debug

import pytest
from flask import testing
from werkzeug.datastructures import Headers

from app import app_factory, mock_factory, CREDS1, CREDS2


class TestClient(testing.FlaskClient):
    def open(self, *args, **kwargs):
        token_headers = Headers({"token": self.token})
        headers = kwargs.pop("headers", Headers())
        headers.extend(token_headers)
        kwargs["headers"] = headers
        return super().open(*args, **kwargs)


@pytest.fixture()
def empty_app():
    app = app_factory(
        environment="testing", **dict(SQLALCHEMY_DATABASE_URI="sqlite://")
    )
    # setup
    yield app
    # cleanup


@pytest.fixture()
def empty_client(empty_app):
    return empty_app.test_client()


@pytest.fixture()
def empty_runner(empty_app):
    return empty_app.test_cli_runner()


@pytest.fixture()
def app():
    app = app_factory(
        environment="testing", **dict(SQLALCHEMY_DATABASE_URI="sqlite://")
    )
    # setup
    auth = mock_factory(app)
    token = auth["token"]
    yield app, token
    # cleanup


@pytest.fixture()
def client(app):
    app, token = app
    klass = TestClient
    klass.token = token
    app.test_client_class = klass
    return app.test_client()


@pytest.fixture()
def runner(app):
    return runner.test_cli_runner()


#
# TESTS
#
def _test_api_index(empty_client):
    response = empty_client.get("/api/v1/")
    assert response.status_code == 200
    assert isinstance(response.json, dict)


def _test_api_auth(empty_client):
    """ """
    creds = {
        "email": "hello@world.com",
        "username": "myusername",
        "password": "mypassword",
    }
    # register
    response = empty_client.post("/api/v1/auth/register", json=creds)
    assert response.status_code == 200
    # login not existing
    response = empty_client.post(
        "/api/v1/auth/login", json={"username": "doesnotexist", "password": None}
    )
    assert response.status_code == 400
    # login bad creds
    response = empty_client.post(
        "/api/v1/auth/login", json=dict(username="myusername", password="wrongpassword")
    )
    assert response.status_code == 400
    # login pass
    response = empty_client.post(
        "/api/v1/auth/login",
        json=creds,
    )
    assert response.status_code == 200
    token = response.json["data"]["token"]
    # renew
    response = empty_client.post("/api/v1/auth/renew", headers=dict(token=token))
    assert response.status_code == 200
    token = response.json["data"]["token"]
    key = response.json["data"]["key"]
    # identity
    response = empty_client.get(
        f"/api/v1/auth/identity/{key}", headers=dict(token=token)
    )
    assert response.status_code == 200
    assert isinstance(response.json["data"], dict)
    # logout
    response = empty_client.post("/api/v1/auth/logout", headers=dict(token=token))
    assert response.status_code == 200


def _test_api_user(client):
    # create: fail since an entry exists
    # response = client.post(f"/api/v1/user/{CREDS.KEY}")
    # assert response.status_code == 200

    # read
    response = client.get(f"/api/v1/user/{CREDS1.KEY}")
    assert response.status_code == 200
    assert isinstance(response.json.get("data"), dict)
    # update
    patches = {
        "name": "minel",
        "bio": "hello world",
    }
    response = client.patch(f"/api/v1/user/{CREDS1.KEY}", json=patches)
    assert response.status_code == 200
    assert isinstance(response.json.get("data"), dict)
    # check write
    response = client.get(f"/api/v1/user/{CREDS1.KEY}")
    assert response.status_code == 200
    for k, v in patches.items():
        assert response.json["data"].get(k) == v
    # update image
    # update location
    # attributes


def _test_api_network(client):
    # create if not exist
    response = client.post(f"/api/v1/network/follow/{CREDS1.KEY}/{CREDS2.KEY}")
    assert response.status_code == 200
    assert isinstance(response.json["data"], dict)
    # skip if present
    response = client.post(f"/api/v1/network/follow/{CREDS1.KEY}/{CREDS2.KEY}")
    assert response.status_code == 200
    assert response.json["data"] == None
    # get followers
    response = client.get(f"/api/v1/network/followers/{CREDS1.KEY}")
    assert response.status_code == 200
    assert response.json["data"]["content"] == []
    # get following
    response = client.get(f"/api/v1/network/following/{CREDS1.KEY}")
    assert response.status_code == 200
    content = response.json["data"]["content"]
    assert len(content) == 1
    assert content[0]["source"] == CREDS1.KEY
    assert content[0]["target"] == CREDS2.KEY
    # get edges
    response = client.get(f"/api/v1/network/edges/{CREDS1.KEY}/{CREDS2.KEY}")
    assert response.status_code == 200
    edges = response.json["data"]
    assert len(edges) == 1


def _test_api_message(client):
    message = dict(
        source=CREDS1.KEY,
        target=CREDS2.KEY,
        body="hello world!",
    )
    response = client.post(f"/api/v1/message/send", json=message)
    assert response.status_code == 200

    response = client.get(f"/api/v1/message/inbox/{CREDS1.KEY}")
    assert response.status_code == 200
    content = response.json["data"]["content"]
    assert isinstance(content, list)
    assert len(content) > 0

    response = client.get(f"/api/v1/message/chat/{CREDS1.KEY}/{CREDS2.KEY}")
    assert response.status_code == 200
    content = response.json["data"]["content"]
    assert isinstance(content, list)
    assert len(content) > 0

    response = client.get(f"/api/v1/message/notifications/{CREDS1.KEY}")
    assert response.status_code == 200
    data = response.json["data"]
    assert isinstance(data, list)
    n = len(data)
    assert n > 0
    for d in data:
        notification = d["notification"]
        response = client.post(
            f"/api/v1/message/acknowledge/{CREDS1.KEY}/{notification}"
        )
        assert response.status_code == 200
        n -= 1
    assert n == 0


def test_api_calendar(client):
    data = {
        "date": "2020-05-07",  # ISO 8601
        "slot": 1,
        "available": True,
    }
    response = client.post(f"/api/v1/calendar/{CREDS1.KEY}", json=data)
    # create an entry
    # does user have entries between range
    # iterate group by days
    # slots into arrays

    assert False
