from core.scraper import _parse_company_funding_from_text, _parse_sector_search_results


def test_parse_normal_rounds():
    lines = [
        "2020-04-13", "战略投资", "数千万人民币", "腾讯投资", "反馈",
        "2021-05-24", "Pre-A轮", "数千万人民币", "海贝资本（领投）", "高通Qualcomm", "反馈",
    ]
    result = _parse_company_funding_from_text(lines)
    assert len(result) == 2
    assert result[0]["round_date"] == "2020-04-13"
    assert result[0]["round_type"] == "战略投资"
    assert result[0]["amount"] == "数千万人民币"
    assert result[0]["investors"] == "腾讯投资"
    assert result[1]["investors"] == "海贝资本（领投）,高通Qualcomm"


def test_parse_filters_noise_tokens():
    lines = [
        "2022-06-01", "A轮", "未透露", "举报", "纠错", "红杉资本", "反馈",
    ]
    result = _parse_company_funding_from_text(lines)
    assert len(result) == 1
    assert result[0]["investors"] == "红杉资本"


def test_parse_empty_lines():
    assert _parse_company_funding_from_text([]) == []


def test_parse_no_date_lines():
    lines = ["这不是日期", "也不是", "随便什么"]
    assert _parse_company_funding_from_text(lines) == []


def test_parse_round_with_no_investors():
    lines = ["2023-01-01", "B轮", "未透露", "反馈"]
    result = _parse_company_funding_from_text(lines)
    assert len(result) == 1
    assert result[0]["investors"] == ""


def test_parse_sector_search_results_extracts_companies():
    page_text = (
        "ABC科技\n企业服务\nA轮\n5000万元\n2024-03-01\n"
        "噪声行\n"
        "XYZ公司\nAI\nB轮\n1亿元\n2023-11-15"
    )
    company_names = ["ABC科技", "XYZ公司"]
    result = _parse_sector_search_results(page_text, company_names)
    assert len(result) == 2
    assert result[0]["name"] == "ABC科技"
    assert result[0]["stage"] == "A轮"
    assert result[0]["amount"] == "5000万元"
    assert result[1]["name"] == "XYZ公司"
    assert result[1]["stage"] == "B轮"


def test_parse_sector_search_results_no_company_names():
    result = _parse_sector_search_results("random text\nA轮\n1亿", [])
    assert result == []


def test_parse_sector_search_results_caps_at_15():
    names = [f"公司{i}" for i in range(20)]
    text = "\n".join(names)
    result = _parse_sector_search_results(text, names)
    assert len(result) <= 15


def test_parse_sector_search_results_missing_funding_fields():
    result = _parse_sector_search_results("某科技\n噪声内容很长很长超过30字不应该被匹配", ["某科技"])
    assert len(result) == 1
    assert result[0]["name"] == "某科技"
    assert result[0]["stage"] == ""
    assert result[0]["amount"] == ""
