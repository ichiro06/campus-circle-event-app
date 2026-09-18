import argparse
import json
from pathlib import Path

from fastapi import FastAPI

from api.v1 import router as api_v1_router
from main import app as runtime_app


def build_contract_schema() -> dict[str, object]:
    contract_app = FastAPI(
        title=runtime_app.title,
        version=runtime_app.version,
    )
    contract_app.include_router(api_v1_router)
    return contract_app.openapi()


def render_openapi_schema() -> str:
    return (
        json.dumps(
            build_contract_schema(),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate the deterministic OpenAPI schema.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--output", type=Path, help="Write the schema to this path.")
    mode.add_argument("--check", type=Path, help="Fail if this file differs from the schema.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rendered = render_openapi_schema()

    if args.check is not None:
        if not args.check.exists() or args.check.read_text(encoding="utf-8") != rendered:
            print(f"OpenAPI snapshot is out of date: {args.check}")
            return 1
        print(f"OpenAPI snapshot is current: {args.check}")
        return 0

    if args.output is not None:
        args.output.write_text(rendered, encoding="utf-8")
        print(f"Wrote OpenAPI schema: {args.output}")
        return 0

    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
