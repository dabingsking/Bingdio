"""Tests for weather tool."""

import pytest
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools.weather import get_weather, E101, E102


class TestGetWeather:
    def test_config_missing(self):
        with patch("tools.weather._load_config", side_effect=Exception("no config")):
            result = get_weather()
        assert result["code"] == E101
        assert "Failed to load weather config" in result["msg"]

    def test_missing_host_key_location(self):
        with patch("tools.weather._load_config", return_value={"weather": {}}):
            result = get_weather()
        assert result["code"] == E101
        assert "Missing weather config" in result["msg"]

    def test_api_request_failed(self):
        import requests
        with patch("tools.weather._load_config", return_value={
            "weather": {"host": "h", "key": "k", "location": "l"}
        }):
            with patch("requests.get", side_effect=requests.RequestException("network error")):
                result = get_weather()
        assert result["code"] == E102
        assert "API request failed" in result["msg"]

    def test_api_error_response(self):
        with patch("tools.weather._load_config", return_value={
            "weather": {"host": "h", "key": "k", "location": "l"}
        }):
            with patch("requests.get") as mock_get:
                mock_resp = MagicMock()
                mock_resp.json.return_value = {"code": "401", "now": {}}
                mock_resp.raise_for_status = MagicMock()
                mock_get.return_value = mock_resp
                result = get_weather()
        assert result["code"] == E102
        assert "API error" in result["msg"]

    def test_success(self):
        with patch("tools.weather._load_config", return_value={
            "weather": {"host": "h", "key": "k", "location": "l"}
        }):
            with patch("requests.get") as mock_get:
                mock_resp = MagicMock()
                mock_resp.json.return_value = {
                    "code": "200",
                    "now": {
                        "temp": "22",
                        "text": "晴",
                        "windSpeed": "3级",
                        "humidity": "65%",
                    }
                }
                mock_resp.raise_for_status = MagicMock()
                mock_get.return_value = mock_resp
                result = get_weather()
        assert result["code"] == "0"
        assert result["temp"] == "22"
        assert result["text"] == "晴"
        assert result["wind_speed"] == "3级"
        assert result["humidity"] == "65%"
