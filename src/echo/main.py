import argparse
import random
import time
import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

def make_app(default_text: str, error_rate: float = 0.0, delay: float = 0.0) -> Starlette:
    def roll() -> bool:
        return random.random() < error_rate

    def probably(response: Response) -> Response:
        if roll():
            response.status_code = 500
            response.body = "Error!".encode("utf-8")

        if delay > 0.0:
            time.sleep(delay)

        return response

    default_response = default_text.encode()

    async def post_echo(request: Request) -> Response:
        body = await request.body()
        return probably(Response(content=body, status_code=200))

    async def get_echo(_: Request) -> Response:
        return probably(Response(content=default_response, status_code=200))

    async def health(_: Request) -> Response:
        return probably(Response(content="Ok", status_code=200))

    return Starlette(debug=True, routes=[
        Route('/', post_echo, methods=["POST"]),
        Route('/', get_echo, methods=["GET"]),
        Route('/health', health, methods=["HEAD", "GET"])
    ])



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", default="Hello, World!")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8000, type=int)
    parser.add_argument("--error-rate", type=float, default=0.0)
    parser.add_argument("--delay", type=float, default=0.0)
    args = parser.parse_args()

    app = make_app(args.text, args.error_rate, args.delay)
    uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()
