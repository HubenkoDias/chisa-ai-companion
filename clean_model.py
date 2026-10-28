import json
from pathlib import Path

DIR = Path(__file__).resolve().parent / "live2d-models/aimeng"
MODEL = DIR / "aimeng.model3.json"

data = json.loads(MODEL.read_text(encoding="utf-8"))
motions = data.get("FileReferences", {}).get("Motions", {})

removed = []
for group, items in list(motions.items()):
    kept = [m for m in items if (DIR / m["File"]).exists()]
    removed += [f"{group}: {m['File']}" for m in items if m not in kept]
    if kept:
        motions[group] = kept
    else:
        del motions[group]

MODEL.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print("Removed broken references:", removed or "none")