"""Long-term memory for Chisa: keeps only facts that will matter later.

The LLM rates every fact 1-5; the code keeps only important ones (>= THRESHOLD).
memory.json is the source of truth, memory.md is generated from it for the prompt.
"""
import json
import re
from datetime import date
from pathlib import Path

import yaml
from openai import OpenAI

ROOT = Path(__file__).resolve().parent
CHAT_DIR = ROOT / "chat_history"
MEMORY_DIR = ROOT / "memory"
MEMORY_JSON = MEMORY_DIR / "memory.json"
MEMORY_MD = MEMORY_DIR / "memory.md"
STATE_FILE = MEMORY_DIR / "processed.json"

THRESHOLD = 4        # keep facts rated 4-5 only
MAX_ITEMS = 15       # hard cap on memory size
MAX_CHARS_PER_CHAT = 12000

SYSTEM = f"""Ты — фильтр долговременной памяти ассистентки Чисы о пользователе пользователе.
Сегодня {date.today().isoformat()}.

Главный тест для каждого факта: пригодится ли он Чисе ЧЕРЕЗ НЕДЕЛЮ в разговоре на другую тему?

Оцени важность каждого факта от 1 до 5:
5 — ключевое о жизни пользователя: работа, проекты, цели, важные события и сильные эмоции
    (пример: "получил оффер", "сорвался дедлайн по проекту", "готовится к собеседованию в пятницу").
4 — устойчивые предпочтения, планы с датами, обещания, повторяющиеся проблемы,
    шутки или прозвища, которые повторялись несколько раз.
3 — разовые интересные детали.
2 — обычная болтовня.
1 — приветствия, разовые подколы, а также ЛЮБЫЕ проверки и настройка самой Чисы
    (просил показать эмоции, проверял голос, "расскажи что-нибудь", тестовые фразы).

Правила:
- Источник фактов о пользователе — ТОЛЬКО реплики самого пользователя. Утверждения Чисы о пользователе
  НЕ факты: она шутит и выдумывает. Не записывай то, что сказала Чиса, как правду о нём.
- Жалобы и просьбы про работу самой Чисы (скорость ответа, голос, эмоции, характер) — это настройка, оценка 1.
- Объединяй повторы. Обновляй устаревшее (починил то, что было сломано — так и напиши). Удаляй неактуальное.
- Факты пиши коротко, одной фразой, по-русски, от третьего лица ("Пользователь ...").
- Верни ПОЛНЫЙ обновлённый список: старые факты из текущей памяти + новые, каждому — оценка.

Ответ строго в JSON без пояснений:
{{"memory": [{{"fact": "...", "importance": 5, "date": "YYYY-MM-DD или null"}}]}}"""


def find(d, key):
    if isinstance(d, dict):
        if key in d:
            return d[key]
        for v in d.values():
            r = find(v, key)
            if r:
                return r
    return None


def load_transcript(path: Path) -> str:
    items = json.loads(path.read_text(encoding="utf-8"))
    if sum(1 for i in items if i.get("role") == "human") < 2:
        return ""
    lines = []
    for item in items:
        if item.get("role") not in ("human", "ai"):
            continue
        text = re.sub(r"\[[a-z]+\]", "", item.get("content", "")).strip()
        if text:
            lines.append(f"{item.get('name', item['role'])}: {text}")
    return "\n".join(lines)[-MAX_CHARS_PER_CHAT:]


def parse_json(text: str) -> dict:
    """Models sometimes wrap JSON in ```json fences — strip them."""
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    return json.loads(text)


def save(items):
    MEMORY_JSON.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [f"- {i['fact']}" + (f" ({i['date']})" if i.get("date") else "") for i in items]
    MEMORY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    MEMORY_DIR.mkdir(exist_ok=True)
    processed = set(json.loads(STATE_FILE.read_text(encoding="utf-8"))) if STATE_FILE.exists() else set()
    current = json.loads(MEMORY_JSON.read_text(encoding="utf-8")) if MEMORY_JSON.exists() else []

    new_files = sorted(p for p in CHAT_DIR.rglob("*.json") if p.name not in processed)
    transcripts = [f"### Разговор {p.stem[:16]}\n{t}" for p in new_files if (t := load_transcript(p))]

    if transcripts:
        cfg = find(yaml.safe_load((ROOT / "conf.yaml").read_text(encoding="utf-8")), "openai_compatible_llm")
        client = OpenAI(api_key=cfg["llm_api_key"], base_url=cfg["base_url"])
        user = (f"Текущая память (JSON):\n{json.dumps(current, ensure_ascii=False)}\n\n"
                "Новые разговоры:\n\n" + "\n\n".join(transcripts))
        resp = client.chat.completions.create(
            model=cfg["model"],
            messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}],
            temperature=0.2,
            response_format={"type": "json_object"},
            extra_body={"reasoning": {"enabled": False}},
        )
        rated = parse_json(resp.choices[0].message.content)["memory"]

        # The code, not the model, decides what stays: threshold + sort + hard cap
        kept = [i for i in rated if i.get("importance", 0) >= THRESHOLD]
        kept.sort(key=lambda i: (i["importance"], i.get("date") or ""), reverse=True)
        current = kept[:MAX_ITEMS]

        print(f"Rated {len(rated)} facts, kept {len(current)} (importance >= {THRESHOLD}):")
        for i in rated:
            mark = "KEEP" if i in current else "drop"
            print(f"  [{mark}] {i.get('importance')} | {i['fact']}")
    else:
        print("No new conversations to remember.")

    save(current)
    STATE_FILE.write_text(json.dumps(sorted(processed | {p.name for p in new_files})), encoding="utf-8")


if __name__ == "__main__":
    main()