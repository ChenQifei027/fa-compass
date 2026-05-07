import json
from unittest.mock import patch
from core.researcher import generate_industry_research

_MOCK_RESPONSE = json.dumps({
    "industry_overview": "SSD固态硬盘使用NAND Flash芯片存储数据，读写速度远超机械硬盘。",
    "market_size": "2024年全球SSD市场规模约420亿美元，预计2028年达680亿美元，CAGR约13%。",
    "competitive_landscape": [
        {"name": "三星电子", "type": "海外巨头", "note": "全球市占率第一"},
        {"name": "绵存科技", "type": "目标公司", "note": "当前项目"}
    ],
    "financing_heat": {
        "summary": "近两年国内存储赛道融资活跃，以战略融资和B轮为主。",
        "recent_deals": [
            {"company": "长江存储", "stage": "战略融资", "amount": "10亿元", "date": "2024-01"}
        ]
    },
    "target_positioning": "绵存科技专注企业级PCIe 5.0 SSD，与长江存储互补。"
})


def test_generate_returns_all_five_sections():
    project = {
        "name": "绵存科技", "sector": "硬件", "sub_sector": "SSD存储",
        "description": "企业级SSD解决方案", "highlights": "性能第一", "financing_need": "5000万元"
    }
    companies = [{"name": "长江存储", "stage": "战略融资", "amount": "10亿元", "date": "2024-01"}]

    with patch("core.researcher.call_llm", return_value=_MOCK_RESPONSE):
        result = generate_industry_research(project, companies)

    assert result["industry_overview"] != ""
    assert result["market_size"] != ""
    assert isinstance(result["competitive_landscape"], list)
    assert len(result["competitive_landscape"]) >= 1
    assert "summary" in result["financing_heat"]
    assert isinstance(result["financing_heat"]["recent_deals"], list)
    assert result["target_positioning"] != ""


def test_generate_with_empty_companies():
    project = {
        "name": "绵存科技", "sector": "硬件", "sub_sector": "SSD存储",
        "description": "", "highlights": "", "financing_need": ""
    }

    with patch("core.researcher.call_llm", return_value=_MOCK_RESPONSE):
        result = generate_industry_research(project, [])

    assert isinstance(result, dict)
    assert "industry_overview" in result


def test_generate_returns_defaults_on_bad_json():
    project = {
        "name": "绵存科技", "sector": "硬件", "sub_sector": "SSD存储",
        "description": "", "highlights": "", "financing_need": ""
    }

    with patch("core.researcher.call_llm", return_value="not valid json at all"):
        result = generate_industry_research(project, [])

    assert isinstance(result, dict)
    for key in ("industry_overview", "market_size", "competitive_landscape",
                "financing_heat", "target_positioning"):
        assert key in result
