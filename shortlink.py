#!/usr/bin/env python3
""" Main script to start server
"""

import argparse
import http.server as http
from service import handler_factory


def main():
    """ Initializes the HTTP server with our URL shortening handler
    """

    parser = argparse.ArgumentParser(
            prog="shortlink.py",
            description="URL shortening HTTP service")

    parser.add_argument('--address', type=str, default="0.0.0.0",
                        action='store', help="IP address to bind to")
    parser.add_argument('--port', type=int, default=8000,
                        help="IP port to listen at")
    parser.add_argument('--baseurl', type=str, default="http://short.est",
                        help="Base URL to build the shortened version")
    args = parser.parse_args()

    print(f"Listening on address: {args.address}:{args.port}")
    server_address = (args.address, args.port)

    handler = handler_factory.get_handler(args.baseurl)

    httpd = http.HTTPServer(server_address, handler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print(" was hit. Goodbye...")


if __name__ == "__main__":
    main()
