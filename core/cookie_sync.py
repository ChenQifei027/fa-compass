import json
from pathlib import Path


def sync_safari_cookies(state_path: str) -> int:
    """从 Safari 提取 IT桔子 cookie 写入 browser_state.json，返回同步数量。"""
    import browser_cookie3

    raw = list(browser_cookie3.safari(domain_name="itjuzi.com"))

    playwright_cookies = []
    for c in raw:
        playwright_cookies.append({
            "name": c.name,
            "value": c.value,
            "domain": c.domain,
            "path": c.path or "/",
            "expires": int(c.expires) if c.expires else -1,
            "httpOnly": False,
            "secure": bool(c.secure),
            "sameSite": "Lax",
        })

    path = Path(state_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    existing = {}
    if path.exists():
        try:
            existing = json.loads(path.read_text())
        except Exception:
            pass

    existing["cookies"] = playwright_cookies
    path.write_text(json.dumps(existing, ensure_ascii=False))
    return len(playwright_cookies)
