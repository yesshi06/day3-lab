import { NavLink, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import './Layout.css'

const NAV_ITEMS = [
  { path: '/', label: '公司列表' },
]

export default function Layout({ children }) {
  const location = useLocation()
  const companyId = location.pathname.match(/\/company\/([^/]+)/)?.[1]

  const dynamicNav = companyId
    ? [
        { path: '/', label: '公司列表' },
        { path: `/company/${companyId}`, label: '公司详情' },
        { path: `/company/${companyId}/comparables`, label: '可比公司' },
        { path: `/company/${companyId}/valuation`, label: '估值分析' },
        { path: `/company/${companyId}/result`, label: '估值结果' },
      ]
    : NAV_ITEMS

  return (
    <>
      <nav className="top-nav">
        <div className="logo">📊 公司估值系统</div>
        <div className="nav-items">
          {dynamicNav.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end
              className={({ isActive }) => `nav-btn${isActive ? ' active' : ''}`}
            >
              {item.label}
            </NavLink>
          ))}
        </div>
      </nav>
      <AnimatePresence mode="wait">
        <motion.main
          key={location.pathname}
          className="page-container"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -16 }}
          transition={{ duration: 0.25 }}
        >
          {children}
        </motion.main>
      </AnimatePresence>
    </>
  )
}
