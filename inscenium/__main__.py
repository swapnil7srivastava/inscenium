# Auto-generated CLI trampoline for Inscenium
from importlib import import_module
import sys

def _try_targets():
    # Try common places where a Typer app(named `app`) might live
    for mod, attr in (
        ("inscenium.cli", "app"),
        ("inscenium.cli.video", "app"),
        ("inscenium.cli.__main__", "app"),
    ):
        try:
            m = import_module(mod)
            a = getattr(m, attr)
            return ("typer-app", a)  # Typer app callable
        except Exception:
            pass
    # Fallback: if there is a `video` function, wrap it into a tiny Typer app
    try:
        m = import_module("inscenium.cli.video")
        if hasattr(m, "video"):
            import typer  # must be installed in deps
            app = typer.Typer()
            app.command()(getattr(m, "video"))
            return ("constructed-app", app)
    except Exception:
        pass
    return (None, None)

def main():
    kind, obj = _try_targets()
    if obj is None:
        print("inscenium: CLI entrypoint not found. Expected Typer `app` or a `video` command.", file=sys.stderr)
        sys.exit(2)
    # If we got a Typer app (or constructed one), invoke it
    return obj()

if __name__ == "__main__":
    main()