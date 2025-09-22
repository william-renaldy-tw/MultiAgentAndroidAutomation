from google import genai
from app.config import settings

client = genai.Client(api_key=settings.GOOGLE_API_KEY_TOKENIZER)

DEFAULT_MODEL = settings.DEFAULT_MODEL

def count_tokens(text: str, model: str = DEFAULT_MODEL) -> int:
    """
    Count tokens used by a string for a given model.

    Args:
        text: Input text
        model: Gemini model to use

    Returns:
        Number of tokens (int)
    """
    try:
        response = client.models.count_tokens(
            model=model,
            contents=text
        )
        return response.total_tokens
    except Exception as e:
        print("Token count failed:", e)
        return 0


def trim_text_to_tokens(text: str, max_tokens: int, model: str = DEFAULT_MODEL) -> str:
    """
    Trim text safely so that it fits within token limits.

    Args:
        text: Full text to trim
        max_tokens: Token threshold
        model: Gemini model

    Returns:
        Trimmed text
    """
    words = text.split()
    step = 100

    while count_tokens(" ".join(words), model) > max_tokens:
        words = words[:-step]
        if len(words) <= step:
            break
        if step > 10:
            step = step // 2 

    return " ".join(words)


def estimate_total_tokens(history: list[dict], model: str = DEFAULT_MODEL) -> int:
    """
    Estimate total token usage across a history list.

    Args:
        history: List of messages (dicts with sender/type/content)
        model: Gemini model

    Returns:
        Total token count
    """
    total = 0
    for msg in history:
        try:
            formatted = f"[{msg['sender']}] ({msg['type']}): {msg['content']}"
            total += count_tokens(formatted, model)
        except Exception as e:
            print(f"Skipping token count for message due to error: {e}")
            continue

    return total