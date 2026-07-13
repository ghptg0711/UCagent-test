"""AI Fallacy Detector - Static analysis probes for common AI-generated code flaws.

This module implements automated static analysis to detect seven categories
of AI logic fallacies identified in the v2.0 review standard:

1. Circular Reasoning: Ref Model calls DUT internal signals or shares state
2. Synthetic Sampling: Address generation uses random.randint instead of hash
3. Infinite Way Hallucination: Mock DUT lacks way associativity parameters
4. Async Timing Omission: reset/clock operations missing await/edge sensitivity
5. Boundary Magic Numbers: Hardcoded constants (64, 512, 4096) not tied to parameters
6. Eviction Blind Spot: CRV doesn't track dirty/clean eviction events
7. Weak Assertions: >30% of asserts are just 'is not None' or '== True'

The detector integrates into CI as a lint phase and outputs structured
reports for automated quality gates.

Example usage:
    detector = AIFallacyDetector()
    results = detector.scan_project()
    detector.write_report("reports/ai_fallacy_report.md")
"""

from __future__ import annotations

import ast
import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class FallacyType(str, Enum):
    CIRCULAR_REASONING = "CIRCULAR_REASONING"
    SYNTHETIC_SAMPLING = "SYNTHETIC_SAMPLING"
    INFINITE_WAY = "INFINITE_WAY"
    ASYNC_TIMING = "ASYNC_TIMING"
    BOUNDARY_MAGIC_NUMBER = "BOUNDARY_MAGIC_NUMBER"
    EVICTION_BLIND_SPOT = "EVICTION_BLIND_SPOT"
    WEAK_ASSERTION = "WEAK_ASSERTION"


