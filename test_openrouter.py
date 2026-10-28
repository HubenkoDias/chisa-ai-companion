import time
import requests
import yaml
from openai import OpenAI

KEYWORDS = ["deepseek-v4.1-flash", "venice-uncensored", "hermes-3"]
SYSTEM = ("Ты Чиса, дерзкая аниме-девчонка, живёшь на рабочем столе у пользователя. "
          "Обожаешь его подкалывать, язвишь, можешь ругнуться к месту. "
          "Отвечай только по-русски, 1-2 предложения.")
USER = "Ну давай, подколи меня как-нибудь пожёстче."


def find(d, key):
    if isinstance(d, dict):
        if key in d:
            return d[key]
        for v in d.values():
            r = find(v, key)
            if r:
                return r
    return None


cfg = find(yaml.safe_load(open("conf.yaml", encoding="utf-8")), "openai_compatible_llm")
client = OpenAI(api_key=cfg["llm_api_key"], base_url="https://openrouter.ai/api/v1")

models = requests.get("https://openrouter.ai/api/v1/models", timeout=30).json()["data"]

for kw in KEYWORDS:
    matches = [m for m in models if kw in m["id"]]
    if not matches:
        print(f"\n=== {kw}: модель не найдена")
        continue
    m = sorted(matches, key=lambda x: len(x["id"]))[0]
    price_in = float(m["pricing"]["prompt"]) * 1e6
    price_out = float(m["pricing"]["completion"]) * 1e6
    print(f"\n=== {m['id']}  (${price_in:.2f} / ${price_out:.2f} за 1M токенов)")

    try:
        start = time.time()
        first = None
        text = ""
        stream = client.chat.completions.create(
            model=m["id"],
            messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": USER}],
            stream=True,
            extra_body={
                "reasoning": {"enabled": False},
                "provider": {"sort": "latency"},
            },
        )
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                if first is None:
                    first = time.time() - start
                text += chunk.choices[0].delta.content
        print(f"Первое слово: {first:.2f} с | весь ответ: {time.time() - start:.2f} с")
        print(text.strip())
    except Exception as e:
        print("Ошибка:", str(e)[:300])