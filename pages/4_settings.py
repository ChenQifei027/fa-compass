import asyncio
import os
import streamlit as st
from dotenv import load_dotenv, set_key
from pathlib import Path

load_dotenv()
ENV_PATH = Path(".env")
BROWSER_STATE = Path(os.getenv("BROWSER_STATE_PATH", "data/browser_state.json"))


def _check_itjuzi_status() -> tuple[bool, int]:
    """返回 (已登录, cookie数量)，通过 browser_cookie3 直接读 Chrome。"""
    try:
        import browser_cookie3
        cookies = list(browser_cookie3.chrome(domain_name="itjuzi.com"))
        auth = [c for c in cookies if c.name in ("juzi_user", "juzi_token")]
        return len(auth) >= 1, len(cookies)
    except Exception:
        return False, 0


def _check_chrome_debug() -> bool:
    """检查 Chrome 是否正在以调试模式运行（port 9222）。"""
    import socket
    try:
        s = socket.create_connection(("127.0.0.1", 9222), timeout=1)
        s.close()
        return True
    except OSError:
        return False


async def _do_login():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
        )
        page = await context.new_page()
        await page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        await page.goto("https://www.itjuzi.com/user/login")
        try:
            await page.wait_for_function(
                "!window.location.href.includes('/user/login')",
                timeout=180000
            )
        except Exception:
            pass
        await asyncio.sleep(2)
        BROWSER_STATE.parent.mkdir(parents=True, exist_ok=True)
        await context.storage_state(path=str(BROWSER_STATE))
        await context.close()
        await browser.close()


_PRESETS = {
    "Claude Code CLI（本机登录态）": {"base_url": "__cli__", "model": "claude-sonnet-4-6"},
    "Claude (Anthropic)": {"base_url": "", "model": "claude-sonnet-4-6"},
    "DeepSeek": {"base_url": "https://api.deepseek.com/v1", "model": "deepseek-chat"},
    "阿里百炼 (Qwen)": {"base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "model": "qwen-turbo"},
    "Ollama (本地)": {"base_url": "http://localhost:11434/v1", "model": "qwen2.5:7b"},
}

st.title("⚙️ 设置")

# ── 推理模型配置 ──────────────────────────────────
st.subheader("推理模型配置")

preset = st.selectbox("快速填充预设", ["（手动填写）"] + list(_PRESETS.keys()))

cur_provider = os.getenv("LLM_PROVIDER", "")
cur_api_key = os.getenv("LLM_API_KEY") or os.getenv("ANTHROPIC_API_KEY", "")
cur_base_url = os.getenv("LLM_BASE_URL", "")
cur_model = os.getenv("LLM_MODEL", "claude-sonnet-4-6")

if preset != "（手动填写）":
    default_url = _PRESETS[preset]["base_url"]
    default_model = _PRESETS[preset]["model"]
else:
    default_url = cur_base_url
    default_model = cur_model

is_cli_mode = (default_url == "__cli__")

if is_cli_mode:
    st.info("使用本机 Claude Code CLI 登录态，无需 API Key。注意：网页抓取功能在此模式下不可用。")
    model_input = st.text_input("模型名称", value=default_model, placeholder="claude-sonnet-4-6")
    api_key_input = ""
    base_url_input = "__cli__"
else:
    api_key_input = st.text_input(
        "API Key", type="password", value=cur_api_key,
        placeholder="Anthropic: sk-ant-... | DeepSeek: sk-... | 阿里百炼: sk-..."
    )
    base_url_input = st.text_input(
        "API Base URL（Claude 可留空）", value=default_url,
        placeholder="https://api.deepseek.com/v1"
    )
    model_input = st.text_input("模型名称", value=default_model, placeholder="claude-sonnet-4-6")

if st.button("💾 保存模型配置"):
    if base_url_input == "__cli__":
        set_key(str(ENV_PATH), "LLM_PROVIDER", "claude_cli")
        set_key(str(ENV_PATH), "LLM_BASE_URL", "")
        set_key(str(ENV_PATH), "LLM_API_KEY", "")
        set_key(str(ENV_PATH), "LLM_MODEL", model_input)
    else:
        set_key(str(ENV_PATH), "LLM_PROVIDER", "")
        set_key(str(ENV_PATH), "LLM_API_KEY", api_key_input)
        set_key(str(ENV_PATH), "LLM_BASE_URL", base_url_input)
        set_key(str(ENV_PATH), "LLM_MODEL", model_input)
        if not base_url_input and api_key_input.startswith("sk-ant-"):
            set_key(str(ENV_PATH), "ANTHROPIC_API_KEY", api_key_input)
    st.success("已保存，请重启应用生效")

st.divider()

# ── IT桔子 抓取环境 ──────────────────────────────────
st.subheader("IT桔子 抓取环境")

logged_in, cookie_count = _check_itjuzi_status()
chrome_ready = _check_chrome_debug()

col_a, col_b = st.columns(2)
if logged_in:
    col_a.success(f"✅ Chrome 中已登录 IT桔子（{cookie_count} 个 cookie）")
else:
    col_a.warning("⚠️ Chrome 中未检测到 IT桔子 登录态\n\n请先在 Chrome 中登录 itjuzi.com")

if chrome_ready:
    col_b.success("✅ Chrome 调试模式已就绪（port 9222）")
else:
    col_b.error("❌ Chrome 未以调试模式运行")
    st.code(
        "/Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome"
        " --remote-debugging-port=9222"
        " --user-data-dir=/tmp/chrome-debug",
        language="bash"
    )
    st.caption("在终端执行上面的命令启动 Chrome 调试实例（只需启动一次，保持运行即可）")

st.divider()

# ── 数据存储 ──────────────────────────────────
st.subheader("数据存储")
db_path = os.getenv("DB_PATH", "data/fa_matching.db")
bp_dir = os.getenv("BP_DIR", "data/bps")
st.text(f"数据库路径：{Path(db_path).absolute()}")
st.text(f"BP 文件目录：{Path(bp_dir).absolute()}")
