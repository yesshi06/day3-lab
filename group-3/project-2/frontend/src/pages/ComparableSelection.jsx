import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts'
import { api } from '../api'
import Card from '../components/Card'
import Stepper from '../components/Stepper'
import '../components/components.css'

const MOCK_RECS = {
  prompt_summary: '基于字节跳动的行业属性（互联网）、营收规模和业务模式，推荐以下 4 家可比上市公司。',
  recommendations: [
    { comparable_id:'listed_001', name:'腾讯控股', industry:'互联网', reason:'同为互联网平台型公司，营收规模相近', similarity_score:0.92,
      similarity_dimensions:{ industry:95, scale:85, business_model:80, profitability:90, growth:75 }},
    { comparable_id:'listed_002', name:'快手科技', industry:'互联网', reason:'短视频赛道直接竞争对手', similarity_score:0.88,
      similarity_dimensions:{ industry:98, scale:60, business_model:95, profitability:55, growth:85 }},
    { comparable_id:'listed_003', name:'哔哩哔哩', industry:'互联网', reason:'内容平台业务模式相似', similarity_score:0.81,
      similarity_dimensions:{ industry:90, scale:40, business_model:85, profitability:35, growth:80 }},
    { comparable_id:'listed_004', name:'Meta Platforms', industry:'互联网', reason:'全球社交+广告业务对标', similarity_score:0.78,
      similarity_dimensions:{ industry:70, scale:95, business_model:75, profitability:95, growth:70 }},
  ],
}

const MOCK_COMPARABLES = [
  { comparable_id:'listed_001', name:'腾讯控股', industry:'互联网', stock_price:380, pe:22.5, pb:4.8, net_profit:12500000, net_assets:5800000, revenue:55000000 },
  { comparable_id:'listed_002', name:'快手科技', industry:'互联网', stock_price:55, pe:28.3, pb:3.2, net_profit:800000, net_assets:950000, revenue:11000000 },
  { comparable_id:'listed_003', name:'哔哩哔哩', industry:'互联网', stock_price:18.5, pe:35.2, pb:2.1, net_profit:250000, net_assets:420000, revenue:6500000 },
  { comparable_id:'listed_004', name:'Meta Platforms', industry:'互联网', stock_price:520, pe:18.8, pb:6.5, net_profit:39000000, net_assets:12000000, revenue:134000000 },
]

const DIM_LABELS = { industry:'行业相似度', scale:'规模匹配', business_model:'业务模式', profitability:'盈利能力', growth:'增长趋势' }
const RADAR_COLORS = ['#4F6BF6','#22C55E','#F59E0B','#8B5CF6']

function normalizeComparable(item) {
  return {
    comparable_id: item.comparable_id,
    name: item.name,
    industry: item.industry ?? '-',
    stock_price: item.stock_price ?? 0,
    pe: item.pe ?? 0,
    pb: item.pb ?? 0,
    net_profit: item.net_profit ?? 0,
    net_assets: item.net_assets ?? 0,
    revenue: item.revenue ?? 0,
  }
}

function getComparablesFromResponse(data) {
  if (Array.isArray(data?.comparables) && data.comparables.length > 0) {
    return data.comparables.map(normalizeComparable)
  }

  if (Array.isArray(data?.recommendations) && data.recommendations.length > 0) {
    return data.recommendations.map(normalizeComparable)
  }

  return []
}

