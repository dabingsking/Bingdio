"""Textual TUI for Bingody Music Agent - Voxel Edition."""

from __future__ import annotations

import os
import sys
import threading
from typing import Optional

import yaml
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.events import Key
from textual.reactive import reactive
from textual.widgets import Button, Header, Static

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from tools import weather as weather_tool
    from tools import netease as netease_tool
    from tools import playlist as playlist_tool
except ImportError:
    weather_tool = netease_tool = playlist_tool = None

CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.yaml"
)

# =============================================================================
# Design Tokens
# =============================================================================
COLORS = {
    "gold": "#d8b83a",
    "cyan": "#2ad2d2",
    "error": "#ee5555",
    "bg_deep": "#0f172a",
    "surface": "#1a1a2e",
    "border": "#313131",
    "text": "#f1f1f1",
    "text_dim": "#aaaaaa",
    "text_muted": "#777777",
}


# =============================================================================
# Player State
# =============================================================================
class PlayerState:
    def __init__(self):
        self.is_playing: bool = False
        self.is_paused: bool = False
        self.current_song: Optional[dict] = None
        self.volume: float = 0.8
        self.playlist: list = []
        self.playlist_index: int = 0
        self.mood: str = "idle"
        self.affinity: int = 0


# =============================================================================
# Bingody ASCII Sprite Frames
# =============================================================================
BINGODY_FRAMES = {
    "idle": [
        "       ╭──────╮       ",
        "     ╭─┤◉    ◉├─╮     ",
        "     ││ (◕‿◕) ││     ",
        "     ╰│  ~~~  │╯╰     ",
        "      ╰─╥───╥─╯      ",
        "       ═╩═╩═       ",
        "    ═══[headphones]═══",
    ],
    "play": [
        "       ╭──────╮       ",
        "     ╭─┤◉    ◉├─╮     ",
        "     ││  ^◡^  ││     ",
        "     ╰│ [♪♫]  │╯╰     ",
        "      ╰─╥───╥─╯      ",
        "       ═╩═╩═       ",
        "    ═══[HEADPHONES]═══",
    ],
    "search": [
        "       ╭──────╮       ",
        "     ╭─┤ಠ    ಠ├─╮     ",
        "     ││  ? ?  ││     ",
        "     ╰│  ~~~  │╯╰     ",
        "      ╰─╥───╥─╯      ",
        "       ═╩═╩═       ",
        "    ═══[headphones]═══",
    ],
    "error": [
        "       ╭──XX──╮       ",
        "     ╭─┤X    X├─╮     ",
        "     ││  x_x  ││     ",
        "     ╰│  ~~~  │╯╰     ",
        "      ╰─╥───╥─╯      ",
        "       ═╩═╩═       ",
        "    ═══[BROKEN]════",
    ],
    "chill": [
        "       ╭──────╮       ",
        "     ╭─┤◉    ◉├─╮     ",
        "     ││  ◡‿◡  ││     ",
        "     ╰│ [☕]  │╯╰     ",
        "      ╰─╥───╥─╯      ",
        "       ═╩═╩═       ",
        "    ═══[CHILL]═════",
    ],
}

SPEECH_LINES = {
    "idle": ["你好！我是 Bingody~", "有什么好听的吗？", "给我大饼问好！", "今天想听什么歌？", "喂我音符吧~"],
    "play": ["好听的歌来啦~", "这首歌超棒！", "摇摆起来！", "♪ ♫ ♬", "喜欢吗？"],
    "search": ["让我找找...", "搜索中~", "找到了！", "稍等一下哦~"],
    "error": ["好像出错了...", "网络不太稳定", "没找到呢...", "再试一次？"],
    "chill": ["放松一下~", "好惬意的时光", "好舒服的感觉", "轻音乐最棒了"],
}


