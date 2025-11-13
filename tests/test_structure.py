"""
Test placeholder for CVE Matter-Analysis OS

This module contains basic tests to validate the repository structure.
Actual tests will be implemented alongside each task (010-090).
"""

import pytest
from pathlib import Path


def test_repository_structure():
    """Test that required directories exist."""
    required_dirs = [
        "src",
        "tests",
        "prompts",
        "capsules",
        ".copilot",
        ".copilot/tasks",
        ".github/workflows",
    ]

    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        assert dir_path.exists(), f"Required directory missing: {dir_name}"
        assert dir_path.is_dir(), f"Path is not a directory: {dir_name}"


def test_prompts_exist():
    """Test that prompt files exist."""
    required_prompts = [
        "prompts/legendary_lidlift_v14.md",
        "prompts/micro_core.txt",
        "prompts/nano_core.txt",
    ]

    for prompt_file in required_prompts:
        file_path = Path(prompt_file)
        assert file_path.exists(), f"Required prompt file missing: {prompt_file}"
        assert file_path.is_file(), f"Path is not a file: {prompt_file}"


def test_capsules_exist():
    """Test that capsule files exist."""
    required_capsules = [
        "capsules/lidlift-v1.json",
        "capsules/hmoc-0.2.json",
        "capsules/runbooks.json",
    ]

    for capsule_file in required_capsules:
        file_path = Path(capsule_file)
        assert file_path.exists(), f"Required capsule file missing: {capsule_file}"
        assert file_path.is_file(), f"Path is not a file: {capsule_file}"


def test_task_definitions_exist():
    """Test that all task definition files exist."""
    expected_tasks = [
        "010_ingest_nvd.md",
        "020_alignment.md",
        "030_arbiter.md",
        "040_refractors.md",
        "050_evidence.md",
        "060_notion_sync.md",
        "070_capsules_publish.md",
        "080_cuda_support.md",
        "090_bridge.md",
    ]

    tasks_dir = Path(".copilot/tasks")
    for task_file in expected_tasks:
        file_path = tasks_dir / task_file
        assert file_path.exists(), f"Required task file missing: {file_path}"
        assert file_path.is_file(), f"Path is not a file: {file_path}"


def test_workflows_exist():
    """Test that GitHub Actions workflows exist."""
    expected_workflows = [
        "ci.yml",
        "codeql.yml",
        "container-scan.yml",
        "notion-sync.yml",
        "publish-capsules.yml",
    ]

    workflows_dir = Path(".github/workflows")
    for workflow_file in expected_workflows:
        file_path = workflows_dir / workflow_file
        assert file_path.exists(), f"Required workflow file missing: {file_path}"
        assert file_path.is_file(), f"Path is not a file: {file_path}"


def test_security_files_exist():
    """Test that security files exist."""
    security_files = [
        "SECURITY.md",
        "CODEOWNERS",
        ".gitignore",
    ]

    for security_file in security_files:
        file_path = Path(security_file)
        assert file_path.exists(), f"Required security file missing: {security_file}"
        assert file_path.is_file(), f"Path is not a file: {security_file}"


def test_python_config_exists():
    """Test that Python configuration files exist."""
    config_files = [
        "pyproject.toml",
        "requirements.txt",
        "requirements-dev.txt",
    ]

    for config_file in config_files:
        file_path = Path(config_file)
        assert file_path.exists(), f"Required config file missing: {config_file}"
        assert file_path.is_file(), f"Path is not a file: {config_file}"


def test_main_module_exists():
    """Test that main module exists."""
    main_module = Path("src/main.py")
    assert main_module.exists(), "Main module missing: src/main.py"
    assert main_module.is_file(), "Path is not a file: src/main.py"


@pytest.mark.slow
def test_main_module_runs():
    """Test that main module can be imported and run."""
    try:
        from src import main

        # Don't actually run main() as it may have side effects
        assert hasattr(main, "main"), "main() function not found in src.main"
    except ImportError as e:
        pytest.fail(f"Failed to import src.main: {e}")


# Marker examples for future tests
@pytest.mark.integration
def test_integration_placeholder():
    """Placeholder for integration tests (to be implemented)."""
    pass


@pytest.mark.gpu
def test_gpu_placeholder():
    """Placeholder for GPU tests (to be implemented in Task 080)."""
    pass


@pytest.mark.heavy
def test_heavy_placeholder():
    """Placeholder for heavy computational tests (to be implemented)."""
    pass
