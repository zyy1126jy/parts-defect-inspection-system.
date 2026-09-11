"""
NEU 表面缺陷数据集预处理脚本
- 输入：NEU 原始目录（6 个子类，每类 300 张 200x200 灰度 bmp）
- 输出：统一 resize 到 224x224、按 8:2 划分 train/val、生成索引文件
用法：
    python data/preprocess.py --src ./NEU --dst ./data/NEU_proc
"""
import argparse
import shutil
from pathlib import Path
import cv2

CLASSES = ["crazing", "inclusion", "patches",
           "pitted_surface", "rolled-in_scale", "scratches"]
IMG_SIZE = (224, 224)
RATIO = 0.8   # 训练集比例


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="NEU 原始根目录")
    ap.add_argument("--dst", default="./data/NEU_proc")
    args = ap.parse_args()

    src, dst = Path(args.src), Path(args.dst)
    if not src.exists():
        raise SystemExit(f"[!] 找不到数据目录 {src}，请先从 "
                         "http://faculty.neu.edu.cn/songkechen/zh_CN/zdylm/263270/list/index.htm "
                         "或 Kaggle 镜像下载")

    for split in ["train", "val"]:
        for c in CLASSES:
            (dst / split / c).mkdir(parents=True, exist_ok=True)

    index_lines = []
    for c in CLASSES:
        files = sorted((src / c).glob("*.bmp"))
        n_train = int(len(files) * RATIO)
        for i, p in enumerate(files):
            img = cv2.imread(str(p), cv2.IMREAD_GRAYSCALE)
            if img is None:
                continue
            img = cv2.resize(img, IMG_SIZE)
            split = "train" if i < n_train else "val"
            out = dst / split / c / p.name
            cv2.imwrite(str(out), img)
            index_lines.append(f"{split}/{c}/{p.name}\t{c}")

    (dst / "index.txt").write_text("\n".join(index_lines), encoding="utf-8")
    print(f"[OK] 预处理完成，共 {len(index_lines)} 张 -> {dst}")


if __name__ == "__main__":
    main()
