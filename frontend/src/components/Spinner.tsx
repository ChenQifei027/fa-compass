if (typeof document !== 'undefined' && !document.getElementById('sp-kf')) {
  const s = document.createElement('style')
  s.id = 'sp-kf'
  s.textContent = '@keyframes spin{to{transform:rotate(360deg)}}'
  document.head.appendChild(s)
}
export default function Spinner({ size = 16 }: { size?: number }) {
  return <span style={{ display:'inline-block', width:size, height:size, border:'2px solid var(--border)', borderTopColor:'var(--accent)', borderRadius:'50%', animation:'spin .7s linear infinite' }} />
}
