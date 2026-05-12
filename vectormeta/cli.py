"""Command line interface for vectormeta."""

from __future__ import annotations

import typer

app = typer.Typer(help="Detect and fix oversized vector database metadata.")


def main() -> None:
    """Run the CLI application."""
    app()


if __name__ == "__main__":
    main()
