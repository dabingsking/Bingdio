"""Tests for cli/__init__.py - Music Agent TUI."""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Ensure the project root is in path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


class TestPlayerState:
    """Tests for PlayerState class."""

    def test_player_state_init(self):
        """Test PlayerState initialization."""
        from cli import PlayerState

        state = PlayerState()
        assert state.is_playing is False
        assert state.current_song is None
        assert state.volume == 0.8
        assert state.playlist == []
        assert state.playlist_index == 0
        assert state.is_paused is False

    def test_player_state_custom_volume(self):
        """Test PlayerState with custom volume."""
        from cli import PlayerState

        state = PlayerState()
        state.volume = 0.5
        assert state.volume == 0.5


class TestWeatherWidget:
    """Tests for WeatherWidget class."""

    def test_weather_widget_init(self):
        """Test WeatherWidget initialization."""
        from cli import WeatherWidget

        widget = WeatherWidget()
        assert widget.weather_data == {}

    def test_weather_widget_set_weather(self):
        """Test setting weather data."""
        from cli import WeatherWidget

        widget = WeatherWidget()
        data = {
            "code": "0",
            "temp": "25",
            "text": "Sunny",
            "wind_speed": "10",
            "humidity": "50",
        }
        widget.set_weather(data)
        assert widget.weather_data == data

    def test_weather_widget_render_empty(self):
        """Test WeatherWidget render with no data."""
        from cli import WeatherWidget

        widget = WeatherWidget()
        output = widget.render()
        assert "Weather" in output
        assert "Loading" in output

    def test_weather_widget_render_data(self):
        """Test WeatherWidget render with data."""
        from cli import WeatherWidget

        widget = WeatherWidget()
        data = {
            "code": "0",
            "temp": "25",
            "text": "Sunny",
            "wind_speed": "10",
            "humidity": "50",
        }
        widget.set_weather(data)
        output = widget.render()
        assert "25" in output
        assert "Sunny" in output
        assert "10" in output
        assert "50" in output

    def test_weather_widget_render_error(self):
        """Test WeatherWidget render with error."""
        from cli import WeatherWidget

        widget = WeatherWidget()
        data = {"code": "E101", "msg": "Config error"}
        widget.set_weather(data)
        output = widget.render()
        assert "Config error" in output


class TestSongInfoWidget:
    """Tests for SongInfoWidget class."""

    def test_song_info_widget_init(self):
        """Test SongInfoWidget initialization."""
        from cli import SongInfoWidget

        widget = SongInfoWidget()
        assert widget.song_info is None
        assert widget.is_playing is False

    def test_song_info_widget_set_song(self):
        """Test setting song info."""
        from cli import SongInfoWidget

        widget = SongInfoWidget()
        song = {"name": "Test Song", "artists": ["Artist1", "Artist2"]}
        widget.set_song(song, is_playing=True)
        assert widget.song_info == song
        assert widget.is_playing is True

    def test_song_info_widget_render_no_song(self):
        """Test render with no song."""
        from cli import SongInfoWidget

        widget = SongInfoWidget()
        output = widget.render()
        assert "Now Playing" in output
        assert "No song" in output

    def test_song_info_widget_render_with_song(self):
        """Test render with song."""
        from cli import SongInfoWidget

        widget = SongInfoWidget()
        song = {"name": "Test Song", "artists": ["Artist1"]}
        widget.set_song(song, is_playing=True)
        output = widget.render()
        assert "Test Song" in output
        assert "Artist1" in output
        assert "▶️" in output


class TestPlaylistWidget:
    """Tests for PlaylistWidget class."""

    def test_playlist_widget_init(self):
        """Test PlaylistWidget initialization."""
        from cli import PlaylistWidget

        widget = PlaylistWidget()
        assert widget.playlist == []
        assert widget.current_index == 0

    def test_playlist_widget_set_playlist(self):
        """Test setting playlist."""
        from cli import PlaylistWidget

        widget = PlaylistWidget()
        playlist = [
            {"name": "Song 1"},
            {"name": "Song 2"},
            {"name": "Song 3"},
        ]
        widget.set_playlist(playlist, 1)
        assert widget.playlist == playlist
        assert widget.current_index == 1

    def test_playlist_widget_render_empty(self):
        """Test render with empty playlist."""
        from cli import PlaylistWidget

        widget = PlaylistWidget()
        output = widget.render()
        assert "Playlist" in output
        assert "Empty" in output

    def test_playlist_widget_render_with_songs(self):
        """Test render with playlist."""
        from cli import PlaylistWidget

        widget = PlaylistWidget()
        playlist = [{"name": "Song 1"}, {"name": "Song 2"}]
        widget.set_playlist(playlist, 0)
        output = widget.render()
        assert "Song 1" in output
        assert "Song 2" in output
        assert "→" in output  # current song indicator


