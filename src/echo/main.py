import argparse
import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route


def make_app(default_text: str) -> Starlette:
    default_response = default_text.encode()

    async def post_echo(request: Request) -> Response:
        body = await request.body()
        return Response(content=body, status_code=200)

    async def get_echo(_: Request) -> Response:
        return Response(content=default_response, status_code=200)

    async def health(_: Request) -> Response:
        return Response(content="Ok", status_code=200)

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
    args = parser.parse_args()

    app = make_app(args.text)
    uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()
