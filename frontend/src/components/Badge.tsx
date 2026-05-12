import React from 'react'

type Variant = 'purple' | 'blue' | 'green' | 'amber' | 'default'
const C: Record<Variant, [string, string]> = {
  purple:  ['rgba(91,91,214,.15)',  '#8b8bf8'],
  blue:    ['rgba(59,130,246,.12)', '#60a5fa'],
  green:   ['rgba(62,207,142,.12)', '#3ecf8e'],
  amber:   ['rgba(245,158,11,.12)', '#f59e0b'],
  default: ['var(--bg-elevated)',   'var(--text-secondary)'],
}
export default function Badge({ children, variant = 'default' }: { children: React.ReactNode; variant?: Variant }) {
  const [bg, color] = C[variant]
  return <span style={{ display:'inline-block', padding:'2px 8px', borderRadius:999, fontSize:11, fontWeight:500, background:bg, color, margin:'0 2px' }}>{children}</span>
}
