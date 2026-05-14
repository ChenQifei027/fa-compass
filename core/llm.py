import os
import subprocess


def _call_claude_cli(prompt: str, model: str) -> str:
    # 从子进程环境中移除 API key，让 claude CLI 使用本地登录态而非 API key 认证
    env = {k: v for k, v in os.environ.items()
           if k not in ("ANTHROPIC_API_KEY", "LLM_API_KEY")}
    # claude -p <prompt> 期望 prompt 作为位置参数，不是 stdin
    cmd = ["claude", "-p", prompt]
    if model:
        cmd.extend(["--model", model])
    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=300, env=env
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "（无输出）").strip()[:500]
        raise RuntimeError(f"Claude CLI 调用失败 (rc={result.returncode}): {detail}")
    if not result.stdout.strip():
        stderr_hint = result.stderr.strip()[:200] if result.stderr else ""
        raise RuntimeError(f"Claude CLI 返回空输出。stderr: {stderr_hint or '（无）'}")
    return result.stdout.strip()


def _call_anthropic(prompt: str, api_key: str, model: str) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text


def _call_openai_compatible(prompt: str, api_key: str, base_url: str, model: str) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=api_key or "ollama", base_url=base_url)
    response = client.chat.completions.create(
        model=model,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content


def call_llm(prompt: str) -> str:
    provider = os.getenv("LLM_PROVIDER", "").strip()
    model = os.getenv("LLM_MODEL", "claude-sonnet-4-6")

    if provider == "claude_cli":
        return _call_claude_cli(prompt, model)

    api_key = os.getenv("LLM_API_KEY") or os.getenv("ANTHROPIC_API_KEY", "")
    base_url = os.getenv("LLM_BASE_URL", "").strip()

    if not base_url or model.startswith("claude-"):
        return _call_anthropic(prompt, api_key, model)
    return _call_openai_compatible(prompt, api_key, base_url, model)


_PLAYWRIGHT_TOOLS = ",".join([
    "mcp__playwright__browser_navigate",
    "mcp__playwright__browser_snapshot",
    "mcp__playwright__browser_click",
    "mcp__playwright__browser_type",
    "mcp__playwright__browser_fill_form",
    "mcp__playwright__browser_wait_for",
    "mcp__playwright__browser_press_key",
    "mcp__playwright__browser_select_option",
    "mcp__playwright__browser_scroll",
])


def call_claude_with_browser(task: str) -> str:
    """通过 Claude CLI + Playwright MCP 执行浏览器自动化任务，返回 Claude 的最终输出。"""
    model = os.getenv("LLM_MODEL", "claude-sonnet-4-6")
    cmd = ["claude", "-p", task, "--model", model, "--allowedTools", _PLAYWRIGHT_TOOLS]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        raise RuntimeError(f"Claude 浏览器调用失败: {result.stderr.strip()}")
    return result.stdout.strip()


def get_langchain_llm():
    """返回适配当前配置的 langchain LLM 实例，供 browser-use 使用。"""
    if os.getenv("LLM_PROVIDER", "").strip() == "claude_cli":
        raise RuntimeError("Claude Code CLI 模式不支持 browser-use，请切换为 API 模式")

    api_key = os.getenv("LLM_API_KEY") or os.getenv("ANTHROPIC_API_KEY", "")
    base_url = os.getenv("LLM_BASE_URL", "").strip()
    model = os.getenv("LLM_MODEL", "claude-sonnet-4-6")

    if not base_url or model.startswith("claude-"):
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=model, anthropic_api_key=api_key)

    from langchain_openai import ChatOpenAI
    return ChatOpenAI(model=model, openai_api_key=api_key or "ollama",
                      openai_api_base=base_url)


def llm_is_configured() -> bool:
    if os.getenv("LLM_PROVIDER", "").strip() == "claude_cli":
        return True
    api_key = os.getenv("LLM_API_KEY") or os.getenv("ANTHROPIC_API_KEY", "")
    base_url = os.getenv("LLM_BASE_URL", "").strip()
    return bool(base_url or api_key)
