/**
 * Bingody Music Agent - Terminal UI Framework
 * Handles all interactive functionality and state management
 */

// ============================================================================
// State Management
// ============================================================================
const state = {
    currentView: 'welcome', // welcome | search | nowPlaying | playlist
    bingodyState: 'idle',    // idle | play | search | error | chill
    isPlaying: false,
    volume: 80,
    currentTrack: null,
    queue: [],
    searchHistory: [],
    commandHistory: [],
    historyIndex: -1,
    particles: [],
    spectrumBars: []
};

const config = {
    particleInterval: 300,
    particleColors: ['#d8b83a', '#2ad2d2', '#ee5555'],
    speechLines: {
        idle: [
            '你好！我是 Bingody~',
            '想听什么歌吗？',
            '今天天气不错呢~',
            '给我大饼问好！',
            '有什么好听的吗？'
        ],
        play: [
            '好听的歌来啦~',
            '这首歌超棒！',
            '摇摆起来~',
            '♪ ♫ ♬',
            '喜欢这首歌吗？'
        ],
        search: [
            '让我找找...',
            '搜索中~',
            '找到了！',
            '这是什么好呢...',
            '稍等一下哦~'
        ],
        error: [
            '好像出错了...',
            '网络好像不太稳定',
            '没找到呢...',
            '再试一次？',
            '呜呜，出问题了'
        ],
        chill: [
            '放松一下~',
            '好惬意的时光',
            '☕ ☁️',
            '轻音乐最棒了',
            '好舒服的感觉'
        ]
    },
    moods: ['chill', 'energetic', 'focus', 'sleepy']
};

// ============================================================================
// DOM Elements Cache
// ============================================================================
const elements = {
    terminal: document.getElementById('terminal'),
    bingodySprite: document.getElementById('bingody-sprite'),
    speechText: document.getElementById('speech-text'),
    searchInput: document.getElementById('search-input'),
    searchBtn: document.getElementById('search-btn'),
    terminalInput: document.getElementById('terminal-input'),
    submitBtn: document.getElementById('submit-btn'),
    inputPrefix: document.getElementById('input-prefix'),
    particles: document.getElementById('particles'),
    toastContainer: document.getElementById('toast-container'),
    contentArea: document.getElementById('content-area'),
    welcomeSection: document.getElementById('welcome-section'),
    searchResultsSection: document.getElementById('search-results-section'),
    nowPlayingSection: document.getElementById('now-playing-section'),
    playlistSection: document.getElementById('playlist-section'),
    resultsList: document.getElementById('results-list'),
    playlistList: document.getElementById('playlist-list'),
    playlistCount: document.getElementById('playlist-count'),
    commandLog: document.getElementById('command-log'),
    commandHints: document.getElementById('command-hints'),
    progressFill: document.getElementById('progress-fill'),
    progressHandle: document.getElementById('progress-handle'),
    progressBar: document.getElementById('progress-bar'),
    timeCurrent: document.getElementById('time-current'),
    timeTotal: document.getElementById('time-total'),
    npTitle: document.getElementById('np-title'),
    npArtist: document.getElementById('np-artist'),
    npPlayPause: document.getElementById('np-play-pause'),
    npPrev: document.getElementById('np-prev'),
    npNext: document.getElementById('np-next'),
    spectrumContainer: document.getElementById('spectrum-container'),
    volumeValue: document.getElementById('volume-value'),
    playStatus: document.getElementById('play-status'),
    netStatus: document.getElementById('net-status'),
    closeResultsBtn: document.getElementById('close-results-btn'),
    mascotZone: document.getElementById('mascot-zone')
};

// ============================================================================
// Bingody State Management
// ============================================================================
function setBingodyState(newState) {
    state.bingodyState = newState;

    // Hide all SVG states
    const svgs = elements.bingodySprite.querySelectorAll('.bingody-svg');
    svgs.forEach(svg => svg.style.display = 'none');

    // Show appropriate SVG
    const targetSvg = elements.bingodySprite.querySelector(`.state-${newState}`);
    if (targetSvg) {
        targetSvg.style.display = 'block';
    } else {
        const defaultSvg = elements.bingodySprite.querySelector('.bingody-svg');
        if (defaultSvg) defaultSvg.style.display = 'block';
    }

    // Update speech bubble with random line
    updateSpeechBubble(newState);

    // Log state change
    console.log(`[Bingody] State changed to: ${newState}`);
}

