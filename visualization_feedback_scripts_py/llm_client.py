"""Small OpenAI Responses API wrapper used by every model-backed feature."""

import os

from openai import OpenAI


MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-5.4")


def call_openai(system_prompt, user_input, api_key=None):
    """Call the configured model without persisting the caller's API key."""
    if not api_key:
        raise ValueError("An OpenAI API key is required.")
    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model=MODEL_NAME,
        instructions=system_prompt,
        input=user_input,
    )
    return response.output_text


def stream_openai(system_prompt, user_input, api_key=None):
    """Yield response text as the Responses API produces it."""
    if not api_key:
        raise ValueError("An OpenAI API key is required.")
    client = OpenAI(api_key=api_key)
    stream = client.responses.create(
        model=MODEL_NAME,
        instructions=system_prompt,
        input=user_input,
        stream=True,
    )
    for event in stream:
        if event.type == "response.output_text.delta" and event.delta:
            yield event.delta


def conversation_input(messages):
    """Convert app messages into the Responses API's role/content format."""
    return [
        {"role": item["role"], "content": item["content"]}
        for item in messages
        if item.get("role") in {"user", "assistant"}
    ]
