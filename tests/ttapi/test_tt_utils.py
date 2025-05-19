import re

from TTRestAPI.tt_utils import (
    create_request_id,
    generate_guid,
    is_valid_guid,
    sanitize_request_id_part,
)


def test_generate_guid_is_valid() -> None:
    guid = generate_guid()
    assert is_valid_guid(guid)


def test_create_request_id_format() -> None:
    req_id = create_request_id("My App", "Acme Co")
    prefix, guid = req_id.split("--")
    assert prefix == "My_App-Acme_Co"
    assert is_valid_guid(guid)


def test_sanitize_request_id_part() -> None:
    text = "My @App/Name"
    sanitized = sanitize_request_id_part(text)
    assert sanitized == "My_AppName"

