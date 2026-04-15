import { useLocation } from 'react-router-dom'

const STEPS = [
  { label: '选定公司', path: '/' },
  { label: '公司详情', pathKey: 'detail' },
  { label: '可比公司', pathKey: 'comparables' },
  { label: '估值分析', pathKey: 'valuation' },
  { label: '估值结果', pathKey: 'result' },
]

function getStepIndex(pathname) {
  if (pathname === '/') return 0
  if (pathname.includes('/result')) return 4
  if (pathname.includes('/valuation')) return 3
  if (pathname.includes('/comparables')) return 2
  if (pathname.match(/^\/company\/[^/]+$/)) return 1
  return 0
}

export default function Stepper() {
  const { pathname } = useLocation()
  const current = getStepIndex(pathname)

  return (
    <div className="stepper">
      {STEPS.map((step, i) => (
        <div key={i} style={{ display: 'flex', alignItems: 'center' }}>
          <div className={`step ${i < current ? 'done' : ''} ${i === current ? 'active' : ''}`}>
            <div className="circle">{i < current ? '✓' : i + 1}</div>
            <div className="step-label">{step.label}</div>
          </div>
          {i < STEPS.length - 1 && (
            <div className={`step-line${i < current ? ' done' : ''}`} />
          )}
        </div>
      ))}
    </div>
  )
}
