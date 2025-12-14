from __future__ import annotations
import argparse
import sys

from .receiver import ReceiverServer
from .sender import Sender
from .config import DEFAULT_HOST, DEFAULT_PORT

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="imgtx", description="Image transfer system (TCP) with integrity checks.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_recv = sub.add_parser("recv", help="Run receiver server (serve once).")
    p_recv.add_argument("--host", default=DEFAULT_HOST)
    p_recv.add_argument("--port", type=int, default=DEFAULT_PORT)
    p_recv.add_argument("--out", default="outputs/received")

    p_send = sub.add_parser("send", help="Send image to receiver.")
    p_send.add_argument("--host", default=DEFAULT_HOST)
    p_send.add_argument("--port", type=int, default=DEFAULT_PORT)
    p_send.add_argument("--file", required=True)

    args = parser.parse_args(argv)

    if args.cmd == "recv":
        srv = ReceiverServer(host=args.host, port=args.port, output_dir=args.out)
        result = srv.serve_once()
        print("RECEIVED OK:")
        print(result)
        return 0

    if args.cmd == "send":
        s = Sender(host=args.host, port=args.port)
        header = s.send_image(args.file)
        print("SENT OK:")
        print(header)
        return 0

    return 1

if __name__ == "__main__":
    raise SystemExit(main())
