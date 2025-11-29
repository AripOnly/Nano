# app/utils/cleaner.py

from openai.types.responses import ResponseOutputText


def clean_openai_output(items: list):
    """
    Bersihkan output OpenAI response ke format sederhana.

    Args:
        items: List dari response.output (OpenAI)

    Returns:
        List[dict]: hasil bersih dalam format message sederhana
    """
    clean = []
    for item in items:
        # Jika model memanggil function
        if getattr(item, "type", None) == "function_call":
            clean.append(
                {
                    "call_id": item.call_id,
                    "type": item.type,
                    "name": item.name,
                    "arguments": item.arguments,
                }
            )

        # Jika model mengirim pesan biasa
        elif item.type == "message":
            text_chunks = [
                c.text for c in item.content if isinstance(c, ResponseOutputText)
            ]
            clean.append(
                {
                    "role": "assistant",
                    "content": "\n".join(text_chunks),
                }
            )

    return clean
