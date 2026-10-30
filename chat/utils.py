import os
import logging

try:
    import openai
except Exception:
    openai = None

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
DEFAULT_MODEL = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')


def call_openai_chat(prompt: str, model: str = None, max_tokens: int = 500, temperature: float = 0.7):
    """Call OpenAI ChatCompletion (gpt-3.5/gpt-4 family) and return assistant text.

    Returns string on success, or raises RuntimeError on failure.
    """
    if openai is None:
        raise RuntimeError('openai package is not installed')

    if not OPENAI_API_KEY:
        raise RuntimeError('OPENAI_API_KEY environment variable not set')

    openai.api_key = OPENAI_API_KEY
    model = model or DEFAULT_MODEL

    try:
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ]
        resp = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        # Extract text
        choices = resp.get('choices')
        if not choices:
            raise RuntimeError('OpenAI returned no choices')
        message = choices[0].get('message') or {}
        content = message.get('content') or choices[0].get('text')
        if content is None:
            raise RuntimeError('OpenAI response format unexpected')
        return content.strip()
    except Exception as e:
        logger.exception('OpenAI API call failed')
        raise RuntimeError(f'OpenAI API call failed: {e}')
