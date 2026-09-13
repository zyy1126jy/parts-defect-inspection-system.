# -*- coding: utf-8 -*-
"""
================================================================================
 C/S 架构桌面客户端（Client 端）—— 汽车零部件表面缺陷智能检测系统
================================================================================
本程序是系统的【C/S 客户端】(Client)，通过 HTTP 与【服务器端】(Server, FastAPI)
通信；与 B/S 端（浏览器打开 index.html）共用同一台服务器，构成 B/S 与 C/S
两种客户端形态的对照，满足课程设计“B/S、C/S 界面”的要求。

服务器端接口（backend/app.py）：
    GET  /api/health          健康检查（探测服务器是否在线）
    POST /api/detect          上传图片，返回缺陷类别/置信度/等级/缺陷框/标注图
    GET  /api/history?limit=n 历史检测记录
    GET  /api/stats           合格率、缺陷分布、SPC 控制图聚合数据

覆盖课程技术方向（≥3 个章节）：
    方向一 数字图像处理/机器视觉：展示服务器 OpenCV 流水线得到的缺陷框、
           面积占比、外接矩形长宽比、灰度均值/标准差（灰度化→高斯去噪→
           Otsu 阈值分割→形态学→轮廓提取）。
    方向二 机器学习缺陷分类：展示随机森林/规则分类器输出的 6 类缺陷、
           置信度与严重等级（良品/轻微/严重）。
    方向三 工业大数据与 SPC：质量看板展示合格率、缺陷类型分布柱状图、
           SPC 单值控制图（CL/UCL/LCL = 均值±3σ）。
    方向四 网络与体系结构：C/S 桌面客户端 + B/S 浏览器双端、HTTP 接口通信、
           前后端分离。

依赖（与服务器端一致，无需额外安装 Pillow）：
    tkinter（Python 标准库 GUI）、requests（HTTP）、opencv-python、numpy
运行：
    python client/desktop_client.py        或双击根目录“启动桌面客户端.bat”
================================================================================
"""
import base64
import queue
import threading
import subprocess
import sys
import webbrowser
from pathlib import Path

import numpy as np

try:
    import cv2
except ImportError:
    print("缺少 opencv-python，请先执行：pip install opencv-python numpy")
    raise

try:
    import requests
except ImportError:
    print("缺少 requests，请先执行：pip install requests")
    raise

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# 仓库根目录（本文件位于 ROOT/client/ 下）
ROOT = Path(__file__).resolve().parent.parent
SAMPLE_DIR = ROOT / "data" / "samples"
DEFAULT_URL = "http://127.0.0.1:8000"

# 严重等级配色
SEV_COLOR = {"良品": ("#2e9e5b", "#ffffff"),
             "轻微缺陷": ("#e6a23c", "#ffffff"),
             "严重缺陷": ("#e34d59", "#ffffff")}


