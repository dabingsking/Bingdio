"""Tests for playlist tool."""

import pytest
import os
import sys
import time
import tempfile
import sqlite3
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import tools.playlist as playlist

# Error code constants
E303 = playlist.E303
ERR_CONFIG_MISSING = playlist.ERR_CONFIG_MISSING
ERR_CONFIG_INVALID = playlist.ERR_CONFIG_INVALID
ERR_DB_ERROR = playlist.ERR_DB_ERROR
ERR_INVALID_PARAM = playlist.ERR_INVALID_PARAM


class TestConfigLoading:
    def test_config_missing(self):
        with patch.dict(os.environ, {"PLAYLIST_CONFIG_PATH": "/nonexistent/path.yaml"}):
            playlist._CONFIG_CACHE = None
            try:
                result = playlist._load_config()
                pytest.fail("Should raise FileNotFoundError")
            except FileNotFoundError:
                pass

    def test_config_cached(self):
        config = {"database": {"path": "test.db"}}
        playlist._CONFIG_CACHE = config
        result = playlist._load_config()
        assert result == config

    def test_config_env_var(self):
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False, mode="w") as f:
            f.write("database:\n  path: /tmp/test.db\n")
            f.flush()
            path = f.name

        try:
            playlist._CONFIG_CACHE = None
            with patch.dict(os.environ, {"PLAYLIST_CONFIG_PATH": path}):
                result = playlist._load_config()
                assert result["database"]["path"] == "/tmp/test.db"
        finally:
            os.unlink(path)
            playlist._CONFIG_CACHE = None


