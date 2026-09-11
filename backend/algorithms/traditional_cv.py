"""
技术方向一：数字图像处理与传统机器视觉
对工件图像进行灰度化、高斯去噪、自适应阈值分割、形态学处理、
轮廓提取，输出缺陷区域的几何特征（面积、外接矩形、长宽比等）。
对应课程知识点：图像采集预处理、滤波去噪、阈值分割、边缘检测、形态学处理。
"""
import cv2
import numpy as np


def extract_defect_regions(image_bytes):
    """从图片字节流中提取缺陷候选区域。

    Returns:
        result: dict，含 bboxes、features、vis_encoded（标注图 base64）
    """
    arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("无法解码图片")

    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    # Otsu 自适应阈值：缺陷通常比背景更暗
    _, th = cv2.threshold(blur, 0, 255,
                          cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # 形态学开运算去噪点
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    th = cv2.morphologyEx(th, cv2.MORPH_OPEN, kernel, iterations=1)
    th = cv2.morphologyEx(th, cv2.MORPH_CLOSE, kernel, iterations=1)

    contours, _ = cv2.findContours(th, cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)

    bboxes = []
    features_list = []
    vis = img.copy()

    for c in contours:
        area = cv2.contourArea(c)
        if area < 20 or area > 0.4 * h * w:   # 过滤噪点和整图误检
            continue
        x, y, bw, bh = cv2.boundingRect(c)
        peri = cv2.arcLength(c, True)
        rect = cv2.minAreaRect(c)
        (rw, rh) = sorted([rect[1][0], rect[1][1]])
        aspect = (rh / rw) if rw > 0 else 1.0   # 长边/短边，越大越细长
        extent = area / (bw * bh) if bw * bh > 0 else 0.0

        # 缺陷区域灰度均值/方差
        mask = np.zeros(gray.shape, np.uint8)
        cv2.drawContours(mask, [c], -1, 255, -1)
        mean, std = cv2.meanStdDev(gray, mask=mask)

        bboxes.append({"x": int(x), "y": int(y),
                       "w": int(bw), "h": int(bh)})
        features_list.append({
            "area": float(area),
            "area_ratio": float(area / (h * w)),
            "perimeter": float(peri),
            "aspect_ratio": float(aspect),
            "extent": float(extent),
            "gray_mean": float(mean[0][0]),
            "gray_std": float(std[0][0]),
        })
        cv2.rectangle(vis, (x, y), (x + bw, y + bh), (0, 0, 255), 2)

    # 若没有检出连通块，用整图纹理特征兜底
    if not features_list:
        features_list.append({
            "area": 0.0, "area_ratio": 0.0, "perimeter": 0.0,
            "aspect_ratio": 1.0, "extent": 1.0,
            "gray_mean": float(gray.mean()),
            "gray_std": float(gray.std()),
        })

    return {
        "bboxes": bboxes,
        "features": features_list,
        "image_shape": [int(h), int(w)],
        "vis_image": vis,
    }