# ----------------------------------------------------------------------------
# 图像工具：统一用 OpenCV 解码/缩放，再转 PNG 交给 tkinter 显示（Tk 8.6 原生支持，免 Pillow）
# ----------------------------------------------------------------------------
def path_to_bgr(path):
    """读图（np.fromfile 兼容中文路径），返回 BGR ndarray。"""
    raw = np.fromfile(str(path), dtype=np.uint8)
    img = cv2.imdecode(raw, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("图片无法解码：%s" % path)
    return img


def datauri_to_bgr(uri):
    """把后端返回的 data:image/jpeg;base64,xxx 解码为 BGR ndarray。"""
    _, b64 = uri.split(",", 1)
    raw = base64.b64decode(b64)
    arr = np.frombuffer(raw, dtype=np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)


def bgr_to_photo(bgr, max_w=380, max_h=300):
    """BGR 图像等比缩放并编码为 PNG，返回 tk.PhotoImage（Tk 8.6 原生支持 PNG，免 Pillow）。"""
    h, w = bgr.shape[:2]
    scale = min(max_w / w, max_h / h, 1.0)
    nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
    img = cv2.resize(bgr, (nw, nh))
    ok, buf = cv2.imencode(".png", img)
    if not ok:
        raise RuntimeError("PNG 编码失败")
    return tk.PhotoImage(data=base64.b64encode(buf.tobytes()).decode("ascii"))


# ----------------------------------------------------------------------------
# 服务器接口封装（C/S 中的 Client 侧通信层）
# ----------------------------------------------------------------------------
class ApiClient:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip("/")

    def health(self):
        r = requests.get(self.base_url + "/api/health", timeout=2)
        r.raise_for_status()
        return r.json()

    def detect(self, file_path):
        with open(file_path, "rb") as f:
            files = {"file": (Path(file_path).name, f.read(), "image/jpeg")}
        r = requests.post(self.base_url + "/api/detect", files=files, timeout=15)
        r.raise_for_status()
        return r.json()

    def history(self, limit=50):
        r = requests.get(self.base_url + "/api/history",
                         params={"limit": limit}, timeout=5)
        r.raise_for_status()
        return r.json()

    def stats(self):
        r = requests.get(self.base_url + "/api/stats", timeout=5)
        r.raise_for_status()
        return r.json()


# ----------------------------------------------------------------------------
# 主窗口
# ----------------------------------------------------------------------------
class DefectClientApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("汽车零部件表面缺陷智能检测系统 · C/S 桌面客户端")
        self.geometry("1120x860")
        self.minsize(1000, 760)
        self.api = ApiClient(DEFAULT_URL)
        self.current_image = None          # 当前选中的图片路径
        self._result_photo = None
        self._input_photo = None
        self._ui_queue = queue.Queue()     # 子线程 -> 主线程 的 UI 任务队列（线程安全）

        self._build_style()
        self._build_topbar()
        self._build_detect_area()
        self._build_notebook()
        self._build_statusbar()
        self._layout_weights()

        # 主线程周期处理子线程回传的 UI 任务（保证所有 Tk 操作都在主线程）
        self.after(50, self._drain_ui_queue)
        # 启动后自动探测一次服务器并加载数据
        self.after(200, self.test_connection)
        self.after(400, self.refresh_history)
        self.after(500, self.refresh_dashboard)

    # ---- 样式 ----
    def _build_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TButton", font=("Microsoft YaHei", 10), padding=4)
        style.configure("TLabel", font=("Microsoft YaHei", 10))
        style.configure("Card.TLabelframe.Label",
                        font=("Microsoft YaHei", 10, "bold"), foreground="#0b6e8c")
        style.configure("Treeview", font=("Microsoft YaHei", 9), rowheight=24)
        style.configure("Treeview.Heading", font=("Microsoft YaHei", 9, "bold"))
        self.configure(bg="#eef1f4")

    # ---- 顶部：服务器连接栏 ----
    def _build_topbar(self):
        bar = ttk.Frame(self, padding=(10, 8))
        bar.grid(row=0, column=0, sticky="ew")
        ttk.Label(bar, text="服务器地址:").pack(side="left")
        self.url_var = tk.StringVar(value=DEFAULT_URL)
        ttk.Entry(bar, textvariable=self.url_var, width=28).pack(side="left", padx=6)
        ttk.Button(bar, text="测试连接", command=self.test_connection).pack(side="left")
        # 状态灯 + 文字
        self.lamp = tk.Canvas(bar, width=16, height=16, highlightthickness=0)
        self.lamp.pack(side="left", padx=(10, 3))
        self.conn_var = tk.StringVar(value="未检测")
        ttk.Label(bar, textvariable=self.conn_var, foreground="#555").pack(side="left")
        ttk.Button(bar, text="启动本地服务器", command=self.start_server).pack(side="left", padx=(16, 4))
        ttk.Button(bar, text="打开网页版(B/S)", command=self.open_web).pack(side="left")

    # ---- 中部：检测区（左原图 / 右结果+判定） ----
    def _build_detect_area(self):
        area = ttk.Frame(self, padding=(10, 4))
        area.grid(row=1, column=0, sticky="nsew")

        # 左：原图与操作
        left = ttk.Labelframe(area, text="① 选择 / 上传零件图片", style="Card.TLabelframe", padding=8)
        left.pack(side="left", fill="both", expand=True, padx=(0, 6))
        self.input_img = tk.Label(left, text="请选择图片", bg="#fafafa", fg="#888",
                                  width=52, height=16, relief="groove", bd=1)
        self.input_img.pack(fill="both", expand=True)
        row1 = ttk.Frame(left); row1.pack(fill="x", pady=6)
        ttk.Button(row1, text="选择图片…", command=self.choose_file).pack(side="left")
        ttk.Label(row1, text="  样例:").pack(side="left")
        self.sample_var = tk.StringVar()
        self.sample_box = ttk.Combobox(row1, textvariable=self.sample_var,
                                       width=18, state="readonly")
        self.sample_box.pack(side="left", padx=4)
        ttk.Button(row1, text="载入样例", command=self.load_sample).pack(side="left")
        self.detect_btn = ttk.Button(left, text="② 开始检测", command=self.do_detect, state="disabled")
        self.detect_btn.pack(fill="x", pady=(2, 0))
        self._fill_samples()

        # 右：结果图 + 判定信息
        right = ttk.Labelframe(area, text="③ 检测结果与判定", style="Card.TLabelframe", padding=8)
        right.pack(side="left", fill="both", expand=True, padx=(6, 0))
        self.result_img = tk.Label(right, text="等待检测", bg="#fafafa", fg="#888",
                                   width=52, height=12, relief="groove", bd=1)
        self.result_img.pack(fill="both", expand=True)

        info = ttk.Frame(right); info.pack(fill="x", pady=(8, 0))
        self.cls_var = tk.StringVar(value="缺陷类别：—")
        self.sev_var = tk.StringVar(value="—")
        ttk.Label(info, textvariable=self.cls_var,
                  font=("Microsoft YaHei", 12, "bold")).grid(row=0, column=0, sticky="w", columnspan=3)
        self.sev_lbl = tk.Label(info, textvariable=self.sev_var, fg="#fff", bg="#9aa6b2",
                                font=("Microsoft YaHei", 11, "bold"), width=10)
        self.sev_lbl.grid(row=0, column=3, sticky="e", padx=8)
        info.columnconfigure(2, weight=1)

        ttk.Label(info, text="置信度:").grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.conf_bar = ttk.Progressbar(info, length=240, maximum=100)
        self.conf_bar.grid(row=1, column=1, columnspan=2, sticky="we", pady=(6, 0), padx=6)
        self.conf_var = tk.StringVar(value="0.0%")
        ttk.Label(info, textvariable=self.conf_var).grid(row=1, column=3, sticky="e", pady=(6, 0))

        self.feat_var = tk.StringVar(value="缺陷框数量：—　面积占比：—　长宽比：—　灰度标准差：—")
        ttk.Label(info, textvariable=self.feat_var, foreground="#444", wraplength=480,
                  justify="left").grid(row=2, column=0, columnspan=4, sticky="w", pady=(6, 0))

    # ---- 下部：Notebook（历史记录 / 质量看板） ----
    def _build_notebook(self):
        nb = ttk.Notebook(self, padding=(8, 4))
        nb.grid(row=2, column=0, sticky="nsew", padx=8, pady=6)

        # Tab1 历史记录
        tab1 = ttk.Frame(nb, padding=6)
        nb.add(tab1, text="历史检测记录")
        top = ttk.Frame(tab1); top.pack(fill="x")
        ttk.Button(top, text="刷新历史", command=self.refresh_history).pack(side="right")
        cols = ("id", "time", "name", "cls", "conf", "sev", "area")
        heads = ("#", "时间", "文件名", "缺陷类别", "置信度", "等级", "面积占比")
        widths = (46, 140, 200, 150, 80, 90, 90)
        tree_frame = ttk.Frame(tab1); tree_frame.pack(fill="both", expand=True, pady=(6, 0))
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
        for c, h, w in zip(cols, heads, widths):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w, anchor="center")
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        self.tree.tag_configure("良品", background="#e8f6ee")
        self.tree.tag_configure("严重缺陷", background="#fdecee")
        self.tree.tag_configure("轻微缺陷", background="#fdf6ec")

        # Tab2 质量看板（技术方向三：SPC 统计）
        tab2 = ttk.Frame(nb, padding=6)
        nb.add(tab2, text="质量统计看板（SPC）")
        top2 = ttk.Frame(tab2); top2.pack(fill="x")
        ttk.Button(top2, text="刷新看板", command=self.refresh_dashboard).pack(side="right")

        cards = ttk.Frame(tab2); cards.pack(fill="x", pady=(6, 4))
        self.card_total = self._stat_card(cards, "总检测数", "0", 0)
        self.card_pass = self._stat_card(cards, "合格率", "0%", 1)
        self.card_ok = self._stat_card(cards, "良品数", "0", 2)
        self.card_ng = self._stat_card(cards, "缺陷数", "0", 3)
        self.card_sev = self._stat_card(cards, "轻微/严重", "0 / 0", 4)

        charts = ttk.Frame(tab2); charts.pack(fill="both", expand=True)
        ch1 = ttk.Labelframe(charts, text="缺陷类型分布（柱状图）", style="Card.TLabelframe", padding=4)
        ch1.pack(side="left", fill="both", expand=True, padx=(0, 4))
        self.canvas_bar = tk.Canvas(ch1, height=230, bg="#ffffff", highlightthickness=0)
        self.canvas_bar.pack(fill="both", expand=True)
        ch2 = ttk.Labelframe(charts, text="缺陷面积占比 SPC 单值控制图（UCL/CL/LCL=均值±3σ）",
                             style="Card.TLabelframe", padding=4)
        ch2.pack(side="left", fill="both", expand=True, padx=(4, 0))
        self.canvas_spc = tk.Canvas(ch2, height=230, bg="#ffffff", highlightthickness=0)
        self.canvas_spc.pack(fill="both", expand=True)
        self.spc_var = tk.StringVar(value="CL=—　UCL=—　LCL=—")
        ttk.Label(tab2, textvariable=self.spc_var, foreground="#555").pack(anchor="w")

    def _stat_card(self, parent, title, value, col):
        f = tk.Frame(parent, bg="#ffffff", bd=1, relief="solid")
        f.grid(row=0, column=col, padx=5, sticky="nsew")
        parent.columnconfigure(col, weight=1)
        tk.Label(f, text=title, bg="#ffffff", fg="#777",
                 font=("Microsoft YaHei", 9)).pack(pady=(8, 0))
        v = tk.Label(f, text=value, bg="#ffffff", fg="#0b6e8c",
                     font=("Microsoft YaHei", 16, "bold"))
        v.pack(pady=(0, 8))
        return v

    def _build_statusbar(self):
        self.status_var = tk.StringVar(value="就绪。")
        bar = ttk.Label(self, textvariable=self.status_var, relief="sunken",
                        anchor="w", padding=(8, 3))
        bar.grid(row=3, column=0, sticky="ew")

    def _layout_weights(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=2)
        self.rowconfigure(2, weight=3)

    # ---------------- 业务动作 ----------------
    def _fill_samples(self):
        imgs = []
        if SAMPLE_DIR.exists():
            imgs = [p.name for p in sorted(SAMPLE_DIR.glob("*"))
                    if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".bmp")]
        self.sample_box["values"] = imgs
        if imgs:
            self.sample_box.current(0)

    def set_status(self, msg, color="#333"):
        self.status_var.set(msg)

    def _set_lamp(self, ok):
        self.lamp.delete("all")
        color = "#2e9e5b" if ok else "#e34d59"
        self.lamp.create_oval(2, 2, 14, 14, fill=color, outline="")
        self.conn_var.set("已连接" if ok else "未连接")

    def _async(self, func, on_ok, on_err=None):
        """在子线程执行 func（不阻塞界面）；结果只投递到队列，由主线程统一回调。"""
        def worker():
            try:
                data = func()
                self._ui_queue.put(("ok", on_ok, data))
            except Exception as e:  # noqa
                self._ui_queue.put(("err", on_err or self._default_err, e))
        threading.Thread(target=worker, daemon=True).start()

    def _drain_ui_queue(self):
        """主线程周期调用：取出子线程回传的任务并在主线程执行（tkinter 非线程安全）。"""
        try:
            while True:
                _kind, cb, payload = self._ui_queue.get_nowait()
                try:
                    cb(payload)
                except Exception as e:  # noqa
                    messagebox.showerror("界面更新失败", str(e))
        except queue.Empty:
            pass
        self.after(50, self._drain_ui_queue)

    def _default_err(self, e):
        self.set_status("请求失败：%s" % e, "#c0392b")
        messagebox.showerror("通信失败", "与服务器通信出错：\n%s\n\n请确认服务器已启动（点“启动本地服务器”）。" % e)

    def _refresh_api(self):
        self.api = ApiClient(self.url_var.get().strip() or DEFAULT_URL)

    def test_connection(self):
        self._refresh_api()
        self.set_status("正在连接服务器…")

        def ok(d):
            self._set_lamp(True)
            self.set_status("服务器在线：%s（%s）" % (self.api.base_url, d.get("status")))

        def err(e):
            self._set_lamp(False)
            self.set_status("服务器未连接：%s" % e, "#c0392b")
        self._async(self.api.health, ok, err)

    def start_server(self):
        try:
            subprocess.Popen([sys.executable, str(ROOT / "run.py")], cwd=str(ROOT))
            self.set_status("正在后台启动服务器，约 2~5 秒后点“测试连接”…")
            self.after(4000, self.test_connection)
        except Exception as e:  # noqa
            messagebox.showerror("启动失败", str(e))

    def open_web(self):
        webbrowser.open(self.api.base_url)

    def choose_file(self):
        path = filedialog.askopenfilename(
            title="选择零件图片",
            filetypes=[("图片文件", "*.jpg *.jpeg *.png *.bmp"), ("所有文件", "*.*")])
        if path:
            self._load_input(path)

    def load_sample(self):
        name = self.sample_var.get()
        if not name:
            return
        self._load_input(SAMPLE_DIR / name)

    def _load_input(self, path):
        try:
            bgr = path_to_bgr(path)
            self._input_photo = bgr_to_photo(bgr)
            self.input_img.configure(image=self._input_photo, text="", width=0, height=0)
            self.current_image = str(path)
            self.detect_btn.configure(state="normal")
            self.set_status("已载入图片：%s" % Path(path).name)
        except Exception as e:  # noqa
            messagebox.showerror("载入失败", str(e))

    def do_detect(self):
        if not self.current_image:
            return
        self._refresh_api()
        self.detect_btn.configure(state="disabled")
        self.result_img.configure(text="检测中…", image="")
        self.set_status("正在调用服务器 /api/detect …")

        def ok(d):
            self.detect_btn.configure(state="normal")
            self._update_result(d)
            self.set_status("检测完成：%s（记录#%s）" % (d.get("defect_cn"), d.get("record_id")))
            self.refresh_history()
            self.refresh_dashboard()

        def err(e):
            self.detect_btn.configure(state="normal")
            self.result_img.configure(text="检测失败", image="")
            self._default_err(e)
        self._async(lambda: self.api.detect(self.current_image), ok, err)

    def _update_result(self, d):
        # 结果标注图
        try:
            bgr = datauri_to_bgr(d["vis_image"])
            self._result_photo = bgr_to_photo(bgr, max_h=240)
            self.result_img.configure(image=self._result_photo, text="", width=0, height=0)
        except Exception:
            self.result_img.configure(text="(结果图显示失败)")

        # 类别 / 等级
        self.cls_var.set("缺陷类别：%s（%s）" %
                         (d.get("defect_cn"), d.get("defect_class")))
        sev = d.get("severity", "—")
        bg, fg = SEV_COLOR.get(sev, ("#9aa6b2", "#ffffff"))
        self.sev_lbl.configure(text=sev, bg=bg, fg=fg)

        # 置信度
        conf = float(d.get("confidence", 0))
        self.conf_bar["value"] = conf * 100
        self.conf_var.set("%.1f%%" % (conf * 100))

        # 特征明细（技术方向一：图像处理特征）
        f = d.get("features", {})
        self.feat_var.set(
            "缺陷框数量：%d　面积占比：%.2f%%　外接矩形长宽比：%.2f　灰度均值：%.1f　灰度标准差：%.1f"
            % (len(d.get("bboxes", [])),
               float(f.get("area_ratio", 0)) * 100,
               float(f.get("aspect_ratio", 0)),
               float(f.get("gray_mean", 0)),
               float(f.get("gray_std", 0))))

    # ---- 历史记录 ----
    def refresh_history(self):
        self._refresh_api()

        def ok(rows):
            for i in self.tree.get_children():
                self.tree.delete(i)
            for r in rows:
                sev = r.get("severity", "")
                self.tree.insert("", "end", values=(
                    r.get("id"), r.get("timestamp"), r.get("image_name") or "-",
                    r.get("defect_class"),
                    "%.1f%%" % ((r.get("confidence") or 0) * 100),
                    sev,
                    "%.2f%%" % ((r.get("defect_area_ratio") or 0) * 100),
                ), tags=(sev,))
            self.set_status("历史记录已加载，共 %d 条。" % len(rows))
        self._async(lambda: self.api.history(50), ok)

    # ---- 质量看板（技术方向三） ----
    def refresh_dashboard(self):
        self._refresh_api()

        def ok(s):
            total = s.get("total", 0)
            by_sev = s.get("by_severity", {}) or {}
            ok_n = by_sev.get("良品", 0)
            minor = by_sev.get("轻微缺陷", 0)
            major = by_sev.get("严重缺陷", 0)
            self.card_total.configure(text=str(total))
            self.card_pass.configure(text="%.1f%%" % s.get("pass_rate", 0))
            self.card_ok.configure(text=str(ok_n))
            self.card_ng.configure(text=str(total - ok_n))
            self.card_sev.configure(text="%d / %d" % (minor, major))
            self._draw_bar(s.get("by_class", {}) or {})
            cc = s.get("control_chart", {}) or {}
            self._draw_spc(cc.get("points", []) or [], cc.get("cl", 0),
                           cc.get("ucl", 0), cc.get("lcl", 0))
            self.spc_var.set("CL=%.4f　UCL=%.4f　LCL=%.4f（近 %d 个样本）"
                             % (cc.get("cl", 0), cc.get("ucl", 0), cc.get("lcl", 0),
                                len(cc.get("points", []) or [])))
        self._async(self.api.stats, ok)

    def _draw_bar(self, data):
        c = self.canvas_bar
        c.delete("all")
        c.update_idletasks()
        w = max(c.winfo_width(), 300)
        h = max(c.winfo_height(), 200)
        if not data:
            c.create_text(w / 2, h / 2, text="暂无数据（先做几次检测）", fill="#999")
            return
        items = sorted(data.items(), key=lambda kv: kv[1], reverse=True)
        n = len(items)
        vmax = max(v for _, v in items) or 1
        base_y = h - 34
        top_y = 24
        slot = w / n
        bar_w = min(60, slot * 0.55)
        # 坐标轴
        c.create_line(36, top_y, 36, base_y, fill="#888")
        c.create_line(36, base_y, w - 8, base_y, fill="#888")
        for i, (name, v) in enumerate(items):
            cx = 36 + slot * i + slot / 2
            bh = (base_y - top_y) * (v / vmax)
            x0, x1 = cx - bar_w / 2, cx + bar_w / 2
            c.create_rectangle(x0, base_y - bh, x1, base_y, fill="#217ad9", outline="")
            c.create_text(cx, base_y - bh - 8, text=str(v), fill="#333",
                          font=("Microsoft YaHei", 9))
            c.create_text(cx, base_y + 12, text=name, fill="#444",
                          font=("Microsoft YaHei", 8), width=slot - 6)

    def _draw_spc(self, points, cl, ucl, lcl):
        c = self.canvas_spc
        c.delete("all")
        c.update_idletasks()
        w = max(c.winfo_width(), 300)
        h = max(c.winfo_height(), 200)
        left, right, top, base = 40, w - 12, 20, h - 30
        if not points:
            c.create_text(w / 2, h / 2, text="暂无数据（至少 2 次检测后生成控制限）", fill="#999")
            return
        vals = list(points)
        allv = vals + [ucl, cl, lcl]
        vmax, vmin = max(allv), min(allv)
        span = (vmax - vmin) or (abs(vmax) or 1)
        pad = span * 0.1
        vmax, vmin = vmax + pad, max(0.0, vmin - pad)

        def y_of(v):
            return base - (v - vmin) / ((vmax - vmin) or 1) * (base - top)

        def x_of(i):
            if len(vals) == 1:
                return (left + right) / 2
            return left + (right - left) * i / (len(vals) - 1)

        # 三条控制限
        for val, color, dash, tag in ((ucl, "#e34d59", (5, 4), "UCL"),
                                      (cl, "#888888", (3, 3), "CL"),
                                      (lcl, "#e34d59", (5, 4), "LCL")):
            yy = y_of(val)
            c.create_line(left, yy, right, yy, fill=color, dash=dash)
            c.create_text(right - 4, yy - 8, text="%s=%.3f" % (tag, val),
                          fill=color, anchor="e", font=("Consolas", 8))
        # 数据折线 + 点
        pts = [(x_of(i), y_of(v)) for i, v in enumerate(vals)]
        for i in range(len(pts) - 1):
            c.create_line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1],
                          fill="#0b6e8c", width=2)
        for x, y in pts:
            c.create_oval(x - 3, y - 3, x + 3, y + 3, fill="#0b6e8c", outline="")
        # 超限点标红
        for i, v in enumerate(vals):
            if v > ucl or v < lcl:
                x, y = pts[i]
                c.create_oval(x - 5, y - 5, x + 5, y + 5, outline="#e34d59", width=2)
        c.create_text(left, top - 6, text="面积占比（最近 %d 点）" % len(vals),
                      fill="#555", anchor="w", font=("Microsoft YaHei", 8))


def main():
    app = DefectClientApp()
    app.mainloop()


if __name__ == "__main__":
    main()
