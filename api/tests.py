#!/usr/bin/env python3 -m pytest tests.py -k test_ -v
#
# SHARED
#
import pytest
from app import app_factory


@pytest.fixture()
def app():
    app = app_factory(environment="testing")
    # setup
    yield app
    # cleanup


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()


#
# TESTS
#
def test_api_index(client):
    response = client.get("/api/v1/")
    assert response.status_code == 200
    assert isinstance(response.json, dict)


def test_api_identity_register():
    """
    parse data
    verify user does not exist
    hash pw
    call login method
    """
    assert False


# def test_identity_login():
#     """
#     verify user does exist
#     parse creds
#     check creds
#     set last login time
#     return token
#     """
#     assert False


# def test_identity_authenticate():
#     """
#     parse token
#     confirm token
#     confirm session
#     """
#     assert False
