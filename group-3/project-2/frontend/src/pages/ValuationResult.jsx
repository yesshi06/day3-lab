import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts'
import { api } from '../api'
import Card from '../components/Card'
import Stepper from '../components/Stepper'
import '../components/components.css'

const fmtWanyi = v => {
  if (v >= 10000000) return (v / 10000000).toFixed(1) + ' 万亿'
  if (v >= 10000) return (v / 10000).toFixed(0) + ' 亿'
  return v.toLocaleString() + ' 万'
}

const METHOD_COLORS = { pe_comparable:'#4F6BF6', dcf:'#22C55E', pb:'#F59E0B' }

const MOCK_TEMPLATE = {
  valuation_center:28000000, valuation_range_low:20000000, valuation_range_high:38400000,
  methods_summary:[
    { method_name:'pe_comparable', display_name:'PE 可比法', valuation_low:24000000, valuation_mid:27000000, valuation_high:34000000, valuation_range:'2.4万亿 ~ 3.4万亿', weight:40 },
    { method_name:'dcf', display_name:'DCF 法', valuation_low:20000000, valuation_mid:25000000, valuation_high:30000000, valuation_range:'2.0万亿 ~ 3.0万亿', weight:35 },
    { method_name:'pb', display_name:'P/B 法', valuation_low:25600000, valuation_mid:32000000, valuation_high:38400000, valuation_range:'2.56万亿 ~ 3.84万亿', weight:25 },
  ],
  ai_recommendation:{
    recommended_method:'PE可比法',
    reason: '目标公司处于成熟期，盈利稳定，PE可比法最能反映市场对该行业的估值共识',
    summary: '综合三种估值方法，目标公司估值中枢约2.8万亿元。考虑到公司盈利能力稳定且可比公司样本充足，PE可比法最具参考价值。DCF法受折现率假设影响较大，P/B法因轻资产属性偏高，建议以PE法为锚。',
    confidence:82,
  },
  sensitivity_analysis:{
    discount_rates:[8,9,10,11,12,13,14],
    scenarios:[
      {growth_rate:3,valuations:[3.10,2.85,2.60,2.40,2.22,2.08,1.95]},
      {growth_rate:5,valuations:[3.50,3.15,2.85,2.60,2.40,2.22,2.08]},
      {growth_rate:7,valuations:[4.10,3.60,3.20,2.88,2.62,2.40,2.22]},
    ],
  },
  confidence_scores:[
    {method_name:'pe_comparable',display_name:'PE 可比法',data_quality:90,method_applicability:85,sample_sufficiency:88},
    {method_name:'dcf',display_name:'DCF 法',data_quality:75,method_applicability:80,sample_sufficiency:70},
    {method_name:'pb',display_name:'P/B 法',data_quality:70,method_applicability:60,sample_sufficiency:72},
  ],
}

function buildMockSummary(companyId, companyName) {
  return {
    ...MOCK_TEMPLATE,
    company_id: companyId,
    company_name: companyName || `公司 ${companyId}`,
  }
}

