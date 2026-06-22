import os
import re

import groq


def call_llm(prompt: str) -> str:
    """
    Send prompt to Groq and return the text response with code fences stripped.
    Raises RuntimeError on missing API key or API failure.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY environment variable is not set")

    try:
        client = groq.Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.choices[0].message.content
    except groq.GroqError as e:
        raise RuntimeError(f"LLM API call failed: {e}") from e

    # Strip outer markdown code fences (```python ... ``` or ``` ... ```)
    text = re.sub(r"^```(?:\w+)?\n(.*)\n```$", r"\1", text.strip(), flags=re.DOTALL)
    return text.strip()
