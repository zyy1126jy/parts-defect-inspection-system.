# -*- coding: utf-8 -*-
"""
双击启动入口：启动 FastAPI 后端并自动打开浏览器。
- 若 8000 端口已被占用（说明服务已在运行），直接打开浏览器；
- 否则启动服务，就绪后自动打开页面；
- 关闭本窗口即停止服务。
"""
import os
import sys
import time
import socket
import threading
import webbrowser

os.chdir(os.path.dirname(os.path.abspath(__file__)))
URL = "http://127.0.0.1:8000"


def port_open(host="127.0.0.1", port=8000):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def open_when_ready():
    for _ in range(40):           # 最多等 20 秒
        if port_open():
            webbrowser.open(URL)
            return
        time.sleep(0.5)


def main():
    if port_open():
        print("检测到服务已在运行，直接打开浏览器...")
        webbrowser.open(URL)
        time.sleep(1.5)
        return

    print("=" * 48)
    print("  汽车零部件表面缺陷智能检测系统 启动中...")
    print("  浏览器将自动打开，请勿关闭本窗口")
    print("  停止服务：直接关闭本窗口")
    print("=" * 48)

    threading.Thread(target=open_when_ready, daemon=True).start()

    import uvicorn
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, log_level="info")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
