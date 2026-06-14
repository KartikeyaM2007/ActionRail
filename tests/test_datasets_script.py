"""
Tests for scripts/download_sample_datasets.py.

These tests never call the real Kaggle network. They use temp directories
and monkeypatching to simulate credential/package presence.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPT = _REPO_ROOT / "scripts" / "download_sample_datasets.py"


def _load_module(monkeypatch=None, env_overrides: dict | None = None):
    """Load the script as a module each time so global state is fresh."""
    if env_overrides and monkeypatch:
        for k, v in env_overrides.items():
            monkeypatch.setenv(k, v)
    spec = importlib.util.spec_from_file_location("download_sample_datasets", _SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# 1. --check-kaggle exits cleanly when credentials missing + prints setup
# ---------------------------------------------------------------------------

def test_check_kaggle_no_credentials(tmp_path, monkeypatch, capsys):
    """With no credentials at any standard location, --check-kaggle prints setup instructions."""
    # Point USERPROFILE to an empty temp dir so the official Windows path is absent.
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    # Patch home() to the same temp dir.
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))

    mod = _load_module()
    # Override credential detection to use the patched environment.
    # Re-patch inside the module's own namespace.
    original_detect = mod.detect_kaggle_credentials

    def _no_creds():
        from scripts.download_sample_datasets import KaggleCredStatus
        return KaggleCredStatus(found=False, path=None, is_project_local=False, warning=None)

    monkeypatch.setattr(mod, "detect_kaggle_credentials", _no_creds)

    mod.check_kaggle()
    out = capsys.readouterr().out
    assert "Credentials found" in out
    assert "NO" in out
    assert "mkdir" in out.lower() or "USERPROFILE" in out or "kaggle" in out.lower()
    # Must never print anything that looks like a JSON secret value.
    assert '"key"' not in out
    assert '"username"' not in out


# ---------------------------------------------------------------------------
# 2. Project-local kaggle/kaggle.json detection with a fake credential
# ---------------------------------------------------------------------------

def test_detect_project_local_credential(tmp_path, monkeypatch):
    """detect_kaggle_credentials() finds kaggle/kaggle.json in the project-local dir."""
    # Ensure the official locations don't exist so we fall through to local.
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))

    mod = _load_module()

    # Create fake local credential
    local_kaggle_dir = tmp_path / "fake_repo" / "kaggle"
    local_kaggle_dir.mkdir(parents=True)
    fake_cred = local_kaggle_dir / "kaggle.json"
    fake_cred.write_text(json.dumps({"username": "fakeuser", "key": "fakekey"}), encoding="utf-8")

    # Patch _REPO_ROOT in the loaded module to point at fake_repo
    monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path / "fake_repo")

    cred = mod.detect_kaggle_credentials()
    assert cred.found is True
    assert cred.is_project_local is True
    assert cred.path is not None
    assert cred.warning is not None
    assert "never be committed" in cred.warning


# ---------------------------------------------------------------------------
# 3. .gitignore protects kaggle.json
# ---------------------------------------------------------------------------

def test_gitignore_protects_kaggle_credentials():
    gitignore = _REPO_ROOT / ".gitignore"
    content = gitignore.read_text(encoding="utf-8")
    # At least one of these patterns must be present
    assert "kaggle/" in content or "kaggle.json" in content or "**/kaggle.json" in content


# ---------------------------------------------------------------------------
# 4. --source kaggle-invoices --instructions prints the dataset command
# ---------------------------------------------------------------------------

def test_kaggle_instructions_prints_command(capsys):
    mod = _load_module()
    mod.print_kaggle_instructions()
    out = capsys.readouterr().out
    assert "kaggle datasets download" in out
    assert "osamahosamabdellatif/high-quality-invoice-images-for-ocr" in out
    assert "kaggle-invoices" in out or "data/datasets" in out


# ---------------------------------------------------------------------------
# 5. Unknown source gives readable error (via argparse choices)
# ---------------------------------------------------------------------------

def test_unknown_source_fails_cleanly(monkeypatch, capsys):
    mod = _load_module()
    with pytest.raises(SystemExit) as exc_info:
        monkeypatch.setattr(sys, "argv", ["prog", "--source", "totally_unknown_source"])
        mod.main()
    # argparse exits with code 2 for invalid choices
    assert exc_info.value.code in (1, 2)


# ---------------------------------------------------------------------------
# 6. --source kaggle-invoices --download without package doesn't stack trace
# ---------------------------------------------------------------------------

def test_kaggle_download_no_package_exits_cleanly(monkeypatch, capsys):
    """When the kaggle package is absent, the script exits with a clear message."""
    mod = _load_module()

    # Make the package check return False
    monkeypatch.setattr(mod, "kaggle_package_available", lambda: False)

    with pytest.raises(SystemExit) as exc_info:
        mod.download_kaggle_invoices()

    out = capsys.readouterr().out
    assert "not installed" in out.lower() or "kaggle" in out.lower()
    # Must exit non-zero, not zero
    assert exc_info.value.code != 0


def test_kaggle_download_no_credentials_exits_cleanly(monkeypatch, capsys):
    """When credentials are absent (but package present), the script exits with a clear message."""
    mod = _load_module()

    monkeypatch.setattr(mod, "kaggle_package_available", lambda: True)

    from scripts.download_sample_datasets import KaggleCredStatus

    monkeypatch.setattr(
        mod,
        "detect_kaggle_credentials",
        lambda: KaggleCredStatus(found=False, path=None, is_project_local=False, warning=None),
    )

    with pytest.raises(SystemExit) as exc_info:
        mod.download_kaggle_invoices()

    out = capsys.readouterr().out
    assert "credentials" in out.lower() or "kaggle.json" in out.lower()
    assert exc_info.value.code != 0
