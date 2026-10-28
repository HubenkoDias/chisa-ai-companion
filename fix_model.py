import json
import math
import re
from pathlib import Path

NAME = "shiroko"
DIR = Path(__file__).resolve().parent / "live2d-models" / NAME
MODEL = DIR / f"{NAME}.model3.json"
MODEL_DICT = Path(__file__).resolve().parent / "model_dict.json"

data = json.loads(MODEL.read_text(encoding="utf-8"))
refs = data.setdefault("FileReferences", {})

# 1. Read real parameter IDs straight from the .moc3 binary (both naming styles)
moc = DIR / refs["Moc"]
raw = moc.read_bytes()
param_ids = {m.decode() for m in re.findall(rb"PARAM_[A-Z0-9_]+|Param[A-Za-z0-9_]+", raw)}


def pick(*candidates):
    """Return the first candidate ID that actually exists in the model."""
    return next((c for c in candidates if c in param_ids), None)


ANGLE_X = pick("PARAM_ANGLE_X", "ParamAngleX")
ANGLE_Y = pick("PARAM_ANGLE_Y", "ParamAngleY")
ANGLE_Z = pick("PARAM_ANGLE_Z", "ParamAngleZ")
BODY_X = pick("PARAM_BODY_ANGLE_X", "ParamBodyAngleX", "Param49")  # Param49 = body X on shiroko
BREATH = pick("PARAM_BREATH", "ParamBreath")
EYE_L = pick("PARAM_EYE_L_OPEN", "ParamEyeLOpen")
EYE_R = pick("PARAM_EYE_R_OPEN", "ParamEyeROpen")
MOUTH = pick("PARAM_MOUTH_OPEN_Y", "ParamMouthOpenY")

# 2. EyeBlink and LipSync groups (replace whatever was there before)
groups = [g for g in data.get("Groups", []) if g.get("Name") not in ("EyeBlink", "LipSync")]
blink = [p for p in (EYE_L, EYE_R) if p]
if blink:
    groups.append({"Target": "Parameter", "Name": "EyeBlink", "Ids": blink})
if MOUTH:
    groups.append({"Target": "Parameter", "Name": "LipSync", "Ids": [MOUTH]})
data["Groups"] = groups

# 3. Generated idle motion: smooth seamless 6-second loop
DURATION, STEP = 6.0, 0.2
waves = {
    ANGLE_X: lambda t: 8 * math.sin(2 * math.pi * t / 6),
    ANGLE_Y: lambda t: 4 * math.sin(2 * math.pi * t / 3),
    ANGLE_Z: lambda t: 5 * math.sin(2 * math.pi * t / 6 + 1.0),
    BODY_X: lambda t: 4 * math.sin(2 * math.pi * t / 6 + 0.5),
    BREATH: lambda t: 0.5 + 0.5 * math.sin(2 * math.pi * t / 3),
}
curves, seg_total, pt_total = [], 0, 0
times = [round(i * STEP, 3) for i in range(int(DURATION / STEP) + 1)]
for pid, f in waves.items():
    if not pid:
        continue
    segs = [times[0], round(f(times[0]), 4)]
    for t in times[1:]:
        segs += [0, t, round(f(t), 4)]  # 0 = linear segment
    curves.append({"Target": "Parameter", "Id": pid, "Segments": segs})
    seg_total += len(times) - 1
    pt_total += len(times)
# Blinking baked into the idle loop: two blinks per 6-second cycle
BLINKS = (2.2, 5.0)  # seconds within the loop when she blinks


def blink_points():
    pts = [(0.0, 1.0)]
    for b in BLINKS:
        pts += [(b, 1.0), (b + 0.07, 0.0), (b + 0.17, 1.0)]  # close fast, open a bit slower
    pts.append((DURATION, 1.0))
    return pts


for pid in (EYE_L, EYE_R):
    if not pid:
        continue
    pts = blink_points()
    segs = [pts[0][0], pts[0][1]]
    for t, v in pts[1:]:
        segs += [0, round(t, 3), v]
    curves.append({"Target": "Parameter", "Id": pid, "Segments": segs})
    seg_total += len(pts) - 1
    pt_total += len(pts)
motion = {
    "Version": 3,
    "Meta": {
        "Duration": DURATION, "Fps": 30.0, "Loop": True, "AreBeziersRestricted": True,
        "CurveCount": len(curves), "TotalSegmentCount": seg_total,
        "TotalPointCount": pt_total, "UserDataCount": 0, "TotalUserDataSize": 0,
    },
    "Curves": curves,
}
(DIR / "idle_generated.motion3.json").write_text(json.dumps(motion, indent=2), encoding="utf-8")
refs.setdefault("Motions", {})["Idle"] = [{"File": "idle_generated.motion3.json"}]
MODEL.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

# 4. Tell the project to use the Idle group
md = json.loads(MODEL_DICT.read_text(encoding="utf-8"))
for m in md:
    if m.get("name") == NAME:
        m["idleMotionGroupName"] = "Idle"
MODEL_DICT.write_text(json.dumps(md, ensure_ascii=False, indent=2), encoding="utf-8")

print("Found params:", len(param_ids))
print("Groups:", [(g["Name"], g["Ids"]) for g in groups])
print("Idle motion curves:", [c["Id"] for c in curves])