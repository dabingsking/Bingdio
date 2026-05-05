"""Tests for TTS tool."""

import pytest
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools.tts import speak_text, E301, E302


class TestSpeakText:
    def test_config_missing(self):
        with patch("tools.tts._load_config", side_effect=Exception("no config")):
            result = speak_text("hello")
        assert result["code"] == E301
        assert "Failed to load tts config" in result["msg"]

    def test_missing_base_url_endpoint(self):
        with patch("tools.tts._load_config", return_value={"tts": {}}):
            result = speak_text("hello")
        assert result["code"] == E301
        assert "Missing tts config" in result["msg"]

    def test_api_request_failed(self):
        import requests
        with patch("tools.tts._load_config", return_value={
            "tts": {"base_url": "https://api.xiaomimimo.com/v1", "endpoint": "/audio/speech"}
        }):
            with patch("requests.post", side_effect=requests.RequestException("network error")):
                result = speak_text("hello")
        assert result["code"] == E302
        assert "API request failed" in result["msg"]

    def test_api_error_response(self):
        import requests
        with patch("tools.tts._load_config", return_value={
            "tts": {"base_url": "https://api.xiaomimimo.com/v1", "endpoint": "/audio/speech"}
        }):
            with patch("requests.post") as mock_post:
                mock_resp = MagicMock()
                mock_resp.raise_for_status = MagicMock()
                mock_resp.headers = {"Content-Type": "application/json"}
                mock_resp.json.return_value = {"error": "bad request"}
                mock_post.return_value = mock_resp
                result = speak_text("hello")
        assert result["code"] == E302
        assert "Unexpected response content type" in result["msg"]

    def test_success(self):
        with patch("tools.tts._load_config", return_value={
            "tts": {"base_url": "https://api.xiaomimimo.com/v1", "endpoint": "/audio/speech"}
        }):
            with patch("requests.post") as mock_post:
                mock_resp = MagicMock()
                mock_resp.raise_for_status = MagicMock()
                mock_resp.headers = {"Content-Type": "audio/mpeg"}
                mock_resp.content = b"fake mp3 data"
                mock_post.return_value = mock_resp
                with patch("tools.tts.uuid.uuid4", return_value=MagicMock(hex="testuuid")):
                    result = speak_text("hello")
        assert result["code"] == "0"
        assert "tmp/tts_testuuid.mp3" in result["mp3_path"]
        assert os.path.exists(result["mp3_path"])
        with open(result["mp3_path"], "rb") as f:
            assert f.read() == b"fake mp3 data"
        os.remove(result["mp3_path"])