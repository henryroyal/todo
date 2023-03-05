import pytest
from flask import Response


def test_get_index(client):
    r: Response = client.get("/")
    assert r.status_code == 200
