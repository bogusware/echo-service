from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route


async def echo(request: Request) -> Response:
    body = await request.body()
    return  Response(content=body, status_code=200)

async def health(_: Request) -> Response:
    return Response(content="Ok", status_code=200)

app = Starlette(debug=True, routes=[
    Route('/', echo, methods=["POST"]),
    Route('/health', health, methods=["HEAD", "GET"])
])

