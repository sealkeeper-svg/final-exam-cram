import ssl
import time

import certifi
import httpx
from openai import OpenAI


def _make_client(api_key, timeout_sec=60.0):
    ctx = ssl.create_default_context(cafile=certifi.where())
    return OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com",
        timeout=httpx.Timeout(timeout_sec, connect=5.0),
        http_client=httpx.Client(verify=ctx),
    )


def deepseek_verify(api_key):
    try:
        client = _make_client(api_key, timeout_sec=10.0)
        client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=5,
        )
        return True, ""
    except Exception as e:
        return False, str(e)


def deepseek_chat(messages, api_key, model="deepseek-chat"):
    client = _make_client(api_key, timeout_sec=60.0)
    last_exc = None
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
            )
            return response.choices[0].message.content
        except Exception as e:
            last_exc = e
            if attempt < 2:
                time.sleep(2**attempt)
    raise RuntimeError(f"DeepSeek API call failed after 3 retries: {last_exc}")
