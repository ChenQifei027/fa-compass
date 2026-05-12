# Frontend Redesign: React + Vite + FastAPI

**Date:** 2026-05-12  
**Status:** Approved

## Overview

Replace the Streamlit frontend with a React + Vite single-page application styled after Linear's design system (dark theme, purple accent). A thin FastAPI layer wraps the existing `core/` Python functions as REST endpoints. The `core/` package and SQLite database are untouched. The original Streamlit `pages/` directory is kept in place as an archive.

## Design Decisions

- **Style:** Linear design system — `#0f0f1a` background, `#5b5bd6` / `#8b5cf6` accent, Inter font, subtle `#2a2a4a` borders
- **Navigation:** Top nav bar with four items: 项目管理 / 机构管理 / 匹配推荐 / 设置
- **Framework:** React + Vite (not Next.js — SSR provides no benefit for an internal tool)
- **API:** FastAPI with uvicorn, CORS enabled for localhost dev, Vite proxy `/api/*` → `:8000`
- **State:** React `useState` / `useEffect` only — no Redux or Zustand needed at this scope

## Directory Structure

```
fa-matching/
├── frontend/                  ← NEW: React + Vite app
│   ├── index.html
│   ├── vite.config.ts
│   ├── package.json
│   └── src/
│       ├── main.tsx
│       ├── App.tsx            ← top nav shell + page routing
│       ├── styles/
│       │   └── globals.css    ← Linear token variables, resets
│       ├── components/
│       │   ├── TopNav.tsx
│       │   ├── Badge.tsx
│       │   ├── ActionButton.tsx
│       │   ├── StatusDot.tsx
│       │   └── Modal.tsx      ← upload BP / add institution drawer
│       ├── pages/
│       │   ├── Projects.tsx
│       │   ├── Institutions.tsx
│       │   ├── Matching.tsx
│       │   └── Settings.tsx
│       └── api/
│           ├── client.ts      ← base fetch wrapper
│           ├── projects.ts
│           ├── institutions.ts
│           ├── matching.ts
│           └── settings.ts
│
├── api/                       ← NEW: FastAPI app
│   ├── main.py                ← app init, CORS, router registration
│   ├── jobs.py                ← in-memory job registry for background tasks
│   └── routers/
│       ├── projects.py
│       ├── institutions.py
│       ├── matching.py
│       ├── settings.py
│       └── jobs.py
│
├── core/                      ← UNCHANGED
├── data/                      ← UNCHANGED
├── pages/                     ← ARCHIVED (Streamlit, kept as-is)
├── app.py                     ← ARCHIVED (Streamlit entry, kept as-is)
└── tests/                     ← UNCHANGED
```

## Pages

### Projects.tsx (项目管理)

- **Toolbar:** "＋ 上传 BP" button (opens Modal) + search input, right-aligned project count
- **Table columns:** 项目名称 / 赛道 / 细分领域 / 融资阶段 / 所在地 / 操作
- **Row actions:** 📊 报告 · 🔬 行研 · 🔗 匹配 (links to Matching page with project pre-selected)
- **Upload Modal:** file picker (PDF/PPTX) → POST `/api/projects/parse` → editable form → POST `/api/projects`
- **Report Panel:** inline expansion below table row — shows basic info table + funding rounds table, 导出 Excel
- **Research Panel:** inline expansion — shows 行业概述 / 市场规模 / 竞争格局 / 融资热度 / 本项目定位

### Institutions.tsx (机构管理)

- **Tabs:** 机构列表 / 新增机构 / 导入 Excel
- **List tab table columns:** 机构名称 / 关注赛道 / 偏好阶段 / 投资记录数 / 操作
- **Row actions:** 详情 · 🔄 刷新（re-scrape IT桔子）
- **新增机构 tab:** form → POST `/api/institutions` → triggers background scrape
- **导入 Excel tab:** file upload → POST `/api/institutions/import`

### Matching.tsx (匹配推荐)

