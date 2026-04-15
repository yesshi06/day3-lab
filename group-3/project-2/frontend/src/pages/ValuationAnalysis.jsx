import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  BarChart, Bar, ComposedChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  ScatterChart, Scatter, ZAxis,
} from 'recharts'
import { api } from '../api'
import Card from '../components/Card'
import StatCard from '../components/StatCard'
import Stepper from '../components/Stepper'
import '../components/components.css'

const fmt = v => {
  if (v >= 100000000) return (v / 100000000).toFixed(1) + '亿'
  if (v >= 10000) return (v / 10000).toFixed(0) + '万'
  return v
}

const fmtWanyi = v => {
  if (v >= 10000000) return (v / 10000000).toFixed(1) + ' 万亿'
  if (v >= 10000) return (v / 10000).toFixed(0) + ' 亿'
  return v.toLocaleString() + ' 万'
}

const METHOD_COLORS = { pe_comparable: '#4F6BF6', dcf: '#22C55E', pb: '#F59E0B' }
const METHOD_CLASS = { pe_comparable: '', dcf: ' dcf', pb: ' pb' }

const MOCK_METHODS = {
  company_id:'comp_001', company_name:'字节跳动', target_net_profit:1200000, target_net_assets:8000000, comparable_count:4,
  methods: [
    { method_name:'pe_comparable', display_name:'PE 可比法', valuation_low:24000000, valuation_mid:27000000, valuation_high:34000000,
      params:{ comparable_pe_median:22.5, comparable_pe_range:[18.0,28.3], comparable_companies:['腾讯控股','快手科技','哔哩哔哩','Meta Platforms'] },
      calculation_detail:'取4家可比公司PE中位数22.5，乘以目标公司净利润1,200,000万元，得估值27,000,000万元' },
    { method_name:'dcf', display_name:'DCF 现金流折现法', valuation_low:20000000, valuation_mid:25000000, valuation_high:30000000,
      params:{ discount_rate:0.10, growth_rate:0.05, projection_years:5, base_cashflow:1500000 },
      calculation_detail:'基于经营现金流1,500,000万元，5年预测期，折现率10%，永续增长率5%' },
    { method_name:'pb', display_name:'P/B 市净率法', valuation_low:25600000, valuation_mid:32000000, valuation_high:38400000,
      params:{ comparable_pb_median:4.0, comparable_pb_range:[2.1,6.5] },
      calculation_detail:'取可比公司PB中位数4.0，乘以目标公司净资产8,000,000万元，得估值32,000,000万元' },
  ],
  dcf_projection: {
    base_cashflow:1500000, discount_rate:0.10, growth_rate:0.05, projection_years:5,
    yearly_cashflows:[
      {year:'2026E',projected:1575000,discounted:1431818},
      {year:'2027E',projected:1653750,discounted:1368760},
      {year:'2028E',projected:1736438,discounted:1308728},
      {year:'2029E',projected:1823259,discounted:1251598},
      {year:'2030E',projected:1914422,discounted:1197227},
    ],
    terminal_value:38288448, terminal_value_discounted:23775000,
  },
  comparable_scatter: [
    {name:'腾讯控股',pe:22.5,pb:4.8,revenue:55000000},
    {name:'快手科技',pe:28.3,pb:3.2,revenue:11000000},
    {name:'哔哩哔哩',pe:35.2,pb:2.1,revenue:6500000},
    {name:'Meta Platforms',pe:18.8,pb:6.5,revenue:134000000},
  ],
}

function buildMockMethods(companyId, previousData) {
  return {
    ...MOCK_METHODS,
    ...previousData,
    company_id: companyId,
    company_name: previousData?.company_name ?? '当前公司',
  }
}

