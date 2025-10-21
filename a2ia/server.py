"""Main server entry point for A2IA.

Supports both MCP (stdio) and HTTP modes.
"""

import argparse


def main():
    """Main entry point with mode selection."""
    parser = argparse.ArgumentParser(description="A2IA Server")
    parser.add_argument(
        "--mode",
        choices=["mcp", "http"],
        default="mcp",
        help="Server mode: mcp (stdio) or http (REST API)",
    )
    parser.add_argument(
        "--host", default="0.0.0.0", help="HTTP server host (http mode only)"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="HTTP server port (http mode only)"
    )
    parser.add_argument(
        "--password", default=None, help="Override API password (http mode only)"
    )

    args = parser.parse_args()

    if args.mode == "mcp":
        # Run MCP server via stdio
        from .mcp_server import run

        run()
    elif args.mode == "http":
        # Set password if provided
        if args.password:
            import os

            os.environ["A2IA_PASSWORD"] = args.password

        # Run RESTful HTTP server
        from .rest_server import run_rest_server

        print(f"Starting A2IA REST server on {args.host}:{args.port}")
        print(f"OpenAPI docs: http://{args.host}:{args.port}/docs")
        print("API Style: RESTful (GET/PUT/PATCH/DELETE)")
        run_rest_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
