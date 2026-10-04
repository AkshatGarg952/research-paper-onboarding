"""
Structured Output Module (Phase 8)
Transforms raw reasoning results into structured JSON deliverables and
human-readable pedagogical onboarding guides with clear provenance.
"""

from typing import Dict, List, Any, Optional
import json


class StructuredOutputFormatter:
    """Formats reasoning outputs for programmatic inspection and human readability."""

    @staticmethod
    def synthesize_summary(query_title: str, reading_path: List[Dict[str, Any]], is_in_domain: bool) -> str:
        """Synthesizes a human-readable summary of the reading path."""
        if not is_in_domain or not reading_path:
            return (
                f"The input paper '{query_title}' does not contain recognized Retrieval-Augmented "
                f"Generation concepts or methods from the 2017-2024 corpus. No reading path generated."
            )

        n = len(reading_path)
        first_paper = reading_path[0]["title"]
        last_paper = reading_path[-1]["title"]

        summary = (
            f"To build complete conceptual and architectural competence for '{query_title}', "
            f"you should read {n} prerequisite papers in sequence. "
            f"Begin with foundational architectures starting at '{first_paper}', "
            f"progress through core dense retrieval and seq2seq marginalization milestones, "
            f"and conclude with immediate precursor '{last_paper}'."
        )
        return summary

    @classmethod
    def format_json_output(cls, raw_result: Dict[str, Any], indent: int = 2) -> Dict[str, Any]:
        """Ensures all standard fields are populated in the canonical JSON output schema."""
        query_paper = raw_result.get("query_paper", {})
        reading_path = raw_result.get("reading_path", [])
        is_in_domain = raw_result.get("status") == "success"

        summary = cls.synthesize_summary(query_paper.get("title", "Submitted Paper"), reading_path, is_in_domain)

        canonical_output = {
            "status": raw_result.get("status", "unknown"),
            "query_paper": query_paper,
            "summary": summary,
            "reading_path": reading_path,
            "reasoning_metadata": raw_result.get("reasoning_metadata", {})
        }
        return canonical_output

    @classmethod
    def format_console_report(cls, raw_result: Dict[str, Any]) -> str:
        """Generates a clean, terminal-friendly report for quick CLI inspection."""
        query_paper = raw_result.get("query_paper", {})
        status = raw_result.get("status", "unknown")
        lines = []

        lines.append("=" * 64)
        lines.append("  CALYB AI - DOMAIN B: PREREQUISITE READING PATH")
        lines.append("=" * 64)
        lines.append(f"Input Paper: \"{query_paper.get('title', 'Unknown')}\"")

        concepts = query_paper.get("matched_concepts", [])
        methods = query_paper.get("matched_methods", [])

        lines.append(f"Matched Concepts: {', '.join(concepts) if concepts else 'None'}")
        lines.append(f"Matched Methods:  {', '.join(methods) if methods else 'None'}")
        lines.append("-" * 64)

        if status == "out_of_domain":
            lines.append("Result: OUT OF DOMAIN")
            lines.append(f"Notice: {raw_result.get('message', 'No matching concepts found.')}")
            lines.append("=" * 64)
            return "\n".join(lines)

        reading_path = raw_result.get("reading_path", [])
        lines.append(f"Pedagogical Reading Path ({len(reading_path)} papers in dependency order):\n")

        for item in reading_path:
            order = item.get("order", 0)
            year = item.get("year", "N/A")
            title = item.get("title", "Untitled")
            why = item.get("why_needed", "")
            chain = item.get("dependency_chain", "")

            lines.append(f"  {order}. [{year}] {title}")
            lines.append(f"     WHY:   {why}")
            if chain and chain != "(Direct Linage)":
                lines.append(f"     CHAIN: {chain}")
            lines.append("")

        meta = raw_result.get("reasoning_metadata", {})
        summary = cls.synthesize_summary(query_paper.get("title", "Submitted Paper"), reading_path, True)
        lines.append("-" * 64)
        lines.append(f"Summary: {summary}")
        lines.append(
            f"Metadata: {meta.get('total_prerequisites_found', 0)} papers selected, "
            f"max dependency depth {meta.get('max_dependency_depth', 0)}, "
            f"algorithm: {meta.get('algorithm', 'topological_sort')}"
        )
        lines.append("=" * 64)

        return "\n".join(lines)
