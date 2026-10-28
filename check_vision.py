import requests

WATCH = ["deepseek-v4.1-flash", "mimo-v2.6-flash", "glm-5.3-flash", "gemini", "kimi-k3"]

models = requests.get("https://openrouter.ai/api/v1/models", timeout=30).json()["data"]
for m in models:
    if any(w in m["id"] for w in WATCH):
        mods = m.get("architecture", {}).get("input_modalities", [])
        sees = "ВИДИТ" if "image" in mods else "не видит"
        p_in = float(m["pricing"]["prompt"]) * 1e6
        p_out = float(m["pricing"]["completion"]) * 1e6
        print(f"{sees:9} | ${p_in:.2f} / ${p_out:.2f} | {m['id']}")