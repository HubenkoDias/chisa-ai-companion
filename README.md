\# Chisa — Russian-speaking tsundere desktop AI companion



A voice-driven anime desktop assistant that lives on top of your windows, talks in Russian,

remembers previous conversations, follows your cursor and comments on what is on your screen.



> \*\*Fork notice.\*\* This project is a fork of \[Open-LLM-VTuber](https://github.com/Open-LLM-VTuber/Open-LLM-VTuber)

> (MIT). The original README is kept in \[README.upstream.md](README.upstream.md).

> The desktop client lives in a separate fork: \*\*Open-LLM-VTuber-Web (branch `chisa`)\*\*.



\## Features



| Feature | How |

|---|---|

| Fast "brain" | DeepSeek V4.1 Flash via OpenRouter, reasoning disabled, latency-sorted routing (\~0.6–1 s to first token) |

| Speech recognition | Groq Whisper large-v3-turbo (Russian) |

| Voice | Local F5-TTS Russian with voice cloning from a short reference sample, tuned to avoid clipped word endings |

| Character | Tsundere persona with few-shot dialogue examples |

| Long-term memory | Lightweight memory: an LLM rates facts 1–5, code keeps only important ones |

| Proactive speech | She speaks up on her own after silence, with a one-shot screenshot of your screen |

| Desktop pet | Transparent always-on-top window, global cursor tracking |

| Live2D tooling | Scripts that add idle motion, blinking, lip sync and emotions to models made for VTube Studio |



\## Architecture



```

&#x20;Mic ──► Groq Whisper (ASR) ──► OpenRouter / DeepSeek (LLM) ──► F5-TTS (local GPU) ──► voice

&#x20;                                    ▲          │

&#x20;                        memory/memory.md       └──► emotion tags ──► Live2D expressions

&#x20;                                    ▲

&#x20;             update\_memory.py (runs on every launch, one LLM call)

```



\## Requirements



\- Windows 10/11, NVIDIA GPU (tested on RTX 4070 Ti, \~2 GB VRAM for TTS)

\- \[uv](https://github.com/astral-sh/uv), ffmpeg, Node.js LTS (for the desktop client)

\- API keys: \[OpenRouter](https://openrouter.ai) and \[Groq](https://console.groq.com)



\## Setup



```powershell

git clone -b chisa https://github.com/HubenkoDias/Open-LLM-VTuber chisa

cd chisa

uv sync                       # installs CUDA PyTorch (see pyproject.toml)

copy conf.example.yaml conf.yaml

notepad conf.yaml             # put your API keys, edit the persona

```



\*\*Voice reference.\*\* Put a clean 8–12 s sample of the voice you want into `voice/ref.wav`

(mono, 24 kHz) and its exact transcript into `voice/ref.txt` (UTF-8, one line).

Use only voices you have the right to use.



\*\*Run:\*\* `uv run run\_server.py`, or the silent launcher `launch-chisa.vbs start-chisa.ps1`

(starts the server hidden, updates memory, opens the desktop client). Stop with `stop-chisa.ps1`.



\## Live2D models



No third-party models are bundled (their licenses do not allow redistribution).

The default `mao\_pro` sample works out of the box. To use a VTube Studio model:



```powershell

uv run python check\_model.py <model\_folder>         # format, expressions, idle, parameter style

uv run python install\_model.py <model\_folder> <name>

uv run python fix\_model.py                          # idle sway + breathing + blinking (edit NAME)

uv run python build\_emotions.py <name>              # emotions from facial parameters

```



Developed with the free model "神宫白子 (Kamiyahakuko)" — download it only from the author's

official Bilibili account (神宫凉子, UID 13737731) and follow its license.



\## Scripts



| Script | Purpose |

|---|---|

| `update\_memory.py` | Rates facts from new chats (1–5), keeps important ones in `memory/` |

| `check\_model.py` | Checks a Live2D model before installing |

| `install\_model.py` | Installs a model and registers its expressions |

| `fix\_model.py` | Generates an idle motion, blinking and lip sync groups |

| `build\_emotions.py` | Builds emotion expressions from facial parameters |

| `clean\_model.py` | Removes references to missing motion files |

| `test\_openrouter.py`, `check\_vision.py` | Compare LLMs by latency/character, find vision-capable models |



\## Changes vs upstream



\- `tts/coqui\_tts.py` — replaced with an F5-TTS Russian engine (thread-safe, explicit duration to prevent clipped endings)

\- `stateless\_llm/openai\_compatible\_llm.py` — OpenRouter: reasoning off, latency routing

\- `agents/basic\_memory\_agent.py` — injects long-term memory into the system prompt

\- `prompts/utils/proactive\_speak\_prompt.txt` — proactive speech that reacts to a screenshot



\## Privacy



`conf.yaml`, `memory/`, `chat\_history/`, `logs/` and `voice/` are git-ignored.

Conversations and screenshots are sent to OpenRouter and Groq — keep that in mind.



\## License



MIT — see \[LICENSE](LICENSE). Based on Open-LLM-VTuber by Yi-Ting Chiu and contributors.

Third-party models (F5-TTS Russian weights, Live2D models, voices) keep their own licenses.

