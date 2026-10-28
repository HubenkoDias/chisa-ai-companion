import json
import sys
from pathlib import Path

folder = Path(sys.argv[1])
models = list(folder.rglob("*.model3.json"))
if not models:
    sys.exit("No .model3.json found - this model will NOT work")

for m in models:
    data = json.loads(m.read_text(encoding="utf-8"))
    refs = data.get("FileReferences", {})
    moc = m.parent / refs.get("Moc", "")
    raw = moc.read_bytes() if moc.is_file() else b""
    motions = refs.get("Motions", {})
    print(f"\n=== {m.relative_to(folder)}")
    print("Moc file found:", moc.is_file())
    print("Expressions (.exp3):", len(refs.get("Expressions", [])))
    print("Motion groups:", {g: len(v) for g, v in motions.items()})
    print("Has Idle group:", any(g.lower().startswith("idle") for g in motions))
    print("Param names:", "standard (ParamAngleX)" if b"ParamAngleX" in raw
          else "old (PARAM_ANGLE_X)" if b"PARAM_ANGLE_X" in raw else "unknown")

print("\nLoose .exp3.json files:", len(list(folder.rglob("*.exp3.json"))))
print("Loose .motion3.json files:", len(list(folder.rglob("*.motion3.json"))))