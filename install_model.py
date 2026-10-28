"""Install any Live2D model into the project.

Usage: uv run python install_model.py <folder with .model3.json> <ascii_name>
"""
import json
import shutil
import sys
from pathlib import Path

src = Path(sys.argv[1])
NAME = sys.argv[2]
DST = Path(__file__).resolve().parent / "live2d-models" / NAME
MODEL_DICT = Path(__file__).resolve().parent / "model_dict.json"

model_src = next(src.rglob("*.model3.json"))

# 1. Copy the folder that contains the model and give the model file an ASCII name
if DST.exists():
    shutil.rmtree(DST)
shutil.copytree(model_src.parent, DST)
for p in DST.glob("*.model3.json"):
    if p.name != model_src.name:
        p.unlink()
model_path = DST / f"{NAME}.model3.json"
(DST / model_src.name).rename(model_path)

# 2. Register loose .exp3.json files as model expressions
data = json.loads(model_path.read_text(encoding="utf-8"))
refs = data.setdefault("FileReferences", {})
exp_files = sorted(DST.rglob("*.exp3.json"))
refs["Expressions"] = [
    {"Name": p.name.replace(".exp3.json", ""), "File": p.relative_to(DST).as_posix()}
    for p in exp_files
]
model_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

# 3. Register the model in model_dict.json (based on the mao_pro entry)
md = json.loads(MODEL_DICT.read_text(encoding="utf-8"))
md = [m for m in md if m.get("name") != NAME]
entry = dict(next(m for m in md if m.get("name") == "mao_pro"))
entry.update({
    "name": NAME,
    "url": f"/live2d-models/{NAME}/{NAME}.model3.json",
    "emotionMap": {},
    "tapMotions": {},
    "idleMotionGroupName": "",
})
md.append(entry)
MODEL_DICT.write_text(json.dumps(md, ensure_ascii=False, indent=2), encoding="utf-8")

print("Installed as:", NAME)
print("Expressions (index: name):")
for i, e in enumerate(refs["Expressions"]):
    print(f"  {i}: {e['Name']}")