export default function ValuationResult() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [company, setCompany] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => { loadData() }, [id])

  async function loadData() {
    setLoading(true)
    // 先获取公司基本信息，确保能展示正确的公司名称
    let companyInfo = null
    try {
      companyInfo = await api.getCompany(id)
      setCompany(companyInfo)
    } catch {
      // 公司信息获取失败时使用 ID 作为标识
      companyInfo = { company_id: id, name: `公司 ${id}`, industry: '-' }
      setCompany(companyInfo)
    }
    try {
      const d = await api.getValuationSummary(id)
      // 确保返回数据中的公司信息与当前路由 ID 一致
      setData({
        ...d,
        company_id: id,
        company_name: d.company_name || companyInfo?.name || `公司 ${id}`,
      })
    } catch {
      setData(buildMockSummary(id, companyInfo?.name))
    } finally {
      setLoading(false)
    }
  }

  if (loading || !data) {
    return <div className="loading-container"><div className="spinner" /><span style={{color:'var(--text2)'}}>加载中…</span></div>
  }

  // Waterfall data
  const waterfallData = [
    ...data.methods_summary.map(m => ({
      name: m.display_name,
      range: [m.valuation_low / 10000000, m.valuation_high / 10000000],
    })),
    { name: '估值中枢', range: [data.valuation_center / 10000000 * 0.93, data.valuation_center / 10000000 * 1.07] },
  ]

  // Weight pie
  const weightData = data.methods_summary.map(m => ({ name: `${m.display_name} (${m.weight}%)`, value: m.weight }))

  // Sensitivity chart data
  const sensiData = data.sensitivity_analysis.discount_rates.map((dr, i) => {
    const point = { discount_rate: dr + '%' }
    data.sensitivity_analysis.scenarios.forEach(s => {
      point[`增长率 ${s.growth_rate}%`] = s.valuations[i]
    })
    return point
  })
  const sensiColors = ['#4F6BF6', '#22C55E', '#F59E0B']

  // Confidence bar data
  const confData = data.confidence_scores.map(c => ({
    name: c.display_name,
    数据质量: c.data_quality,
    方法适用性: c.method_applicability,
    样本充足度: c.sample_sufficiency,
  }))

  const ai = data.ai_recommendation

  return (
    <>
      <h1 className="page-title">估值结果综合展示</h1>
      <p className="page-desc">
        <strong>{data.company_name}</strong>
        {company?.industry && <span className="badge badge-blue" style={{ marginLeft: 8, fontSize: 11 }}>{company.industry}</span>}
        {' '} — 多方法估值汇总、估值中枢与 AI 推荐
      </p>
      <Stepper />

      {/* Big Center Value */}
      <motion.div
        className="card-component"
        style={{ textAlign:'center', padding:36 }}
        initial={{ opacity:0, scale:0.9 }}
        animate={{ opacity:1, scale:1 }}
        transition={{ duration:0.5, type:'spring' }}
      >
        <div style={{fontSize:14,color:'var(--text2)',marginBottom:4}}>估值中枢（三种方法加权平均）</div>
        <motion.div
          style={{fontSize:52,fontWeight:800,color:'var(--primary)',lineHeight:1.2}}
          initial={{ opacity:0, y:20 }}
          animate={{ opacity:1, y:0 }}
          transition={{ delay:0.3, duration:0.5 }}
        >
          {fmtWanyi(data.valuation_center)}元
        </motion.div>
        <div style={{fontSize:14,color:'var(--text2)',marginTop:4}}>
          区间：{fmtWanyi(data.valuation_range_low)} ~ {fmtWanyi(data.valuation_range_high)}
        </div>
        <div style={{ display:'flex', justifyContent:'center', gap:32, marginTop:20 }}>
          {data.methods_summary.map(m => (
            <motion.div
              key={m.method_name}
              initial={{ opacity:0, y:10 }}
              animate={{ opacity:1, y:0 }}
              transition={{ delay:0.4 }}
            >
              <div style={{fontSize:12,color:'var(--text2)'}}>{m.display_name}</div>
              <div style={{fontSize:20,fontWeight:700,color:METHOD_COLORS[m.method_name]}}>{fmtWanyi(m.valuation_mid)}</div>
            </motion.div>
          ))}
        </div>
      </motion.div>

      <div className="grid-2">
        {/* Methods Summary Table */}
        <Card title="各方法估值摘要" delay={0.15}>
          <table>
            <thead><tr><th>方法</th><th>估值区间</th><th>中位数</th><th>权重</th></tr></thead>
            <tbody>
              {data.methods_summary.map((m, i) => (
                <motion.tr
                  key={m.method_name}
                  initial={{ opacity:0, x:-10 }}
                  animate={{ opacity:1, x:0 }}
                  transition={{ delay: 0.2 + i*0.05 }}
                >
                  <td><span className="badge" style={{background:`${METHOD_COLORS[m.method_name]}20`,color:METHOD_COLORS[m.method_name]}}>{m.display_name}</span></td>
                  <td>{m.valuation_range}</td>
                  <td><strong>{fmtWanyi(m.valuation_mid)}</strong></td>
                  <td>{m.weight}%</td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </Card>

        {/* AI Recommendation */}
        <motion.div
          className="ai-card"
          style={{ height:'fit-content' }}
          initial={{ opacity:0, x:20 }}
          animate={{ opacity:1, x:0 }}
          transition={{ delay:0.2, duration:0.4 }}
        >
          <div className="ai-label"><span>🤖</span> AI 估值总结与推荐</div>
          <p style={{marginBottom:12}}><strong>推荐方法：{ai.recommended_method}</strong></p>
          <p>{ai.summary}</p>
          <div style={{marginTop:14,paddingTop:12,borderTop:'1px solid #C7D2FE'}}>
            <div style={{fontSize:12,color:'var(--text2)',marginBottom:4}}>置信度</div>
            <div className="progress-bar" style={{height:10}}>
              <motion.div
                className="fill"
                style={{ background:'var(--primary)' }}
                initial={{ width: 0 }}
                animate={{ width: `${ai.confidence}%` }}
                transition={{ delay:0.5, duration:1 }}
              />
            </div>
            <div style={{fontSize:13,fontWeight:600,color:'var(--primary)',marginTop:4}}>
              {ai.confidence}% — {ai.confidence >= 80 ? '高置信度' : ai.confidence >= 60 ? '中等置信度' : '低置信度'}
            </div>
          </div>
        </motion.div>
      </div>

      {/* Result Charts */}
      <div className="grid-2">
        <Card title="估值区间瀑布图" delay={0.25}>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={waterfallData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
              <XAxis type="number" domain={[1.5, 4.5]} unit=" 万亿" />
              <YAxis type="category" dataKey="name" width={80} />
              <Tooltip formatter={(v) => {
                if (Array.isArray(v)) return `${v[0].toFixed(2)} ~ ${v[1].toFixed(2)} 万亿`
                return v
              }} />
              <Bar dataKey="range" fill="#4F6BF6" radius={6} barSize={24} animationDuration={1000}>
                {waterfallData.map((_, i) => (
                  <Cell key={i} fill={i === waterfallData.length - 1 ? '#8B5CF6' : ['#4F6BF6','#22C55E','#F59E0B'][i]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card title="各方法估值占比" delay={0.3}>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={weightData}
                dataKey="value"
                nameKey="name"
                cx="50%" cy="50%"
                innerRadius={60} outerRadius={100}
                paddingAngle={4}
                animationBegin={300}
                animationDuration={800}
              >
                <Cell fill="#4F6BF6" />
                <Cell fill="#22C55E" />
                <Cell fill="#F59E0B" />
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </Card>
      </div>

      <div className="grid-2">
        <Card title="敏感性分析 — 折现率 vs 增长率对估值影响" delay={0.35}>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={sensiData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
              <XAxis dataKey="discount_rate" />
              <YAxis unit=" 万亿" />
              <Tooltip />
              <Legend />
              {data.sensitivity_analysis.scenarios.map((s, i) => (
                <Line
                  key={s.growth_rate}
                  type="monotone"
                  dataKey={`增长率 ${s.growth_rate}%`}
                  stroke={sensiColors[i]}
                  strokeWidth={2}
                  dot={{ r:4 }}
                  animationDuration={1000 + i*200}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </Card>

        <Card title="估值方法可信度评分" delay={0.4}>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={confData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
              <XAxis type="number" domain={[0, 100]} />
              <YAxis type="category" dataKey="name" width={80} />
              <Tooltip />
              <Legend />
              <Bar dataKey="数据质量" fill="rgba(79,107,246,.15)" stroke="#4F6BF6" strokeWidth={1.5} radius={[0,6,6,0]} animationDuration={1000} />
              <Bar dataKey="方法适用性" fill="rgba(34,197,94,.15)" stroke="#22C55E" strokeWidth={1.5} radius={[0,6,6,0]} animationDuration={1200} />
              <Bar dataKey="样本充足度" fill="rgba(245,158,11,.15)" stroke="#F59E0B" strokeWidth={1.5} radius={[0,6,6,0]} animationDuration={1400} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Actions */}
      <Card delay={0.45} style={{ display:'flex', gap:12, justifyContent:'space-between', alignItems:'center', flexWrap:'wrap' }}>
        <div style={{ display:'flex', gap:10 }}>
          <button className="btn btn-outline" onClick={() => navigate(`/company/${id}/comparables`)}>← 调整可比公司</button>
          <button className="btn btn-outline" onClick={() => navigate(`/company/${id}/valuation`)}>← 调整参数重算</button>
        </div>
        <button className="btn btn-primary" onClick={() => navigate('/')}>返回公司列表</button>
      </Card>
    </>
  )
}
