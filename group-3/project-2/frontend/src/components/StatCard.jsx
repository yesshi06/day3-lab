import { motion } from 'framer-motion'

export default function StatCard({ label, value, sub, warn, delay = 0 }) {
  return (
    <motion.div
      className="stat-card-component"
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.35, delay }}
      whileHover={{ y: -2, boxShadow: '0 6px 20px rgba(0,0,0,0.08)' }}
    >
      <div className="sc-label">{label}</div>
      <div className="sc-value">{value}</div>
      {sub && <div className={`sc-sub${warn ? ' warn' : ''}`}>{sub}</div>}
    </motion.div>
  )
}