export default function ValuationAnalysis() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [dcfParams, setDcfParams] = useState({ discount_rate:10, growth_rate:5, projection_years:5 })

  useEffect(() => { runAndLoad() }, [id])

  async function runAndLoad(params) {
    setLoading(true)
    try {
      await api.runValuation(id, params || {})
      const m = await api.getValuationMethods(id)
      setData(m)
      if (m.methods) {
        const dcf = m.methods.find(m => m.method_name === 'dcf')
        if (dcf?.params) {
          setDcfParams({
            discount_rate: Math.round(dcf.params.discount_rate * 100),
            growth_rate: Math.round(dcf.params.growth_rate * 100),
            projection_years: dcf.params.projection_years,
          })
        }
      }
    } catch {
      setData(prev => buildMockMethods(id, prev))
    } finally {
      setLoading(false)
    }
  }

  function handleRecalc() {
    runAndLoad({
      dcf_discount_rate: dcfParams.discount_rate / 100,
      dcf_growth_rate: dcfParams.growth_rate / 100,
      dcf_projection_years: dcfParams.projection_years,
    })
  }

  if (loading || !data) {
    return <div className="loading-container"><div className="spinner" /><span style={{color:'var(--text2)'}}>估值计算中…</span></div>
  }

  // Range comparison chart data
  const rangeData = data.methods.map(m => ({
    name: m.display_name,
    low: m.valuation_low / 10000000,
    mid: (m.valuation_mid - m.valuation_low) / 10000000,
    high: (m.valuation_high - m.valuation_mid) / 10000000,
  }))

  // DCF projection chart
  const dcfChartData = data.dcf_projection ? [
    { year: `基期`, projected: data.dcf_projection.base_cashflow, discounted: data.dcf_projection.base_cashflow, terminal: null },
    ...data.dcf_projection.yearly_cashflows.map(y => ({ year: y.year, projected: y.projected, discounted: y.discounted, terminal: null })),
    { year: '终值', projected: null, discounted: data.dcf_projection.terminal_value_discounted, terminal: data.dcf_projection.terminal_value },
  ] : []

  // Scatter data
  const scatterData = (data.comparable_scatter || []).map(s => ({
    ...s, z: Math.max(Math.sqrt(s.revenue / 1000000) * 3, 8),
  }))

  return (
    <>
      <h1 className="page-title">多方法估值分析</h1>
      <p className="page-desc">基于 {data.comparable_count} 家已确认可比公司，并行运行 PE 可比法、DCF 法、P/B 法</p>
      <Stepper />

      {/* Target Info */}
      <div className="grid-4" style={{ marginBottom:20 }}>
        <StatCard label="目标公司" value={data.company_name} delay={0} />
        <StatCard label="目标净利润" value={fmtWanyi(data.target_net_profit)} delay={0.05} />
        <StatCard label="目标净资产" value={fmtWanyi(data.target_net_assets)} delay={0.1} />
        <StatCard label="可比公司" value={`${data.comparable_count} 家`} delay={0.15} />
      </div>

      {/* Three Method Cards */}
      <div className="grid-3">
        {data.methods.map((m, i) => (
          <Card key={m.method_name} className={`method-card${METHOD_CLASS[m.method_name] || ''}`} delay={0.1 + i*0.08}>
            <div className="card-title"><span className="dot" style={{ background: METHOD_COLORS[m.method_name] }} />{m.display_name}</div>
            <div style={{ textAlign:'center', marginBottom:16 }}>
              <div style={{fontSize:12,color:'var(--text2)'}}>估值中位数</div>
              <div style={{fontSize:32,fontWeight:800,color:METHOD_COLORS[m.method_name]}}>{fmtWanyi(m.valuation_mid)}</div>
              <div style={{fontSize:12,color:'var(--text2)'}}>区间：{fmtWanyi(m.valuation_low)} ~ {fmtWanyi(m.valuation_high)}</div>
            </div>

            {m.method_name === 'pe_comparable' && (
              <table style={{fontSize:13}}>
                <tbody>
                  <tr><td style={{color:'var(--text2)'}}>可比 PE 中位数</td><td><strong>{m.params.comparable_pe_median}x</strong></td></tr>
                  <tr><td style={{color:'var(--text2)'}}>PE 范围</td><td>{m.params.comparable_pe_range[0]} ~ {m.params.comparable_pe_range[1]}</td></tr>
                  <tr><td style={{color:'var(--text2)'}}>目标净利润</td><td>{data.target_net_profit.toLocaleString()} 万</td></tr>
                </tbody>
              </table>
            )}

            {m.method_name === 'dcf' && (
              <>
                <div className="param-group">
                  <label>折现率</label>
                  <input type="range" min={1} max={30} value={dcfParams.discount_rate}
                    onChange={e => setDcfParams(p => ({...p, discount_rate: +e.target.value}))} />
                  <span className="param-val">{dcfParams.discount_rate}%</span>
                </div>
                <div className="param-group">
                  <label>永续增长率</label>
                  <input type="range" min={0} max={15} value={dcfParams.growth_rate}
                    onChange={e => setDcfParams(p => ({...p, growth_rate: +e.target.value}))} />
                  <span className="param-val">{dcfParams.growth_rate}%</span>
                </div>
                <div className="param-group">
                  <label>预测年数</label>
                  <input type="range" min={3} max={10} value={dcfParams.projection_years}
                    onChange={e => setDcfParams(p => ({...p, projection_years: +e.target.value}))} />
                  <span className="param-val">{dcfParams.projection_years} 年</span>
                </div>
                <div style={{marginTop:8,textAlign:'right'}}>
                  <button className="btn btn-outline btn-sm" onClick={handleRecalc}>🔄 调参重算</button>
                </div>
              </>
            )}

            {m.method_name === 'pb' && (
              <table style={{fontSize:13}}>
                <tbody>
                  <tr><td style={{color:'var(--text2)'}}>可比 P/B 中位数</td><td><strong>{m.params.comparable_pb_median}x</strong></td></tr>
                  <tr><td style={{color:'var(--text2)'}}>P/B 范围</td><td>{m.params.comparable_pb_range[0]} ~ {m.params.comparable_pb_range[1]}</td></tr>
                  <tr><td style={{color:'var(--text2)'}}>目标净资产</td><td>{data.target_net_assets.toLocaleString()} 万</td></tr>
                </tbody>
              </table>
            )}

            <motion.div
              style={{marginTop:12,padding:10,background:'#F8FAFC',borderRadius:8,fontSize:12,color:'var(--text2)',lineHeight:1.6}}
              initial={{ opacity:0 }}
              animate={{ opacity:1 }}
              transition={{ delay: 0.5 + i*0.1 }}
            >
              💡 {m.calculation_detail}
            </motion.div>
          </Card>
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid-2" style={{ marginTop:4 }}>
        <Card title="三种估值方法区间对比" delay={0.3}>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={rangeData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
              <XAxis type="number" unit=" 万亿" />
              <YAxis type="category" dataKey="name" width={100} />
              <Tooltip formatter={v => v.toFixed(2) + ' 万亿'} />
              <Legend />
              <Bar dataKey="low" name="估值下限" stackId="a" fill="rgba(79,107,246,.3)" radius={[0,0,0,0]} animationDuration={1000} />
              <Bar dataKey="mid" name="估值中位" stackId="a" fill="#4F6BF6" animationDuration={1000} />
              <Bar dataKey="high" name="估值上限" stackId="a" fill="rgba(79,107,246,.5)" radius={[0,6,6,0]} animationDuration={1000} />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card title="可比公司 PE / P/B 散点分布" delay={0.35}>
          <ResponsiveContainer width="100%" height={300}>
            <ScatterChart>
              <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
              <XAxis dataKey="pe" name="PE" unit="" />
              <YAxis dataKey="pb" name="P/B" unit="" />
              <ZAxis dataKey="z" range={[50, 400]} />
              <Tooltip cursor={{ strokeDasharray:'3 3' }} content={({ payload }) => {
                if (!payload?.length) return null
                const d = payload[0].payload
                return (
                  <div style={{background:'#fff',padding:10,borderRadius:8,boxShadow:'0 2px 8px rgba(0,0,0,.12)',fontSize:13}}>
                    <strong>{d.name}</strong><br />
                    PE: {d.pe} · P/B: {d.pb}<br />
                    营收: {d.revenue.toLocaleString()} 万
                  </div>
                )
              }} />
              <Scatter data={scatterData} fill="#4F6BF6" fillOpacity={0.6} animationDuration={1200} />
            </ScatterChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* DCF Chart */}
      {data.dcf_projection && (
        <Card title="DCF 现金流预测（单位：万元）" delay={0.4}>
          <ResponsiveContainer width="100%" height={260}>
            <ComposedChart data={dcfChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
              <XAxis dataKey="year" />
              <YAxis tickFormatter={fmt} />
              <Tooltip formatter={v => v ? v.toLocaleString() + ' 万' : '-'} />
              <Legend />
              <Bar dataKey="projected" name="预测现金流" fill="rgba(34,197,94,.15)" stroke="#22C55E" strokeWidth={1.5} radius={[6,6,0,0]} animationDuration={1000} />
              <Bar dataKey="terminal" name="终值" fill="rgba(139,92,246,.15)" stroke="#8B5CF6" strokeWidth={1.5} radius={[6,6,0,0]} animationDuration={1000} />
              <Line type="monotone" dataKey="discounted" name="折现后" stroke="#4F6BF6" strokeWidth={2} dot={{ r:4 }} animationDuration={1200} />
            </ComposedChart>
          </ResponsiveContainer>
        </Card>
      )}

      <div style={{ textAlign:'right', marginTop:8 }}>
        <button className="btn btn-primary" onClick={() => navigate(`/company/${id}/result`)}>
          查看综合结果 →
        </button>
      </div>
    </>
  )
}
