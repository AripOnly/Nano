# app/utils/token_count.py

import tiktoken

ENCODING_FALLBACK = "o200k_base"


def safe_encoding_for_model(model_name: str):
    """
    Gunakan encoding_for_model() bawaan tiktoken.
    Jika model belum didukung → fallback.
    """
    try:
        return tiktoken.encoding_for_model(model_name)
    except Exception:
        return tiktoken.get_encoding(ENCODING_FALLBACK)


def token_count(text: str, model_name: str = None, encoding_name: str = None) -> int:
    if not text:
        return 0

    # Prioritas: model_name
    if model_name:
        enc = safe_encoding_for_model(model_name)
        return len(enc.encode(text))

    # Jika pakai nama encoding langsung
    if encoding_name:
        try:
            enc = tiktoken.get_encoding(encoding_name)
        except Exception:
            enc = tiktoken.get_encoding(ENCODING_FALLBACK)
        return len(enc.encode(text))

    # Default fallback
    enc = tiktoken.get_encoding(ENCODING_FALLBACK)
    return len(enc.encode(text))