- **Tabs:** 项目 → 推荐机构 / 机构 → 推荐项目
- **Left panel:** scrollable list of projects (or institutions) as selectable cards
- **Right panel:** match result cards — each shows 机构名 / 分数 badge / 赛道+阶段 badges / 推荐理由 paragraph
- **"开始匹配" button:** POST `/api/matching/project-to-institutions` or `/institution-to-projects`
- Loading state: spinner overlay on right panel while streaming

### Settings.tsx (设置)

- **Section 1 — 推理模型:** API Key input (password masked) + model selector + 验证 button → GET `/api/settings/verify-llm`
- **Section 2 — IT桔子:** read-only Cookie status (detected / not detected) + last sync time + 手动同步 button → POST `/api/settings/sync-cookies`

## API Endpoints

### Projects
| Method | Path | Core function |
|--------|------|---------------|
| GET | `/api/projects` | `list_projects` |
| POST | `/api/projects` | `insert_project` |
| GET | `/api/projects/{id}` | `get_project` |
| PUT | `/api/projects/{id}` | `update_project` |
| DELETE | `/api/projects/{id}` | `delete_project` |
| POST | `/api/projects/parse` | `extract_text_from_file` + `extract_project_info` |
| POST | `/api/projects/{id}/report` | `extract_report_info` + `scrape_company_funding` |
| POST | `/api/projects/{id}/research` | `generate_industry_research` + `scrape_sector_companies` |
| GET | `/api/projects/{id}/funding-rounds` | `list_funding_rounds` |

### Institutions
| Method | Path | Core function |
|--------|------|---------------|
| GET | `/api/institutions` | `list_institutions` |
| POST | `/api/institutions` | `insert_institution` + `scrape_institution_investments` |
| GET | `/api/institutions/{id}` | `get_institution` |
| PUT | `/api/institutions/{id}` | `update_institution` |
| DELETE | `/api/institutions/{id}` | `delete_institution` |
| POST | `/api/institutions/{id}/scrape` | `scrape_institution_investments` |
| POST | `/api/institutions/import` | Excel parse + bulk `insert_institution` |
| GET | `/api/institutions/{id}/records` | `list_investment_records` |

### Matching
| Method | Path | Core function |
|--------|------|---------------|
| POST | `/api/matching/project-to-institutions` | `match_project_to_institutions` |
| POST | `/api/matching/institution-to-projects` | `match_institution_to_projects` |

### Jobs
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/jobs/{job_id}` | Poll background job status — returns `{status: pending\|running\|completed\|failed, result?: ...}` |

### Settings
| Method | Path | Core function |
|--------|------|---------------|
| GET | `/api/settings` | read `.env` |
| PUT | `/api/settings` | write `.env` |
| GET | `/api/settings/verify-llm` | `llm_is_configured` |
| POST | `/api/settings/sync-cookies` | `sync_safari_cookies` |

## CSS Design Tokens

```css
:root {
  --bg-base:       #080810;
  --bg-surface:    #0f0f1a;
  --bg-elevated:   #1a1a2e;
  --border:        #2a2a4a;
  --text-primary:  #e2e2e8;
  --text-secondary:#888;
  --text-muted:    #555;
  --accent:        #5b5bd6;
  --accent-light:  #8b5cf6;
  --success:       #3ecf8e;
  --warning:       #f59e0b;
  --radius-sm:     4px;
  --radius-md:     6px;
  --radius-lg:     8px;
}
```

## Long-running Operations

Scraping and LLM calls can take 30–180 seconds. Strategy:

1. Frontend fires POST → immediately gets `202 Accepted` + `job_id`
2. FastAPI runs the operation in a `BackgroundTask`
3. Frontend polls `GET /api/jobs/{job_id}` every 2s for status
4. On `completed`, refetch the relevant resource

This avoids HTTP timeout issues and keeps the UI responsive.

## Development Setup

```bash
# API
cd api
pip install fastapi uvicorn python-multipart
uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev          # http://localhost:5173
```

Vite proxy config in `vite.config.ts`:
```ts
server: {
  proxy: {
    '/api': 'http://localhost:8000'
  }
}
```

## Out of Scope

- Authentication / login — single-user local tool, no auth needed
- Mobile responsiveness — desktop-only internal tool
- Dark/light mode toggle — dark only, matching Linear default
- Pagination — project and institution counts are small (<200 rows)
