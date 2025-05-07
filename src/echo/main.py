import argparse
import asyncio
import random
import sys
import time
import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route
from prometheus_fastapi_instrumentator import Instrumentator

# Default values
DEFAULT_ERROR_RATE = 0.0
DEFAULT_DELAY = 0.0
DEFAULT_JITTER = 0.0
DEFAULT_LATENCY_SCALE = 1.0
DEFAULT_ERROR_TYPES = [500]
DEFAULT_RESPONSE_BYTES = 0
DEFAULT_RESPONSE_JITTER = 0


# Bogus change

def make_app(
    default_text: str,
    error_rate: float = DEFAULT_ERROR_RATE,
    delay: float = DEFAULT_DELAY,
    jitter: float = DEFAULT_JITTER,
    latency_scale: float = DEFAULT_LATENCY_SCALE,
    error_types: list[int] = DEFAULT_ERROR_TYPES,
    response_bytes: int = DEFAULT_RESPONSE_BYTES,
    response_jitter: int = DEFAULT_RESPONSE_JITTER,
) -> Starlette:

    def roll_error() -> bool:
        return random.random() < error_rate

    def compute_delay() -> float:
        jitter_val = random.uniform(-jitter, jitter) if jitter > 0 else 0.0
        raw_delay = delay + jitter_val
        return max(0.0, raw_delay * latency_scale)

    def make_response(content: bytes, status: int = 200) -> Response:
        jitter_bytes = random.randint(-response_jitter, response_jitter) if response_jitter > 0 else 0
        final_size = max(0, response_bytes + jitter_bytes)
        if final_size > 0:
            content += b" " * final_size
        return Response(content=content, status_code=status)

    async def handler(request: Request) -> Response:
        content = (
            await request.body()
            if request.method == "POST"
            else default_text.encode()
        )

        status = random.choice(error_types) if roll_error() else 200
        time.sleep(compute_delay())

        return make_response(content, status)

    return Starlette(debug=True, routes=[
        Route("/", handler, methods=["GET", "POST"]),
    ])

def make_diagnostics_app(instrumentator: Instrumentator) -> Starlette:
    async def healthcheck(_: Request) -> Response:
        return Response("ok")

    app = Starlette(routes=[
        Route("/health", healthcheck, methods=["GET", "HEAD"]),
    ])

    _ = instrumentator.expose(app, include_in_schema=False, should_gzip=True)
    return app


class Namespace(argparse.Namespace):
    text: str              # pyright:  ignore[reportUninitializedInstanceVariable]
    host: str              # pyright:  ignore[reportUninitializedInstanceVariable]
    port: int              # pyright:  ignore[reportUninitializedInstanceVariable]
    diagnostics_host: str              # pyright:  ignore[reportUninitializedInstanceVariable]
    diagnostics_port: int              # pyright:  ignore[reportUninitializedInstanceVariable]
    error_rate: int        # pyright:  ignore[reportUninitializedInstanceVariable]
    error_types: list[int] # pyright:  ignore[reportUninitializedInstanceVariable]
    delay: float           # pyright:  ignore[reportUninitializedInstanceVariable]
    jitter: float          # pyright:  ignore[reportUninitializedInstanceVariable]
    latency_scale: float   # pyright:  ignore[reportUninitializedInstanceVariable]
    response_bytes: int    # pyright:  ignore[reportUninitializedInstanceVariable]
    response_jitter: int   # pyright:  ignore[reportUninitializedInstanceVariable]



async def main():
    parser = argparse.ArgumentParser()

    _ = parser.add_argument("--text", default="Hello, World!")
    _ = parser.add_argument("--host", default="127.0.0.1")
    _ = parser.add_argument("--port", type=int, default=8000)

    _ = parser.add_argument("--diagnostics-host", default="127.0.0.1")
    _ = parser.add_argument("--diagnostics-port", type=int, default=8001)

    _ = parser.add_argument("--error-rate", type=float, default=DEFAULT_ERROR_RATE)
    _ = parser.add_argument("--error-types", nargs="+", type=int, default=DEFAULT_ERROR_TYPES)

    _ = parser.add_argument("--delay", type=float, default=DEFAULT_DELAY)
    _ = parser.add_argument("--jitter", type=float, default=DEFAULT_JITTER)
    _ = parser.add_argument("--latency-scale", type=float, default=DEFAULT_LATENCY_SCALE)

    _ = parser.add_argument("--response-bytes", type=int, default=DEFAULT_RESPONSE_BYTES)
    _ = parser.add_argument("--response-jitter", type=int, default=DEFAULT_RESPONSE_JITTER)

    args = parser.parse_args(namespace=Namespace())

    app = make_app(
        default_text=args.text,
        error_rate=args.error_rate,
        delay=args.delay,
        jitter=args.jitter,
        latency_scale=args.latency_scale,
        error_types=args.error_types,
        response_bytes=args.response_bytes,
        response_jitter=args.response_jitter,
    )

    insrumentator = Instrumentator().instrument(app)
    diagnostics_app = make_diagnostics_app(insrumentator)

    async def run_server(host: str, port: int, app_ref: Starlette):
        server_config = uvicorn.Config(app_ref, port=port, host=host)
        server = uvicorn.Server(server_config)
        await server.serve()

    _ = await asyncio.gather(
        run_server(args.host, args.port, app),
        run_server(args.diagnostics_host, args.diagnostics_port, diagnostics_app)
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
    except:
        raise
