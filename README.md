# 汽车零部件表面缺陷智能检测系统

> 制造智能技术课程设计 · **同时提供 B/S 与 C/S 两种客户端界面** · 基于 NEU 表面缺陷数据库
> 一台服务器（FastAPI）同时服务【浏览器 B/S】与【桌面 C/S】两种客户端，覆盖 ≥3 个课程章节。

## 功能

- 上传零件图片，后端自动跑 OpenCV 传统视觉 + 机器学习分类
- 返回缺陷类别（NEU 6 类 + 良品）、置信度、缺陷外接框、严重等级
- SQLite 持久化检测记录，支持历史查询
- 实时质量看板：合格率、缺陷类型分布、SPC 单值控制图（UCL/CL/LCL）
- **B/S 界面**：浏览器打开 `index.html`，无需安装客户端
- **C/S 界面**：`client/desktop_client.py` 桌面程序（tkinter），含连接管理、检测、
  结果图、判定面板、历史表格、SPC 看板，可一键启动本地服务器、一键打开网页版

## 两种架构对照（B/S 与 C/S）

| 对比项 | B/S（浏览器/服务器） | C/S（客户端/服务器） |
|---|---|---|
| 客户端 | 浏览器（Chrome/Edge） | 桌面程序 `client/desktop_client.py`（tkinter） |
| 启动方式 | 双击 `启动检测系统.bat`（或 `python start.py`） | 双击 `启动桌面客户端.bat` |
| 前端技术 | 原生 HTML + ECharts | Python tkinter + ttk + Canvas |
| 与服务器通信 | fetch / HTTP | requests / HTTP |
| 服务器端 | 同一套 FastAPI（`backend/app.py`），接口完全复用 | 同左 |
| 适用场景 | 零安装、多人通过浏览器访问 | 质检员工位固定客户端、界面功能更集中 |

> 两种客户端调用的是**同一台服务器、同一套 REST 接口**，体现前后端分离与体系结构知识点。

## 技术栈

- 服务器端：FastAPI + SQLite + Uvicorn
- 算法：OpenCV（传统视觉）+ scikit-learn（随机森林，缺权重时规则分类兜底）
- B/S 前端：原生 HTML + ECharts
- C/S 客户端：Python 标准库 tkinter（GUI）+ requests（HTTP），图片用 OpenCV 转 PNG 显示，**无需 Pillow**

## 快速启动

### 0. 安装依赖（仅首次）

```bash
pip install -r requirements.txt
```

### 1. 启动服务器（B/S 与 C/S 都依赖它）

- **方式一（一键）**：Windows 双击 `启动检测系统.bat`，服务启动后浏览器自动打开 http://127.0.0.1:8000 ；关闭命令行窗口即停止服务。
- **方式二（手动）**：`python start.py`（自动开浏览器）或 `python run.py`（只起服务）。

### 2a. 使用 B/S 界面

服务器启动后，浏览器访问 http://127.0.0.1:8000 ，上传图片 → 开始检测。

### 2b. 使用 C/S 桌面客户端

- 双击 `启动桌面客户端.bat`（或 `python client/desktop_client.py`）；
- 顶部确认状态灯为“已连接”（若服务器未启动，可直接点界面上的【启动本地服务器】）；
- 左侧“选择图片”或下拉“载入样例” → 点【开始检测】，右侧看结果图与判定；
- 下方两个页签查看【历史检测记录】与【质量统计看板（SPC）】；
- 点【打开网页版(B/S)】可随时切换到浏览器界面。

## 数据集

- **NEU 东北大学表面缺陷数据库**
  - 官方：http://faculty.neu.edu.cn/songkechen/zh_CN/zdylm/263270/list/index.htm
  - Kaggle：https://www.kaggle.com/datasets/kaustubhdikshit/neu-surface-defect-database
- 6 类 × 300 张 = 1800 张，200×200 灰度 bmp
- 下载后执行 `python data/preprocess.py --src ./NEU --dst ./data/NEU_proc`
- 原始图片不入库，详见 [data/README.md](data/README.md)；`data/samples/` 内置 3 张演示图，可直接验证全流程。

## 覆盖的课程章节（≥3 个技术方向）

| # | 课程技术方向 / 章节 | 对应知识点 | 代码位置 | B/S 体现 | C/S 体现 |
|---|---|---|---|---|---|
| 1 | 数字图像处理 / 机器视觉 | 灰度化、高斯去噪、Otsu 阈值分割、形态学、轮廓提取、外接矩形 | `backend/algorithms/traditional_cv.py` | 结果缺陷框图、特征 | 结果图、面积占比/长宽比/灰度特征面板 |
| 2 | 机器学习缺陷分类 | 特征工程、随机森林（`train_classifier.py`）、规则兜底、置信度、评级 | `backend/algorithms/classifier.py` | 类别/置信度/等级标签 | 类别、置信度进度条、等级彩色标签 |
| 3 | 工业大数据与质量统计（SPC） | 合格率、缺陷分布、单值控制图 UCL/CL/LCL=均值±3σ | `backend/algorithms/stats.py` | ECharts 柱状图 + 控制图 | Canvas 柱状图 + SPC 控制图 + 统计卡片 |
| 4 | 网络与软件体系结构 | B/S 与 C/S 架构、HTTP/REST、前后端分离、SQLite 持久化 | `backend/app.py`、`index.html`、`client/desktop_client.py` | 浏览器客户端 | tkinter 桌面客户端 |

## 目录

```
├── index.html                  # B/S 前端（浏览器页面）
├── client/
│   └── desktop_client.py       # C/S 桌面客户端（tkinter）
├── start.py                    # 一键启动服务器（自动开浏览器）
├── run.py                      # 基础启动入口（只起服务）
├── 启动检测系统.bat             # 双击：启动服务器（B/S）
├── 启动桌面客户端.bat           # 双击：启动 C/S 桌面客户端
├── requirements.txt
├── backend/
│   ├── app.py                  # FastAPI 路由（/api/health /api/detect /api/history /api/stats）
│   ├── database.py             # SQLite
│   └── algorithms/            # 三个课程技术方向 + 训练脚本
├── data/
│   ├── README.md              # 数据集说明
│   ├── preprocess.py          # 预处理
│   └── samples/               # 内置 3 张演示样例图
├── prompt/ai_record.json       # AI 对话记录
├── tests/test_api.py           # 冒烟测试
├── 答辩PPT.pptx
└── 学习笔记/选题说明/方案设计/设计说明书/需求规格说明书/演示视频脚本 .md
```

## 接口一览（B/S、C/S 共用）

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/` | 返回 B/S 前端页面 |
| GET | `/api/health` | 健康检查（客户端探测服务器在线状态） |
| POST | `/api/detect` | 上传图片，返回类别/置信度/等级/缺陷框/标注图(base64) |
| GET | `/api/history?limit=n` | 历史检测记录 |
| GET | `/api/stats` | 合格率/缺陷分布/SPC 聚合数据 |

## 文档

- [学习笔记.md](学习笔记.md)
- [选题说明.md](选题说明.md)
- [方案设计.md](方案设计.md)
- [需求规格说明书.md](需求规格说明书.md)
- [设计说明书.md](设计说明书.md)
- [演示视频脚本.md](演示视频脚本.md)
- 答辩PPT.pptx
