# Chisa — Russian-speaking tsundere desktop AI companion

A voice-driven anime desktop assistant that lives on top of your windows, talks in Russian,
remembers previous conversations, follows your cursor and comments on what is on your screen.

> **Fork notice.** This project is a fork of [Open-LLM-VTuber](https://github.com/Open-LLM-VTuber/Open-LLM-VTuber)
> (MIT). The original README is kept in [README.upstream.md](README.upstream.md).
> The desktop client lives in a separate fork: [chisa-desktop-client](https://github.com/HubenkoDias/chisa-desktop-client) (branch `chisa`).

## Features

| Feature | How |
|---|---|
| Fast "brain" | DeepSeek V4.1 Flash via OpenRouter, reasoning disabled, latency-sorted routing (~0.6–1 s to first token) |
| Speech recognition | Groq Whisper large-v3-turbo (Russian) |
| Voice | Local F5-TTS Russian with voice cloning from a short reference sample, tuned to avoid clipped word endings |
| Character | Tsundere persona with few-shot dialogue examples |
| Long-term memory | Lightweight memory: an LLM rates facts 1–5, code keeps only important ones |
| Proactive speech | She speaks up on her own after silence, with a one-shot screenshot of your screen |
| Desktop pet | Transparent always-on-top window, global cursor tracking |
| Live2D tooling | Scripts that add idle motion, blinking, lip sync and emotions to models made for VTube Studio |

## Architecture

```
 Mic --> Groq Whisper (ASR) --> OpenRouter / DeepSeek (LLM) --> F5-TTS (local GPU) --> voice
                                      ^           |
                          memory/memory.md        +--> emotion tags --> Live2D expressions
                                      ^
               update_memory.py (runs on every launch, one LLM call)
```

## Requirements

- Windows 10/11, NVIDIA GPU (tested on RTX 4070 Ti, ~2 GB VRAM for TTS)
- [uv](https://github.com/astral-sh/uv), ffmpeg, Node.js LTS (for the desktop client)
- API keys: [OpenRouter](https://openrouter.ai) and [Groq](https://console.groq.com)

## Setup

```powershell
git clone -b chisa https://github.com/HubenkoDias/chisa-ai-companion chisa
cd chisa
uv sync                       # installs CUDA PyTorch (see pyproject.toml)
copy conf.example.yaml conf.yaml
notepad conf.yaml             # put your API keys, edit the persona
```

**Voice reference.** Put a clean 8–12 s sample of the voice you want into `voice/ref.wav`
(mono, 24 kHz) and its exact transcript into `voice/ref.txt` (UTF-8, one line).
Use only voices you have the right to use.

**Run:** `uv run run_server.py`, or the silent launcher `launch-chisa.vbs start-chisa.ps1`
(starts the server hidden, updates memory, opens the desktop client). Stop with `stop-chisa.ps1`.

## Live2D models

No third-party models are bundled (their licenses do not allow redistribution).
The default `mao_pro` sample works out of the box. To use a VTube Studio model:

```powershell
uv run python check_model.py <model_folder>          # format, expressions, idle, parameter style
uv run python install_model.py <model_folder> <name>
uv run python fix_model.py                           # idle sway + breathing + blinking (edit NAME)
uv run python build_emotions.py <name>               # emotions from facial parameters
```

Developed with the free model "神宫白子 (Kamiyahakuko)" — download it only from the author's
official Bilibili account (神宫凉子, UID 13737731) and follow its license.

## Scripts

| Script | Purpose |
|---|---|
| `update_memory.py` | Rates facts from new chats (1–5), keeps important ones in `memory/` |
| `check_model.py` | Checks a Live2D model before installing |
| `install_model.py` | Installs a model and registers its expressions |
| `fix_model.py` | Generates an idle motion, blinking and lip sync groups |
| `build_emotions.py` | Builds emotion expressions from facial parameters |
| `clean_model.py` | Removes references to missing motion files |
| `test_openrouter.py`, `check_vision.py` | Compare LLMs by latency/character, find vision-capable models |

## Changes vs upstream

- `tts/coqui_tts.py` — replaced with an F5-TTS Russian engine (thread-safe, explicit duration to prevent clipped endings)
- `stateless_llm/openai_compatible_llm.py` — OpenRouter: reasoning off, latency routing
- `agents/basic_memory_agent.py` — injects long-term memory into the system prompt
- `prompts/utils/proactive_speak_prompt.txt` — proactive speech that reacts to a screenshot

## Privacy

`conf.yaml`, `memory/`, `chat_history/`, `logs/` and `voice/` are git-ignored.
Conversations and screenshots are sent to OpenRouter and Groq — keep that in mind.

## License and credits

This is a **non-commercial** personal project.

- Code: MIT, see [LICENSE](LICENSE). Based on [Open-LLM-VTuber](https://github.com/Open-LLM-VTuber/Open-LLM-VTuber) by Yi-Ting Chiu and contributors.
- Desktop client: Open-LLM-VTuber License 1.0 (Apache 2.0 with additional conditions, non-commercial use).
- Voice: [F5-TTS](https://github.com/SWivid/F5-TTS) by Yushen Chen et al. (code MIT, pretrained weights CC BY-NC 4.0)
  and [F5-TTS_RUSSIAN](https://huggingface.co/Misha24-10/F5-TTS_RUSSIAN) by Misha24-10 (CC BY-NC 4.0).
  The weights are downloaded at runtime and are not redistributed here. They may not be used commercially.
- Live2D: the bundled `mao_pro` sample belongs to Live2D Inc. and is subject to the Live2D Free Material License
  and the Live2D Cubism Sample Data Terms of Use, which restrict erotic, violent or otherwise offensive use of sample characters.
- Third-party Live2D models and voices are not included and keep their own licenses.