function updateSpeechBubble(stateKey) {
    const lines = config.speechLines[stateKey] || config.speechLines.idle;
    const randomLine = lines[Math.floor(Math.random() * lines.length)];
    elements.speechText.textContent = randomLine;
}

// ============================================================================
// View Management
// ============================================================================
function showView(viewName) {
    state.currentView = viewName;

    // Hide all sections
    elements.welcomeSection.classList.add('hidden');
    elements.searchResultsSection.classList.add('hidden');
    elements.nowPlayingSection.classList.add('hidden');
    elements.playlistSection.classList.add('hidden');

    // Show target section
    switch (viewName) {
        case 'welcome':
            elements.welcomeSection.classList.remove('hidden');
            break;
        case 'search':
            elements.searchResultsSection.classList.remove('hidden');
            break;
        case 'nowPlaying':
            elements.nowPlayingSection.classList.remove('hidden');
            break;
        case 'playlist':
            elements.playlistSection.classList.remove('hidden');
            break;
    }
}

// ============================================================================
// Particle System
// ============================================================================
function createParticle() {
    const particle = document.createElement('div');
    particle.classList.add('particle');

    const size = Math.random() * 8 + 4;
    particle.style.width = size + 'px';
    particle.style.height = size + 'px';
    particle.style.backgroundColor = config.particleColors[Math.floor(Math.random() * config.particleColors.length)];

    // Random position near Bingody
    const startX = Math.random() * elements.mascotZone.offsetWidth;
    const startY = Math.random() * elements.mascotZone.offsetHeight;
    particle.style.left = startX + 'px';
    particle.style.top = startY + 'px';

    elements.particles.appendChild(particle);

    const duration = Math.random() * 3 + 2;
    const dx = (Math.random() - 0.5) * 150;
    const dy = -Math.random() * 200 - 100;

    particle.animate([
        { transform: 'translate(0, 0) scale(1)', opacity: 0 },
        { transform: 'translate(0, 0) scale(1)', opacity: 1, offset: 0.1 },
        { transform: `translate(${dx}px, ${dy}px) scale(0.2)`, opacity: 0 }
    ], {
        duration: duration * 1000,
        easing: 'ease-out',
        fill: 'forwards'
    }).onfinish = () => particle.remove();
}

function startParticleSystem() {
    setInterval(createParticle, config.particleInterval);
}

// ============================================================================
// Spectrum Visualizer
// ============================================================================
function initSpectrum() {
    const bars = elements.spectrumContainer.querySelectorAll('.spectrum-bar');
    state.spectrumBars = Array.from(bars);

    // Set random heights for animation
    state.spectrumBars.forEach(bar => {
        bar.style.height = Math.random() * 60 + 20 + '%';
    });
}

function updateSpectrum() {
    if (!state.isPlaying) {
        state.spectrumBars.forEach(bar => {
            bar.style.height = '10%';
        });
        return;
    }

    state.spectrumBars.forEach(bar => {
        const minHeight = 15;
        const maxHeight = 95;
        const height = Math.random() * (maxHeight - minHeight) + minHeight;
        bar.style.height = height + '%';
    });
}

