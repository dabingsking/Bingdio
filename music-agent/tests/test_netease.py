"""Tests for netease tool."""

import pytest
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools.netease import (
    search_song, get_url, get_lyric, get_playlist, play_song,
    E201, E202
)


class TestSearchSong:
    def test_config_missing(self):
        with patch("tools.netease._get_base_url", side_effect=Exception("no config")):
            result = search_song("test")
        assert result["code"] == E201
        assert "Configuration error" in result["msg"]

    def test_api_request_failed(self):
        import requests
        with patch("tools.netease._get_base_url", return_value="https://api.no0a.cn/api/cloudmusic"):
            with patch("requests.get", side_effect=requests.RequestException("network error")):
                result = search_song("test")
        assert result["code"] == E202
        assert "API request failed" in result["msg"]

    def test_api_error_response(self):
        with patch("tools.netease._get_base_url", return_value="https://api.no0a.cn/api/cloudmusic"):
            with patch("requests.get") as mock_get:
                mock_resp = MagicMock()
                mock_resp.json.return_value = {"code": 400}
                mock_resp.raise_for_status = MagicMock()
                mock_get.return_value = mock_resp
                result = search_song("test")
        assert result["code"] == E202
        assert "API error" in result["msg"]

    def test_success(self):
        with patch("tools.netease._get_base_url", return_value="https://api.no0a.cn/api/cloudmusic"):
            with patch("requests.get") as mock_get:
                mock_resp = MagicMock()
                mock_resp.json.return_value = {
                    "code": 200,
                    "result": {
                        "songs": [
                            {
                                "id": 12345,
                                "name": "Test Song",
                                "artists": [{"name": "Artist1"}],
                                "album": {"name": "Album1"},
                                "duration": 180000,
                            }
                        ]
                    }
                }
                mock_resp.raise_for_status = MagicMock()
                mock_get.return_value = mock_resp
                result = search_song("test")
        assert result["code"] == "0"
        assert len(result["songs"]) == 1
        assert result["songs"][0]["name"] == "Test Song"
        assert result["songs"][0]["artists"] == ["Artist1"]


class TestGetUrl:
    def test_config_missing(self):
        with patch("tools.netease._get_base_url", side_effect=Exception("no config")):
            result = get_url(12345)
        assert result["code"] == E201

    def test_api_request_failed(self):
        import requests
        with patch("tools.netease._get_base_url", return_value="https://api.no0a.cn/api/cloudmusic"):
            with patch("requests.get", side_effect=requests.RequestException("network error")):
                result = get_url(12345)
        assert result["code"] == E202

    def test_api_error_response(self):
        with patch("tools.netease._get_base_url", return_value="https://api.no0a.cn/api/cloudmusic"):
            with patch("requests.get") as mock_get:
                mock_resp = MagicMock()
                mock_resp.json.return_value = {"code": 400}
                mock_resp.raise_for_status = MagicMock()
                mock_get.return_value = mock_resp
                result = get_url(12345)
        assert result["code"] == E202

    def test_empty_url_list(self):
        with patch("tools.netease._get_base_url", return_value="https://api.no0a.cn/api/cloudmusic"):
            with patch("requests.get") as mock_get:
                mock_resp = MagicMock()
                mock_resp.json.return_value = {"code": 200, "data": []}
                mock_resp.raise_for_status = MagicMock()
                mock_get.return_value = mock_resp
                result = get_url(12345)
        assert result["code"] == E202
        assert "No URL" in result["msg"]

    def test_success(self):
        with patch("tools.netease._get_base_url", return_value="https://api.no0a.cn/api/cloudmusic"):
            with patch("requests.get") as mock_get:
                mock_resp = MagicMock()
                mock_resp.json.return_value = {
                    "code": 200,
                    "data": [{"url": "https://example.com/song.mp3"}]
                }
                mock_resp.raise_for_status = MagicMock()
                mock_get.return_value = mock_resp
                result = get_url(12345)
        assert result["code"] == "0"
        assert result["url"] == "https://example.com/song.mp3"


