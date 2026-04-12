import asyncio
import json
import random
import time

import requests
from fastapi import Body, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from merl import ask, init

session = requests.Session()

data = init(session)
etag = data.get("etag", None)

if __name__ == "__main__":
    while True:
        question = input(": ")
        response, etag, usage = ask(session, data, etag, question)
        print(response)
else:
    app = FastAPI()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=[
            "POST",
            "GET",
            "OPTIONS",
        ],
        allow_headers=["*"],
    )

    @app.post("/v1/chat/completions", response_class=JSONResponse)
    async def completions(request: Request, body=Body(...)):
        global etag, session, data
        try:
            question = body["messages"][-1]["content"]
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not find messages array",
            )

        response, etag, usage = ask(session, data, etag, question)
        if response is None:
            data = init(session)
            etag = data.get("etag", None)
            response, etag, usage = ask(session, data, etag, question)
        if response is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Session re-initialization failed. Please try again later.",
            )
        elif response == 413:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail="Request body too large",
            )

        if body.get("stream", False):

            async def generator(text):
                arr = text.split(" ")
                i = 0
                yield (
                    'data: {"id":"chatcmpl-'
                    + request.headers.get("Cf-Ray", "")
                    + '","object":"chat.completion.chunk","created":'
                    + str(int(time.time()))
                    + ',"model":"merl", "choices":[{"index":0,"delta":{"role":"assistant","content":""},"logprobs":null,"finish_reason":null}]}\n\n'
                )
                while True:
                    if await request.is_disconnected() or i == len(arr):
                        stoppacket = (
                            'data: {"id":"chatcmpl-'
                            + request.headers.get("Cf-Ray", "")
                            + '","object":"chat.completion.chunk","created":'
                            + str(int(time.time()))
                            + ',"model":"merl", "choices":[{"index":0,"delta":{},"logprobs":null,"finish_reason":"stop"}]}\n\n'
                        )
                        yield stoppacket
                        break

                    token = (
                        arr[i]
                        .replace("\\", "\\\\")
                        .replace('"', '\\"')
                        .replace("\n", "\\n")
                        .replace("\r", "\\r")
                        .replace("<br></br>", "\\n")
                    )
                    packet = (
                        'data: {"id":"chatcmpl-'
                        + request.headers.get("Cf-Ray", "")
                        + '","object":"chat.completion.chunk","created":'
                        + str(int(time.time()))
                        + ',"model":"merl", "choices":[{"index":0,"delta":{"content":"'
                        + token
                        + " "
                        + '"},"logprobs":null,"finish_reason":null}]}\n\n'
                    )
                    yield packet
                    i += 1

                    await asyncio.sleep(random.random() / 25)

            return StreamingResponse(
                generator(response), media_type="text/event-stream"
            )

        else:
            return {
                "id": f"chatcmpl-{request.headers.get('Cf-Ray', '')}",
                "created": int(time.time()),
                "model": "merl",
                "object": "chat.completion",
                "choices": [
                    {
                        "text": response,
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": usage.get("promptTokens", ""),
                    "completion_tokens": usage.get("completionTokens", ""),
                    "total_tokens": usage.get("totalTokens", ""),
                },
            }

    @app.get("/v1/models")
    def models():
        return {
            "object": "list",
            "data": [
                {
                    "id": "merl",
                    "object": "model",
                    "created": 67,
                    "owned_by": "microsoft",
                }
            ],
        }
