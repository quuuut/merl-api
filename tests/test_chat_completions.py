import json
import pytest
import httpx

BASE_PAYLOAD = {
    "messages": [{"role": "user", "content": "Hello!"}]
}


# normal

def test_chat_status(client):
    r = client.post("/v1/chat/completions", json=BASE_PAYLOAD)
    assert r.status_code == 200


def test_chat_response_shape(client):
    data = client.post("/v1/chat/completions", json=BASE_PAYLOAD).json()
    assert data["object"] == "chat.completion"
    assert "choices" in data
    assert len(data["choices"]) > 0


def test_chat_choice_fields(client):
    choice = client.post("/v1/chat/completions", json=BASE_PAYLOAD).json()["choices"][0]
    assert choice["index"] == 0
    assert "message" in choice
    assert choice["message"]["role"] == "assistant"
    assert isinstance(choice["message"]["content"], str)
    assert len(choice["message"]["content"]) > 0


def test_chat_usage_fields(client):
    usage = client.post("/v1/chat/completions", json=BASE_PAYLOAD).json().get("usage")
    assert usage is not None
    assert "prompt_tokens" in usage
    assert "completion_tokens" in usage
    assert "total_tokens" in usage

def test_chat_missing_messages(client):
    r = client.post("/v1/chat/completions", json={})
    assert r.status_code == 422


# streaming

STREAM_PAYLOAD = {**BASE_PAYLOAD, "stream": True}


@pytest.mark.asyncio
async def test_stream_status(async_client):
    async with httpx.AsyncClient(base_url=async_client, timeout=30) as client:
        async with client.stream("POST", "/v1/chat/completions", json=STREAM_PAYLOAD) as r:
            assert r.status_code == 200
            assert "text/event-stream" in r.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_stream_yields_chunks(async_client):
    chunks = []
    async with httpx.AsyncClient(base_url=async_client, timeout=30) as client:
        async with client.stream("POST", "/v1/chat/completions", json=STREAM_PAYLOAD) as r:
            async for line in r.aiter_lines():
                if line.startswith("data:"):
                    payload = line[len("data:"):].strip()
                    if payload == "[DONE]":
                        break
                    chunks.append(json.loads(payload))

    assert len(chunks) > 0


@pytest.mark.asyncio
async def test_stream_chunk_shape(async_client):
    async with httpx.AsyncClient(base_url=async_client, timeout=30) as client:
        async with client.stream("POST", "/v1/chat/completions", json=STREAM_PAYLOAD) as r:
            async for line in r.aiter_lines():
                if not line.startswith("data:"):
                    continue
                payload = line[len("data:"):].strip()
                if payload == "[DONE]":
                    break
                chunk = json.loads(payload)
                assert chunk["object"] == "chat.completion.chunk"
                assert "choices" in chunk
                delta = chunk["choices"][0]["delta"]
                assert "content" in delta or "role" in delta
                break


@pytest.mark.asyncio
async def test_stream_assembles_full_response(async_client):
    content = ""
    async with httpx.AsyncClient(base_url=async_client, timeout=30) as client:
        async with client.stream("POST", "/v1/chat/completions", json=STREAM_PAYLOAD) as r:
            async for line in r.aiter_lines():
                if not line.startswith("data:"):
                    continue
                payload = line[len("data:"):].strip()
                if payload == "[DONE]":
                    break
                delta = json.loads(payload)["choices"][0]["delta"]
                content += delta.get("content", "")

    assert len(content) > 0