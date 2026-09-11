"""API 冒烟测试：启动后 python tests/test_api.py"""
import requests, sys

BASE = "http://127.0.0.1:8000"

def test_health():
    r = requests.get(BASE + "/api/stats", timeout=3)
    assert r.status_code == 200, r.status_code
    print("[OK] /api/stats ->", r.json())

def test_history():
    r = requests.get(BASE + "/api/history", timeout=3)
    assert r.status_code == 200
    print("[OK] /api/history, records =", len(r.json()))

if __name__ == "__main__":
    try:
        test_health(); test_history()
    except Exception as e:
        print("[FAIL]", e); sys.exit(1)
