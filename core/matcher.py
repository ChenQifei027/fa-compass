# core/matcher.py
import json
import re

P2I_PROMPT = """你是专业的投资 FA 助手。根据项目信息和各机构的投资偏好画像，推荐最适合的投资机构。

项目信息：
{project_info}

投资机构列表（含偏好画像和历史记录）：
{institutions_info}

匹配评分维度（按优先级）：
1. 赛道吻合：项目赛道/细分是否出现在机构高频赛道或关注领域中
2. 轮次吻合：项目融资阶段是否在机构常投轮次或历史轮次分布中
3. 金额区间：项目融资需求是否与机构历史披露金额规模相符
4. 地域偏好：机构是否有投资同城市/地区项目的记录

评分标准：
- 高：赛道+轮次双吻合，或有明确历史投资同类项目
- 中：赛道或轮次单项吻合，其余无明显冲突
- 低：有一定关联但主要方向不符，或信息不足

返回前10名，JSON数组，每条包含：
- institution_id: 机构ID（整数）
- institution_name: 机构名称
- match_level: 高/中/低
- reason: 推荐理由（70字以内，具体说明哪条历史记录或偏好特征与项目对应）

只返回 JSON 数组，不要其他内容。"""

I2P_PROMPT = """你是专业的投资 FA 助手。根据投资机构的历史投资偏好画像，从项目列表中推荐最匹配的项目。

投资机构信息（含偏好画像和历史记录）：
{institution_info}

项目列表：
{projects_info}

匹配评分维度（按优先级）：
1. 赛道吻合：项目赛道/细分是否出现在机构高频赛道或关注领域中
2. 轮次吻合：项目融资阶段是否在机构常投轮次或历史轮次分布中
3. 金额区间：项目融资需求是否与机构历史披露金额规模相符
4. 地域偏好：机构是否有投资同城市/地区项目的记录

评分标准：
- 高：赛道+轮次双吻合，或有明确历史投资同类项目
- 中：赛道或轮次单项吻合，其余无明显冲突
- 低：有一定关联但主要方向不符，或信息不足

返回所有项目的评分，JSON数组，每条包含：
- project_id: 项目ID（整数）
- project_name: 项目名称
- match_level: 高/中/低
- reason: 推荐理由（70字以内，具体说明赛道/轮次/金额哪些维度与机构历史对应）

只返回 JSON 数组，不要其他内容。"""


def analyze_investment_records(records: list) -> dict:
    """从历史投资记录中统计投资偏好特征。"""
    from collections import Counter
    from datetime import datetime

    if not records:
        return {}

    sectors = [r["sector"] for r in records if r.get("sector") and r["sector"] not in ("", "未知")]
    stages = [r["stage"] for r in records if r.get("stage") and r["stage"] not in ("", "未知", "未透露")]
    top_sectors = [s for s, _ in Counter(sectors).most_common(5)]
    top_stages = [s for s, _ in Counter(stages).most_common(5)]

    cutoff_year = datetime.now().year - 2
    recent_count = sum(
        1 for r in records
        if r.get("invested_date") and len(r["invested_date"]) >= 4
        and int(r["invested_date"][:4]) >= cutoff_year
    )

    disclosed_amounts = [
        r["amount"] for r in records
        if r.get("amount") and "透露" not in r["amount"] and "披露" not in r["amount"]
    ]

    return {
        "total_count": len(records),
        "recent_2y_count": recent_count,
        "top_sectors": top_sectors,
        "top_stages": top_stages,
        "amount_samples": disclosed_amounts[:8],
    }


def _fmt_project(p: dict) -> str:
    return (f"名称:{p.get('name')} | 赛道:{p.get('sector')} | 细分:{p.get('sub_sector')} | "
            f"阶段:{p.get('stage')} | 地点:{p.get('location')} | "
            f"简介:{p.get('description')} | 亮点:{p.get('highlights')} | "
            f"融资需求:{p.get('financing_need')}")


def _fmt_institution(inst: dict) -> str:
    analysis = inst.get("portfolio_analysis") or {}
    if analysis:
        analysis_str = (
            f"\n【投资偏好画像（基于{analysis['total_count']}条历史记录）】"
            f"\n  高频赛道：{', '.join(analysis['top_sectors']) or '暂无'}"
            f"\n  高频轮次：{', '.join(analysis['top_stages']) or '暂无'}"
            f"\n  近2年活跃：{analysis['recent_2y_count']}笔"
            f"\n  披露金额样本：{', '.join(analysis['amount_samples']) or '暂无'}"
        )
    else:
        analysis_str = ""

    records_sample = inst.get("investment_records_sample") or ""

    return (
        f"ID:{inst.get('id')} | 名称:{inst.get('name')} | "
        f"关注领域（标注）:{inst.get('preferred_sectors')} | "
        f"投资轮次（标注）:{inst.get('preferred_stages')} | "
        f"管理规模:{inst.get('aum')} | 地点:{inst.get('location')} | "
        f"特殊偏好:{inst.get('known_preferences')}"
        f"{analysis_str}"
        f"\n  近期投资记录（公司/赛道/轮次/金额）：{records_sample}"
    )


def _parse_json_list(text: str) -> list:
    text = re.sub(r"^```json\s*|\s*```$", "", text.strip(), flags=re.MULTILINE).strip()
    try:
        result = json.loads(text)
        return result if isinstance(result, list) else []
    except json.JSONDecodeError:
        return []


def match_project_to_institutions(project: dict, institutions: list, api_key: str = "") -> list:
    from core.llm import call_llm
    project_info = _fmt_project(project)
    institutions_info = "\n".join(_fmt_institution(i) for i in institutions)
    raw = call_llm(P2I_PROMPT.format(project_info=project_info,
                                     institutions_info=institutions_info))
    return _parse_json_list(raw)


def match_institution_to_projects(institution: dict, projects: list, api_key: str = "") -> list:
    from core.llm import call_llm
    institution_info = _fmt_institution(institution)
    projects_info = "\n".join(f"ID:{p.get('id')} | {_fmt_project(p)}" for p in projects)
    raw = call_llm(I2P_PROMPT.format(institution_info=institution_info,
                                     projects_info=projects_info))
    return _parse_json_list(raw)