export default function ComparableSelection() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [recs, setRecs] = useState(null)
  const [selected, setSelected] = useState(new Set())
  const [comparables, setComparables] = useState([])
  const [loading, setLoading] = useState(true)
  const [confirming, setConfirming] = useState(false)

  useEffect(() => { loadData() }, [id])

  async function loadData() {
    setLoading(true)
    try {
      const data = await api.recommendComparables(id)
      setRecs(data)
      setSelected(new Set(data.recommendations.map(r => r.comparable_id)))
      setComparables(getComparablesFromResponse(data))
      try {
        const comp = await api.getComparables(id)
        const normalized = getComparablesFromResponse(comp)
        if (normalized.length > 0) setComparables(normalized)
      } catch {
        // Keep the recommendation payload as the primary source before confirmation.
      }
    } catch {
      setRecs(MOCK_RECS)
      setSelected(new Set(MOCK_RECS.recommendations.map(r => r.comparable_id)))
      setComparables(MOCK_COMPARABLES)
    } finally {
      setLoading(false)
    }
  }

  function toggleSelect(cid) {
    setSelected(prev => {
      const next = new Set(prev)
      next.has(cid) ? next.delete(cid) : next.add(cid)
      return next
    })
  }

  async function handleConfirm() {
    setConfirming(true)
    try {
      await api.confirmComparables(id, [...selected])
    } catch { /* demo fallback */ }
    navigate(`/company/${id}/valuation`)
  }

  if (loading || !recs) {
    return <div className="loading-container"><div className="spinner" /><span style={{color:'var(--text2)'}}>AI 推荐中…</span></div>
  }

  const radarData = Object.keys(DIM_LABELS).map(key => {
    const point = { name: DIM_LABELS[key] }
    recs.recommendations.forEach(r => { point[r.name] = r.similarity_dimensions[key] })
    return point
  })

  const displayComparables = comparables.length > 0
    ? comparables
    : getComparablesFromResponse(recs)

  const barData = displayComparables.map(c => ({ name: c.name, PE: c.pe, 'P/B': c.pb }))

  const selectedNames = recs.recommendations.filter(r => selected.has(r.comparable_id)).map(r => r.name)

  return (
    <>
      <h1 className="page-title">可比公司 — AI 推荐与确认</h1>
      <p className="page-desc">系统基于行业、规模、业务模式推荐 4~6 家可比公司，您可勾选确认或手动增删</p>
      <Stepper />

      <div className="grid-2">
        {/* Left: AI Recommendations */}
        <div>
          <motion.div
            className="ai-card"
            style={{ marginBottom: 16 }}
            initial={{ opacity:0, x:-20 }}
            animate={{ opacity:1, x:0 }}
            transition={{ duration:0.4 }}
          >
            <div className="ai-label"><span>🤖</span> AI 可比公司推荐</div>
            <p>{recs.prompt_summary}</p>
          </motion.div>

          {recs.recommendations.map((r, i) => (
            <motion.div
              key={r.comparable_id}
              className={`comp-check ${selected.has(r.comparable_id) ? 'checked' : ''}`}
              onClick={() => toggleSelect(r.comparable_id)}
              initial={{ opacity:0, y:10 }}
              animate={{ opacity:1, y:0 }}
              transition={{ delay: 0.1 + i*0.08 }}
              whileHover={{ scale: 1.01 }}
            >
              <input
                type="checkbox"
                checked={selected.has(r.comparable_id)}
                onChange={() => toggleSelect(r.comparable_id)}
                onClick={e => e.stopPropagation()}
              />
              <div className="info">
                <div className="name">{r.name} <span className="badge badge-blue" style={{fontSize:11}}>{r.industry}</span></div>
                <div className="reason">{r.reason}</div>
              </div>
              <div className="score">{Math.round(r.similarity_score * 100)}%</div>
            </motion.div>
          ))}

          <div style={{ marginTop:16, display:'flex', gap:10 }}>
            <button className="btn btn-outline btn-sm">＋ 手动添加公司</button>
            <button className="btn btn-outline btn-sm" onClick={loadData}>🔄 重新推荐</button>
          </div>
        </div>

        {/* Right: Charts */}
        <div>
          <Card title="可比公司相似度雷达图" delay={0.15}>
            <ResponsiveContainer width="100%" height={280}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="#E2E8F0" />
                <PolarAngleAxis dataKey="name" tick={{fontSize:12}} />
                {recs.recommendations.map((r, i) => (
                  <Radar
                    key={r.comparable_id}
                    name={r.name}
                    dataKey={r.name}
                    stroke={RADAR_COLORS[i]}
                    fill={RADAR_COLORS[i]}
                    fillOpacity={0.1}
                    strokeWidth={2}
                    dot={{ r:3 }}
                    animationDuration={1000 + i*200}
                  />
                ))}
                <Legend />
                <Tooltip />
              </RadarChart>
            </ResponsiveContainer>
          </Card>

          <Card title="可比公司核心指标对比" delay={0.2}>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={barData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                <XAxis dataKey="name" tick={{fontSize:12}} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="PE" fill="rgba(79,107,246,.15)" stroke="#4F6BF6" strokeWidth={1.5} radius={[6,6,0,0]} animationDuration={1000} />
                <Bar dataKey="P/B" fill="rgba(245,158,11,.15)" stroke="#F59E0B" strokeWidth={1.5} radius={[6,6,0,0]} animationDuration={1200} />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </div>
      </div>

      {/* Comparable Detail Table */}
      <Card title="可比公司财务指标明细" delay={0.25} style={{marginTop:4}}>
        <table>
          <thead>
            <tr><th>公司</th><th>行业</th><th>股价</th><th>PE</th><th>P/B</th><th>净利润（万元）</th><th>净资产（万元）</th><th>营收（万元）</th></tr>
          </thead>
          <tbody>
            {displayComparables.map((c, i) => (
              <motion.tr
                key={c.comparable_id}
                initial={{ opacity:0, x:-10 }}
                animate={{ opacity:1, x:0 }}
                transition={{ delay: 0.3 + i*0.05 }}
              >
                <td><strong>{c.name}</strong></td>
                <td>{c.industry}</td>
                <td>{c.stock_price}</td>
                <td>{c.pe}</td>
                <td>{c.pb}</td>
                <td>{c.net_profit.toLocaleString()}</td>
                <td>{c.net_assets.toLocaleString()}</td>
                <td>{c.revenue.toLocaleString()}</td>
              </motion.tr>
            ))}
          </tbody>
        </table>

        <div style={{ marginTop:12, display:'flex', gap:10, justifyContent:'space-between', alignItems:'center' }}>
          <div>
            <span style={{fontSize:13,color:'var(--text2)'}}>已选中：</span>
            {selectedNames.map(name => (
              <span key={name} className="tag">{name} <span className="remove" onClick={() => {
                const rec = recs.recommendations.find(r => r.name === name)
                if (rec) toggleSelect(rec.comparable_id)
              }}>×</span></span>
            ))}
          </div>
          <button
            className="btn btn-primary"
            onClick={handleConfirm}
            disabled={selected.size === 0 || confirming}
          >
            {confirming ? '确认中…' : '确认并开始估值 →'}
          </button>
        </div>
      </Card>
    </>
  )
}
