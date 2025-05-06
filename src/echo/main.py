import argparse
import random
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
        Route("/health", handler, methods=["GET", "HEAD"]),
    ])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", default="Hello, World!")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)

    parser.add_argument("--error-rate", type=float, default=DEFAULT_ERROR_RATE)
    parser.add_argument("--error-types", nargs="+", type=int, default=DEFAULT_ERROR_TYPES)

    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY)
    parser.add_argument("--jitter", type=float, default=DEFAULT_JITTER)
    parser.add_argument("--latency-scale", type=float, default=DEFAULT_LATENCY_SCALE)

    parser.add_argument("--response-bytes", type=int, default=DEFAULT_RESPONSE_BYTES)
    parser.add_argument("--response-jitter", type=int, default=DEFAULT_RESPONSE_JITTER)

    args = parser.parse_args()

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

    _ = Instrumentator().instrument(app).expose(app)
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
