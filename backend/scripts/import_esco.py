from __future__ import annotations

import argparse
from pathlib import Path

from app.db.bootstrap import initialize_datastores
from app.esco_store import import_esco_csv_package, seed_esco_partial


def main() -> int:
    parser = argparse.ArgumentParser(description="Load ESCO into AUGUR local SQLite.")
    parser.add_argument(
        "path",
        nargs="?",
        help="Folder containing the official ESCO CSV package.",
    )
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Load the built-in partial official seed for pipeline validation.",
    )
    parser.add_argument(
        "--version",
        default="1.2.1",
        help="ESCO dataset version label.",
    )
    args = parser.parse_args()

    initialize_datastores()

    if args.seed:
        result = seed_esco_partial()
    elif args.path:
        result = import_esco_csv_package(Path(args.path), version=args.version)
    else:
        parser.error("Provide a package path or use --seed.")

    print("AUGUR ESCO import")
    for key, value in result.items():
        print(f"{key}: {value}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
