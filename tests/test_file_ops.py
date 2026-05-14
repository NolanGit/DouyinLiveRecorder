# -*- encoding: utf-8 -*-
"""Tests for :mod:`src.app.file_ops`."""
from src.app import file_ops, state


def test_get_no_proxy_env_strips_proxy_keys(monkeypatch):
    monkeypatch.setenv("HTTP_PROXY", "http://x:1")
    monkeypatch.setenv("https_proxy", "http://y:2")
    env = file_ops.get_no_proxy_env()
    assert "HTTP_PROXY" not in env
    assert "https_proxy" not in env


def test_update_file_replaces_in_place(tmp_path):
    p = tmp_path / "u.ini"
    p.write_text("https://a/1\nhttps://b/2\n", encoding=state.text_encoding)
    new = file_ops.update_file(str(p), "https://a/1", "https://a/1?x=y")
    assert new == "https://a/1?x=y"
    content = p.read_text(encoding=state.text_encoding)
    assert "https://a/1?x=y" in content
    assert "https://b/2" in content


def test_update_file_noop_when_equal(tmp_path):
    p = tmp_path / "u.ini"
    p.write_text("aa\nbb\n", encoding=state.text_encoding)
    res = file_ops.update_file(str(p), "aa", "aa")
    assert res == "aa"


def test_delete_line_removes_first_match(tmp_path):
    p = tmp_path / "u.ini"
    p.write_text("alpha\nbeta\ngamma\n", encoding=state.text_encoding)
    file_ops.delete_line(str(p), "beta")
    txt = p.read_text(encoding=state.text_encoding)
    assert "beta" not in txt
    assert "alpha" in txt and "gamma" in txt


def test_backup_file_keeps_limit(tmp_path):
    src = tmp_path / "config.ini"
    src.write_text("k=v", encoding=state.text_encoding)
    backup_dir = tmp_path / "bak"
    for _ in range(8):
        file_ops.backup_file(str(src), str(backup_dir), limit_counts=3)
    backups = [n for n in backup_dir.iterdir() if n.name.startswith("config.ini")]
    assert len(backups) <= 3
