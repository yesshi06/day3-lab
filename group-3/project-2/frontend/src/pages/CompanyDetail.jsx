import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  BarChart, Bar, LineChart, Line, RadarChart, Radar, PolarGrid, PolarAngleAxis,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, AreaChart,
  ComposedChart,
} from 'recharts'
import { api } from '../api'
import Card from '../components/Card'
import StatCard from '../components/StatCard'
import Stepper from '../components/Stepper'
import '../components/components.css'

const fmt = v => {
  if (v >= 10000) return (v / 10000).toFixed(0) + '万'
  return v
}

const emptySummary = {
  period: '-',
  revenue: 0,
  net_profit: 0,
  total_assets: 0,
  net_assets: 0,
  operating_cashflow: 0,
  yoy_revenue: 0,
  yoy_net_profit: 0,
  yoy_net_assets: 0,
  summary_note: '暂无财务数据',
}

const emptyRatios = {
  net_profit_margin: 0,
  roa: 0,
  revenue_growth: 0,
  cashflow_ratio: 0,
  debt_ratio: 0,
}

function normalizeCompany(company) {
  if (!company) return null
  return {
    ...company,
    industry_info: {
      avg_pe: company.industry_info?.avg_pe ?? 0,
      growth_rate: company.industry_info?.growth_rate ?? 0,
      company_count: company.industry_info?.company_count ?? 0,
      pe_distribution: company.industry_info?.pe_distribution ?? [],
    },
  }
}

function normalizeFinancials(financials) {
  const rows = Array.isArray(financials?.financials) ? financials.financials : []
  const latest = financials?.latest_summary ?? rows.at(-1) ?? emptySummary

  return {
    ...financials,
    latest_summary: { ...emptySummary, ...latest },
    financials: rows,
    ratios: { ...emptyRatios, ...(financials?.ratios ?? {}) },
    industry_avg_ratios: { ...emptyRatios, ...(financials?.industry_avg_ratios ?? {}) },
  }
}

