from __future__ import annotations

import argparse
import json
import os

from shmlrp.config import load_config
from shmlrp.logging_config import setup_logging
from shmlrp.orchestration.pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="shmlrp",
        description="Self-Healing ML Reliability Platform",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run the pipeline once")
    run_parser.add_argument("--drift-prob", type=float, default=None)
    run_parser.add_argument("--sample-size", type=int, default=None)
    run_parser.add_argument("--seed", type=int, default=None)

    api_parser = subparsers.add_parser("api", help="Start the API server")
    api_parser.add_argument("--host", type=str, default=None)
    api_parser.add_argument("--port", type=int, default=None)
    api_parser.add_argument("--reload", action="store_true")

    args = parser.parse_args()
    config = load_config()
    setup_logging(config.log_level)

    if args.command == "run":
        report = run_pipeline(
            config,
            drift_probability=args.drift_prob,
            sample_size=args.sample_size,
            seed=args.seed,
        )
        print(json.dumps(report, indent=2))
        return

    import uvicorn

    host = args.host or os.getenv("HOST") or config.api_host
    env_port = os.getenv("PORT")
    port = args.port or (int(env_port) if env_port and env_port.isdigit() else config.api_port)
    browser_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
    print(f"API ready: http://{browser_host}:{port}")
    print(f"UI: http://{browser_host}:{port}/ui")
    print(f"Docs: http://{browser_host}:{port}/docs")
    uvicorn.run("shmlrp.api.app:app", host=host, port=port, reload=args.reload)


if __name__ == "__main__":
    main()
