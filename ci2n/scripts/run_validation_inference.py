#!/usr/bin/env python3
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path


TIMESTAMP_RE = re.compile(r"\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}")


def timestamp_dirs(verbose_root: Path) -> set[Path]:
    if not verbose_root.exists():
        return set()
    return {
        path
        for path in verbose_root.iterdir()
        if path.is_dir() and TIMESTAMP_RE.fullmatch(path.name)
    }


def move_verbose_artifacts(task_verbose_dir: Path, new_dirs: set[Path]) -> list[str]:
    moved = []
    task_verbose_dir.mkdir(parents=True, exist_ok=True)

    for src_dir in sorted(new_dirs):
        moved.append(src_dir.name)
        for child in src_dir.iterdir():
            target = task_verbose_dir / child.name
            if target.exists():
                target = task_verbose_dir / f"{src_dir.name}_{child.name}"
            shutil.move(str(child), str(target))
        src_dir.rmdir()

    return moved


def main() -> int:
    ci2n_root = Path(__file__).resolve().parents[1]
    image2net_root = ci2n_root.parent

    source_images_dir = image2net_root / "ci2n_datasets" / "validation" / "images"
    inputs_dir = ci2n_root / "inputs" / "validation"
    outputs_dir = ci2n_root / "outputs" / "run1"
    verbose_root = ci2n_root / "verbose"
    run_verbose_dir = verbose_root / "run1"

    inputs_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)
    run_verbose_dir.mkdir(parents=True, exist_ok=True)

    images = sorted(source_images_dir.glob("*.png"))
    if not images:
        raise RuntimeError(f"No validation images found in {source_images_dir}")

    for image in images:
        shutil.copy2(image, inputs_dir / image.name)

    summary = []
    total = len(images)

    for index, source_image in enumerate(images, start=1):
        task_id = source_image.stem
        input_path = inputs_dir / source_image.name
        output_path = outputs_dir / f"{task_id}.json"
        task_verbose_dir = run_verbose_dir / task_id
        task_verbose_dir.mkdir(parents=True, exist_ok=True)
        log_path = task_verbose_dir / "run.log"

        before = timestamp_dirs(verbose_root)
        start = time.time()

        cmd = [
            sys.executable,
            "run.py",
            "--path",
            str(input_path.relative_to(ci2n_root)),
            "--output",
            str(output_path.relative_to(ci2n_root)),
            "--verbose=True",
        ]

        print(f"[{index:03d}/{total:03d}] running {task_id}", flush=True)
        with log_path.open("w") as log_file:
            completed = subprocess.run(
                cmd,
                cwd=ci2n_root,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                text=True,
            )

        after = timestamp_dirs(verbose_root)
        moved_verbose_dirs = move_verbose_artifacts(task_verbose_dir, after - before)

        elapsed = time.time() - start
        status = {
            "id": task_id,
            "input": str(input_path.relative_to(ci2n_root)),
            "output": str(output_path.relative_to(ci2n_root)),
            "verbose": str(task_verbose_dir.relative_to(ci2n_root)),
            "returncode": completed.returncode,
            "success": completed.returncode == 0 and output_path.exists(),
            "elapsed_seconds": round(elapsed, 3),
            "moved_verbose_dirs": moved_verbose_dirs,
        }
        summary.append(status)

        result_label = "ok" if status["success"] else f"failed rc={completed.returncode}"
        print(f"[{index:03d}/{total:03d}] {task_id} {result_label} in {elapsed:.1f}s", flush=True)

    summary_path = outputs_dir / "_run1_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))

    successes = sum(1 for item in summary if item["success"])
    print(f"finished run1: {successes}/{total} successful outputs", flush=True)
    print(f"summary written to {summary_path.relative_to(ci2n_root)}", flush=True)
    return 0 if successes == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
