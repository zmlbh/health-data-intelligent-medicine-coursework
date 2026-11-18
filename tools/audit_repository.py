#!/usr/bin/env python3
"""Audit the public course repository with Python's standard library only."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LESSONS = ROOT / "lessons"
OUTPUT = ROOT / "outputs" / "repository-audit.csv"

CODE_SUFFIXES = {".py", ".ipynb", ".mjs", ".js", ".r"}
DATA_SUFFIXES = {".csv", ".tsv", ".json", ".data", ".dat"}
RESULT_SUFFIXES = {".csv", ".png", ".pdf", ".docx", ".txt"}
FORBIDDEN_PARTS = {".venv", "venv", "__pycache__", ".ipynb_checkpoints"}
SECRET_NAMES = {".env", "id_rsa", "id_ed25519"}


def files_under(path: Path) -> list[Path]:
    return [item for item in path.rglob("*") if item.is_file()]


def contains_result(path: Path, files: list[Path]) -> bool:
    result_markers = {"assets", "outputs", "results", "submission_materials"}
    return any(
        file.suffix.lower() in RESULT_SUFFIXES
        and result_markers.intersection(file.relative_to(path).parts)
        for file in files
    )


def main() -> int:
    rows: list[dict[str, str]] = []
    problems: list[str] = []

    for lesson in sorted(path for path in LESSONS.iterdir() if path.is_dir()):
        files = files_under(lesson)
        assignment_files = files_under(lesson / "assignment") if (lesson / "assignment").exists() else []
        code_files = [file for file in files if file.suffix.lower() in CODE_SUFFIXES]
        data_files = [file for file in files if file.suffix.lower() in DATA_SUFFIXES]
        has_readme = (lesson / "project" / "README.md").exists() or lesson.name.startswith("lesson-01")
        has_result = (
            contains_result(lesson, files)
            or bool(assignment_files)
            or (lesson.name.startswith("lesson-01") and any(file.suffix.lower() == ".pptx" for file in files))
        )

        if not code_files and not lesson.name.startswith("lesson-01"):
            problems.append(f"{lesson.name}: no code or notebook found")
        if not has_readme:
            problems.append(f"{lesson.name}: project README missing")

        rows.append(
            {
                "lesson": lesson.name,
                "assignment_files": str(len(assignment_files)),
                "code_files": str(len(code_files)),
                "data_files": str(len(data_files)),
                "has_readme": "yes" if has_readme else "no",
                "has_result": "yes" if has_result else "no",
                "status": "reviewable" if has_readme and has_result else "needs-review",
            }
        )

    for file in files_under(ROOT):
        relative = file.relative_to(ROOT)
        if FORBIDDEN_PARTS.intersection(relative.parts):
            problems.append(f"forbidden generated path: {relative}")
        if file.name.lower() in SECRET_NAMES or file.suffix.lower() in {".pem", ".key", ".pfx", ".p12"}:
            problems.append(f"secret-like file name: {relative}")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    print("lesson, assignment, code, data, README, result, status")
    for row in rows:
        print(
            f"{row['lesson']}, {row['assignment_files']}, {row['code_files']}, "
            f"{row['data_files']}, {row['has_readme']}, {row['has_result']}, {row['status']}"
        )
    print(f"\nGenerated: {OUTPUT.relative_to(ROOT)}")

    if problems:
        print("\nReview notes:")
        for problem in problems:
            print(f"- {problem}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
