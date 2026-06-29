# Voice Architecture — Post Agent Zero Analysis

## Pipeline Flow

```
[User speaks]
     ↓
hermes-talk ────→ daemon(START_RECORDING) ────→ faster-whisper ────→ transcript
                                                                         ↓
                                                              [transcript in terminal]
                                                                         ↓
                                                              [copied to Hermes chat]
                                                                         ↓
                                                              [Agent responds]
                                                                         ↓
                                                    hermes-say-clean (strips markdown/code/URLs)
                                                                         ↓
                                                    hermes-say ──→ daemon(SYNTHESIZE_TTS) ──→ Kokoro ──→ speakers
                                                                         ↓
                                                          waits 0.87s × word_count
                                                                         ↓
                                                          hermes-chime (chime + record)
                                                                         ↓
                                                              [loop]
```

## What We Stole From Agent Zero

| Decision | Before | After | Why |
|----------|--------|-------|-----|
| Text cleaning | Raw markdown → TTS | Strip `**`, `#`, URLs, code, emojis via `hermes-say-clean` | Code blocks and URLs sound like noise through TTS |
| Sentence chunking | Entire response at once | 135-char sentence chunks (configurable) | Natural pacing, no cutoff |
| VAD silence | Fixed 15s window | faster-whisper already strips silence; next: adaptive stop | 15s of silence is wasted time |
| Mic/TTS exclusivity | Both could overlap | hermes-chime interrupts TTS before recording | Can't listen and speak at same time |

## Architecture Decisions (Underlined)

### 1. Terminal-native, not browser-native
Agent Zero uses browser Web APIs (MediaRecorder, AnalyserNode, AudioContext). We use a Unix daemon with sounddevice. **Decision**: Stay daemon-based. The daemon already handles playback interruption, Kokoro TTS, and Whisper STT. Browser APIs would require a web server and lose our terminal-first workflow.

### 2. IPC over Unix socket
Agent Zero uses HTTP API calls (`/plugins/_whisper_stt/transcribe`). We use length-prefixed JSON frames over `/tmp/hermes_audio.sock`. **Decision**: Stay with Unix socket IPC — lower latency, no HTTP overhead, no port conflicts.

### 3. Pacing = word_count × 0.87s (capped 25s)
Agent Zero uses browser AudioContext timing. We use a post-speech sleep. **Decision**: Keep the sleep. 0.87s/word ensures the full audio plays before the chime fires. Browser AudioContext can't help here — we're not streaming chunks.

### 4. Single chime + record cycle per loop
Agent Zero has a continuous mic (LISTENING state → RECORDING on speech → PROCESSING on silence → LISTENING). We fire one START_CHIME_LISTEN per cycle. **Decision**: Keep our discrete cycle. Our daemon doesn't maintain a persistent mic stream between cycles — each cycle is a fresh recording. This is simpler and avoids resource leaks.

### 5. Text cleaning is a mandatory pipeline stage
Agent Zero cleans in JS before sending to TTS API. We clean with `hermes-say-clean` before `hermes-say`. **Decision**: Mandatory. Every TTS response must pass through cleaning. The pipeline is: `clean → chunk → speak → wait → chime`.

## Missing Piece: Full Automation

The current gap: transcript goes to terminal, user copies to Hermes chat. Agent Zero solves this by having the mic button auto-fill the chat input and auto-send.

**Fix**: `hermes -z "$transcript" --continue <SESSION_ID>` — but this creates a new agent session, not THIS session.

**Cleanest solution**: A dedicated `voice-agent` profile that runs a persistent Hermes session in voice-only mode. The transcript pipes to it, it responds, response pipes to `hermes-say`. All behind a single `hermes-voice-agent` command.