class TestDbPath:
    def test_db_path_from_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_file = os.path.join(tmpdir, "test.db")
            with patch.object(playlist, "_load_config", return_value={"database": {"path": db_file}}):
                path = playlist._get_db_path()
                assert path == db_file

    def test_db_path_relative(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_file = "test.db"
            with patch.object(playlist, "_load_config", return_value={"database": {"path": db_file}}):
                with patch.object(playlist, "_CONFIG_CACHE", None):
                    pass
            playlist._CONFIG_CACHE = {"database": {"path": db_file}}
            path = playlist._get_db_path()
            assert path.endswith("test.db")

    def test_db_path_creates_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_dir = os.path.join(tmpdir, "subdir", "nested")
            db_file = os.path.join(db_dir, "test.db")
            playlist._CONFIG_CACHE = {"database": {"path": db_file}}
            path = playlist._get_db_path()
            assert os.path.exists(os.path.dirname(path))


class TestInitTables:
    def test_init_tables_creates_tables(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            conn = sqlite3.connect(db_path)
            playlist._init_tables(conn)
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [r[0] for r in cur.fetchall()]
            assert "mood_logs" in tables
            assert "play_history" in tables
            conn.close()

    def test_init_tables_creates_indexes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            conn = sqlite3.connect(db_path)
            playlist._init_tables(conn)
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='index'")
            indexes = [r[0] for r in cur.fetchall()]
            assert any("idx_mood_created" in i for i in indexes)
            assert any("idx_history_played" in i for i in indexes)
            conn.close()


class TestErrorHelper:
    def test_error_helper(self):
        result = playlist._error("E30301", "test message")
        assert result["code"] == "E30301"
        assert result["msg"] == "test message"


class TestDt24hAgo:
    def test_returns_timestamp_24h_ago(self):
        result = playlist._dt_24h_ago()
        dt = datetime.strptime(result, "%Y-%m-%d %H:%M:%S")
        expected = datetime.now() - timedelta(hours=24)
        diff = abs((dt - expected).total_seconds())
        assert diff < 5


class TestAddMoodLog:
    def setup_method(self):
        self._cleanup()

    def teardown_method(self):
        self._cleanup()

    def _cleanup(self):
        playlist._CONFIG_CACHE = None
        if hasattr(self, "_tmpdir") and self._tmpdir:
            import shutil
            shutil.rmtree(self._tmpdir, ignore_errors=True)

    def _make_config(self, tmpdir):
        self._tmpdir = tmpdir
        db_path = os.path.join(tmpdir, "test.db")
        return {"database": {"path": db_path}}

    def test_config_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = self._make_config(tmpdir)
            with patch.object(playlist, "_load_config", side_effect=Exception("no config")):
                result = playlist.add_mood_log("happy", 0.8)
                assert result["code"] == ERR_CONFIG_MISSING

    def test_invalid_mood_score_non_numeric(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = self._make_config(tmpdir)
            with patch.object(playlist, "_load_config", return_value=cfg):
                result = playlist.add_mood_log("happy", "not_a_number")
                assert result["code"] == ERR_INVALID_PARAM

    def test_invalid_mood_score_out_of_range(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = self._make_config(tmpdir)
            with patch.object(playlist, "_load_config", return_value=cfg):
                result = playlist.add_mood_log("happy", 2.0)
                assert result["code"] == ERR_INVALID_PARAM

    def test_invalid_mood_score_negative_range(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = self._make_config(tmpdir)
            with patch.object(playlist, "_load_config", return_value=cfg):
                result = playlist.add_mood_log("sad", -2.0)
                assert result["code"] == ERR_INVALID_PARAM

    def test_add_mood_log_success(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = self._make_config(tmpdir)
            with patch.object(playlist, "_load_config", return_value=cfg):
                result = playlist.add_mood_log("happy", 0.8, context="test context", song_playing="song A")
                assert result["code"] == "0"
                assert "id" in result

    def test_add_mood_log_minimal(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = self._make_config(tmpdir)
            with patch.object(playlist, "_load_config", return_value=cfg):
                result = playlist.add_mood_log("neutral", 0.0)
                assert result["code"] == "0"
                assert "id" in result

    def test_add_mood_log_db_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = self._make_config(tmpdir)
            with patch.object(playlist, "_load_config", return_value=cfg):
                with patch.object(playlist, "_get_conn", side_effect=sqlite3.Error("disk error")):
                    result = playlist.add_mood_log("happy", 0.5)
                    assert result["code"] == ERR_DB_ERROR


class TestGetMoodLogs:
    def setup_method(self):
        playlist._CONFIG_CACHE = None

    def teardown_method(self):
        playlist._CONFIG_CACHE = None

    def test_get_mood_logs_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            cfg = {"database": {"path": db_path}}
            with patch.object(playlist, "_load_config", return_value=cfg):
                result = playlist.get_mood_logs()
                assert result["code"] == "0"
                assert result["data"] == []

    def test_get_mood_logs_with_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            cfg = {"database": {"path": db_path}}
            conn = sqlite3.connect(db_path)
            conn.close()
            with patch.object(playlist, "_load_config", return_value=cfg):
                playlist.add_mood_log("happy", 0.8, context="test context", song_playing="song A")
                result = playlist.get_mood_logs()
                assert result["code"] == "0"
                assert len(result["data"]) == 1
                assert result["data"][0]["mood_label"] == "happy"

    def test_get_mood_logs_limit_offset(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            cfg = {"database": {"path": db_path}}
            with patch.object(playlist, "_load_config", return_value=cfg):
                for i in range(5):
                    playlist.add_mood_log(f"mood_{i}", 0.5)
                result = playlist.get_mood_logs(limit=2, offset=1)
                assert result["code"] == "0"
                assert len(result["data"]) == 2

    def test_get_mood_logs_db_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            cfg = {"database": {"path": db_path}}
            with patch.object(playlist, "_load_config", return_value=cfg):
                with patch.object(playlist, "_get_conn", side_effect=sqlite3.Error("disk error")):
                    result = playlist.get_mood_logs()
                    assert result["code"] == ERR_DB_ERROR

    def test_dedup_24h(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            cfg = {"database": {"path": db_path}}
            with patch.object(playlist, "_load_config", return_value=cfg):
                playlist.add_mood_log("happy", 0.8, context="same_context", song_playing="same_song")
                result = playlist.get_mood_logs()
                assert result["code"] == "0"
                assert len(result["data"]) == 1


class TestDeleteMoodLog:
    def setup_method(self):
        playlist._CONFIG_CACHE = None

    def teardown_method(self):
        playlist._CONFIG_CACHE = None

    def test_delete_mood_log_success(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            cfg = {"database": {"path": db_path}}
            with patch.object(playlist, "_load_config", return_value=cfg):
                result = playlist.add_mood_log("happy", 0.8)
                log_id = result["id"]
                result = playlist.delete_mood_log(log_id)
                assert result["code"] == "0"
                assert result["deleted"] == 1

    def test_delete_mood_log_not_found(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            cfg = {"database": {"path": db_path}}

            with patch.object(playlist, "_load_config", return_value=cfg):
                result = playlist.delete_mood_log(9999)
                assert result["code"] == ERR_INVALID_PARAM

    def test_delete_mood_log_db_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            cfg = {"database": {"path": db_path}}
            with patch.object(playlist, "_load_config", return_value=cfg):
                with patch.object(playlist, "_get_conn", side_effect=sqlite3.Error("disk error")):
                    result = playlist.delete_mood_log(1)
                    assert result["code"] == ERR_DB_ERROR


class TestAddPlayHistory:
    def setup_method(self):
        playlist._CONFIG_CACHE = None

    def teardown_method(self):
        playlist._CONFIG_CACHE = None

    def test_config_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = {"database": {"path": os.path.join(tmpdir, "test.db")}}
            with patch.object(playlist, "_load_config", side_effect=Exception("no config")):
                result = playlist.add_play_history("song_001", "Test Song", artist="Test Artist")
                assert result["code"] == ERR_CONFIG_MISSING

    def test_missing_song_id(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = {"database": {"path": os.path.join(tmpdir, "test.db")}}
            with patch.object(playlist, "_load_config", return_value=cfg):
                result = playlist.add_play_history("", "Test Song")
                assert result["code"] == ERR_INVALID_PARAM

    def test_missing_song_name(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = {"database": {"path": os.path.join(tmpdir, "test.db")}}
            with patch.object(playlist, "_load_config", return_value=cfg):
                result = playlist.add_play_history("song_001", "")
                assert result["code"] == ERR_INVALID_PARAM

    def test_add_play_history_success(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            cfg = {"database": {"path": db_path}}
            with patch.object(playlist, "_load_config", return_value=cfg):
                result = playlist.add_play_history("song_001", "Test Song", artist="Test Artist", source="local")
                assert result["code"] == "0"
                assert "id" in result

    def test_add_play_history_db_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            cfg = {"database": {"path": db_path}}
            with patch.object(playlist, "_load_config", return_value=cfg):
                with patch.object(playlist, "_get_conn", side_effect=sqlite3.Error("disk error")):
                    result = playlist.add_play_history("song_001", "Test Song")
                    assert result["code"] == ERR_DB_ERROR


class TestGetPlayHistory:
    def setup_method(self):
        playlist._CONFIG_CACHE = None

    def teardown_method(self):
        playlist._CONFIG_CACHE = None

    def test_get_play_history_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            cfg = {"database": {"path": db_path}}
            with patch.object(playlist, "_load_config", return_value=cfg):
                result = playlist.get_play_history()
                assert result["code"] == "0"
                assert result["data"] == []

    def test_get_play_history_with_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            cfg = {"database": {"path": db_path}}
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            playlist._init_tables(conn)
            cur.execute(
                "INSERT INTO play_history (song_id, song_name, artist, source) VALUES (?, ?, ?, ?)",
                ("song_001", "Test Song", "Test Artist", "local")
            )
            conn.commit()
            conn.close()

            with patch.object(playlist, "_load_config", return_value=cfg):
                with patch.object(playlist, "_init_tables"):
                    result = playlist.get_play_history()
                    assert result["code"] == "0"
                    assert len(result["data"]) == 1
                    assert result["data"][0]["song_name"] == "Test Song"

    def test_get_play_history_limit_offset(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            cfg = {"database": {"path": db_path}}
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            playlist._init_tables(conn)
            for i in range(5):
                cur.execute(
                    "INSERT INTO play_history (song_id, song_name) VALUES (?, ?)",
                    (f"song_{i:03d}", f"Song {i}")
                )
            conn.commit()
            conn.close()

            with patch.object(playlist, "_load_config", return_value=cfg):
                with patch.object(playlist, "_init_tables"):
                    result = playlist.get_play_history(limit=2, offset=1)
                    assert result["code"] == "0"
                    assert len(result["data"]) == 2

    def test_get_play_history_db_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            cfg = {"database": {"path": db_path}}
            with patch.object(playlist, "_load_config", return_value=cfg):
                with patch.object(playlist, "_get_conn", side_effect=sqlite3.Error("disk error")):
                    result = playlist.get_play_history()
                    assert result["code"] == ERR_DB_ERROR

    def test_dedup_24h_same_song_id(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            cfg = {"database": {"path": db_path}}
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            playlist._init_tables(conn)
            for _ in range(3):
                cur.execute(
                    "INSERT INTO play_history (song_id, song_name) VALUES (?, ?)",
                    ("song_duplicate", "Same Song")
                )
            conn.commit()
            conn.close()

            with patch.object(playlist, "_load_config", return_value=cfg):
                with patch.object(playlist, "_init_tables"):
                    result = playlist.get_play_history()
                    assert result["code"] == "0"
                    assert len(result["data"]) == 1
                    assert result["data"][0]["song_id"] == "song_duplicate"


class TestDeletePlayHistory:
    def setup_method(self):
        playlist._CONFIG_CACHE = None

    def teardown_method(self):
        playlist._CONFIG_CACHE = None

    def test_delete_play_history_success(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            cfg = {"database": {"path": db_path}}
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            playlist._init_tables(conn)
            cur.execute(
                "INSERT INTO play_history (song_id, song_name) VALUES (?, ?)",
                ("song_001", "Test Song")
            )
            hist_id = cur.lastrowid
            conn.commit()
            conn.close()

            with patch.object(playlist, "_load_config", return_value=cfg):
                with patch.object(playlist, "_init_tables"):
                    result = playlist.delete_play_history(hist_id)
                    assert result["code"] == "0"
                assert result["deleted"] == 1

    def test_delete_play_history_not_found(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            cfg = {"database": {"path": db_path}}

            with patch.object(playlist, "_load_config", return_value=cfg):
                result = playlist.delete_play_history(9999)
                assert result["code"] == ERR_INVALID_PARAM

    def test_delete_play_history_db_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            cfg = {"database": {"path": db_path}}
            with patch.object(playlist, "_load_config", return_value=cfg):
                with patch.object(playlist, "_get_conn", side_effect=sqlite3.Error("disk error")):
                    result = playlist.delete_play_history(1)
                    assert result["code"] == ERR_DB_ERROR