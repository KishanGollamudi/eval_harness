"""Serve the repository root so the static storefront can fetch its local data."""

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import argparse


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the DevGear Studio storefront.")
    parser.add_argument("--host", default="localhost", help="Interface to bind (default: localhost)")
    parser.add_argument("--port", type=int, default=8501, help="HTTP port (default: 8501)")
    args = parser.parse_args()

    handler = partial(SimpleHTTPRequestHandler, directory=str(PROJECT_ROOT))
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"DevGear Studio is available at http://{args.host}:{args.port}/frontend/index.html")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping DevGear Studio server.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
