"""
在 NEU 数据集上训练随机森林分类器，输出 data/rf_model.json。
用法：
    python -m backend.algorithms.train_classifier --data-root ./data/NEU
NEU 目录结构：
    NEU/
      crazing/xxx.jpg
      inclusion/xxx.jpg
      ...
若未下载数据集，本脚本会退出并提示；系统在缺模型时自动走规则分类。
"""
import argparse, json, sys
from pathlib import Path
import cv2
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

LABELS = ["crazing", "inclusion", "patches",
          "pitted_surface", "rolled-in_scale", "scratches"]


def feat(img_path):
    img = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        return None
    img = cv2.resize(img, (224, 224))
    blur = cv2.GaussianBlur(img, (5, 5), 0)
    _, th = cv2.threshold(blur, 0, 255,
                          cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    cnts, _ = cv2.findContours(th, cv2.RETR_EXTERNAL,
                               cv2.CHAIN_APPROX_SIMPLE)
    areas, ars, stds = [], [], []
    for c in cnts:
        a = cv2.contourArea(c)
        if a < 20:
            continue
        areas.append(a)
        r = cv2.minAreaRect(c)
        ws = sorted([r[1][0], r[1][1]])
        ars.append(ws[1] / ws[0] if ws[0] else 1)
    return [
        sum(areas) / (224 * 224),
        max(ars) if ars else 1.0,
        float(img.std()),
        float(th.mean() / 255.0),
        len(areas),
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", required=True)
    args = ap.parse_args()
    root = Path(args.data_root)
    if not root.exists():
        print(f"[!] 数据集目录不存在: {root}", file=sys.stderr)
        sys.exit(1)

    X, y = [], []
    for label in LABELS:
        d = root / label
        if not d.exists():
            continue
        for p in d.glob("*.bmp"):
            f = feat(p)
            if f:
                X.append(f); y.append(label)
    if not X:
        print("[!] 未读到样本", file=sys.stderr)
        sys.exit(1)

    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, stratify=y)
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(Xtr, ytr)
    print(classification_report(yte, clf.predict(Xte)))

    centers = {lab: [float(np.mean([x for x, t in zip(X, y) if t == lab], 0)[i])
                     for i in range(5)] for lab in LABELS}
    out = Path(__file__).resolve().parent.parent.parent / "data" / "rf_model.json"
    out.write_text(json.dumps({"centers": {k: dict(zip(
        ["area_ratio", "aspect_ratio", "gray_std", "th_mean", "n_cnt"], v))
        for k, v in centers.items()}}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    print(f"[OK] 模型已写入 {out}")


if __name__ == "__main__":
    main()