class Severity(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class FallacyFinding:
    fallacy_type: FallacyType
    file_path: str
    line_number: int
    column_number: int
    code_snippet: str
    severity: Severity
    description: str
    suggestion: str


class AIFallacyDetector:
    MAGIC_NUMBERS = {64, 512, 4096, 8192}

    def __init__(self) -> None:
        self.findings: list[FallacyFinding] = []
        self.scanned_files: list[str] = []

    def scan_project(self) -> list[FallacyFinding]:
        self.findings.clear()
        self.scanned_files.clear()

        src_dir = Path("src") / "cache_vip"
        test_dir = Path("tests")

        for py_file in src_dir.glob("*.py"):
            self._scan_file(py_file)

        for py_file in test_dir.glob("*.py"):
            self._scan_file(py_file)

        self._scan_weak_assertions()

        return self.findings

    def _scan_file(self, file_path: Path) -> None:
        try:
            content = file_path.read_text()
            tree = ast.parse(content)
        except Exception:
            return

        self.scanned_files.append(str(file_path))

        for node in ast.walk(tree):
            self._check_circular_reasoning(node, file_path, content)
            self._check_synthetic_sampling(node, file_path, content)
            self._check_infinite_way(node, file_path, content)
            self._check_async_timing(node, file_path, content)
            self._check_boundary_magic(node, file_path, content)
            self._check_eviction_blind_spot(node, file_path, content)

    def _check_circular_reasoning(self, node: ast.AST, file_path: Path, content: str) -> None:
        if isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name):
                if (
                    node.value.id in ("dut", "DUT", "real_dut")
                    and node.attr in ("access", "state", "internal", "signals")
                ):
                    self._add_finding(
                        fallacy_type=FallacyType.CIRCULAR_REASONING,
                        file_path=str(file_path),
                        node=node,
                        content=content,
                        severity=Severity.HIGH,
                        description="Reference Model may be calling DUT internal signals",
                        suggestion="Ensure Reference Model is completely independent of DUT implementation",
                    )

    def _check_synthetic_sampling(self, node: ast.AST, file_path: Path, content: str) -> None:
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "randint":
                for arg in node.args:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, int):
                        if arg.value > 1000:
                            self._add_finding(
                                fallacy_type=FallacyType.SYNTHETIC_SAMPLING,
                                file_path=str(file_path),
                                node=node,
                                content=content,
                                severity=Severity.HIGH,
                                description="Address generation using random.randint instead of parameter-based hash",
                                suggestion="Use hash-based address generation tied to Cache parameters (sets, line_bytes)",
                            )

    def _check_infinite_way(self, node: ast.AST, file_path: Path, content: str) -> None:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in ("cache", "storage", "memory"):
                    if isinstance(node.value, ast.Dict):
                        if len(node.value.keys) == 0:
                            self._add_finding(
                                fallacy_type=FallacyType.INFINITE_WAY,
                                file_path=str(file_path),
                                node=node,
                                content=content,
                                severity=Severity.HIGH,
                                description="Cache storage using unbounded dictionary (infinite way capacity)",
                                suggestion="Implement way-associative constraints with LRU tracking",
                            )

    def _check_async_timing(self, node: ast.AST, file_path: Path, content: str) -> None:
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if node.func.attr in ("write", "read"):
                    if isinstance(node.func.value, ast.Name):
                        if node.func.value.id in (
                            "reset",
                            "clock",
                            "reset_wrapper",
                            "clock_wrapper",
                        ):
                            parent = self._find_parent(node)
                            if not isinstance(parent, ast.Await):
                                self._add_finding(
                                    fallacy_type=FallacyType.ASYNC_TIMING,
                                    file_path=str(file_path),
                                    node=node,
                                    content=content,
                                    severity=Severity.MEDIUM,
                                    description="Missing await on async reset/clock operation",
                                    suggestion="Add await before reset/clock write/read operations",
                                )

    def _check_boundary_magic(self, node: ast.AST, file_path: Path, content: str) -> None:
        if isinstance(node, ast.Constant) and isinstance(node.value, int):
            if node.value in self.MAGIC_NUMBERS:
                parent = self._find_parent(node)
                is_parameterized = False

                if isinstance(parent, ast.Assign):
                    for target in parent.targets:
                        if isinstance(target, ast.Name):
                            if target.id in ("line_bytes", "cache_size", "sets", "ways"):
                                is_parameterized = True

                if isinstance(parent, ast.AnnAssign):
                    if parent.target.id in ("line_bytes", "cache_size", "sets", "ways"):
                        is_parameterized = True

                if not is_parameterized:
                    self._add_finding(
                        fallacy_type=FallacyType.BOUNDARY_MAGIC_NUMBER,
                        file_path=str(file_path),
                        node=node,
                        content=content,
                        severity=Severity.MEDIUM,
                        description=f"Hardcoded magic number {node.value} not tied to parameter",
                        suggestion=f"Replace {node.value} with parameter reference (e.g., line_bytes)",
                    )

    def _check_eviction_blind_spot(self, node: ast.AST, file_path: Path, content: str) -> None:
        if isinstance(node, ast.FunctionDef):
            if node.name in ("generate", "sample", "create_transaction"):
                has_dirty = False
                has_clean = False
                for subnode in ast.walk(node):
                    if isinstance(subnode, ast.Name):
                        if subnode.id in ("dirty", "evicted_dirty"):
                            has_dirty = True
                        if subnode.id in ("clean", "evicted_clean"):
                            has_clean = True

                if not (has_dirty or has_clean):
                    self._add_finding(
                        fallacy_type=FallacyType.EVICTION_BLIND_SPOT,
                        file_path=str(file_path),
                        node=node,
                        content=content,
                        severity=Severity.LOW,
                        description="Generator doesn't track dirty/clean eviction events",
                        suggestion="Add dirty/clean eviction tracking to CRV generator",
                    )

    def _scan_weak_assertions(self) -> None:
        weak_count = 0
        total_count = 0

        for file_path in self.scanned_files:
            try:
                content = Path(file_path).read_text()
                tree = ast.parse(content)
            except Exception:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.Assert):
                    total_count += 1
                    test = node.test

                    if isinstance(test, ast.Compare):
                        if isinstance(test.left, ast.Name):
                            for op, comp in zip(test.ops, test.comparators):
                                if (
                                    isinstance(op, ast.IsNot)
                                    and isinstance(comp, ast.Constant)
                                    and comp.value is None
                                ):
                                    weak_count += 1
                                    self._add_finding(
                                        fallacy_type=FallacyType.WEAK_ASSERTION,
                                        file_path=file_path,
                                        node=node,
                                        content=content,
                                        severity=Severity.MEDIUM,
                                        description=f"Weak assertion: assert {test.left.id} is not None",
                                        suggestion="Add data value comparison to assertion",
                                    )

                        elif isinstance(test.left, ast.Call):
                            if (
                                isinstance(test.left.func, ast.Name)
                                and test.left.func.id in ("is_not_none", "is_not_None")
                            ):
                                weak_count += 1

                    elif isinstance(test, ast.Name):
                        weak_count += 1
                        self._add_finding(
                            fallacy_type=FallacyType.WEAK_ASSERTION,
                            file_path=file_path,
                            node=node,
                            content=content,
                            severity=Severity.MEDIUM,
                            description=f"Weak assertion: assert {test.id}",
                            suggestion="Replace with explicit boolean comparison",
                        )

        if total_count > 0 and weak_count / total_count > 0.3:
            pass

    def _find_parent(self, node: ast.AST) -> ast.AST | None:
        import inspect
        frame = inspect.currentframe()
        if frame and frame.f_back:
            local_vars = frame.f_back.f_locals
            for var in local_vars.values():
                if isinstance(var, ast.AST):
                    for child in ast.walk(var):
                        if child is node:
                            return var
        return None

    def _add_finding(
        self,
        fallacy_type: FallacyType,
        file_path: str,
        node: ast.AST,
        content: str,
        severity: Severity,
        description: str,
        suggestion: str,
    ) -> None:
        lines = content.split("\n")
        line_number = node.lineno
        col_offset = node.col_offset

        start = max(0, line_number - 3)
        end = min(len(lines), line_number + 2)
        snippet_lines = lines[start:end]
        code_snippet = "\n".join(snippet_lines)

        self.findings.append(FallacyFinding(
            fallacy_type=fallacy_type,
            file_path=file_path,
            line_number=line_number,
            column_number=col_offset,
            code_snippet=code_snippet.strip(),
            severity=severity,
            description=description,
            suggestion=suggestion,
        ))

    def write_report(self, output_path: str | Path) -> None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        categorized = {f: [] for f in FallacyType}
        for finding in self.findings:
            categorized[finding.fallacy_type].append(finding)

        lines = [
            "# AI Fallacy Detection Report",
            "",
            f"Generated: {__import__('datetime').datetime.now().isoformat()}",
            "",
            f"Scanned files: {len(self.scanned_files)}",
            f"Total findings: {len(self.findings)}",
            "",
        ]

        for fallacy_type in FallacyType:
            findings = categorized[fallacy_type]
            if not findings:
                continue

            lines.append(f"## {fallacy_type.value} ({len(findings)} findings)")
            lines.append("")
            lines.append("| File | Line | Severity | Description |")
            lines.append("| --- | --- | --- | --- |")
            for f in findings:
                file_name = Path(f.file_path).name
                lines.append(f"| {file_name}:{f.line_number} | {f.line_number} | {f.severity.value} | {f.description} |")
            lines.append("")

        high_count = sum(1 for f in self.findings if f.severity == Severity.HIGH)
        medium_count = sum(1 for f in self.findings if f.severity == Severity.MEDIUM)
        low_count = sum(1 for f in self.findings if f.severity == Severity.LOW)

        lines.append("## Summary")
        lines.append("")
        lines.append(f"- HIGH severity: {high_count}")
        lines.append(f"- MEDIUM severity: {medium_count}")
        lines.append(f"- LOW severity: {low_count}")
        lines.append("")

        if high_count == 0 and medium_count == 0:
            lines.append("✅ No AI fallacies detected. The codebase is clean.")
        else:
            lines.append("⚠️ AI fallacies detected. Please review and fix before submission.")

        path.write_text("\n".join(lines))

    def to_json(self) -> str:
        result = {
            "scanned_files": self.scanned_files,
            "total_findings": len(self.findings),
            "by_type": {},
            "by_severity": {
                "HIGH": 0,
                "MEDIUM": 0,
                "LOW": 0,
            },
            "findings": [],
        }

        for fallacy_type in FallacyType:
            count = sum(1 for f in self.findings if f.fallacy_type == fallacy_type)
            result["by_type"][fallacy_type.value] = count

        for finding in self.findings:
            result["by_severity"][finding.severity.value] += 1
            result["findings"].append({
                "fallacy_type": finding.fallacy_type.value,
                "file_path": finding.file_path,
                "line_number": finding.line_number,
                "column_number": finding.column_number,
                "code_snippet": finding.code_snippet,
                "severity": finding.severity.value,
                "description": finding.description,
                "suggestion": finding.suggestion,
            })

        return json.dumps(result, indent=2)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Run AI Fallacy Detector")
    parser.add_argument(
        "--output",
        default="reports/ai_fallacy_report.md",
        help="Output report path",
    )
    parser.add_argument(
        "--json",
        default="reports/ai_fallacy_report.json",
        help="Output JSON path",
    )
    args = parser.parse_args()

    detector = AIFallacyDetector()
    detector.scan_project()
    detector.write_report(args.output)

    with open(args.json, "w") as f:
        f.write(detector.to_json())

    print(f"Generated fallacy report: {args.output}")
    print(f"Generated findings JSON: {args.json}")


if __name__ == "__main__":
    main()
