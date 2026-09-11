"""FastAPI 主应用：对外提供检测、历史、统计三类 API。"""
import base64
import cv2
import numpy as np
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from . import database
from .algorithms import traditional_cv, classifier, stats

ROOT = Path(__file__).resolve().parent.parent

app = FastAPI(title="汽车零部件表面缺陷检测系统", version="1.0")


@app.get("/", response_class=HTMLResponse)
def index():
    return (ROOT / "index.html").read_text(encoding="utf-8")


@app.post("/api/detect")
async def detect(file: UploadFile = File(...)):
    raw = await file.read()
    if not raw:
        raise HTTPException(400, "空文件")

    # 技术方向一：传统视觉提取缺陷区域
    try:
        cv_result = traditional_cv.extract_defect_regions(raw)
    except ValueError:
        raise HTTPException(400, "图片解码失败，请上传 jpg/png")

    # 技术方向二：分类
    pred = classifier.classify(cv_result["features"])

    # 把标注图编码为 base64 返回
    ok, buf = cv2.imencode(".jpg", cv_result["vis_image"])
    vis_b64 = base64.b64encode(buf.tobytes()).decode() if ok else ""

    record_id = database.insert_record(
        image_name=file.filename,
        defect_class=pred["defect_class"],
        confidence=pred["confidence"],
        severity=pred["severity"],
        defect_area_ratio=cv_result["features"][0]["area_ratio"],
        bbox=cv_result["bboxes"],
        raw_features=cv_result["features"][0],
    )

    return JSONResponse({
        "record_id": record_id,
        "defect_class": pred["defect_class"],
        "defect_cn": pred["defect_cn"],
        "confidence": pred["confidence"],
        "severity": pred["severity"],
        "bboxes": cv_result["bboxes"],
        "features": cv_result["features"][0],
        "vis_image": "data:image/jpeg;base64," + vis_b64,
    })


@app.get("/api/history")
def history(limit: int = 50):
    return database.query_history(limit)


@app.get("/api/stats")
def stats_api():
    records = database.query_history(200)
    return stats.build_dashboard(records)