class TestGetLyric:
    def test_config_missing(self):
        with patch("tools.netease._get_base_url", side_effect=Exception("no config")):
            result = get_lyric(12345)
        assert result["code"] == E201

    def test_api_request_failed(self):
        import requests
        with patch("tools.netease._get_base_url", return_value="https://api.no0a.cn/api/cloudmusic"):
            with patch("requests.get", side_effect=requests.RequestException("network error")):
                result = get_lyric(12345)
        assert result["code"] == E202

    def test_api_error_response(self):
        with patch("tools.netease._get_base_url", return_value="https://api.no0a.cn/api/cloudmusic"):
            with patch("requests.get") as mock_get:
                mock_resp = MagicMock()
                mock_resp.json.return_value = {"code": 400}
                mock_resp.raise_for_status = MagicMock()
                mock_get.return_value = mock_resp
                result = get_lyric(12345)
        assert result["code"] == E202

    def test_success(self):
        with patch("tools.netease._get_base_url", return_value="https://api.no0a.cn/api/cloudmusic"):
            with patch("requests.get") as mock_get:
                mock_resp = MagicMock()
                mock_resp.json.return_value = {
                    "code": 200,
                    "lrc": {"lyric": "[00:00.00]Test lyric"}
                }
                mock_resp.raise_for_status = MagicMock()
                mock_get.return_value = mock_resp
                result = get_lyric(12345)
        assert result["code"] == "0"
        assert result["lyric"] == "[00:00.00]Test lyric"


class TestGetPlaylist:
    def test_config_missing(self):
        with patch("tools.netease._get_base_url", side_effect=Exception("no config")):
            result = get_playlist(12345)
        assert result["code"] == E201

    def test_api_request_failed(self):
        import requests
        with patch("tools.netease._get_base_url", return_value="https://api.no0a.cn/api/cloudmusic"):
            with patch("requests.get", side_effect=requests.RequestException("network error")):
                result = get_playlist(12345)
        assert result["code"] == E202

    def test_api_error_response(self):
        with patch("tools.netease._get_base_url", return_value="https://api.no0a.cn/api/cloudmusic"):
            with patch("requests.get") as mock_get:
                mock_resp = MagicMock()
                mock_resp.json.return_value = {"code": 400}
                mock_resp.raise_for_status = MagicMock()
                mock_get.return_value = mock_resp
                result = get_playlist(12345)
        assert result["code"] == E202

    def test_success(self):
        with patch("tools.netease._get_base_url", return_value="https://api.no0a.cn/api/cloudmusic"):
            with patch("requests.get") as mock_get:
                mock_resp = MagicMock()
                mock_resp.json.return_value = {
                    "code": 200,
                    "playlist": {
                        "id": 12345,
                        "name": "Test Playlist",
                        "description": "A test playlist",
                        "tracks": [
                            {
                                "id": 1,
                                "name": "Song1",
                                "ar": [{"name": "Artist1"}],
                                "al": {"name": "Album1"}
                            }
                        ]
                    }
                }
                mock_resp.raise_for_status = MagicMock()
                mock_get.return_value = mock_resp
                result = get_playlist(12345)
        assert result["code"] == "0"
        assert result["playlist"]["name"] == "Test Playlist"
        assert len(result["playlist"]["tracks"]) == 1
        assert result["playlist"]["tracks"][0]["name"] == "Song1"


class TestPlaySong:
    def test_get_url_fails(self):
        with patch("tools.netease._get_base_url", return_value="https://api.no0a.cn/api/cloudmusic"):
            with patch("requests.get") as mock_get:
                mock_resp = MagicMock()
                mock_resp.json.return_value = {"code": 400}
                mock_resp.raise_for_status = MagicMock()
                mock_get.return_value = mock_resp
                result = play_song(12345)
        assert result["code"] == E202

    def test_empty_url(self):
        with patch("tools.netease._get_base_url", return_value="https://api.no0a.cn/api/cloudmusic"):
            with patch("requests.get") as mock_get:
                mock_resp = MagicMock()
                mock_resp.json.return_value = {"code": 200, "data": [{"url": ""}]}
                mock_resp.raise_for_status = MagicMock()
                mock_get.return_value = mock_resp
                result = play_song(12345)
        assert result["code"] == E202
        assert "Empty song URL" in result["msg"]

    def test_ffmpeg_not_found(self):
        with patch("tools.netease._get_base_url", return_value="https://api.no0a.cn/api/cloudmusic"):
            with patch("requests.get") as mock_get:
                mock_resp = MagicMock()
                mock_resp.json.return_value = {
                    "code": 200,
                    "data": [{"url": "https://example.com/song.mp3"}]
                }
                mock_resp.raise_for_status = MagicMock()
                mock_get.return_value = mock_resp

                with patch("subprocess.run", side_effect=FileNotFoundError()):
                    result = play_song(12345)
        assert result["code"] == E202
        assert "FFmpeg" in result["msg"]

    def test_playback_success(self):
        with patch("tools.netease._get_base_url", return_value="https://api.no0a.cn/api/cloudmusic"):
            with patch("requests.get") as mock_get:
                mock_resp = MagicMock()
                mock_resp.json.return_value = {
                    "code": 200,
                    "data": [{"url": "https://example.com/song.mp3"}]
                }
                mock_resp.raise_for_status = MagicMock()
                mock_get.return_value = mock_resp

                with patch("subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock()
                    result = play_song(12345)
        assert result["code"] == "0"
        mock_run.assert_called_once()
