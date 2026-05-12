import { useEffect } from 'react'
interface Props { title: string; onClose: () => void; children: React.ReactNode; width?: number }
export default function Modal({ title, onClose, children, width = 520 }: Props) {
  useEffect(() => {
    const h = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', h)
    return () => window.removeEventListener('keydown', h)
  }, [onClose])
  return (
    <div onClick={onClose} style={{ position:'fixed', inset:0, background:'rgba(0,0,0,.6)', display:'flex', alignItems:'center', justifyContent:'center', zIndex:100 }}>
      <div onClick={e => e.stopPropagation()} style={{ background:'var(--bg-surface)', border:'1px solid var(--border)', borderRadius:'var(--radius-lg)', width, maxWidth:'90vw', maxHeight:'85vh', overflow:'auto', padding:24 }}>
        <div style={{ display:'flex', alignItems:'center', marginBottom:20 }}>
          <h2 style={{ fontSize:15, fontWeight:600, flex:1 }}>{title}</h2>
          <button onClick={onClose} style={{ background:'none', border:'none', color:'var(--text-secondary)', fontSize:18 }}>✕</button>
        </div>
        {children}
      </div>
    </div>
  )
}
