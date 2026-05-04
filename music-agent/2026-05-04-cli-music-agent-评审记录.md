# CLI Music Agent 推进记录

## 日期：2026-05-04

---

## 1. 项目确认信息

| 项目 | 内容 |
|------|------|
| 项目路径 | E:\Bingdio\music-agent\ |
| 名称 | Bingdio |
| 语言 | Python |
| CLI 框架 | Textual (TUI) |
| LLM | MiniMax / Xiaomi MiMo-v2.5-pro（二选一，待定） |
| TTS | Xiaomi MiMo TTS |
| 克隆音色 | 3 个预设 + 用户自定义 |
| 天气 API | OpenWeatherMap（免费） |
| 持久化 | SQLite |

---

## 2. 播放模块确认

| 项目 | 内容 |
|------|------|
| 原方案 | mpg123（仅支持 mp1/mp2/mp3） |
| 确认方案 | 换成 mpv 或 ffmpeg，支持更多格式 |

---

## 3. 网易云音乐 API 方案

### 方案：可插拔设计

```
netease/
├── api_no0a.py      ← 第三方 API（快速启动用）
├── api_tjit.py      ← 备选第三方
└── api_official.py  ← 官方 cookie 方案（稳定后切换）
```

### 接口示例（api.no0a.cn）
```
搜索：https://api.no0a.cn/api/cloudmusic/search/{关键词}
URL：https://api.no0a.cn/api/cloudmusic/url/{歌曲ID}
歌词：https://api.no0a.cn/api/cloudmusic/lyric/{歌曲ID}
歌单：https://api.no0a.cn/api/cloudmusic/playlist/{歌单ID}
```

### 风险提示
- 第三方 API 不稳定，可能限流或下线
- 官方 cookie 方案更稳定，但需要用户提供 cookie

### 待确认
- [ ] 用户是否提供网易云 cookie
- [ ] 还是先用第三方 API 快速启动

---

## 4. 歌单时间规划

| 时间段 | 行为 |
|--------|------|
| 早/中/晚 | 自动切歌 |

- 当前方案：早/中/晚三个时间段
- 切换方式：自动切歌

### 待确认
- [ ] 时间段划分是否细化（如早 7-12/中 12-18/晚 18-24）
- [ ] 是否有午休/深夜特殊时段

---

## 5. 克隆音色说明（暂不深入）

```
参考音频（3-10秒）→ 提取音色特征 → 建立声学模型 → 生成同音色新语音
```

- 预设 3 个音色：日语雪之下风格/英文/中文
- 用户可自定义音色
- 本地运行需要 GPU，API 方案不需要

### 待确认
- [ ] 是否第一版实现
- [ ] 硬件配置是否支持本地运行

---

## 6. MVP 范围（建议）

### 第一阶段必须
- [ ] 音乐播放（搜索 + 控制）
- [ ] 天气感知推荐
- [ ] 心情点歌
- [ ] 克隆音色 TTS 播报（用现成 API）
- [ ] 基础歌单管理

### 第二阶段
- [ ] 情绪曲线跟踪
- [ ] 智能衔接（DJ 过渡语）
- [ ] 蒸馏式偏好学习

---

## 7. 待确认事项

| 优先级 | 待确认项 | 状态 |
|--------|----------|------|
| 高 | 网易云 cookie 是否提供 | 待回复 |
| 高 | LLM 最终用哪个 | 二选一 |
| 中 | 时间段划分细化 | 待定 |
| 中 | 克隆音色是否第一版实现 | 暂不深入 |
| 低 | 硬件配置是否支持本地 GPU | 待定 |

---

## 8. 参考项目

- RadioNowhere: https://github.com/CJackHwang/RadioNowhere
  - 多 Agent 架构参考（Writer/Director/TTS）
  - 技术栈：Next.js + React + TypeScript（Web 版参考）
