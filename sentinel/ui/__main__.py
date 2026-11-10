"""python -m sentinel.ui [--listen ADDR] [--port N] [--config FILE]"""
import argparse
import os
import sys

from .server import serve


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m sentinel.ui", description="appsec-sentinel web UI")
    ap.add_argument("--listen", default=os.environ.get("SENTINEL_UI_LISTEN", "127.0.0.1"),
                    help="address to bind (default 127.0.0.1; use 0.0.0.0 inside a container)")
    ap.add_argument("--port", type=int, default=int(os.environ.get("SENTINEL_UI_PORT", "8090")))
    ap.add_argument("--config", help="config file to preselect, e.g. config/target.demo.yaml")
    args = ap.parse_args(argv)
    return serve(args.listen, args.port, args.config)


if __name__ == "__main__":
    sys.exit(main())
