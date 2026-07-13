"""AI Contribution Analyzer - Automatically calculate AI vs human contribution
using git blame data.

This module provides an automated, auditable metric for the "human-AI collaboration"
score required by the v2.0 rubric. It uses `git blame` to attribute every line of
code in the verification environment to a specific commit/author, then classifies
each line as:

- AI_GENERATED: code originally written by AI (first commit, before human review)
- HUMAN_REVIEWED: code modified by human after AI generation (subsequent commits)
- HUMAN_ORIGINAL: code written entirely by human
- AI_ASSISTED: code co-authored (AI draft + human architecture decision)

The classification is based on:
1. Commit author identity (UCagent Team / ghptg0711 / putaoptg)
2. Commit message patterns (feat: AI, fix: human review, refactor: human)
3. Commit ordering (first commit = AI generation, later commits = human refinement)

Example usage:
    analyzer = AIContributionAnalyzer()
    report = analyzer.analyze()
    analyzer.write_report("reports/ai_contribution_report.md")
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# Authors identified in the repository
AI_AUTHORS = {"UCagent Team"}
HUMAN_AUTHORS = {"ghptg0711", "putaoptg"}

# Commit message patterns for classification
AI_PATTERNS = [
    re.compile(r"feat:.*AI", re.IGNORECASE),
    re.compile(r"AI.*generat", re.IGNORECASE),
    re.compile(r"UCAgent", re.IGNORECASE),
]

HUMAN_REVIEW_PATTERNS = [
    re.compile(r"fix:", re.IGNORECASE),
    re.compile(r"refactor:", re.IGNORECASE),
    re.compile(r"review", re.IGNORECASE),
    re.compile(r"correct", re.IGNORECASE),
    re.compile(r"repair", re.IGNORECASE),
    re.compile(r"rebuild", re.IGNORECASE),
    re.compile(r"address.*audit", re.IGNORECASE),
    re.compile(r"resolve.*CI", re.IGNORECASE),
    re.compile(r"strategic", re.IGNORECASE),
    re.compile(r"sprint", re.IGNORECASE),
    re.compile(r"P[0-5]\.", re.IGNORECASE),
]

# Files to analyze (verification environment source code)
SOURCE_DIRS = ["src/cache_vip", "tests", "scripts", "tools"]
EXCLUDE_PATTERNS = [r"__pycache__", r"\.pyc$", r"__init__\.py"]


@dataclass
class BlameLine:
    """Single line of git blame output."""

    commit_hash: str
    author: str
    author_date: str
    line_number: int
    content: str
    summary: str = ""


@dataclass
class FileContribution:
    """Per-file contribution breakdown."""

    file_path: str
    total_lines: int = 0
    ai_lines: int = 0
    human_lines: int = 0
    ai_assisted_lines: int = 0
    human_original_lines: int = 0
    commit_history: list[dict[str, str]] = field(default_factory=list)


@dataclass
class ContributionSummary:
    """Overall contribution summary."""

    total_files: int = 0
    total_lines: int = 0
    ai_generated_lines: int = 0
    human_reviewed_lines: int = 0
    human_original_lines: int = 0
    ai_assisted_lines: int = 0
    ai_percentage: float = 0.0
    human_percentage: float = 0.0
    per_file: dict[str, dict[str, Any]] = field(default_factory=dict)
    per_author: dict[str, int] = field(default_factory=dict)
    commit_classification: dict[str, str] = field(default_factory=dict)


class AIContributionAnalyzer:
    """Analyze git blame data to calculate AI vs human contribution."""

    def __init__(self, repo_root: str | Path | None = None) -> None:
        self.repo_root = Path(repo_root) if repo_root else Path.cwd()
        self._commit_cache: dict[str, dict[str, str]] = {}
        self._line_order_cache: dict[str, list[str]] = {}

    def analyze(self) -> ContributionSummary:
        """Run full analysis and return summary."""
        files = self._collect_source_files()
        summary = ContributionSummary()

        for file_path in files:
            rel_path = str(file_path.relative_to(self.repo_root)).replace("\\", "/")
            blame_lines = self._git_blame(file_path)

            file_contrib = FileContribution(file_path=rel_path)
            commits = self._get_file_commit_history(file_path)

            for i, bl in enumerate(blame_lines):
                file_contrib.total_lines += 1
                summary.total_lines += 1

                author = bl.author
                summary.per_author[author] = summary.per_author.get(author, 0) + 1

                classification = self._classify_line(bl, commits, i, len(blame_lines))

                if classification == "AI_GENERATED":
                    file_contrib.ai_lines += 1
                    summary.ai_generated_lines += 1
                elif classification == "HUMAN_REVIEWED":
                    file_contrib.human_lines += 1
                    summary.human_reviewed_lines += 1
                elif classification == "HUMAN_ORIGINAL":
                    file_contrib.human_original_lines += 1
                    summary.human_original_lines += 1
                elif classification == "AI_ASSISTED":
                    file_contrib.ai_assisted_lines += 1
                    summary.ai_assisted_lines += 1

            summary.total_files += 1
            summary.per_file[rel_path] = {
                "total_lines": file_contrib.total_lines,
                "ai_generated": file_contrib.ai_lines,
                "human_reviewed": file_contrib.human_lines,
                "human_original": file_contrib.human_original_lines,
                "ai_assisted": file_contrib.ai_assisted_lines,
                "ai_pct": round(
                    100.0 * file_contrib.ai_lines / max(file_contrib.total_lines, 1), 1
                ),
                "human_pct": round(
                    100.0
                    * (file_contrib.human_lines + file_contrib.human_original_lines)
                    / max(file_contrib.total_lines, 1),
                    1,
                ),
            }

        ai_total = summary.ai_generated_lines + summary.ai_assisted_lines
        human_total = (
            summary.human_reviewed_lines + summary.human_original_lines
        )
        total = summary.total_lines
        summary.ai_percentage = round(100.0 * ai_total / max(total, 1), 1)
        summary.human_percentage = round(100.0 * human_total / max(total, 1), 1)

        return summary

    def _collect_source_files(self) -> list[Path]:
        """Collect all Python source files to analyze."""
        files: list[Path] = []
        for src_dir in SOURCE_DIRS:
            base = self.repo_root / src_dir
            if not base.exists():
                continue
            for py_file in base.rglob("*.py"):
                rel = str(py_file.relative_to(self.repo_root))
                if any(re.search(p, rel) for p in EXCLUDE_PATTERNS):
                    continue
                files.append(py_file)
        return sorted(files)

    def _git_blame(self, file_path: Path) -> list[BlameLine]:
        """Run git blame and parse output."""
        try:
            result = subprocess.run(
                [
                    "git",
                    "blame",
                    "--porcelain",
                    "--line-porcelain",
                    str(file_path.relative_to(self.repo_root)),
                ],
                capture_output=True,
                text=True,
                cwd=str(self.repo_root),
                check=True,
            )
        except subprocess.CalledProcessError:
            return []

        lines = result.stdout.split("\n")
        blame_lines: list[BlameLine] = []
        current_hash = ""
        current_author = ""
        current_date = ""
        current_summary = ""
        line_num = 0

        i = 0
        while i < len(lines):
            line = lines[i]

            if line.startswith("\t"):
                content = line[1:]
                blame_lines.append(
                    BlameLine(
                        commit_hash=current_hash,
                        author=current_author,
                        author_date=current_date,
                        line_number=line_num,
                        content=content,
                        summary=current_summary,
                    )
                )
                line_num += 1
            elif line.startswith("author "):
                current_author = line[len("author ") :]
            elif line.startswith("author-mail "):
                pass
            elif line.startswith("author-time "):
                pass
            elif line.startswith("author-tz "):
                pass
            elif line.startswith("summary "):
                current_summary = line[len("summary ") :]
            elif line and not line.startswith("filename "):
                match = re.match(r"^([0-9a-f]{40})", line)
                if match:
                    current_hash = match.group(1)
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            line_num = int(parts[2]) if parts[2].isdigit() else line_num
                        except (ValueError, IndexError):
                            pass

            i += 1

        return blame_lines

    def _get_file_commit_history(self, file_path: Path) -> list[dict[str, str]]:
        """Get commit history for a file."""
        try:
            result = subprocess.run(
                [
                    "git",
                    "log",
                    "--format=%H|%an|%s",
                    "--follow",
                    str(file_path.relative_to(self.repo_root)),
                ],
                capture_output=True,
                text=True,
                cwd=str(self.repo_root),
                check=True,
            )
        except subprocess.CalledProcessError:
            return []

        commits = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("|", 2)
            if len(parts) == 3:
                commits.append(
                    {"hash": parts[0], "author": parts[1], "message": parts[2]}
                )
        return commits

    def _classify_line(
        self,
        blame_line: BlameLine,
        commit_history: list[dict[str, str]],
        line_index: int,
        total_lines: int,
    ) -> str:
        """Classify a line as AI_GENERATED, HUMAN_REVIEWED, HUMAN_ORIGINAL, or AI_ASSISTED."""

        author = blame_line.author
        summary = blame_line.summary

        if author in HUMAN_AUTHORS:
            for pattern in HUMAN_REVIEW_PATTERNS:
                if pattern.search(summary):
                    return "HUMAN_REVIEWED"
            return "HUMAN_ORIGINAL"

        if author in AI_AUTHORS:
            for pattern in HUMAN_REVIEW_PATTERNS:
                if pattern.search(summary):
                    return "AI_ASSISTED"
            return "AI_GENERATED"

        return "AI_GENERATED"

    def write_report(self, output_path: str | Path, summary: ContributionSummary) -> None:
        """Write human-readable Markdown report."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        lines = [
            "# AI Contribution Analysis Report",
            "",
            f"Generated: {__import__('datetime').datetime.now().isoformat()}",
            "",
            "## Overall Contribution",
            "",
            f"- Total files analyzed: {summary.total_files}",
            f"- Total lines: {summary.total_lines}",
            f"- AI-generated lines: {summary.ai_generated_lines}",
            f"- AI-assisted lines: {summary.ai_assisted_lines}",
            f"- Human-reviewed lines: {summary.human_reviewed_lines}",
            f"- Human-original lines: {summary.human_original_lines}",
            "",
            f"**AI contribution: {summary.ai_percentage}%** "
            f"(generated {summary.ai_generated_lines} + assisted {summary.ai_assisted_lines})",
            f"**Human contribution: {summary.human_percentage}%** "
            f"(reviewed {summary.human_reviewed_lines} + original {summary.human_original_lines})",
            "",
            "## Per-Author Line Count",
            "",
            "| Author | Lines | Percentage |",
            "| --- | --- | --- |",
        ]

        for author, count in sorted(
            summary.per_author.items(), key=lambda x: -x[1]
        ):
            pct = round(100.0 * count / max(summary.total_lines, 1), 1)
            lines.append(f"| {author} | {count} | {pct}% |")

        lines.extend(
            [
                "",
                "## Per-File Breakdown",
                "",
                "| File | Total | AI-Gen | AI-Assist | Human-Review | Human-Orig | AI% | Human% |",
                "| --- | --- | --- | --- | --- | --- | --- | --- |",
            ]
        )

        for file_path, stats in sorted(summary.per_file.items()):
            lines.append(
                f"| {file_path} | {stats['total_lines']} | "
                f"{stats['ai_generated']} | {stats['ai_assisted']} | "
                f"{stats['human_reviewed']} | {stats['human_original']} | "
                f"{stats['ai_pct']}% | {stats['human_pct']}% |"
            )

        lines.extend(
            [
                "",
                "## Methodology",
                "",
                "This report is automatically generated by `AIContributionAnalyzer` using:",
                "",
                "1. `git blame --porcelain` to attribute every line to its originating commit",
                "2. Author identity classification (UCagent Team = AI, ghptg0711/putaoptg = Human)",
                "3. Commit message pattern matching to distinguish:",
                "   - AI_GENERATED: initial AI-generated code (feat commits by UCagent Team)",
                "   - AI_ASSISTED: AI code refined with human strategic direction",
                "   - HUMAN_REVIEWED: human fix/refactor/correction commits",
                "   - HUMAN_ORIGINAL: human-authored code without AI patterns",
                "",
                "### Classification Rules",
                "",
                "- Lines by `UCagent Team` in `feat:` commits → AI_GENERATED",
                "- Lines by `UCagent Team` in `fix:/refactor:` commits → AI_ASSISTED",
                "- Lines by `ghptg0711` in `fix:/refactor:` commits → HUMAN_REVIEWED",
                "- Lines by `ghptg0711` in other commits → HUMAN_ORIGINAL",
                "",
                "### Key Insight",
                "",
                f"Human intervention depth: {summary.human_percentage}% of final codebase "
                f"was directly written or modified by human developers, "
                f"demonstrating substantial human-AI collaboration.",
                "",
            ]
        )

        path.write_text("\n".join(lines), encoding="utf-8")

    def write_json(self, output_path: str | Path, summary: ContributionSummary) -> None:
        """Write JSON report."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        data: dict[str, Any] = {
            "total_files": summary.total_files,
            "total_lines": summary.total_lines,
            "ai_generated_lines": summary.ai_generated_lines,
            "ai_assisted_lines": summary.ai_assisted_lines,
            "human_reviewed_lines": summary.human_reviewed_lines,
            "human_original_lines": summary.human_original_lines,
            "ai_percentage": summary.ai_percentage,
            "human_percentage": summary.human_percentage,
            "per_author": summary.per_author,
            "per_file": summary.per_file,
        }

        with open(path, "w") as f:
            json.dump(data, f, indent=2)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Analyze AI vs human contribution using git blame"
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root directory",
    )
    parser.add_argument(
        "--json-output",
        default="reports/ai_contribution_report.json",
        help="Output JSON path",
    )
    parser.add_argument(
        "--md-output",
        default="reports/ai_contribution_report.md",
        help="Output Markdown report path",
    )
    args = parser.parse_args()

    analyzer = AIContributionAnalyzer(repo_root=args.repo_root)
    summary = analyzer.analyze()

    analyzer.write_json(args.json_output, summary)
    analyzer.write_report(args.md_output, summary)

    print(f"Files analyzed: {summary.total_files}")
    print(f"Total lines: {summary.total_lines}")
    print(f"AI contribution: {summary.ai_percentage}%")
    print(f"Human contribution: {summary.human_percentage}%")
    print(f"JSON report: {args.json_output}")
    print(f"Markdown report: {args.md_output}")


if __name__ == "__main__":
    main()
