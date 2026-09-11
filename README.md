# 汽车零部件表面缺陷智能检测系统

> 制造智能技术课程设计 · B/S 架构 demo · 基于 NEU 表面缺陷数据库

## 功能

- 上传零件图片，后端自动跑 OpenCV 传统视觉 + 机器学习分类
- 返回缺陷类别（NEU 6 类）、置信度、缺陷外接框、严重等级
- SQLite 持久化检测记录
- 实时看板：合格率、缺陷分布、SPC 单值控制图

## 技术栈

- 后端：FastAPI + SQLite
- 算法：OpenCV（传统视觉）+ scikit-learn（随机森林）
- 前端：原生 HTML + ECharts

## 快速启动

**方式一（推荐，一键）**：Windows 双击 `启动检测系统.bat`（或桌面快捷方式），
服务启动后浏览器自动打开 http://127.0.0.1:8000 ；关闭命令行窗口即停止服务。

**方式二（手动）**：

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动（start.py 会自动打开浏览器；或用 run.py 手动开浏览器）
python start.py

# 3. 浏览器打开
#    http://127.0.0.1:8000
```

## 数据集

- **NEU 东北大学表面缺陷数据库**
  - 官方：http://faculty.neu.edu.cn/songkechen/zh_CN/zdylm/263270/list/index.htm
  - Kaggle：https://www.kaggle.com/datasets/kaustubhdikshit/neu-surface-defect-database
- 6 类 × 300 张 = 1800 张，200×200 灰度 bmp
- 下载后执行 `python data/preprocess.py --src ./NEU --dst ./data/NEU_proc`
- 原始图片不入库，详见 [data/README.md](data/README.md)

## 三个技术方向

| 方向 | 文件 | 作用 |
|---|---|---|
| 数字图像处理 | `backend/algorithms/traditional_cv.py` | 灰度化/高斯/Otsu/形态学/轮廓提取 |
| 机器学习分类 | `backend/algorithms/classifier.py` | 几何特征 + 随机森林/规则分类 |
| 工业大数据 SPC | `backend/algorithms/stats.py` | 合格率、缺陷分布、UCL/CL/LCL |

## 目录

```
├── index.html              # 前端
├── start.py                # 一键启动（自动开浏览器）
├── run.py                  # 基础启动入口
├── 启动检测系统.bat         # Windows 双击启动
├── requirements.txt
├── backend/
│   ├── app.py              # FastAPI 路由
│   ├── database.py         # SQLite
│   └── algorithms/        # 三个技术方向 + 训练脚本
├── data/
│   ├── README.md           # 数据集说明
│   ├── preprocess.py        # 预处理
│   └── samples/             # 样例图
├── prompt/ai_record.json    # AI 对话记录
├── tests/test_api.py        # 冒烟测试
├── 答辩PPT.pptx
└── 学习笔记/选题说明/方案设计/设计说明书/需求规格说明书/演示视频脚本 .md
```

## 文档

- [学习笔记.md](学习笔记.md)
- [选题说明.md](选题说明.md)
- [方案设计.md](方案设计.md)
- [需求规格说明书.md](需求规格说明书.md)
- [设计说明书.md](设计说明书.md)
- [演示视频脚本.md](演示视频脚本.md)
- 答辩PPT.pptx
