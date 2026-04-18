"""Entry point for bilinovel CLI."""

import sys

from bilinovel_cli.cli.commands import run


def main():
    sys.exit(run())


if __name__ == "__main__":
    main()
