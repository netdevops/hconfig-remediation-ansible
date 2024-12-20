import pytest
import subprocess
from pathlib import Path

# Define paths to fixtures
FIXTURES_DIR = Path("tests/fixtures")
RUNNING_CONFIG = FIXTURES_DIR / "router1-running.conf"
GENERATED_CONFIG = FIXTURES_DIR / "router1-generated.conf"
TAG_RULES = FIXTURES_DIR / "tag_rules.yml"


def run_ansible_playbook(playbook_path, extra_vars=None):
    """Run an Ansible playbook."""
    cmd = [
        "ansible-playbook",
        str(playbook_path),
        "-i",
        "tests/fixtures/inventory.ini",
        "-vvvv",
    ]
    if extra_vars:
        cmd.extend(["--extra-vars", extra_vars])
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


@pytest.fixture
def setup_fixtures():
    """Ensure that required fixture files exist."""
    assert RUNNING_CONFIG.exists(), f"Missing fixture: {RUNNING_CONFIG}"
    assert GENERATED_CONFIG.exists(), f"Missing fixture: {GENERATED_CONFIG}"
    assert TAG_RULES.exists(), f"Missing fixture: {TAG_RULES}"


def test_remediation_config_without_tags(setup_fixtures):
    """Test remediation config generation without tags."""
    playbook_path = FIXTURES_DIR / "test_remediation.yml"
    returncode, stdout, stderr = run_ansible_playbook(playbook_path)
    assert returncode == 0, f"Playbook failed with error: {stderr}"
    remediation_path = FIXTURES_DIR / "router1-remediation.conf"
    assert remediation_path.exists(), f"Expected output not found: {remediation_path}"


def test_remediation_config_with_include_tags(setup_fixtures):
    """Test remediation config generation with include tags."""
    playbook_path = FIXTURES_DIR / "test_remediation_include_tags.yml"
    returncode, stdout, stderr = run_ansible_playbook(playbook_path)
    assert returncode == 0, f"Playbook failed with error: {stderr}"
    remediation_path = FIXTURES_DIR / "router1-remediation-with-include-tags.conf"
    assert remediation_path.exists(), f"Expected output not found: {remediation_path}"


def test_remediation_config_with_exclude_tags(setup_fixtures):
    """Test remediation config generation with exclude tags."""
    playbook_path = FIXTURES_DIR / "test_remediation_exclude_tags.yml"
    returncode, stdout, stderr = run_ansible_playbook(playbook_path)
    assert returncode == 0, f"Playbook failed with error: {stderr}"
    remediation_path = FIXTURES_DIR / "router1-remediation-with-exclude-tags.conf"
    assert remediation_path.exists(), f"Expected output not found: {remediation_path}"


def test_remediation_config_with_both_tags(setup_fixtures):
    """Test remediation config generation with both include and exclude tags."""
    playbook_path = FIXTURES_DIR / "test_remediation_both_tags.yml"
    returncode, stdout, stderr = run_ansible_playbook(playbook_path)
    assert returncode == 0, f"Playbook failed with error: {stderr}"
    remediation_path = FIXTURES_DIR / "router1-remediation.conf"
    assert remediation_path.exists(), f"Expected output not found: {remediation_path}"
