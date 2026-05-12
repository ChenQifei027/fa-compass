type Page = 'projects' | 'institutions' | 'matching' | 'settings'
interface Props { current: string; onNavigate: (p: string) => void }

export default function TopNav({ current, onNavigate }: Props) {
  const items: [Page, string][] = [
    ['projects', '项目管理'], ['institutions', '机构管理'], ['matching', '匹配推荐'],
  ]
  const navBtn = (key: string, label: string) => (
    <button key={key} onClick={() => onNavigate(key)} style={{
      padding: '5px 12px', borderRadius: 'var(--radius-md)', border: 'none',
      background: current === key ? 'var(--bg-elevated)' : 'transparent',
      color: current === key ? 'var(--text-primary)' : 'var(--text-secondary)',
      fontSize: 13, fontWeight: current === key ? 500 : 400,
    }}>{label}</button>
  )
  return (
    <nav style={{
      height: 'var(--nav-height)', background: 'var(--bg-surface)',
      borderBottom: '1px solid var(--border)',
      display: 'flex', alignItems: 'center', padding: '0 20px', gap: 4, flexShrink: 0,
    }}>
      <span style={{ color: 'var(--accent-light)', fontWeight: 700, fontSize: 14, marginRight: 20 }}>FA 系统</span>
      {items.map(([k, l]) => navBtn(k, l))}
      <span style={{ marginLeft: 'auto' }}>{navBtn('settings', '设置')}</span>
    </nav>
  )
}
