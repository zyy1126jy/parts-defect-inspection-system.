# 数据集说明

## 数据集：NEU 表面缺陷数据库（NEU Surface Defect Database）

- **发布单位**：东北大学 (Northeastern University, NEU)
- **官方下载**：http://faculty.neu.edu.cn/songkechen/zh_CN/zdylm/263270/list/index.htm
- **Kaggle 镜像**：https://www.kaggle.com/datasets/kaustubhdikshit/neu-surface-defect-database
- **规模**：6 类典型热轧钢带表面缺陷，每类 300 张，共 1800 张
- **原始规格**：200×200 像素灰度图（.bmp）

## 缺陷类别

| 英文目录 | 中文含义 | 形态特征 |
|---|---|---|
| crazing | 裂纹 | 细长线状、低灰度 |
| inclusion | 夹杂 | 不规则小块、灰度不均 |
| patches | 斑块 | 大面积、高对比 |
| pitted_surface | 麻点 | 多个小坑点 |
| rolled-in_scale | 轧入氧化皮 | 大面积纹理状 |
| scratches | 划痕 | 细长亮/暗线 |

## 目录结构

```
data/
├── README.md               # 本文件
├── preprocess.py            # 预处理脚本（resize 224×224、train/val 8:2 划分）
├── preprocess_output_index.txt  # 预处理完成标记
├── samples/                 # 仓库内置少量样例图（供前端演示）
├── inspection.db            # 运行后自动生成的 SQLite 检测记录库
└── rf_model.json            # 运行 train_classifier.py 后生成的分类权重
```

## 使用方式

1. 从上面任一链接下载 NEU 数据集，解压为如下结构：
   ```
   NEU/
     crazing/xxx.bmp
     inclusion/xxx.bmp
     ...
   ```
2. 执行预处理：
   ```
   python data/preprocess.py --src ./NEU --dst ./data/NEU_proc
   ```
3. 训练随机森林分类权重（可选，缺省时系统走规则分类）：
   ```
   python -m backend.algorithms.train_classifier --data-root ./data/NEU_proc/train
   ```

> 因 GitHub 仓库体积限制，原始 1800 张图片不入库，仅保留链接与说明。
