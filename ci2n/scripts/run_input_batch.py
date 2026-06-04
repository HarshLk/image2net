#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path


def parse_bool(value: str) -> bool:
    lowered = value.lower()
    if lowered in {"1", "true", "yes", "y"}:
        return True
    if lowered in {"0", "false", "no", "n"}:
        return False
    raise argparse.ArgumentTypeError(f"invalid boolean value: {value}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run CI2N inference for a folder of input images.")
    parser.add_argument("--input-dir", default="inputs/validation")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--verbose-dir", required=True)
    parser.add_argument("--validation", type=parse_bool, required=True)
    args = parser.parse_args()

    ci2n_root = Path(__file__).resolve().parents[1]
    input_dir = ci2n_root / args.input_dir
    output_dir = ci2n_root / args.output_dir
    verbose_dir = ci2n_root / args.verbose_dir

    if not input_dir.is_dir():
        raise RuntimeError(f"Input directory does not exist: {input_dir}")

    images = sorted(
        path for path in input_dir.iterdir()
        if path.is_file() and path.suffix.lower() in {".png", ".jpg", ".jpeg"}
    )
    if not images:
        raise RuntimeError(f"No images found in {input_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)
    verbose_dir.mkdir(parents=True, exist_ok=True)

    summary = []
    total = len(images)

    for index, image_path in enumerate(images, start=1):
        task_id = image_path.stem
        output_path = output_dir / f"{task_id}.json"
        task_verbose_dir = verbose_dir / task_id
        task_verbose_dir.mkdir(parents=True, exist_ok=True)
        log_path = task_verbose_dir / "run.log"

        cmd = [
            sys.executable,
            "run.py",
            "--path",
            str(image_path.relative_to(ci2n_root)),
            "--output",
            str(output_path.relative_to(ci2n_root)),
            "--verbose=True",
            "--verbose_path",
            str(task_verbose_dir.relative_to(ci2n_root)),
            "--validation",
            str(args.validation),
        ]

        start = time.time()
        print(f"[{index:03d}/{total:03d}] {task_id} validation={args.validation}", flush=True)
        with log_path.open("w") as log_file:
            completed = subprocess.run(
                cmd,
                cwd=ci2n_root,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                text=True,
            )

        elapsed = time.time() - start
        status = {
            "id": task_id,
            "input": str(image_path.relative_to(ci2n_root)),
            "output": str(output_path.relative_to(ci2n_root)),
            "verbose": str(task_verbose_dir.relative_to(ci2n_root)),
            "log": str(log_path.relative_to(ci2n_root)),
            "validation": args.validation,
            "returncode": completed.returncode,
            "success": completed.returncode == 0 and output_path.exists(),
            "elapsed_seconds": round(elapsed, 3),
        }
        summary.append(status)

        result = "ok" if status["success"] else f"failed rc={completed.returncode}"
        print(f"[{index:03d}/{total:03d}] {task_id} {result} in {elapsed:.1f}s", flush=True)

    summary_path = output_dir / "_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))

    successes = sum(item["success"] for item in summary)
    print(f"finished: {successes}/{total} successful outputs", flush=True)
    print(f"summary written to {summary_path.relative_to(ci2n_root)}", flush=True)
    return 0 if successes == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
