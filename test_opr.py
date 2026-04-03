"""Tests for PLTR.OPR - Operation Reporting Tool"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import opr


@pytest.fixture(autouse=True)
def tmp_storage(tmp_path, monkeypatch):
    storage = tmp_path / "test_opr.json"
    monkeypatch.setattr(opr, "STORAGE_FILE", storage)
    return storage


def run(*args):
    parser = opr.build_parser()
    parsed = parser.parse_args(list(args))
    return parsed.func(parsed)


class TestCreate:
    def test_creates_report(self, tmp_storage):
        assert run("create", "Test operation") == 0
        data = json.loads(tmp_storage.read_text())
        assert len(data["reports"]) == 1
        assert data["reports"][0]["title"] == "Test operation"
        assert data["reports"][0]["status"] == "open"
        assert data["reports"][0]["severity"] == "medium"
        assert data["reports"][0]["id"] == 1

    def test_creates_with_description_and_severity(self, tmp_storage):
        assert run("create", "Op report", "-d", "Some details", "-s", "high") == 0
        report = json.loads(tmp_storage.read_text())["reports"][0]
        assert report["description"] == "Some details"
        assert report["severity"] == "high"

    def test_increments_id(self, tmp_storage):
        run("create", "First")
        run("create", "Second")
        data = json.loads(tmp_storage.read_text())
        ids = [r["id"] for r in data["reports"]]
        assert ids == [1, 2]


class TestList:
    def test_empty(self, capsys):
        assert run("list") == 0
        assert "No reports found" in capsys.readouterr().out

    def test_lists_reports(self, capsys):
        run("create", "Alpha")
        run("create", "Beta")
        assert run("list") == 0
        out = capsys.readouterr().out
        assert "Alpha" in out
        assert "Beta" in out

    def test_filter_by_status(self, tmp_storage, capsys):
        run("create", "Alpha")
        run("create", "Beta")
        run("update", "2", "--status", "in_progress")
        capsys.readouterr()
        run("list", "--status", "open")
        out = capsys.readouterr().out
        assert "Alpha" in out
        assert "Beta" not in out


class TestShow:
    def test_show_existing(self, capsys):
        run("create", "My operation", "-d", "Details here", "-s", "critical")
        assert run("show", "1") == 0
        out = capsys.readouterr().out
        assert "My operation" in out
        assert "Details here" in out
        assert "critical" in out

    def test_show_missing(self, capsys):
        assert run("show", "99") == 1
        assert "not found" in capsys.readouterr().err


class TestUpdate:
    def test_update_title(self, tmp_storage):
        run("create", "Old title")
        assert run("update", "1", "-t", "New title") == 0
        report = json.loads(tmp_storage.read_text())["reports"][0]
        assert report["title"] == "New title"

    def test_update_status(self, tmp_storage):
        run("create", "Op")
        assert run("update", "1", "--status", "resolved") == 0
        report = json.loads(tmp_storage.read_text())["reports"][0]
        assert report["status"] == "resolved"

    def test_update_missing(self, capsys):
        assert run("update", "99", "--status", "closed") == 1
        assert "not found" in capsys.readouterr().err


class TestDelete:
    def test_delete_existing(self, tmp_storage):
        run("create", "To delete")
        assert run("delete", "1") == 0
        data = json.loads(tmp_storage.read_text())
        assert len(data["reports"]) == 0

    def test_delete_missing(self, capsys):
        assert run("delete", "99") == 1
        assert "not found" in capsys.readouterr().err


class TestSummary:
    def test_summary_empty(self, capsys):
        assert run("summary") == 0
        assert "Total reports: 0" in capsys.readouterr().out

    def test_summary_counts(self, capsys):
        run("create", "A")
        run("create", "B")
        run("update", "1", "--status", "resolved")
        assert run("summary") == 0
        out = capsys.readouterr().out
        assert "Total reports: 2" in out
        assert "open" in out
        assert "resolved" in out
