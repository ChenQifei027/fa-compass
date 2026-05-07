# core/researcher.py
from core.bp_parser import _parse_json_safe
from core.llm import call_llm

INDUSTRY_RESEARCH_PROMPT = """你是一名资深行业分析师，正在为投资 FA 撰写简明行业研究报告。

目标公司信息：
- 公司名称：{name}
- 一级赛道：{sector}
- 细分领域：{sub_sector}
- 公司简介：{description}
- 核心亮点：{highlights}
- 融资需求：{financing_need}

IT桔子同赛道公司数据（可能为空）：
{sector_companies_text}

生成包含以下5个字段的 JSON：

1. industry_overview (string): 行业概述，3-4句，说明该行业做什么、解决什么问题、产业链位置
2. market_size (string): 市场规模与趋势，含估计规模、增速和预判
3. competitive_landscape (array): 每条含 name/type/note 三字段：
   - type 取值：海外巨头、国内头部、国内新兴、目标公司、IT桔子
   - 将 {name} 标记为 "目标公司"；IT桔子数据中的公司标记为 "IT桔子"
   - 至少5家，不超过10家
4. financing_heat (object): 含 summary (string) 和 recent_deals (array)，
   recent_deals 每条含 company/stage/amount/date，来自IT桔子数据或你的知识
5. target_positioning (string): 目标公司在竞争格局中的定位与差异化，2-3句

注意：JSON 字段值中不能出现裸 ASCII 双引号，如需引用专有名词请用书名号《》。
只返回合法 JSON，不要其他内容。"""

_DEFAULTS = {
    "industry_overview": "",
    "market_size": "",
    "competitive_landscape": [],
    "financing_heat": {"summary": "", "recent_deals": []},
    "target_positioning": "",
}


def generate_industry_research(project: dict, sector_companies: list) -> dict:
    """
    project: dict with keys name, sector, sub_sector, description, highlights, financing_need
    sector_companies: list of {"name", "stage", "amount", "date"} from IT桔子
    Returns: research dict with 5 sections (falls back to _DEFAULTS on parse failure)
    """
    if sector_companies:
        lines = [
            f"{c['name']} | {c.get('stage','')} | {c.get('amount','')} | {c.get('date','')}"
            for c in sector_companies
        ]
        sector_companies_text = "\n".join(lines)
    else:
        sector_companies_text = "（未获取到IT桔子数据，请根据行业知识补充）"

    prompt = INDUSTRY_RESEARCH_PROMPT.format(
        name=project.get("name", ""),
        sector=project.get("sector", ""),
        sub_sector=project.get("sub_sector", ""),
        description=project.get("description", ""),
        highlights=project.get("highlights", ""),
        financing_need=project.get("financing_need", ""),
        sector_companies_text=sector_companies_text,
    )

    raw = call_llm(prompt)
    data = _parse_json_safe(raw)

    result = dict(_DEFAULTS)
    for key in _DEFAULTS:
        if key in data:
            result[key] = data[key]

    if not isinstance(result["financing_heat"], dict):
        result["financing_heat"] = {"summary": "", "recent_deals": []}
    result["financing_heat"].setdefault("summary", "")
    result["financing_heat"].setdefault("recent_deals", [])

    return result