# =============================================================================
# Main TUI Application
# =============================================================================
class BingodyTUI(App):
    """Bingody Music Agent - Voxel Terminal UI."""

    CSS = """
    Screen {
        background: #0f172a;
    }

    /* === Main Layout === */
    #main-container {
        layout: horizontal;
        height: 100%;
    }

    #mascot-zone {
        width: 28%;
        background: #080810;
        border-right: solid #313131;
    }

    #main-view {
        width: 50%;
    }

    #jukebox-widget {
        width: 22%;
        background: #080810;
        border-left: solid #313131;
    }

    /* === Mascot Zone === */
    #bingody-frame {
        height: 55%;
        align: center middle;
        color: #d8b83a;
    }

    #speech-bubble {
        height: 20%;
        align: center middle;
        background: #1a1a2e;
        border: solid #d8b83a;
        padding: 1 2;
        margin: 1 2;
    }

    #speech-text {
        color: #f1f1f1;
        content-align: center middle;
    }

    /* === Main View === */
    #search-area {
        height: 8;
        background: #1a1a2e;
        border-bottom: solid #313131;
        layout: horizontal;
    }

    #search-prefix {
        width: 18;
        background: #313131;
        color: #2ad2d2;
        content-align: center middle;
    }

    #search-input {
        width: 1fr;
    }

    #content-area {
        height: 1fr;
    }

    /* Welcome */
    #welcome-section {
        height: 1fr;
        align: center middle;
    }

    #main-title {
        color: #f1f1f1;
        text-style: bold;
        content-align: center middle;
    }

    #sub-title {
        color: #d8b83a;
        content-align: center middle;
    }

    #status-display {
        color: #aaaaaa;
        content-align: center middle;
    }

    /* Now Playing */
    #now-playing {
        height: 1fr;
        background: #1a1a2e;
        border: solid #313131;
        padding: 2;
        display: none;
    }

    #now-playing.visible {
        display: block;
    }

    #np-title-text {
        color: #f1f1f1;
        text-style: bold;
    }

    #np-artist-text {
        color: #d8b83a;
    }

    #progress-area {
        height: 3;
        layout: horizontal;
    }

    #progress-time {
        width: 10;
        color: #777777;
    }

    #progress-bar-container {
        width: 1fr;
        background: #313131;
    }

    #progress-fill {
        height: 100%;
        background: #d8b83a;
        width: 0%;
    }

    /* Spectrum */
    #spectrum-area {
        height: 6;
        layout: horizontal;
        align: center middle;
    }

    .spectrum-bar {
        width: 2;
        margin: 0 1;
        color: #2ad2d2;
    }

    /* Search Results */
    #search-results {
        height: 1fr;
        background: #1a1a2e;
        border: solid #313131;
        padding: 1 2;
        display: none;
    }

    #search-results.visible {
        display: block;
    }

    /* === Jukebox Widget === */
    .widget-section {
        height: auto;
        background: #1a1a2e;
        border-bottom: solid #313131;
        padding: 1 2;
    }

    .widget-title {
        color: #d8b83a;
        text-style: bold;
    }

    .status-item {
        layout: horizontal;
    }

    .status-label {
        width: 18;
        color: #777777;
    }

    .status-dot {
        width: 8;
    }

    .status-dot.online {
        color: #2ad2d2;
    }

    .status-dot.playing {
        color: #d8b83a;
    }

    .status-dot.offline {
        color: #ee5555;
    }

    #action-buttons {
        layout: horizontal;
        height: 5;
    }

    .action-btn {
        width: 1fr;
        margin: 0 1;
    }

    #mood-buttons {
        layout: horizontal;
        height: 5;
    }

    .mood-btn {
        width: 1fr;
        margin: 0 1;
    }

    /* Log */
    .log-entry {
        color: #777777;
    }

    .log-entry.log-system {
        color: #2ad2d2;
    }

    .log-entry.log-command {
        color: #f1f1f1;
    }

    /* === Input Area === */
    #input-area {
        height: 6;
        background: #12122a;
        border-top: solid #2d2d5a;
        layout: horizontal;
    }

    #input-prefix {
        width: 18;
        background: #313131;
        color: #2ad2d2;
        content-align: center middle;
    }

    #terminal-input {
        width: 1fr;
    }

    #submit-btn {
        width: 14;
    }

    /* === Hints === */
    #hints-area {
        height: 3;
        background: #0a0a14;
        layout: horizontal;
        align: center middle;
    }

    .hint {
        color: #777777;
        margin: 0 4;
    }

    /* === Buttons === */
    #np-prev, #np-next {
        width: 14;
    }

    #np-play {
        width: 18;
    }

    Static {
        margin: 0;
    }

    Button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("space", "toggle_play", "Play"),
        Binding("n", "next_song", "Next"),
        Binding("p", "prev_song", "Prev"),
        Binding("f", "feed", "Feed"),
        Binding("s", "focus_search", "Search"),
        Binding("l", "show_queue", "Queue"),
    ]

    bingody_state = reactive("idle")
    current_view = reactive("welcome")

    def __init__(self):
        super().__init__()
        self.state = PlayerState()
        self._bg_thread: Optional[threading.Thread] = None
        try:
            self.config = load_config()
        except Exception:
            self.config = {}

    def compose(self) -> ComposeResult:
        yield Header()

        with Container(id="main-container"):
            # === LEFT: Mascot ===
            with Vertical(id="mascot-zone"):
                yield Static("\n".join(BINGODY_FRAMES["idle"]), id="bingody-frame")
                yield Static("你好！我是 Bingody~", id="speech-text")

            # === CENTER: Main ===
            with Vertical(id="main-view"):
                with Horizontal(id="search-area"):
                    yield Static("/bingo", id="search-prefix")
                    yield Static("", id="search-input")

                with VerticalScroll(id="content-area"):
                    with Vertical(id="welcome-section"):
                        yield Static("BINGODY", id="main-title")
                        yield Static("music agent", id="sub-title")
                        yield Static(
                            "> Loading Bingody Core [OK]\n"
                            "> Synced with '大饼' ACTIVE\n"
                            "> Awaiting command...",
                            id="status-display"
                        )

                    with Vertical(id="now-playing"):
                        with Horizontal(id="np-header"):
                            with Vertical(id="np-info"):
                                yield Static("--", id="np-title-text")
                                yield Static("--", id="np-artist-text")
                            with Horizontal(id="np-controls"):
                                yield Button("|<<", id="np-prev")
                                yield Button("▶", id="np-play")
                                yield Button(">>|", id="np-next")
                        with Horizontal(id="progress-area"):
                            yield Static("0:00", id="progress-time")
                            yield Static("", id="progress-bar-container")
                            yield Static("0:00", id="progress-time-end")
                        with Horizontal(id="spectrum-area"):
                            for i in range(24):
                                yield Static("█", classes="spectrum-bar")

                    with Vertical(id="search-results"):
                        yield Static("[b]搜索结果[/b]")
                        yield Static("", id="results-content")

                with Horizontal(id="hints-area"):
                    yield Static("/bingo play | search | feed | mood | queue", classes="hint")

            # === RIGHT: Widget ===
            with Vertical(id="jukebox-widget"):
                with VerticalScroll(classes="widget-section"):
                    yield Static("系统状态", classes="widget-title")
                    yield Static("", classes="status-item")
                    yield Static("网络", classes="status-label")
                    yield Static("●", classes="status-dot online")
                    yield Static("播放", classes="status-label")
                    yield Static("○", classes="status-dot", id="play-indicator")
                    yield Static("音量", classes="status-label")
                    yield Static("80%", classes="status-label")

                with VerticalScroll(classes="widget-section"):
                    yield Static("快捷操作", classes="widget-title")
                    with Horizontal(id="action-buttons"):
                        yield Button("▶", classes="action-btn", id="act-play")
                        yield Button("⏭", classes="action-btn", id="act-next")
                        yield Button("☰", classes="action-btn", id="act-queue")
                        yield Button("⚙", classes="action-btn", id="act-settings")

                with VerticalScroll(classes="widget-section"):
                    yield Static("心情模式", classes="widget-title")
                    with Horizontal(id="mood-buttons"):
                        yield Button("😌", classes="mood-btn", id="mood-chill")
                        yield Button("⚡", classes="mood-btn", id="mood-energy")
                        yield Button("🎯", classes="mood-btn", id="mood-focus")
                        yield Button("😴", classes="mood-btn", id="mood-sleep")

                with VerticalScroll(classes="widget-section"):
                    yield Static("最近指令", classes="widget-title")
                    yield Static("系统启动完成", classes="log-entry log-system")

        # === Bottom Input ===
        with Horizontal(id="input-area"):
            yield Static("/bingo", id="input-prefix")
            yield Static("", id="terminal-input")
            yield Button("▶", id="submit-btn")

    def on_mount(self) -> None:
        self._bg_thread = threading.Thread(target=self._init, daemon=True)
        self._bg_thread.start()

    def _init(self) -> None:
        self._fetch_weather()
        self._load_playlist()

    # === Actions ===
    def action_toggle_play(self) -> None:
        if not self.state.current_song and not self.state.playlist:
            self._load_playlist()
            return

        self.state.is_paused = not self.state.is_paused
        self.state.is_playing = not self.state.is_paused
        self.bingody_state = "play" if self.state.is_playing else "idle"
        self._update_bingody_frame()

        btn = self.query_one("#np-play", Button)
        btn.label = "⏸" if not self.state.is_paused else "▶"

        status = self.query_one("#np-title-text", Static)
        status.update("|| PAUSED" if self.state.is_paused else self.state.current_song.get("name", "--"))

    def action_next_song(self) -> None:
        if not self.state.playlist:
            return
        self.state.playlist_index = (self.state.playlist_index + 1) % len(self.state.playlist)
        self._play_current()

    def action_prev_song(self) -> None:
        if not self.state.playlist:
            return
        self.state.playlist_index = (self.state.playlist_index - 1) % len(self.state.playlist)
        self._play_current()

    def action_feed(self) -> None:
        self.state.affinity += 1
        self.bingody_state = "chill"
        self._update_bingody_frame()
        self._update_speech(f"Bingody 吃到了音符！好感度 +{self.state.affinity}")

        def revert():
            import time
            time.sleep(2)
            self.bingody_state = "idle"
            self._update_bingody_frame()
        t = threading.Thread(target=revert, daemon=True)
        t.start()

    def action_focus_search(self) -> None:
        self.query_one("#search-input", Static).focus()

    def action_show_queue(self) -> None:
        self.current_view = "playlist"
        self._update_content()

    def action_quit(self) -> None:
        self.exit()

    # === Event Handlers ===
    def on_key(self, event: Key) -> None:
        if event.key == "enter":
            self._handle_command()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "np-prev":
            self.action_prev_song()
        elif btn_id == "np-next":
            self.action_next_song()
        elif btn_id == "np-play":
            self.action_toggle_play()
        elif btn_id == "act-play":
            self.action_toggle_play()
        elif btn_id == "act-next":
            self.action_next_song()
        elif btn_id == "act-queue":
            self.action_show_queue()
        elif btn_id and btn_id.startswith("mood-"):
            self.bingody_state = "chill"
            self._update_bingody_frame()
            self._update_speech(f"心情切换: {btn_id.replace('mood-', '')}")

    # === Command System ===
    def _handle_command(self) -> None:
        widget = self.query_one("#terminal-input", Static)
        cmd = widget.renderable.strip()
        if not cmd:
            return
        widget.update("")

        if cmd.startswith("/bingo"):
            parts = cmd[6:].strip().split()
        else:
            parts = cmd.split()

        if not parts:
            return

        command = parts[0].lower()
        args = parts[1:]

        if command in ("play", "p"):
            self._cmd_play(args)
        elif command in ("search", "s"):
            self._cmd_search(args)
        elif command in ("feed", "f"):
            self.action_feed()
        elif command in ("mood", "m"):
            self._cmd_mood(args)
        elif command in ("queue", "q", "list", "l"):
            self.action_show_queue()
        elif command in ("help", "h", "?"):
            self._show_help()
        elif command in ("clear", "cls"):
            self.current_view = "welcome"
            self._update_content()
        else:
            self._update_speech(f"未知指令: {command}")
            self.bingody_state = "error"
            self._update_bingody_frame()

        self._add_log(cmd)

    def _cmd_play(self, args: list) -> None:
        self.bingody_state = "play"
        self._update_bingody_frame()
        if args:
            self.state.current_song = {"name": " ".join(args), "artist": "Unknown"}
            self._update_now_playing()
            self._update_speech("好听的歌来啦~")
        elif self.state.playlist:
            self._play_current()

    def _cmd_search(self, args: list) -> None:
        if not args:
            self._update_speech("请输入搜索关键词")
            return
        self.bingody_state = "search"
        self._update_bingody_frame()
        self._update_speech("搜索中...")
        keyword = " ".join(args)

        def do_search():
            try:
                if netease_tool:
                    result = netease_tool.search_song(keyword, limit=10)
                    if result.get("code") == "0":
                        songs = result.get("songs", [])
                        self.call_from_thread(self._show_results, songs)
                    else:
                        self.call_from_thread(self._update_speech, "搜索失败")
                else:
                    mock = [
                        {"name": f"{keyword} - 官方版", "artist": "歌手A"},
                        {"name": f"{keyword} (Remix)", "artist": "DJ小明"},
                        {"name": f"{keyword} - acoustic", "artist": "歌手B"},
                    ]
                    self.call_from_thread(self._show_results, mock)
            except Exception as e:
                self.call_from_thread(self._update_speech, f"搜索出错: {e}")
                self.bingody_state = "error"
                self.call_from_thread(self._update_bingody_frame)

        threading.Thread(target=do_search, daemon=True).start()

    def _cmd_mood(self, args: list) -> None:
        moods = {"chill": "放松", "energetic": "活力", "energy": "活力", "focus": "专注", "sleepy": "助眠", "sleep": "助眠"}
        m = args[0].lower() if args else None
        name = moods.get(m, "放松") if m else "放松"
        self.bingody_state = "chill"
        self._update_bingody_frame()
        self._update_speech(f"心情: {name}")

    def _show_help(self) -> None:
        self._update_speech("/bingo play|search|feed|mood|queue | SPACE播放 | N/P切歌 | Q退出")

    # === UI Updates ===
    def _update_bingody_frame(self) -> None:
        frame = self.query_one("#bingody-frame", Static)
        frame.update("\n".join(BINGODY_FRAMES.get(self.bingody_state, BINGODY_FRAMES["idle"])))

    def _update_speech(self, text: str) -> None:
        speech = self.query_one("#speech-text", Static)
        speech.update(text)

    def _update_now_playing(self) -> None:
        if not self.state.current_song:
            return
        self.query_one("#np-title-text", Static).update(self.state.current_song.get("name", "--"))
        self.query_one("#np-artist-text", Static).update(self.state.current_song.get("artist", "--"))
        self.current_view = "now_playing"
        self._update_content()

    def _update_content(self) -> None:
        self.query_one("#welcome-section").display = self.current_view == "welcome"
        self.query_one("#now-playing").display = self.current_view in ("now_playing", "playlist")
        self.query_one("#search-results").display = self.current_view == "search"

    def _show_results(self, songs: list) -> None:
        self.current_view = "search"
        self.bingody_state = "idle"
        self._update_bingody_frame()
        self.state.playlist = songs
        self.state.playlist_index = 0

        results = self.query_one("#results-content", Static)
        lines = [f"{i+1}. {s.get('name', '?')[:35]}" for i, s in enumerate(songs[:10])]
        if not lines:
            lines = ["没有找到结果"]
            self.bingody_state = "error"
            self._update_bingody_frame()

        results.update("\n".join(lines) if lines else "没有找到结果")
        self._update_content()
        self._update_speech(f"找到 {len(songs)} 首歌曲")

    def _play_current(self) -> None:
        if not self.state.playlist or not 0 <= self.state.playlist_index < len(self.state.playlist):
            return
        self.state.current_song = self.state.playlist[self.state.playlist_index]
        self.state.is_playing = True
        self.state.is_paused = False
        self.bingody_state = "play"
        self._update_bingody_frame()
        self._update_now_playing()
        self._update_speech(f"正在播放: {self.state.current_song.get('name', '?')}")
        self.query_one("#np-play", Button).label = "⏸"

    def _add_log(self, cmd: str) -> None:
        log = self.query_one("#jukebox-widget", Vertical)
        entry = Static(cmd[:50], classes="log-entry log-command")
        # Insert after title
        log.mount(entry, before=log.children[-1] if len(log.children) > 1 else None)

    # === Background ===
    def _fetch_weather(self) -> None:
        try:
            if weather_tool:
                data = weather_tool.get_weather()
                self.call_from_thread(self._update_speech, f"天气: {data.get('text', '?')} {data.get('temp', '?')}°C")
        except Exception:
            pass

    def _load_playlist(self) -> None:
        try:
            if netease_tool:
                result = netease_tool.search_song("中文流行", limit=10)
                if result.get("code") == "0":
                    songs = result.get("songs", [])
                    if songs:
                        self.call_from_thread(self._set_playlist, songs)
        except Exception:
            pass

    def _set_playlist(self, songs: list) -> None:
        self.state.playlist = songs
        self.state.playlist_index = 0
        if songs:
            self._play_current()


def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def run_tui() -> None:
    app = BingodyTUI()
    app.run()


if __name__ == "__main__":
    run_tui()