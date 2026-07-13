"""Coverage Hole Analyzer - Automatically attribute uncovered bins to root causes.

This module implements a systematic approach to explain why certain coverage bins
remain uncovered. Instead of just showing a number (e.g., 95%), it provides:

1. Automated bin classification:
   - UNREACHABLE: Design dead zones that can never be hit
   - HARD_TO_REACH: Require specific long sequences of stimuli
   - BUG_BLOCKED: Unreachable due to RTL bugs
   - CONFIG_BLOCKED: Only reachable with specific configuration
   - POTENTIALLY_REACHABLE: Unknown status, needs investigation

2. Detailed attribution for each missing bin with:
   - Root cause analysis
   - Required conditions for coverage
   - Suggested fix or investigation path
   - Associated test case recommendations

3. Machine-readable output for CI integration

Example usage:
    analyzer = CoverageHoleAnalyzer(coverage_summary)
    attribution = analyzer.analyze()
    analyzer.write_report("reports/coverage_holes_attribution.md")
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class HoleCategory(str, Enum):
    UNREACHABLE = "UNREACHABLE"
    HARD_TO_REACH = "HARD_TO_REACH"
    BUG_BLOCKED = "BUG_BLOCKED"
    CONFIG_BLOCKED = "CONFIG_BLOCKED"
    POTENTIALLY_REACHABLE = "POTENTIALLY_REACHABLE"


@dataclass
class HoleAttribution:
    bin_name: str
    category: HoleCategory
    root_cause: str
    required_conditions: list[str]
    suggested_action: str
    associated_bugs: list[str] = field(default_factory=list)
    difficulty_score: int = 0


class CoverageHoleAnalyzer:
    def __init__(self, coverage_summary: dict[str, Any]) -> None:
        self.summary = coverage_summary
        self.attributions: list[HoleAttribution] = []

    def analyze(self) -> list[HoleAttribution]:
        self.attributions.clear()
        missing = self.summary.get("missing", [])
        extended_missing = self.summary.get("extended_missing", [])

        for bin_name in missing + extended_missing:
            attribution = self._analyze_bin(bin_name)
            self.attributions.append(attribution)

        return self.attributions

    def _analyze_bin(self, bin_name: str) -> HoleAttribution:
        if bin_name.startswith("op."):
            return self._analyze_op_bin(bin_name)
        elif bin_name.startswith("size."):
            return self._analyze_size_bin(bin_name)
        elif bin_name.startswith("access."):
            return self._analyze_access_bin(bin_name)
        elif bin_name.startswith("replacement."):
            return self._analyze_replacement_bin(bin_name)
        elif bin_name.startswith("mask."):
            return self._analyze_mask_bin(bin_name)
        elif bin_name.startswith("addr."):
            return self._analyze_addr_bin(bin_name)
        elif bin_name.startswith("latency."):
            return self._analyze_latency_bin(bin_name)
        elif bin_name.startswith("cross."):
            return self._analyze_cross_bin(bin_name)
        elif bin_name.startswith("policy."):
            return self._analyze_policy_bin(bin_name)
        else:
            return HoleAttribution(
                bin_name=bin_name,
                category=HoleCategory.POTENTIALLY_REACHABLE,
                root_cause="Unknown bin type, requires manual investigation",
                required_conditions=["Unknown"],
                suggested_action="Review coverage definition to understand what this bin represents",
                difficulty_score=3,
            )

    def _analyze_op_bin(self, bin_name: str) -> HoleAttribution:
        op = bin_name.replace("op.", "")
        return HoleAttribution(
            bin_name=bin_name,
            category=HoleCategory.HARD_TO_REACH,
            root_cause=f"Generator may not produce {op} operations with sufficient frequency",
            required_conditions=[
                f"Generator profile must include {op} weight > 0",
                f"CRV must sample {op} operations",
            ],
            suggested_action=f"Adjust generator profile to increase {op} weight or add directed {op} sequences",
            difficulty_score=1,
        )

    def _analyze_size_bin(self, bin_name: str) -> HoleAttribution:
        size = bin_name.replace("size.", "")
        return HoleAttribution(
            bin_name=bin_name,
            category=HoleCategory.HARD_TO_REACH,
            root_cause=f"Size {size} accesses may not be generated frequently enough",
            required_conditions=[
                f"Generator must produce {size}-byte accesses",
                f"Address alignment must allow {size}-byte accesses",
            ],
            suggested_action=f"Add specific {size}-byte access patterns to directed sequences",
            difficulty_score=1,
        )

    def _analyze_access_bin(self, bin_name: str) -> HoleAttribution:
        parts = bin_name.replace("access.", "").split("_")
        op, result = parts[0], parts[1]

        if result == "miss" and op == "write":
            return HoleAttribution(
                bin_name=bin_name,
                category=HoleCategory.CONFIG_BLOCKED,
                root_cause="Write-miss requires write-allocate policy OR no-write-allocate with cache miss",
                required_conditions=[
                    "Cache must be write-allocate (default)",
                    "Target address must not be in cache",
                    "Replacement may occur if set is full",
                ],
                suggested_action="Ensure test includes write accesses to uncached addresses",
                difficulty_score=2,
            )
        elif result == "hit":
            return HoleAttribution(
                bin_name=bin_name,
                category=HoleCategory.HARD_TO_REACH,
                root_cause=f"{op} hit requires prior {op} to same address",
                required_conditions=[
                    f"Prior {op} to same address must have been cached",
                    "No eviction of the cache line between accesses",
                ],
                suggested_action=f"Add back-to-back {op} sequences to same address",
                difficulty_score=1,
            )
        else:
            return HoleAttribution(
                bin_name=bin_name,
                category=HoleCategory.HARD_TO_REACH,
                root_cause=f"{op}_{result} requires specific cache state",
                required_conditions=[
                    "Cache state must allow this access type",
                    "Address must be in appropriate state",
                ],
                suggested_action="Add directed sequences to force this access pattern",
                difficulty_score=2,
            )

    def _analyze_replacement_bin(self, bin_name: str) -> HoleAttribution:
        rep_type = bin_name.replace("replacement.", "")

        if rep_type == "dirty":
            return HoleAttribution(
                bin_name=bin_name,
                category=HoleCategory.HARD_TO_REACH,
                root_cause="Dirty replacement requires a modified cache line to be evicted",
                required_conditions=[
                    "Cache line must be written (dirty)",
                    "Set must be full requiring eviction",
                    "Victim selection must pick the dirty line",
                ],
                suggested_action="Fill cache with dirty lines, then force eviction",
                associated_bugs=["BUG-011"],
                difficulty_score=3,
            )
        elif rep_type == "clean":
            return HoleAttribution(
                bin_name=bin_name,
                category=HoleCategory.HARD_TO_REACH,
                root_cause="Clean replacement requires a read-only cache line to be evicted",
                required_conditions=[
                    "Cache line must be read-only (clean)",
                    "Set must be full requiring eviction",
                    "Victim selection must pick the clean line",
                ],
                suggested_action="Fill cache with read-only lines, then force eviction",
                difficulty_score=2,
            )
        else:
            return HoleAttribution(
                bin_name=bin_name,
                category=HoleCategory.POTENTIALLY_REACHABLE,
                root_cause=f"Unknown replacement type: {rep_type}",
                required_conditions=["Investigate coverage definition"],
                suggested_action="Review coverage definition for this bin",
                difficulty_score=3,
            )

    def _analyze_mask_bin(self, bin_name: str) -> HoleAttribution:
        mask_type = bin_name.replace("mask.", "")

        if mask_type == "full":
            return HoleAttribution(
                bin_name=bin_name,
                category=HoleCategory.HARD_TO_REACH,
                root_cause="Full mask requires all bytes in write to be enabled",
                required_conditions=[
                    "Write operation with mask == (1 << size) - 1",
                    "Generator must produce full-mask writes",
                ],
                suggested_action="Ensure generator produces writes with full mask",
                difficulty_score=1,
            )
        elif mask_type == "single":
            return HoleAttribution(
                bin_name=bin_name,
                category=HoleCategory.HARD_TO_REACH,
                root_cause="Single mask requires exactly one byte in write to be enabled",
                required_conditions=[
                    "Write operation with exactly one bit set in mask",
                    "Generator must produce single-byte partial writes",
                ],
                suggested_action="Add partial write sequences with single-bit masks",
                difficulty_score=2,
            )
        elif mask_type == "sparse":
            return HoleAttribution(
                bin_name=bin_name,
                category=HoleCategory.HARD_TO_REACH,
                root_cause="Sparse mask requires non-contiguous bytes to be enabled",
                required_conditions=[
                    "Write operation with mask having non-contiguous bits set",
                    "Generator must produce sparse-mask writes",
                ],
                suggested_action="Add partial write sequences with sparse masks like 0b0101",
                difficulty_score=3,
            )
        else:
            return HoleAttribution(
                bin_name=bin_name,
                category=HoleCategory.POTENTIALLY_REACHABLE,
                root_cause=f"Unknown mask type: {mask_type}",
                required_conditions=["Investigate coverage definition"],
                suggested_action="Review coverage definition for this bin",
                difficulty_score=3,
            )

    def _analyze_addr_bin(self, bin_name: str) -> HoleAttribution:
        addr_type = bin_name.replace("addr.", "")

        if addr_type == "same_set":
            return HoleAttribution(
                bin_name=bin_name,
                category=HoleCategory.HARD_TO_REACH,
                root_cause="Same-set access requires multiple accesses to addresses mapping to same cache set",
                required_conditions=[
                    "Multiple transactions must target same cache set",
                    "Generator must have hot-set bias enabled",
                ],
                suggested_action="Enable hot-set bias in generator profile or add directed same-set sequences",
                difficulty_score=2,
            )
        elif addr_type == "line_boundary":
            return HoleAttribution(
                bin_name=bin_name,
                category=HoleCategory.HARD_TO_REACH,
                root_cause="Line boundary access requires access near end of cache line",
                required_conditions=[
                    "Access address must be within 8 bytes of line boundary",
                    "Generator must produce boundary accesses",
                ],
                suggested_action="Add line boundary test sequences",
                difficulty_score=2,
            )
        elif addr_type == "back_to_back_same_line":
            return HoleAttribution(
                bin_name=bin_name,
                category=HoleCategory.HARD_TO_REACH,
                root_cause="Back-to-back same line requires consecutive accesses to same cache line",
                required_conditions=[
                    "Two consecutive transactions must target same line",
                    "No interleaving transactions between them",
                ],
                suggested_action="Add consecutive access sequences to same line",
                difficulty_score=2,
            )
        elif addr_type == "stride_access_pattern":
            return HoleAttribution(
                bin_name=bin_name,
                category=HoleCategory.HARD_TO_REACH,
                root_cause="Stride pattern requires accesses spaced by exact line_bytes",
                required_conditions=[
                    "Consecutive accesses must differ by exactly line_bytes",
                    "Generator must produce sequential address patterns",
                ],
                suggested_action="Add sequential access patterns with stride of line_bytes",
                difficulty_score=3,
            )
        else:
            return HoleAttribution(
                bin_name=bin_name,
                category=HoleCategory.POTENTIALLY_REACHABLE,
                root_cause=f"Unknown address type: {addr_type}",
                required_conditions=["Investigate coverage definition"],
                suggested_action="Review coverage definition for this bin",
                difficulty_score=3,
            )

    def _analyze_latency_bin(self, bin_name: str) -> HoleAttribution:
        lat_type = bin_name.replace("latency.", "")

        if lat_type == "long":
            return HoleAttribution(
                bin_name=bin_name,
                category=HoleCategory.CONFIG_BLOCKED,
                root_cause="Long latency requires latency >= 8 cycles, which depends on memory agent configuration",
                required_conditions=[
                    "Memory agent must inject latency >= 8 cycles",
                    "Transaction must hit long-latency condition",
                ],
                suggested_action="Configure memory agent to inject variable latency",
                difficulty_score=1,
            )
        elif lat_type == "short":
            return HoleAttribution(
                bin_name=bin_name,
                category=HoleCategory.HARD_TO_REACH,
                root_cause="Short latency requires latency < 8 cycles",
                required_conditions=[
                    "Memory agent must allow low-latency responses",
                    "Transaction must hit short-latency condition",
                ],
                suggested_action="Ensure memory agent can produce short-latency responses",
                difficulty_score=1,
            )
        else:
            return HoleAttribution(
                bin_name=bin_name,
                category=HoleCategory.POTENTIALLY_REACHABLE,
                root_cause=f"Unknown latency type: {lat_type}",
                required_conditions=["Investigate coverage definition"],
                suggested_action="Review coverage definition for this bin",
                difficulty_score=2,
            )

    def _analyze_cross_bin(self, bin_name: str) -> HoleAttribution:
        parts = bin_name.replace("cross.", "").split(".")
        cross_type = parts[0]
        specific = parts[1] if len(parts) > 1 else ""

        if cross_type == "size_mask":
            size, mask = specific.split("_")
            return HoleAttribution(
                bin_name=bin_name,
                category=HoleCategory.HARD_TO_REACH,
                root_cause=f"Cross coverage requires {size}-byte access with {mask} mask simultaneously",
                required_conditions=[
                    f"Access must be exactly {size} bytes",
                    f"Mask must be {mask} type",
                    "Both conditions must occur in same transaction",
                ],
                suggested_action=f"Add directed test with {size}-byte access and {mask} mask",
                difficulty_score=3,
            )
        elif cross_type == "replacement_type":
            return HoleAttribution(
                bin_name=bin_name,
                category=HoleCategory.HARD_TO_REACH,
                root_cause="Replacement type cross requires specific eviction scenario",
                required_conditions=[
                    "Specific eviction type must occur",
                    "Specific access type must trigger it",
                ],
                suggested_action="Add directed sequences for specific replacement scenarios",
                difficulty_score=4,
            )
        elif cross_type == "access_latency":
            return HoleAttribution(
                bin_name=bin_name,
                category=HoleCategory.HARD_TO_REACH,
                root_cause="Access latency cross requires specific access type with specific latency",
                required_conditions=[
                    "Specific access type (read/write hit/miss)",
                    "Specific latency condition (long/short)",
                    "Both conditions must occur in same transaction",
                ],
                suggested_action="Configure memory agent latency and add matching access patterns",
                difficulty_score=3,
            )
        else:
            return HoleAttribution(
                bin_name=bin_name,
                category=HoleCategory.POTENTIALLY_REACHABLE,
                root_cause=f"Unknown cross coverage type: {cross_type}",
                required_conditions=["Investigate coverage definition"],
                suggested_action="Review coverage definition for this cross bin",
                difficulty_score=4,
            )

    def _analyze_policy_bin(self, bin_name: str) -> HoleAttribution:
        parts = bin_name.replace("policy.", "").split(".")
        policy_type = parts[0]
        specific = parts[1] if len(parts) > 1 else ""

        if policy_type == "write_allocate":
            return HoleAttribution(
                bin_name=bin_name,
                category=HoleCategory.CONFIG_BLOCKED,
                root_cause="Write allocate policy requires write-allocate configuration",
                required_conditions=[
                    "Cache must be configured with write_allocate=True",
                    "Write miss must occur to trigger allocation",
                ],
                suggested_action="Ensure cache params have write_allocate=True",
                difficulty_score=1,
            )
        elif policy_type == "replacement":
            policy = specific.replace("_eviction", "")
            return HoleAttribution(
                bin_name=bin_name,
                category=HoleCategory.CONFIG_BLOCKED,
                root_cause=f"{policy.upper()} eviction requires {policy} replacement policy",
                required_conditions=[
                    f"Cache must be configured with {policy} replacement",
                    "Eviction must occur",
                ],
                suggested_action=f"Run regression with replacement={policy}",
                difficulty_score=2,
            )
        else:
            return HoleAttribution(
                bin_name=bin_name,
                category=HoleCategory.POTENTIALLY_REACHABLE,
                root_cause=f"Unknown policy type: {policy_type}",
                required_conditions=["Investigate coverage definition"],
                suggested_action="Review coverage definition for this policy bin",
                difficulty_score=3,
            )

    def write_report(self, output_path: str | Path) -> None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        categorized = {cat: [] for cat in HoleCategory}
        for attr in self.attributions:
            categorized[attr.category].append(attr)

        report_lines = [
            "# Coverage Hole Attribution Report",
            "",
            f"Generated: {__import__('datetime').datetime.now().isoformat()}",
            "",
            f"Total missing bins: {len(self.attributions)}",
            "",
        ]

        for cat in HoleCategory:
            items = categorized[cat]
            if not items:
                continue
            report_lines.append(f"## {cat.value} ({len(items)} bins)")
            report_lines.append("")
            report_lines.append("| Bin Name | Root Cause | Difficulty | Action |")
            report_lines.append("| --- | --- | --- | --- |")
            for item in items:
                report_lines.append(
                    f"| {item.bin_name} | {item.root_cause} | {'★' * item.difficulty_score} | {item.suggested_action} |"
                )
            report_lines.append("")

            for item in items:
                report_lines.append(f"### {item.bin_name}")
                report_lines.append("")
                report_lines.append(f"- **Category**: {item.category.value}")
                report_lines.append(f"- **Root Cause**: {item.root_cause}")
                report_lines.append("- **Required Conditions**:")
                for cond in item.required_conditions:
                    report_lines.append(f"  - {cond}")
                report_lines.append(f"- **Suggested Action**: {item.suggested_action}")
                if item.associated_bugs:
                    report_lines.append(f"- **Associated Bugs**: {', '.join(item.associated_bugs)}")
                report_lines.append("")

        path.write_text("\n".join(report_lines))

    def to_json(self) -> str:
        result = {
            "total_missing": len(self.attributions),
            "by_category": {},
            "attributions": [],
        }
        for cat in HoleCategory:
            count = sum(1 for a in self.attributions if a.category == cat)
            result["by_category"][cat.value] = count

        for attr in self.attributions:
            result["attributions"].append(
                {
                    "bin_name": attr.bin_name,
                    "category": attr.category.value,
                    "root_cause": attr.root_cause,
                    "required_conditions": attr.required_conditions,
                    "suggested_action": attr.suggested_action,
                    "associated_bugs": attr.associated_bugs,
                    "difficulty_score": attr.difficulty_score,
                }
            )

        return json.dumps(result, indent=2)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Analyze coverage holes and attribute root causes")
    parser.add_argument("--input", required=True, help="Path to coverage summary JSON")
    parser.add_argument(
        "--output",
        default="reports/coverage_holes_attribution.md",
        help="Output report path",
    )
    args = parser.parse_args()

    with open(args.input) as f:
        coverage_summary = json.load(f)

    analyzer = CoverageHoleAnalyzer(coverage_summary)
    analyzer.analyze()
    analyzer.write_report(args.output)

    print(f"Generated coverage hole attribution report: {args.output}")
    print(f"Total missing bins: {len(analyzer.attributions)}")


if __name__ == "__main__":
    main()
