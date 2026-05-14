import { useState, useEffect, useCallback } from 'react'
import { institutionsApi } from '../api/institutions'
import type { Institution, InvestmentRecord } from '../api/institutions'
import { pollJob } from '../api/jobs'
import Badge from '../components/Badge'
import Spinner from '../components/Spinner'

type Tab = 'list' | 'add' | 'import'
type DetailTab = 'info' | 'records'

const inp: React.CSSProperties = {
  background: 'var(--bg-elevated)', border: '1px solid var(--border)',
  borderRadius: 6, padding: '7px 10px', color: 'var(--text-primary)', fontSize: 13, width: '100%'
}
const ghostBtn: React.CSSProperties = {
  background: 'transparent', color: 'var(--text-secondary)', border: '1px solid var(--border)',
  borderRadius: 6, padding: '5px 12px', fontSize: 12, cursor: 'pointer'
}

export default function Institutions() {
  const [tab, setTab] = useState<Tab>('list')
  const [institutions, setInstitutions] = useState<Institution[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [scraping, setScraping] = useState<Record<number, boolean>>({})
  const [scrapingAll, setScrapingAll] = useState(false)
  const [selectedId, setSelectedId] = useState<number | null>(null)

  const reload = useCallback(() =>
    institutionsApi.list().then(setInstitutions).finally(() => setLoading(false))
  , [])

  useEffect(() => { reload() }, [reload])

  const filtered = institutions.filter(i => !search || i.name.includes(search))
  const selected = institutions.find(i => i.id === selectedId) ?? null

  function rescrape(inst: Institution) {
    setScraping(s => ({ ...s, [inst.id]: true }))
    institutionsApi.scrape(inst.id).then(({ job_id }) =>
      pollJob(job_id,
        () => { setScraping(s => ({ ...s, [inst.id]: false })); reload() },
        () => setScraping(s => ({ ...s, [inst.id]: false }))
      )
    )
  }

  function scrapeAll() {
    setScrapingAll(true)
    institutionsApi.scrapeAll().then(({ job_id }) =>
      pollJob(job_id,
        () => { setScrapingAll(false); reload() },
        () => setScrapingAll(false)
      )
    )
  }

  const tabBtn = (t: Tab, l: string) => (
    <button key={t} onClick={() => setTab(t)} style={{ padding: '8px 16px', background: 'none', border: 'none', cursor: 'pointer', color: tab === t ? 'var(--text-primary)' : 'var(--text-secondary)', borderBottom: `2px solid ${tab === t ? 'var(--accent)' : 'transparent'}`, marginBottom: -1, fontSize: 13 }}>{l}</button>
  )

  return (
    <div>
      <h1 style={{ fontSize: 18, fontWeight: 600, marginBottom: 20 }}>机构管理</h1>
      <div style={{ display: 'flex', borderBottom: '1px solid var(--border)', marginBottom: 20 }}>
        {tabBtn('list', '机构列表')}{tabBtn('add', '新增机构')}{tabBtn('import', '导入 Excel')}
      </div>

      {tab === 'list' && <>
        <div style={{ display: 'flex', gap: 10, marginBottom: 16, alignItems: 'center' }}>
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="搜索机构名称…"
            style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', borderRadius: 6, padding: '7px 12px', color: 'var(--text-primary)', fontSize: 12, width: 220 }} />
          <button onClick={scrapeAll} disabled={scrapingAll} style={{ ...ghostBtn, display: 'flex', alignItems: 'center', gap: 6 }}>
            {scrapingAll ? <><Spinner size={12} /> 全量刷新中…</> : '🔄 全量刷新'}
          </button>
          <span style={{ marginLeft: 'auto', color: 'var(--text-muted)', fontSize: 12 }}>共 {filtered.length} 家</span>
        </div>

        {loading ? <Spinner /> : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead><tr>
              {['机构名称', '基本信息', '关注赛道', '偏好阶段', '联系人', '最后更新', '操作'].map(h => (
                <th key={h} style={{ textAlign: 'left', padding: '8px 12px', color: 'var(--text-muted)', fontSize: 11, fontWeight: 500, textTransform: 'uppercase', letterSpacing: .5, borderBottom: '1px solid var(--bg-elevated)', whiteSpace: 'nowrap' }}>{h}</th>
              ))}
            </tr></thead>
            <tbody>
              {filtered.map(inst => (
                <tr key={inst.id} style={{ borderBottom: '1px solid var(--bg-elevated)', background: selectedId === inst.id ? 'var(--bg-elevated)' : 'transparent' }}>
                  <td style={{ padding: '11px 12px', minWidth: 100 }}>
                    <div style={{ color: '#fff', fontWeight: 500, marginBottom: 2 }}>{inst.name}</div>
                    {inst.location && <div style={{ color: 'var(--text-muted)', fontSize: 11 }}>{inst.location}</div>}
                    {inst.website && <a href={inst.website} target="_blank" rel="noreferrer" style={{ color: 'var(--accent)', fontSize: 11 }}>官网</a>}
                  </td>
                  <td style={{ padding: '11px 12px', minWidth: 110 }}>
                    {inst.aum && <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 2 }}>AUM {inst.aum}</div>}
                    {inst.founded_year && <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>成立 {inst.founded_year}</div>}
                    {inst.key_partners && <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>GP: {inst.key_partners.split(',').slice(0, 2).join('、')}</div>}
                  </td>
                  <td style={{ padding: '11px 12px', maxWidth: 200 }}>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
                      {(inst.preferred_sectors || '').split(',').filter(Boolean).slice(0, 5).map(s => (
                        <Badge key={s} variant="blue">{s.trim()}</Badge>
                      ))}
                      {(inst.preferred_sectors || '').split(',').filter(Boolean).length > 5 && (
                        <span style={{ color: 'var(--text-muted)', fontSize: 11 }}>+{(inst.preferred_sectors || '').split(',').filter(Boolean).length - 5}</span>
                      )}
                    </div>
                  </td>
                  <td style={{ padding: '11px 12px', minWidth: 90 }}>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
                      {(inst.preferred_stages || '').split(',').filter(Boolean).map(s => (
                        <Badge key={s} variant="amber">{s.trim()}</Badge>
                      ))}
                    </div>
                  </td>
                  <td style={{ padding: '11px 12px', minWidth: 80 }}>
                    {inst.contact_name && <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{inst.contact_name}</div>}
                    {inst.contact_wechat && <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{inst.contact_wechat}</div>}
                  </td>
                  <td style={{ padding: '11px 12px', minWidth: 80 }}>
                    {inst.last_scraped_at
                      ? <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{inst.last_scraped_at.slice(0, 10)}</span>
                      : <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>未抓取</span>}
                  </td>
                  <td style={{ padding: '11px 12px', whiteSpace: 'nowrap' }}>
                    <div style={{ display: 'flex', gap: 6 }}>
                      <button onClick={() => setSelectedId(selectedId === inst.id ? null : inst.id)}
                        style={{ ...ghostBtn, color: selectedId === inst.id ? 'var(--accent)' : 'var(--text-secondary)' }}>
                        {selectedId === inst.id ? '收起' : '详情'}
                      </button>
                      {scraping[inst.id]
                        ? <Spinner size={14} />
                        : <button onClick={() => rescrape(inst)} style={ghostBtn}>🔄</button>}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {selected && (
          <DetailPanel
            inst={selected}
            onUpdated={reload}
            onDeleted={() => { setSelectedId(null); reload() }}
          />
        )}
      </>}

      {tab === 'add' && <AddForm onSaved={() => { setTab('list'); reload() }} />}
      {tab === 'import' && <ImportForm onSaved={() => { setTab('list'); reload() }} />}
    </div>
  )
}

function DetailPanel({ inst, onUpdated, onDeleted }: { inst: Institution; onUpdated: () => void; onDeleted: () => void }) {
  const [detailTab, setDetailTab] = useState<DetailTab>('info')
  const [records, setRecords] = useState<InvestmentRecord[]>([])
  const [loadingRecs, setLoadingRecs] = useState(false)
  const [scrapingRecs, setScrapingRecs] = useState(false)
  const [fillingDescs, setFillingDescs] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [form, setForm] = useState({
    website: inst.website || '',
    founded_year: inst.founded_year || '',
    aum: inst.aum || '',
    current_fund: inst.current_fund || '',
    key_partners: inst.key_partners || '',
    preferred_sectors: inst.preferred_sectors || '',
    preferred_stages: inst.preferred_stages || '',
    location: inst.location || '',
    known_preferences: inst.known_preferences || '',
    contact_name: inst.contact_name || '',
    contact_wechat: inst.contact_wechat || '',
    fa_fee_note: inst.fa_fee_note || '',
    track_updates: inst.track_updates ?? 1,
  })
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    setForm({
      website: inst.website || '',
      founded_year: inst.founded_year || '',
      aum: inst.aum || '',
      current_fund: inst.current_fund || '',
      key_partners: inst.key_partners || '',
      preferred_sectors: inst.preferred_sectors || '',
      preferred_stages: inst.preferred_stages || '',
      location: inst.location || '',
      known_preferences: inst.known_preferences || '',
      contact_name: inst.contact_name || '',
      contact_wechat: inst.contact_wechat || '',
      fa_fee_note: inst.fa_fee_note || '',
      track_updates: inst.track_updates ?? 1,
    })
  }, [inst.id])

  function loadRecords() {
    setLoadingRecs(true)
    institutionsApi.records(inst.id).then(setRecords).finally(() => setLoadingRecs(false))
  }

  useEffect(() => {
    if (detailTab === 'records') loadRecords()
  }, [detailTab, inst.id])

  async function save() {
    setSaving(true); setSaved(false)
    try { await institutionsApi.update(inst.id, form); setSaved(true); onUpdated() }
    finally { setSaving(false) }
  }

  async function del() {
    await institutionsApi.delete(inst.id); onDeleted()
  }

  function scrapeRecs() {
    setScrapingRecs(true)
    institutionsApi.scrape(inst.id).then(({ job_id }) =>
      pollJob(job_id,
        () => { setScrapingRecs(false); loadRecords(); onUpdated() },
        () => setScrapingRecs(false)
      )
    )
  }

  function fillDescs() {
    setFillingDescs(true)
    institutionsApi.fillDescs(inst.id).then(({ job_id }) =>
      pollJob(job_id,
        () => { setFillingDescs(false); loadRecords() },
        () => setFillingDescs(false)
      )
    )
  }

  const missingDesc = records.filter(r => !r.company_desc && r.event_url).length

  const tabStyle = (t: DetailTab): React.CSSProperties => ({
    padding: '6px 14px', background: 'none', border: 'none', cursor: 'pointer',
    color: detailTab === t ? 'var(--text-primary)' : 'var(--text-secondary)',
    borderBottom: `2px solid ${detailTab === t ? 'var(--accent)' : 'transparent'}`,
    fontSize: 13
  })

  return (
    <div style={{ marginTop: 8, border: '1px solid var(--border)', borderRadius: 8, background: 'var(--bg-surface)', overflow: 'hidden' }}>
      <div style={{ display: 'flex', alignItems: 'center', padding: '12px 20px', borderBottom: '1px solid var(--border)', gap: 16 }}>
        <span style={{ fontWeight: 600, fontSize: 15, color: '#fff' }}>🏦 {inst.name}</span>
        <div style={{ display: 'flex', marginLeft: 8 }}>
          <button style={tabStyle('info')} onClick={() => setDetailTab('info')}>基本信息</button>
          <button style={tabStyle('records')} onClick={() => setDetailTab('records')}>
            投资记录{records.length > 0 ? `（${records.length}）` : ''}
          </button>
        </div>
      </div>

      {detailTab === 'info' && (
        <div style={{ padding: 20 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 12 }}>
            {([['官网', 'website'], ['成立年份', 'founded_year'], ['管理规模 (AUM)', 'aum'], ['当前基金期数', 'current_fund'], ['主要合伙人', 'key_partners'], ['总部地点', 'location'], ['联系人', 'contact_name'], ['联系方式', 'contact_wechat'], ['FA 费用备注', 'fa_fee_note']] as [string, keyof typeof form][]).map(([label, key]) => (
              <div key={key}>
                <div style={{ color: 'var(--text-muted)', fontSize: 11, marginBottom: 4 }}>{label}</div>
                <input value={String(form[key])} onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))} style={inp} />
              </div>
            ))}
          </div>
          <div style={{ marginBottom: 12 }}>
            <div style={{ color: 'var(--text-muted)', fontSize: 11, marginBottom: 4 }}>偏好赛道（逗号分隔）</div>
            <input value={form.preferred_sectors} onChange={e => setForm(f => ({ ...f, preferred_sectors: e.target.value }))} style={inp} />
          </div>
          <div style={{ marginBottom: 12 }}>
            <div style={{ color: 'var(--text-muted)', fontSize: 11, marginBottom: 4 }}>偏好阶段（逗号分隔）</div>
            <input value={form.preferred_stages} onChange={e => setForm(f => ({ ...f, preferred_stages: e.target.value }))} style={inp} />
          </div>
          <div style={{ marginBottom: 16 }}>
            <div style={{ color: 'var(--text-muted)', fontSize: 11, marginBottom: 4 }}>特殊偏好备注</div>
            <textarea value={form.known_preferences} rows={3} onChange={e => setForm(f => ({ ...f, known_preferences: e.target.value }))} style={{ ...inp, resize: 'vertical' }} />
          </div>
          <label style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16, fontSize: 13, color: 'var(--text-secondary)', cursor: 'pointer' }}>
            <input type="checkbox" checked={form.track_updates === 1} onChange={e => setForm(f => ({ ...f, track_updates: e.target.checked ? 1 : 0 }))} />
            加入定期刷新列表
          </label>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <button onClick={save} disabled={saving} style={{ background: 'linear-gradient(135deg,var(--accent),var(--accent-light))', color: '#fff', border: 'none', borderRadius: 6, padding: '8px 16px', fontSize: 13, cursor: 'pointer' }}>
              {saving ? '保存中…' : '💾 保存'}
            </button>
            {saved && <span style={{ color: 'var(--success)', fontSize: 12 }}>✅ 已保存</span>}
            <span style={{ flex: 1 }} />
            {confirmDelete ? (
              <>
                <span style={{ color: 'var(--danger)', fontSize: 12 }}>确认删除？</span>
                <button onClick={del} style={{ ...ghostBtn, color: 'var(--danger)', borderColor: 'var(--danger)' }}>确认</button>
                <button onClick={() => setConfirmDelete(false)} style={ghostBtn}>取消</button>
              </>
            ) : (
              <button onClick={() => setConfirmDelete(true)} style={{ ...ghostBtn, color: 'var(--danger)', borderColor: 'var(--danger)' }}>🗑️ 删除机构</button>
            )}
          </div>
        </div>
      )}

      {detailTab === 'records' && (
        <div style={{ padding: 20 }}>
          <div style={{ display: 'flex', gap: 8, marginBottom: 16, alignItems: 'center' }}>
            <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>已记录 {records.length} 条投资记录</span>
            <button onClick={scrapeRecs} disabled={scrapingRecs} style={{ ...ghostBtn, display: 'flex', alignItems: 'center', gap: 6 }}>
              {scrapingRecs ? <><Spinner size={12} /> 抓取中…</> : '🔄 刷新记录'}
            </button>
            {missingDesc > 0 && (
              <button onClick={fillDescs} disabled={fillingDescs} style={{ ...ghostBtn, display: 'flex', alignItems: 'center', gap: 6 }}>
                {fillingDescs ? <><Spinner size={12} /> 补全中…</> : `🔍 补全简介（${missingDesc}）`}
              </button>
            )}
          </div>
          {loadingRecs ? <Spinner /> : records.length === 0 ? (
            <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>暂无投资记录，点击「刷新记录」从 IT桔子 获取</p>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
              <thead><tr>
                {['公司', '赛道', '轮次', '金额', '日期', '简介'].map(h => (
                  <th key={h} style={{ textAlign: 'left', padding: '6px 10px', color: 'var(--text-muted)', fontSize: 11, borderBottom: '1px solid var(--bg-elevated)', fontWeight: 500 }}>{h}</th>
                ))}
              </tr></thead>
              <tbody>
                {records.map(r => (
                  <tr key={r.id} style={{ borderBottom: '1px solid var(--bg-elevated)' }}>
                    <td style={{ padding: '8px 10px', color: '#fff', fontWeight: 500 }}>
                      {r.event_url
                        ? <a href={r.event_url} target="_blank" rel="noreferrer" style={{ color: 'var(--accent)' }}>{r.company_name}</a>
                        : r.company_name}
                    </td>
                    <td style={{ padding: '8px 10px', color: 'var(--text-secondary)' }}>{r.sector || '—'}</td>
                    <td style={{ padding: '8px 10px' }}>{r.stage ? <Badge variant="amber">{r.stage}</Badge> : '—'}</td>
                    <td style={{ padding: '8px 10px', color: 'var(--text-secondary)' }}>{r.amount || '—'}</td>
                    <td style={{ padding: '8px 10px', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>{r.invested_date || '—'}</td>
                    <td style={{ padding: '8px 10px', color: 'var(--text-muted)', maxWidth: 300 }}>
                      {r.company_desc
                        ? <span title={r.company_desc}>{r.company_desc.slice(0, 80)}{r.company_desc.length > 80 ? '…' : ''}</span>
                        : <span style={{ color: 'var(--border)' }}>—</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  )
}

function AddForm({ onSaved }: { onSaved: () => void }) {
  const [form, setForm] = useState({ name: '', location: '', known_preferences: '', contact_name: '', contact_wechat: '', fa_fee_note: '', response_style: '' })
  const [saving, setSaving] = useState(false)

  async function submit(e: React.FormEvent) {
    e.preventDefault(); if (!form.name.trim()) return
    setSaving(true); try { await institutionsApi.create(form); onSaved() } finally { setSaving(false) }
  }

  const fields: [string, keyof typeof form, boolean][] = [['机构名称 *', 'name', false], ['总部地点', 'location', false], ['联系人', 'contact_name', false], ['联系方式', 'contact_wechat', false], ['FA 费用', 'fa_fee_note', false], ['已知偏好', 'known_preferences', true]]

  return (
    <form onSubmit={submit} style={{ maxWidth: 480, display: 'flex', flexDirection: 'column', gap: 12 }}>
      {fields.map(([l, k, ta]) => (
        <div key={k} style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <label style={{ color: 'var(--text-secondary)', fontSize: 12 }}>{l}</label>
          {ta ? <textarea value={form[k]} rows={3} onChange={e => setForm(f => ({ ...f, [k]: e.target.value }))} style={{ ...inp, resize: 'vertical' }} />
            : <input value={form[k]} onChange={e => setForm(f => ({ ...f, [k]: e.target.value }))} style={inp} />}
        </div>
      ))}
      <button type="submit" disabled={saving} style={{ background: 'linear-gradient(135deg,var(--accent),var(--accent-light))', color: '#fff', border: 'none', borderRadius: 6, padding: '9px 16px', fontWeight: 500, fontSize: 13, marginTop: 8 }}>
        {saving ? '保存中…' : '➕ 新增并自动补全'}
      </button>
    </form>
  )
}

function ImportForm({ onSaved }: { onSaved: () => void }) {
  const [importing, setImporting] = useState(false)
  const [result, setResult] = useState<{ created: number } | null>(null)
  async function pick(file: File) {
    setImporting(true); try { const r = await institutionsApi.importExcel(file); setResult(r); setTimeout(onSaved, 1500) } finally { setImporting(false) }
  }
  return importing ? <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-secondary)' }}><Spinner /> 导入中…</div>
    : result ? <p style={{ color: 'var(--success)' }}>✅ 成功导入 {result.created} 家机构</p>
      : <label style={{ display: 'block', border: '2px dashed var(--border)', borderRadius: 8, padding: 32, textAlign: 'center', cursor: 'pointer', color: 'var(--text-secondary)' }}>点击选择 Excel 文件<input type="file" accept=".xlsx" style={{ display: 'none' }} onChange={e => e.target.files?.[0] && pick(e.target.files[0])} /></label>
}
