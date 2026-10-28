"""Build emotion expressions for a model with standard Live2D parameter names.

Usage: uv run python build_emotions.py <model_name>
"""
import json
import sys
from pathlib import Path

NAME = sys.argv[1]
DIR = Path(__file__).resolve().parent / "live2d-models" / NAME
MODEL = DIR / f"{NAME}.model3.json"
MODEL_DICT = Path(__file__).resolve().parent / "model_dict.json"

# Eye openness is MULTIPLIED (so blinking still works); everything else is overwritten.
# BrowForm: -1 = frowning (angry), 1 = worried. If brows look reversed, flip the signs.
EMOTIONS = {
    "neutral": {},
    "joy": {"ParamEyeLSmile": 1, "ParamEyeRSmile": 1, "ParamMouthForm": 1,
            "Param91": 0.3},
    "smirk": {"ParamEyeLSmile": 0.6, "ParamEyeRSmile": 0.2, "ParamMouthForm": 0.6,
              "ParamEyeLOpen": 0.75, "ParamBrowLForm": -0.3},
    "anger": {"ParamBrowLForm": -1, "ParamBrowRForm": -1, "ParamMouthForm": -1,
              "ParamEyeLOpen": 0.8, "ParamEyeROpen": 0.8,
              "Param92": 1, "Param27": 0.5},
    "surprise": {"ParamBrowLForm": 0.6, "ParamBrowRForm": 0.6, "ParamMouthForm": -0.2,
                 "ParamEyeLOpen": 1.2, "ParamEyeROpen": 1.2},
    "fear": {"ParamBrowLForm": 1, "ParamBrowRForm": 1, "ParamMouthForm": -0.6,
             "ParamEyeLOpen": 1.1, "ParamEyeROpen": 1.1},
    "disgust": {"ParamBrowLForm": -0.7, "ParamBrowRForm": -0.7, "ParamMouthForm": -0.8,
                "ParamEyeLOpen": 0.6, "ParamEyeROpen": 0.6},
    "sadness": {"ParamBrowLForm": 1, "ParamBrowRForm": 1, "ParamMouthForm": -1,
                "ParamEyeLOpen": 0.65, "ParamEyeROpen": 0.65},
    "blush": {"ParamBrowLForm": -0.4, "ParamBrowRForm": -0.4, "ParamMouthForm": -0.3,
              "ParamEyeLOpen": 0.85, "ParamEyeROpen": 0.85,
              "Param91": 1, "Param27": 1},
    "love": {"ParamEyeLSmile": 0.8, "ParamEyeRSmile": 0.8, "ParamMouthForm": 1,
             "Param91": 1},
}
MULTIPLY = {"ParamEyeLOpen", "ParamEyeROpen"}

model = json.loads(MODEL.read_text(encoding="utf-8"))
refs = model.setdefault("FileReferences", {})
# Keep only the model's original expressions, drop ones generated earlier
expressions = [e for e in refs.get("Expressions", []) if not e["Name"].startswith("emo_")]

print("Original expressions and the parameters they change:")
for e in expressions:
    data = json.loads((DIR / e["File"]).read_text(encoding="utf-8"))
    print(f"  {e['Name']}: {[p['Id'] for p in data.get('Parameters', [])]}")

expressions = []  # only our emotions: neutral becomes index 0 = the default face
by_name = {e["Name"]: i for i, e in enumerate(expressions)}
emotion_map = {}
for emotion, spec in EMOTIONS.items():
    if isinstance(spec, str):  # reuse an existing expression
        emotion_map[emotion] = by_name[spec]
        continue
    exp = {
        "Type": "Live2D Expression",
        "FadeInTime": 0.3,
        "FadeOutTime": 0.3,
        "Parameters": [
            {"Id": pid, "Value": v, "Blend": "Multiply" if pid in MULTIPLY else "Overwrite"}
            for pid, v in spec.items()
        ],
    }
    file_name = f"emo_{emotion}.exp3.json"
    (DIR / file_name).write_text(json.dumps(exp, indent=2), encoding="utf-8")
    expressions.append({"Name": f"emo_{emotion}", "File": file_name})
    emotion_map[emotion] = len(expressions) - 1

refs["Expressions"] = expressions
MODEL.write_text(json.dumps(model, ensure_ascii=False, indent=2), encoding="utf-8")

md = json.loads(MODEL_DICT.read_text(encoding="utf-8"))
for m in md:
    if m.get("name") == NAME:
        m["emotionMap"] = emotion_map
MODEL_DICT.write_text(json.dumps(md, ensure_ascii=False, indent=2), encoding="utf-8")
print("\nEmotion map:", emotion_map)