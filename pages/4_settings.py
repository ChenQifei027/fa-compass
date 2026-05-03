import os
import streamlit as st
from dotenv import load_dotenv, set_key
from pathlib import Path

load_dotenv()
ENV_PATH = Path(".env")

st.title("⚙️ 设置")

st.subheader("Claude API Key")
current_key = os.getenv("ANTHROPIC_API_KEY", "")
masked = f"{current_key[:8]}...{current_key[-4:]}" if len(current_key) > 12 else "未配置"
st.text(f"当前：{masked}")
new_key = st.text_input("输入新的 API Key", type="password", placeholder="sk-ant-...")
if st.button("保存 API Key") and new_key:
    set_key(str(ENV_PATH), "ANTHROPIC_API_KEY", new_key)
    st.success("API Key 已保存，请重启应用生效")

st.divider()
st.subheader("IT桔子 登录说明")
st.info("""
**首次使用 IT桔子 数据抓取：**
1. 在机构管理页面点击「抓取投资记录」
2. 系统会自动打开浏览器窗口
3. 手动完成 IT桔子 登录
4. 登录成功后浏览器会自动继续操作
5. 登录态会保存到本地，后续无需重复登录
""")

st.divider()
st.subheader("数据存储")
db_path = os.getenv("DB_PATH", "data/fa_matching.db")
bp_dir = os.getenv("BP_DIR", "data/bps")
st.text(f"数据库路径：{Path(db_path).absolute()}")
st.text(f"BP 文件目录：{Path(bp_dir).absolute()}")