// ============================================================================
// Toast Notifications
// ============================================================================
function showToast(message, type = 'info', duration = 3000) {
    const toast = document.createElement('div');
    toast.classList.add('toast', `toast-${type}`);
    toast.textContent = message;

    elements.toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('toast-out');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// ============================================================================
// Command System
// ============================================================================
function parseCommand(input) {
    const trimmed = input.trim();
    if (!trimmed.startsWith('/bingo')) return { type: 'unknown', raw: trimmed };

    const parts = trimmed.slice(6).trim().split(/\s+/);
    const command = parts[0].toLowerCase();
    const args = parts.slice(1);

    return { type: command, args, raw: trimmed };
}

function executeCommand(input) {
    const cmd = parseCommand(input);

    // Add to command history
    state.commandHistory.push(input);
    state.historyIndex = state.commandHistory.length;

    // Log command
    addToLog(input, 'command');

    switch (cmd.type) {
        case 'play':
            handlePlayCommand(cmd.args);
            break;
        case 'search':
            handleSearchCommand(cmd.args);
            break;
        case 'feed':
            handleFeedCommand();
            break;
        case 'mood':
            handleMoodCommand(cmd.args);
            break;
        case 'queue':
        case 'list':
            showView('playlist');
            setBingodyState('idle');
            break;
        case 'help':
            showHelp();
            break;
        case 'clear':
            clearTerminal();
            break;
        default:
            showToast('未知指令，输入 /bingo help 获取帮助', 'error');
            setBingodyState('error');
    }
}

function handlePlayCommand(args) {
    if (args.length === 0) {
        // Toggle play/pause
        state.isPlaying = !state.isPlaying;
        updatePlayState();
        return;
    }

    const songName = args.join(' ');
    setBingodyState('play');
    state.isPlaying = true;

    // Mock track info
    state.currentTrack = {
        title: songName,
        artist: '未知艺术家',
        duration: '3:45'
    };

    // Update UI
    elements.npTitle.textContent = songName;
    elements.npArtist.textContent = state.currentTrack.artist;
    elements.timeTotal.textContent = state.currentTrack.duration;

    showView('nowPlaying');
    showToast(`正在播放: ${songName}`, 'success');

    // Start progress simulation
    startProgressSimulation();
    updatePlayState();
}

function handleSearchCommand(args) {
    if (args.length === 0) {
        showToast('请输入搜索关键词', 'error');
        return;
    }

    const keyword = args.join(' ');
    setBingodyState('search');

    // Mock search results
    const mockResults = [
        { title: `${keyword} - 官方版`, artist: '歌手A', duration: '4:12' },
        { title: `${keyword} (Remix)`, artist: 'DJ小明', duration: '3:45' },
        { title: `${keyword} - acoustic`, artist: '歌手B', duration: '3:28' },
        { title: `${keyword} (Live)', artist: '歌手C', duration: '5:02' }
    ];

    renderSearchResults(mockResults);
    showView('search');
    showToast(`找到 ${mockResults.length} 个结果`, 'success');
}

function handleFeedCommand() {
    setBingodyState('chill');

    // Create extra particles
    for (let i = 0; i < 10; i++) {
        setTimeout(createParticle, i * 50);
    }

    showToast('Bingody 吃到了音符！好感度+1', 'info');

    // Return to idle after a moment
    setTimeout(() => {
        if (state.bingodyState === 'chill') {
            setBingodyState('idle');
        }
    }, 3000);
}

function handleMoodCommand(args) {
    if (args.length === 0) {
        // Auto mood based on current state
        setBingodyState('chill');
        showToast('当前心情: 放松 🎵', 'info');
        return;
    }

    const mood = args[0].toLowerCase();
    if (config.moods.includes(mood)) {
        setBingodyState('chill');
        const moodNames = { chill: '放松', energetic: '活力', focus: '专注', sleepy: '助眠' };
        showToast(`切换到${moodNames[mood]}模式`, 'info');
    } else {
        showToast('可用心情: chill, energetic, focus, sleepy', 'info');
    }
}

function showHelp() {
    const helpText = `
可用指令:
/bingo play <歌曲名>  - 播放音乐
/bingo search <关键词> - 搜索音乐
/bingo feed           - 喂食 Bingody
/bingo mood           - 心情模式
/bingo queue          - 显示播放队列
/bingo clear          - 清屏
/bingo help           - 显示帮助
    `.trim();

    // Simple alert for now
    showToast('帮助信息已打印到控制台', 'info');
    console.log(helpText);
}

function clearTerminal() {
    elements.contentArea.innerHTML = '';
    showView('welcome');
    showToast('终端已清空', 'info');
}

function addToLog(message, type = 'command') {
    const logEntry = document.createElement('li');
    logEntry.classList.add('log-entry', `log-${type}`);
    logEntry.textContent = message;
    logEntry.textContent = message.length > 30 ? message.substring(0, 30) + '...' : message;

    elements.commandLog.insertBefore(logEntry, elements.commandLog.firstChild);

    // Keep only last 10 entries
    while (elements.commandLog.children.length > 10) {
        elements.commandLog.lastChild.remove();
    }
}

// ============================================================================
// Search Results Rendering
// ============================================================================
function renderSearchResults(results) {
    elements.resultsList.innerHTML = '';

    results.forEach((result, index) => {
        const li = document.createElement('li');
        li.classList.add('result-item');
        li.innerHTML = `
            <div class="result-info">
                <span class="result-title">${result.title}</span>
                <span class="result-artist">${result.artist}</span>
            </div>
            <span class="result-duration">${result.duration}</span>
        `;

        li.addEventListener('click', () => {
            handlePlayCommand([result.title]);
        });

        elements.resultsList.appendChild(li);
    });
}

// ============================================================================
// Playlist Management
// ============================================================================
function addToQueue(track) {
    state.queue.push(track);
    updatePlaylistUI();
}

function removeFromQueue(index) {
    state.queue.splice(index, 1);
    updatePlaylistUI();
}

function updatePlaylistUI() {
    elements.playlistCount.textContent = `${state.queue.length} 首`;
    elements.playlistList.innerHTML = '';

    state.queue.forEach((track, index) => {
        const li = document.createElement('li');
        li.classList.add('playlist-item');
        li.innerHTML = `
            <div class="playlist-info">
                <span class="playlist-title">${track.title}</span>
                <span class="playlist-artist">${track.artist}</span>
            </div>
            <span class="playlist-duration">${track.duration}</span>
        `;

        li.addEventListener('click', () => {
            handlePlayCommand([track.title]);
        });

        elements.playlistList.appendChild(li);
    });
}

// ============================================================================
// Progress Bar Simulation
// ============================================================================
let progressInterval = null;

function startProgressSimulation() {
    if (progressInterval) clearInterval(progressInterval);

    let progress = 0;
    progressInterval = setInterval(() => {
        if (!state.isPlaying) return;

        progress += 0.5;
        if (progress >= 100) {
            progress = 0;
            // Simulate track end
            handleNextTrack();
        }

        elements.progressFill.style.width = progress + '%';
        elements.progressHandle.style.left = progress + '%';

        // Update time display
        const totalSeconds = 225; // 3:45
        const currentSeconds = Math.floor((progress / 100) * totalSeconds);
        const minutes = Math.floor(currentSeconds / 60);
        const seconds = currentSeconds % 60;
        elements.timeCurrent.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
    }, 100);
}

function handleNextTrack() {
    if (state.queue.length > 0) {
        const nextTrack = state.queue.shift();
        handlePlayCommand([nextTrack.title]);
    }
}

// ============================================================================
// Play State Updates
// ============================================================================
function updatePlayState() {
    elements.npPlayPause.textContent = state.isPlaying ? '⏸' : '▶';

    if (state.isPlaying) {
        elements.playStatus.classList.add('playing');
        elements.playStatus.textContent = '●';
        setBingodyState('play');
        startProgressSimulation();
        startSpectrumUpdate();
    } else {
        elements.playStatus.classList.remove('playing');
        elements.playStatus.textContent = '○';
        setBingodyState('idle');
        if (progressInterval) clearInterval(progressInterval);
    }
}

let spectrumInterval = null;

function startSpectrumUpdate() {
    if (spectrumInterval) clearInterval(spectrumInterval);
    spectrumInterval = setInterval(updateSpectrum, 100);
}

// ============================================================================
// Event Listeners
// ============================================================================
function initEventListeners() {
    // Terminal input
    elements.terminalInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            const value = elements.terminalInput.value.trim();
            if (value) {
                // Auto-prepend /bingo if not present
                const cmd = value.startsWith('/bingo') ? value : `/bingo ${value}`;
                executeCommand(cmd);
                elements.terminalInput.value = '';
            }
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            if (state.historyIndex > 0) {
                state.historyIndex--;
                elements.terminalInput.value = state.commandHistory[state.historyIndex] || '';
            }
        } else if (e.key === 'ArrowDown') {
            e.preventDefault();
            if (state.historyIndex < state.commandHistory.length - 1) {
                state.historyIndex++;
                elements.terminalInput.value = state.commandHistory[state.historyIndex] || '';
            } else {
                state.historyIndex = state.commandHistory.length;
                elements.terminalInput.value = '';
            }
        }
    });

    // Search input
    elements.searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            const value = elements.searchInput.value.trim();
            if (value) {
                executeCommand(`/bingo search ${value}`);
                elements.searchInput.value = '';
            }
        }
    });

    elements.searchBtn.addEventListener('click', () => {
        const value = elements.searchInput.value.trim();
        if (value) {
            executeCommand(`/bingo search ${value}`);
            elements.searchInput.value = '';
        }
    });

    // Submit button
    elements.submitBtn.addEventListener('click', () => {
        const value = elements.terminalInput.value.trim();
        if (value) {
            const cmd = value.startsWith('/bingo') ? value : `/bingo ${value}`;
            executeCommand(cmd);
            elements.terminalInput.value = '';
        }
    });

    // Now playing controls
    elements.npPlayPause.addEventListener('click', () => {
        state.isPlaying = !state.isPlaying;
        updatePlayState();
    });

    elements.npPrev.addEventListener('click', () => {
        showToast('上一首', 'info');
    });

    elements.npNext.addEventListener('click', () => {
        handleNextTrack();
    });

    // Close search results
    elements.closeResultsBtn.addEventListener('click', () => {
        showView('welcome');
        setBingodyState('idle');
    });

    // Mood buttons
    document.querySelectorAll('.mood-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const mood = btn.dataset.mood;
            document.querySelectorAll('.mood-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            handleMoodCommand([mood]);
        });
    });

    // Action buttons
    document.querySelectorAll('.action-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const action = btn.dataset.action;
            switch (action) {
                case 'play-pause':
                    state.isPlaying = !state.isPlaying;
                    updatePlayState();
                    break;
                case 'next':
                    handleNextTrack();
                    break;
                case 'queue':
                    showView('playlist');
                    break;
                case 'settings':
                    showToast('设置面板开发中...', 'info');
                    break;
            }
        });
    });

    // Control buttons
    document.querySelectorAll('.ctrl-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const action = btn.dataset.action;
            switch (action) {
                case 'minimize':
                    elements.terminal.style.transform = 'scale(0.9)';
                    elements.terminal.style.opacity = '0.7';
                    break;
                case 'maximize':
                    elements.terminal.style.transform = elements.terminal.style.transform === 'scale(1.05)' ? '' : 'scale(1.05)';
                    break;
                case 'close':
                    showToast('再见！下次见~', 'info');
                    break;
            }
        });
    });

    // Window click to restore
    elements.terminal.addEventListener('click', () => {
        elements.terminal.style.transform = '';
        elements.terminal.style.opacity = '';
    });
}

// ============================================================================
// Initialization
// ============================================================================
function init() {
    console.log('[Bingody] Initializing...');

    // Initialize UI
    setBingodyState('idle');
    showView('welcome');
    initSpectrum();

    // Set up network status indicator
    elements.netStatus.classList.add('online');

    // Set up event listeners
    initEventListeners();

    // Start particle system
    startParticleSystem();

    // Focus terminal input
    elements.terminalInput.focus();

    // Welcome message
    setTimeout(() => {
        showToast('Bingody Music Agent 已就绪！', 'success', 4000);
    }, 500);

    console.log('[Bingody] Ready!');
}

// Start when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

// Export for debugging
window.BingodyUI = {
    state,
    setBingodyState,
    showView,
    showToast,
    executeCommand,
    addToQueue
};