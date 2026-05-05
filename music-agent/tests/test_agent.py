"""Tests for agent module."""

import pytest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import agent


class TestDetectIntent:
    def test_play_intent(self):
        assert agent._detect_intent("播放一首歌") == "play"
        assert agent._detect_intent("来首歌") == "play"

    def test_weather_intent(self):
        assert agent._detect_intent("今天天气怎么样") == "weather"
        assert agent._detect_intent("气温多少") == "weather"

    def test_recommend_intent(self):
        assert agent._detect_intent("给我推荐几首歌") == "recommend"
        assert agent._detect_intent("想听歌") == "recommend"

    def test_mood_intent(self):
        assert agent._detect_intent("今天心情不好") == "mood"
        assert agent._detect_intent("工作有点累") == "mood"

    def test_exit_intent(self):
        assert agent._detect_intent("quit") == "exit"
        assert agent._detect_intent("exit") == "exit"

    def test_chat_intent(self):
        assert agent._detect_intent("你好啊") == "chat"
        assert agent._detect_intent("今天吃了什么") == "chat"


class TestRecommend:
    def test_recommend_returns_list(self):
        with patch.object(agent, "_call_llm", return_value="[]"):
            result = agent.recommend()
            assert isinstance(result, list)

    def test_recommend_with_moods(self):
        with patch.object(agent, "_call_llm", return_value='[{"name":"test","artist":"t","reason":"r"}]'):
            result = agent.recommend(["happy"])
            assert len(result) == 1
            assert result[0]["name"] == "test"

    def test_recommend_fallback(self):
        with patch.object(agent, "_call_llm", side_effect=Exception("fail")):
            result = agent.recommend()
            assert isinstance(result, list)
            assert len(result) > 0


class TestChat:
    def test_chat_returns_string(self):
        with patch.object(agent, "_call_llm", return_value="你好！"):
            result = agent.chat("你好")
            assert isinstance(result, str)
            assert result == "你好！"

    def test_chat_missing_key(self):
        with patch.dict(os.environ, {"LLM_API_KEY": ""}, clear=False):
            with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
                with patch.object(agent, "LLM_API_KEY", ""):
                    try:
                        agent.chat("hello")
                        pytest.fail("Should raise ValueError")
                    except ValueError as e:
                        assert "E401" in str(e)
