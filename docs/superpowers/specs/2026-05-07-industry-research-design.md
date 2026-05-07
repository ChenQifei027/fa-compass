# 行业研究报告功能设计文档

**日期**：2026-05-07  
**状态**：已审批，待实现

---

## 背景

FA 在接到新项目 BP 后，通常对该项目所在细分行业缺乏背景知识（例如"SSD 存储是什么、市场有哪些玩家"）。需要在现有 BP 解析流程之后，增加一键生成行业研究报告的能力，帮助 FA 快速建立行业认知。

---

## 目标

用户在项目列表点击 🔬 按钮后，系统自动：
1. 用 IT桔子 搜索同赛道公司（实时数据）
2. 调用 LLM 综合生成行研报告
3. 缓存到数据库，下次直接展示

---

## 数据流

```
用户点击 [🔬 行研]
  │
  ├─ 有缓存 (research_generated_at 非空) → 直接展示
  │
  └─ 无缓存 → 生成流程：
       ├─ scraper.scrape_sector_companies(sub_sector, state_path)
       │    → IT桔子 搜索同赛道公司列表（最多15条）
       ├─ researcher.generate_industry_research(project, companies)
       │    → 组装 prompt → call_llm → _parse_json_safe → dict
       └─ database.upsert_project_research(db_path, project_id, json)
            → 写入 projects 表两列缓存
```

---

## 组件设计

### 新增文件：`core/researcher.py`

**职责**：接受项目信息 + IT桔子公司列表，返回结构化行研 JSON。

```python
def generate_industry_research(project: dict, sector_companies: list[dict]) -> dict:
    """
    project: {name, sector, sub_sector, description, highlights, financing_need}
    sector_companies: [{"name", "stage", "amount", "date"}, ...]
    返回 research_json dict
    """
```

**Prompt 要求**：
- 输入：项目基本信息 + IT桔子 同赛道公司列表
- 输出：5 个字段的 JSON（见下方输出格式）
- 约束：JSON 值中不出现裸 ASCII 双引号

### 修改文件：`core/scraper.py`

新增函数：

```python
def scrape_sector_companies(keyword: str, state_path: str) -> list[dict]:
    """
    在 IT桔子 搜索 keyword（通常为 sub_sector 或 sector），
    返回最多 15 家公司：[{"name", "stage", "amount", "date"}, ...]
    """
```

实现思路：
1. 访问 `https://www.itjuzi.com/search?data=<keyword>`
2. 提取 `/company/\d+` 链接对应的搜索结果条目
3. 从页面文本解析公司名、轮次、融资额、时间
4. 不需要访问各公司详情页（控制爬取时间）

### 修改文件：`core/database.py`

```python
# migrate：给 projects 表新增两列（幂等）
ALTER TABLE projects ADD COLUMN research_json TEXT;
ALTER TABLE projects ADD COLUMN research_generated_at TEXT;

def upsert_project_research(db_path: str, project_id: int, research_json: str) -> None:
    """写入或更新行研缓存"""
```

### 修改文件：`pages/1_projects.py`

1. 新增 `_render_research_panel(db_path, project, browser_state)` 函数
2. 项目列表列宽从 `[3,2,2,1,1,1,1]` 改为 `[3,2,2,1,1,1,1,1]`，新增 🔬 按钮列
3. session_state 新增 `research_project_id` 键，与现有 `report_project_id` 并列管理

---

## LLM 输出格式（`research_json`）

```json
{
  "industry_overview": "文字段落，3-4句，说明该行业是什么、解决什么问题、产业链位置",

  "market_size": "文字段落，含市场规模数字、增速、预判",

  "competitive_landscape": [
    {"name": "公司名", "type": "海外巨头|国内头部|国内新兴|目标公司|IT桔子", "note": "一句话描述"}
  ],

  "financing_heat": {
    "summary": "近两年融资热度概述",
    "recent_deals": [
      {"company": "公司名", "stage": "轮次", "amount": "金额", "date": "YYYY-MM"}
    ]
  },

  "target_positioning": "文字段落，2-3句，说明目标公司在竞争格局中的位置和差异化"
}
```

---

## UI 布局

### 项目列表行（新增 🔬 列）

```
项目名称 | 赛道 | 细分领域 | 融资阶段 | [📊] | [🔬] | [详情] | [🗑️]
列宽:  3     2      2        1       1     1      1      1
```

### 行研面板

```
🔬 {项目名} — 行业研究报告    [↺ 重新生成]  [📥 导出 MD]  [✕ 关闭]
生成时间：YYYY-MM-DD HH:MM

▌ 行业概述
  [文字]

▌ 市场规模 & 趋势
  [文字]

▌ 竞争格局                        数据来源：LLM + IT桔子
  表格：公司名称 | 类型 | 简介

▌ 融资热度（近两年）
  [概述文字]
  表格：公司 | 轮次 | 金额 | 时间

▌ 本项目定位
  [高亮文字框]
```

### 生成进度（`st.status`）

```
⏳ 正在生成行研报告...
  ✓ 从 IT桔子 搜索同赛道公司...
  ✓ LLM 分析行业格局...
  ✓ 完成，找到 N 家同赛道公司
```

### 导出格式

Markdown 文件：`{项目名}_行研报告.md`，适合粘贴到飞书/Notion。

---

## 错误处理

| 场景 | 处理方式 |
|------|---------|
| IT桔子 未登录 / 无数据 | 跳过爬取，仅用 LLM 知识生成，面板显示提示 |
| LLM 返回非法 JSON | `_parse_json_safe` 兜底，失败则 `st.error` 显示原始内容 |
| 生成过程异常 | `st.warning` 显示错误，不写入缓存 |

---

## 不在本期范围内

- 联网搜索（Tavily / Bing API）
- 多语言输出
- 行研报告版本历史
- 跨项目行研对比
