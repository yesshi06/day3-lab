import { motion } from 'framer-motion'

export default function Card({ title, children, className = '', style, delay = 0 }) {
  return (
    <motion.div
      className={`card-component ${className}`}
      style={style}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay }}
    >
      {title && (
        <div className="card-title">
          <span className="dot" />
          {title}
        </div>
      )}
      {children}
    </motion.div>
  )
}