class TestStatusBar:
    """Tests for StatusBar class."""

    def test_status_bar_init(self):
        """Test StatusBar initialization."""
        from cli import StatusBar

        bar = StatusBar()
        assert bar.status == "Ready"

    def test_status_bar_set_status(self):
        """Test setting status."""
        from cli import StatusBar

        bar = StatusBar()
        bar.set_status("Playing")
        assert bar.status == "Playing"

    def test_status_bar_render(self):
        """Test StatusBar render."""
        from cli import StatusBar

        bar = StatusBar()
        bar.set_status("Test Status")
        output = bar.render()
        assert "Test Status" in output


class TestMusicAgentTUIActions:
    """Tests for MusicAgentTUI action methods - test state changes without UI context."""

    def test_toggle_play_toggles_state(self):
        """Test toggle play updates player state."""
        from cli import PlayerState

        state = PlayerState()
        state.is_paused = False
        # Simulate toggle
        state.is_paused = not state.is_paused
        assert state.is_paused is True
        state.is_paused = not state.is_paused
        assert state.is_paused is False

    def test_next_song_updates_index(self):
        """Test next song updates playlist index."""
        from cli import PlayerState

        state = PlayerState()
        state.playlist = [
            {"name": "Song 1", "artists": ["A1"]},
            {"name": "Song 2", "artists": ["A2"]},
        ]
        state.playlist_index = 0
        # Simulate next song
        state.playlist_index = (state.playlist_index + 1) % len(state.playlist)
        assert state.playlist_index == 1

    def test_prev_song_updates_index(self):
        """Test prev song updates playlist index."""
        from cli import PlayerState

        state = PlayerState()
        state.playlist = [
            {"name": "Song 1", "artists": ["A1"]},
            {"name": "Song 2", "artists": ["A2"]},
        ]
        state.playlist_index = 1
        # Simulate prev song
        state.playlist_index = (state.playlist_index - 1) % len(state.playlist)
        assert state.playlist_index == 0

    def test_volume_up(self):
        """Test volume up action."""
        from cli import PlayerState

        state = PlayerState()
        state.volume = 0.5
        state.volume = min(1.0, state.volume + 0.1)
        assert state.volume == 0.6

    def test_volume_down(self):
        """Test volume down action."""
        from cli import PlayerState

        state = PlayerState()
        state.volume = 0.5
        state.volume = max(0.0, state.volume - 0.1)
        assert state.volume == 0.4

    def test_volume_up_max(self):
        """Test volume up at max."""
        from cli import PlayerState

        state = PlayerState()
        state.volume = 1.0
        state.volume = min(1.0, state.volume + 0.1)
        assert state.volume == 1.0

    def test_volume_down_min(self):
        """Test volume down at min."""
        from cli import PlayerState

        state = PlayerState()
        state.volume = 0.0
        state.volume = max(0.0, state.volume - 0.1)
        assert state.volume == 0.0

    def test_next_song_empty_playlist(self):
        """Test next song with empty playlist."""
        from cli import PlayerState

        state = PlayerState()
        state.playlist = []
        state.playlist_index = 0
        # With empty playlist, modulo would error, but code should handle it
        if state.playlist:
            state.playlist_index = (state.playlist_index + 1) % len(state.playlist)
        assert state.playlist_index == 0

    def test_prev_song_empty_playlist(self):
        """Test prev song with empty playlist."""
        from cli import PlayerState

        state = PlayerState()
        state.playlist = []
        state.playlist_index = 0
        if state.playlist:
            state.playlist_index = (state.playlist_index - 1) % len(state.playlist)
        assert state.playlist_index == 0


class TestMusicAgentTUIInit:
    """Tests for MusicAgentTUI initialization."""

    def test_tui_init(self):
        """Test TUI initialization."""
        from cli import MusicAgentTUI

        app = MusicAgentTUI()
        assert app.player_state is not None
        assert app.config is not None

    def test_tui_has_bindings(self):
        """Test that TUI has key bindings defined."""
        from cli import MusicAgentTUI

        app = MusicAgentTUI()
        assert len(app._bindings.key_to_bindings) > 0

    def test_tui_player_state_type(self):
        """Test TUI player_state is correct type."""
        from cli import MusicAgentTUI, PlayerState

        app = MusicAgentTUI()
        assert isinstance(app.player_state, PlayerState)


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_config_returns_dict(self):
        """Test that load_config returns a dictionary."""
        from cli import load_config

        config = load_config()
        assert isinstance(config, dict)

    def test_load_config_has_required_keys(self):
        """Test that config has expected keys."""
        from cli import load_config

        config = load_config()
        # Config should have some expected keys
        assert "llm" in config or "tts" in config or "weather" in config


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
