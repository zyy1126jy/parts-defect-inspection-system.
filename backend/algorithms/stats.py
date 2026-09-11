"""
技术方向三：工业大数据分析与质量统计
基于历史检测记录计算缺陷分布、合格率、SPC 单值控制图上下限。
对应课程知识点：数据清洗、统计过程控制(SPC)、质量数据可视化。
"""
import statistics
from collections import Counter
from .classifier import CLASS_NAMES


def _cn(cls):
    return CLASS_NAMES.get(cls, "良品" if cls == "normal" else cls)


def build_dashboard(records):
    """把数据库记录聚合成前端可直接渲染的看板数据。"""
    total = len(records)
    if total == 0:
        return {"total": 0, "pass_rate": 0, "by_class": {},
                "by_severity": {}, "control_chart": []}

    ok = sum(1 for r in records if r["severity"] == "良品")
    by_class = Counter(_cn(r["defect_class"]) for r in records)
    by_sev = Counter(r["severity"] for r in records)

    # SPC 单值控制图：对 area_ratio 算 CL/UCL/LCL
    ratios = [r["defect_area_ratio"] for r in records
              if r["defect_area_ratio"] is not None]
    if len(ratios) >= 2:
        mean = statistics.mean(ratios)
        sd = statistics.pstdev(ratios)
        cl, ucl, lcl = mean, mean + 3 * sd, max(0.0, mean - 3 * sd)
    else:
        cl = ucl = lcl = 0.0

    return {
        "total": total,
        "pass_rate": round(ok / total * 100, 2),
        "by_class": dict(by_class),
        "by_severity": dict(by_sev),
        "control_chart": {
            "cl": round(cl, 4),
            "ucl": round(ucl, 4),
            "lcl": round(lcl, 4),
            "points": [round(r, 4) for r in ratios[-50:]],
        },
    }
