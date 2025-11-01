import sys, argparse

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser(prog="inscenium", add_help=True, description="Inscenium CLI")
    sub = parser.add_subparsers(dest="cmd")

    p_hello = sub.add_parser("hello", help="Print a greeting")
    p_hello.add_argument("--name", default="world")

    sub.add_parser("versions", help="Print key library versions")

    if not argv:
        parser.print_help()
        return 0

    args = parser.parse_args(argv)

    if args.cmd == "hello":
        print(f"Hello, {args.name}!")
        return 0

    if args.cmd == "versions":
        try:
            import sys as _sys
            import torch as _torch
            import torchvision as _tv
            import PIL as _pil
            import pydantic as _pyd
            import numpy as _np
        except Exception as e:
            print(f"Import error: {e}", file=sys.stderr)
            return 1
        print(f"Python: {_sys.version.split()[0]}")
        print(f"torch: {_torch.__version__}")
        print(f"torchvision: {_tv.__version__}")
        print(f"Pillow: {_pil.__version__}")
        print(f"pydantic: {_pyd.__version__}")
        print(f"numpy: {_np.__version__}")
        return 0

    parser.print_help()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())