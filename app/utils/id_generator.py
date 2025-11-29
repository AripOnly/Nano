# app/tools/utils/id_generator.py

import uuid
import base64


def generate_id(prefix: str = None) -> str:
    """
    Generate unique ID dengan base64 encoding.

    Args:
        prefix: Optional prefix (e.g., "msg", "call", "doc")

    Returns:
        Unique ID string: "msg_abc123" atau "abc123"
    """
    chat_uuid = uuid.uuid4()
    encoded_id = base64.urlsafe_b64encode(chat_uuid.bytes).rstrip(b"=").decode("ascii")

    if prefix:
        return f"{prefix}_{encoded_id}"
    else:
        return encoded_id


def generate_short_id(length: int = 8) -> str:
    """
    Generate short ID untuk use case yang butuh ID pendek.

    Args:
        length: Panjang ID (default: 8 karakter)

    Returns:
        Short ID string: "abc123de"
    """
    full_id = generate_id()
    return full_id[:length]