export default function CompanyDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [company, setCompany] = useState(null)
  const [financials, setFinancials] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => { loadData() }, [id])

  async function loadData() {
    setLoading(true)
    try {
      const [comp, fin] = await Promise.all([api.getCompany(id), api.getFinancials(id)])
      setCompany(normalizeCompany(comp))
      setFinancials(normalizeFinancials(fin))
    } catch {
      // Fallback mock
      setCompany(normalizeCompany({
        company_id: id, name: `公司 ${id}`, industry: '未知行业', founded_year: '-',
        description: '暂无公司简介（后端服务不可用，当前为演示数据）', has_financials: true,
        industry_info:{
          avg_pe:25.3, growth_rate:12.5, company_count:34,
          pe_distribution:[
            {range:'<15',count:3},{range:'15-20',count:5},{range:'20-25',count:10},
            {range:'25-30',count:8},{range:'30-35',count:5},{range:'>35',count:3},
          ],
        },
      }))
      setFinancials(normalizeFinancials({
        company_id:id,
        latest_summary:{
          period:'2025-FY', revenue:6000000, net_profit:1200000,
          total_assets:15000000, net_assets:8000000, operating_cashflow:1500000,
          yoy_revenue:18.0, yoy_net_profit:22.0, yoy_net_assets:15.0, summary_note:'稳健增长',
        },
        financials:[
          {period:'2021-FY',revenue:2800000,net_profit:350000,total_assets:7200000,net_assets:3600000,operating_cashflow:550000},
          {period:'2022-FY',revenue:3500000,net_profit:520000,total_assets:8900000,net_assets:4700000,operating_cashflow:720000},
          {period:'2023-FY',revenue:4200000,net_profit:750000,total_assets:10500000,net_assets:5800000,operating_cashflow:980000},
          {period:'2024-FY',revenue:5100000,net_profit:980000,total_assets:12800000,net_assets:6950000,operating_cashflow:1250000},
          {period:'2025-FY',revenue:6000000,net_profit:1200000,total_assets:15000000,net_assets:8000000,operating_cashflow:1500000},
        ],
        ratios:{ net_profit_margin:20, roa:8, revenue_growth:18, cashflow_ratio:25, debt_ratio:47 },
        industry_avg_ratios:{ net_profit_margin:15, roa:6, revenue_growth:12, cashflow_ratio:20, debt_ratio:52 },
      }))
    } finally {
      setLoading(false)
    }
  }

  if (loading || !company || !financials) {
    return <div className="loading-container"><div className="spinner" /><span style={{color:'var(--text2)'}}>加载中…</span></div>
  }

  const ls = financials.latest_summary
  const fin = financials.financials.map(f => ({ ...f, year: f.period.replace('-FY','') }))
  const radarData = [
    { name:'净利润率', company:financials.ratios.net_profit_margin, industry:financials.industry_avg_ratios.net_profit_margin },
    { name:'资产回报率', company:financials.ratios.roa, industry:financials.industry_avg_ratios.roa },
    { name:'营收增速', company:financials.ratios.revenue_growth, industry:financials.industry_avg_ratios.revenue_growth },
    { name:'现金流比率', company:financials.ratios.cashflow_ratio, industry:financials.industry_avg_ratios.cashflow_ratio },
    { name:'资产负债率', company:financials.ratios.debt_ratio, industry:financials.industry_avg_ratios.debt_ratio },
  ]
  const assetsData = fin.map(f => ({
    year: f.year,
    net_assets: f.net_assets,
    debt: f.total_assets - f.net_assets,
  }))

  return (
    <>
      <h1 className="page-title">{company.name} — 公司详情</h1>
      <p className="page-desc">查看基本信息、行业概况和财务三表核心数据</p>
      <Stepper />

      {/* Basic Info Row */}
      <div className="grid-3" style={{ marginBottom: 20 }}>
        <Card title="基本信息" delay={0.05}>
          <table>
            <tbody>
              <tr><td style={{color:'var(--text2)'}}>公司名称</td><td><strong>{company.name}</strong></td></tr>
              <tr><td style={{color:'var(--text2)'}}>行业分类</td><td><span className="badge badge-blue">{company.industry}</span></td></tr>
              <tr><td style={{color:'var(--text2)'}}>成立年份</td><td>{company.founded_year}</td></tr>
              <tr><td style={{color:'var(--text2)'}}>公司简介</td><td>{company.description}</td></tr>
              <tr><td style={{color:'var(--text2)'}}>财务数据</td><td><span className="badge badge-green">{company.has_financials ? '已就绪' : '无数据'}</span></td></tr>
            </tbody>
          </table>
        </Card>

        <Card title="行业概况" delay={0.1}>
          <div style={{ marginBottom:16 }}>
            <div style={{fontSize:12,color:'var(--text2)'}}>行业平均 PE</div>
            <div style={{fontSize:32,fontWeight:700}}>{company.industry_info.avg_pe}<span style={{fontSize:14,color:'var(--text2)'}}>x</span></div>
          </div>
          <div style={{ marginBottom:16 }}>
            <div style={{fontSize:12,color:'var(--text2)'}}>行业增速</div>
            <div style={{fontSize:32,fontWeight:700,color:'var(--success)'}}>{company.industry_info.growth_rate}<span style={{fontSize:14}}>%</span></div>
          </div>
          <div>
            <div style={{fontSize:12,color:'var(--text2)'}}>行业公司数量</div>
            <div style={{fontSize:32,fontWeight:700}}>{company.industry_info.company_count}</div>
          </div>
        </Card>

        <Card title="行业 PE 分布" delay={0.15}>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={company.industry_info.pe_distribution}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
              <XAxis dataKey="range" tick={{fontSize:11}} />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" name="公司数" fill="rgba(79,107,246,.15)" stroke="#4F6BF6" strokeWidth={1.5} radius={[4,4,0,0]} animationDuration={800} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Financial Stat Cards */}
      <div className="grid-4" style={{ marginBottom: 20 }}>
        <StatCard label="营收（万元）" value={`${(ls.revenue/10000).toFixed(0)} 万`} sub={`同比 +${ls.yoy_revenue}%`} delay={0.1} />
        <StatCard label="净利润（万元）" value={`${(ls.net_profit/10000).toFixed(0)} 万`} sub={`同比 +${ls.yoy_net_profit}%`} delay={0.15} />
        <StatCard label="总资产（万元）" value={`${(ls.total_assets/10000).toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g,',')} 万`} sub={ls.summary_note || '稳健增长'} delay={0.2} />
        <StatCard label="净资产（万元）" value={`${(ls.net_assets/10000).toFixed(0)} 万`} sub={`同比 +${ls.yoy_net_assets}%`} delay={0.25} />
      </div>

      {!financials.financials.length && (
        <Card title="财务数据提示" delay={0.12}>
          <div style={{ color:'var(--text2)' }}>
            该公司当前缺少财务明细，页面已使用空值兜底展示基础信息。补齐财务数据后，趋势图和财务表会自动恢复。
          </div>
        </Card>
      )}

      {/* Financial Charts */}
      <div className="grid-2">
        <Card title="营收与净利润趋势（近 5 年）" delay={0.15}>
          <ResponsiveContainer width="100%" height={280}>
            <ComposedChart data={fin}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
              <XAxis dataKey="year" />
              <YAxis yAxisId="left" tickFormatter={fmt} />
              <YAxis yAxisId="right" orientation="right" tickFormatter={fmt} />
              <Tooltip formatter={v => v.toLocaleString() + ' 万元'} />
              <Legend />
              <Bar yAxisId="left" dataKey="revenue" name="营收" fill="rgba(79,107,246,.15)" stroke="#4F6BF6" strokeWidth={1.5} radius={[6,6,0,0]} animationDuration={1000} />
              <Line yAxisId="right" type="monotone" dataKey="net_profit" name="净利润" stroke="#22C55E" strokeWidth={2} dot={{ r:4 }} animationDuration={1200} />
            </ComposedChart>
          </ResponsiveContainer>
        </Card>

        <Card title="资产结构变化" delay={0.2}>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={assetsData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
              <XAxis dataKey="year" />
              <YAxis tickFormatter={fmt} />
              <Tooltip formatter={v => v.toLocaleString() + ' 万元'} />
              <Legend />
              <Bar dataKey="net_assets" name="净资产" stackId="a" fill="#4F6BF6" radius={[0,0,0,0]} animationDuration={1000} />
              <Bar dataKey="debt" name="负债" stackId="a" fill="#CBD5E1" radius={[6,6,0,0]} animationDuration={1000} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      <div className="grid-2">
        <Card title="经营现金流趋势" delay={0.25}>
          <ResponsiveContainer width="100%" height={240}>
            <AreaChart data={fin}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
              <XAxis dataKey="year" />
              <YAxis tickFormatter={fmt} />
              <Tooltip formatter={v => v.toLocaleString() + ' 万元'} />
              <Area type="monotone" dataKey="operating_cashflow" name="经营现金流" stroke="#22C55E" fill="rgba(34,197,94,.15)" strokeWidth={2} dot={{ r:4 }} animationDuration={1200} />
            </AreaChart>
          </ResponsiveContainer>
        </Card>

        <Card title="关键财务比率" delay={0.3}>
          <ResponsiveContainer width="100%" height={240}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="#E2E8F0" />
              <PolarAngleAxis dataKey="name" tick={{fontSize:12}} />
              <Radar name={company.name} dataKey="company" stroke="#4F6BF6" fill="rgba(79,107,246,.15)" strokeWidth={2} dot={{ r:3 }} animationDuration={1000} />
              <Radar name="行业平均" dataKey="industry" stroke="#F59E0B" fill="rgba(245,158,11,.15)" strokeWidth={2} dot={{ r:3 }} animationDuration={1200} />
              <Legend />
              <Tooltip />
            </RadarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Financial Table */}
      <Card title="财务三表核心数据（单位：万元）" delay={0.3}>
        <table>
          <thead>
            <tr><th>期间</th><th>营收</th><th>净利润</th><th>总资产</th><th>净资产</th><th>经营现金流</th></tr>
          </thead>
          <tbody>
            {[...financials.financials].reverse().map((f, i) => (
              <motion.tr
                key={f.period}
                initial={{ opacity:0, x:-10 }}
                animate={{ opacity:1, x:0 }}
                transition={{ delay: 0.35 + i*0.05 }}
              >
                <td>{f.period}</td>
                <td>{f.revenue.toLocaleString()}</td>
                <td>{f.net_profit.toLocaleString()}</td>
                <td>{f.total_assets.toLocaleString()}</td>
                <td>{f.net_assets.toLocaleString()}</td>
                <td>{f.operating_cashflow.toLocaleString()}</td>
              </motion.tr>
            ))}
          </tbody>
        </table>
      </Card>

      <div style={{ textAlign:'right', marginTop:8 }}>
        <button className="btn btn-primary" onClick={() => navigate(`/company/${id}/comparables`)}>
          下一步：选择可比公司 →
        </button>
      </div>
    </>
  )
}
