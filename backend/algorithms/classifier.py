"""
技术方向二：机器学习缺陷分类
基于传统CV提取的几何/灰度特征，用规则+轻量分类器判定 NEU 6 类缺陷：
    crazing 裂纹 / inclusion 夹杂 / patches 斑块 /
    pitted_surface 麻点 / rolled-in_scale 轧入氧化皮 / scratches 划痕
附 train_classifier.py 可在 NEU 数据集上训练随机森林，
若权重文件不存在则退化为基于几何特征的规则分类，保证 demo 可跑。
"""
import json
from pathlib import Path

MODEL_PATH = Path(__file__).resolve().parent.parent.parent / \
    "data" / "rf_model.json"

# NEU 六类缺陷中文标签
CLASS_NAMES = {
    "crazing": "裂纹",
    "inclusion": "夹杂",
    "patches": "斑块",
    "pitted_surface": "麻点",
    "rolled-in_scale": "轧入氧化皮",
    "scratches": "划痕",
}


def _rule_classify(f):
    """无权重时的规则分类：依据长宽比、面积占比、灰度差异。"""
    aspect = f["aspect_ratio"]
    area_ratio = f["area_ratio"]
    std = f["gray_std"]

    if area_ratio < 0.005 and std < 30:
        return "normal", 0.55            # 近似良品
    if aspect > 4.0 and area_ratio < 0.05:
        return "scratches", 0.75         # 细长划痕
    if area_ratio > 0.15:
        return "patches", 0.70           # 大面积斑块
    if aspect > 2.5:
        return "crazing", 0.68           # 细长裂纹
    if 0.01 < area_ratio < 0.08 and std > 40:
        return "inclusion", 0.65         # 不规则夹杂
    if area_ratio < 0.02:
        return "pitted_surface", 0.62    # 小麻点
    return "rolled-in_scale", 0.60       # 其余归氧化皮


def _model_classify(feat):
    """读取训练好的随机森林权重做加权投票（简化实现）。"""
    if not MODEL_PATH.exists():
        return None
    try:
        weights = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None
    # 用权重表里每类的特征中心距离做最近邻
    best, best_d = None, 1e18
    for cls, center in weights.get("centers", {}).items():
        d = sum((feat[k] - center.get(k, 0)) ** 2
                for k in ["area_ratio", "aspect_ratio", "gray_std"])
        if d < best_d:
            best_d, best = d, cls
    conf = max(0.5, min(0.95, 1.0 - best_d))
    return best, conf


def classify(features):
    """输入 features_list（traditional_cv 输出），返回整体判定。"""
    f = features[0]
    # 合并多块特征
    if len(features) > 1:
        f = {
            "area": sum(x["area"] for x in features),
            "area_ratio": sum(x["area_ratio"] for x in features),
            "perimeter": sum(x["perimeter"] for x in features),
            "aspect_ratio": max(x["aspect_ratio"] for x in features),
            "extent": sum(x["extent"] for x in features) / len(features),
            "gray_mean": sum(x["gray_mean"] for x in features) / len(features),
            "gray_std": max(x["gray_std"] for x in features),
        }

    if f["area_ratio"] < 0.003 and f["gray_std"] < 25:
        return {
            "defect_class": "normal",
            "defect_cn": "良品",
            "confidence": 0.90,
            "severity": "良品",
        }

    pred = _model_classify(f)
    if pred is None:
        pred = _rule_classify(f)
    cls, conf = pred
    severity = _severity(cls, f["area_ratio"])
    return {
        "defect_class": cls,
        "defect_cn": CLASS_NAMES.get(cls, cls),
        "confidence": round(float(conf), 3),
        "severity": severity,
    }


def _severity(cls, area_ratio):
    if cls == "normal":
        return "良品"
    if area_ratio > 0.10:
        return "严重缺陷"
    if area_ratio > 0.03:
        return "轻微缺陷"
    return "轻微缺陷"
