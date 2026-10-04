"""
End-to-end integration tests for CLI interface and system flow (Phase 10)
"""

import subprocess
import sys
import json
from pathlib import Path


def test_cli_onboard_command(base_dir):
    """Tests running the onboard command via CLI."""
    cmd = [
        sys.executable, "-m", "research_onboarding.cli",
        "onboard", str(base_dir / "examples" / "new_input.json")
    ]
    result = subprocess.run(cmd, cwd=base_dir, capture_output=True, text=True)
    assert result.returncode == 0
    assert "CALYB AI - DOMAIN B: PREREQUISITE READING PATH" in result.stdout
    assert "Pedagogical Reading Path" in result.stdout
    assert "Attention Is All You Need" in result.stdout


def test_cli_onboard_json_mode(base_dir):
    """Tests CLI output in pure structured JSON mode."""
    cmd = [
        sys.executable, "-m", "research_onboarding.cli",
        "onboard", str(base_dir / "examples" / "new_input.json"), "--json"
    ]
    result = subprocess.run(cmd, cwd=base_dir, capture_output=True, text=True)
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["status"] == "success"
    assert len(data["reading_path"]) > 0
    assert "summary" in data


def test_cli_inspect_stats(base_dir):
    """Tests CLI inspection of global statistics."""
    cmd = [
        sys.executable, "-m", "research_onboarding.cli",
        "inspect", "--stats"
    ]
    result = subprocess.run(cmd, cwd=base_dir, capture_output=True, text=True)
    assert result.returncode == 0
    assert "Knowledge State Statistics" in result.stdout
    assert "Relationships: 268" in result.stdout


def test_cli_inspect_concept(base_dir):
    """Tests CLI inspection of a specific concept."""
    cmd = [
        sys.executable, "-m", "research_onboarding.cli",
        "inspect", "--concept", "dense-passage-retrieval"
    ]
    result = subprocess.run(cmd, cwd=base_dir, capture_output=True, text=True)
    assert result.returncode == 0
    assert "Dense Passage Retrieval" in result.stdout
    assert "karpukhin_2020" in result.stdout
