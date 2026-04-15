import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts'
import { api } from '../api'
import Card from '../components/Card'
import StatCard from '../components/StatCard'
import '../components/components.css'

const COLORS_PIE = ['#4F6BF6','#8B5CF6','#22C55E','#06B6D4','#F59E0B','#EF4444','#EC4899','#94A3B8']

export default function Dashboard() {
  const navigate = useNavigate()
  const [companies, setCompanies] = useState(null)
  const [stats, setStats] = useState(null)
  const [keyword, setKeyword] = useState('')
  const [industry, setIndustry] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [])

  async function loadData(params = {}) {
    setLoading(true)
    try {
      const [compData, statData] = await Promise.all([
        api.getCompanies(params),
        api.getStatistics(),
      ])
      setCompanies(compData)
      setStats(statData)
    } catch {
      // Fallback mock data for demo
      setCompanies({
        total: 6, page: 1, page_size: 20,
        companies: [
          { company_id:'comp_001', name:'字节跳动', industry:'互联网', has_valuation:false },
          { company_id:'comp_002', name:'米哈游', industry:'游戏', has_valuation:true },
          { company_id:'comp_003', name:'蚂蚁集团', industry:'金融科技', has_valuation:false },
          { company_id:'comp_004', name:'大疆创新', industry:'智能硬件', has_valuation:true },
          { company_id:'comp_005', name:'SpaceX', industry:'航天', has_valuation:false },
          { company_id:'comp_006', name:'Shein', industry:'电商', has_valuation:false },
        ],
      })
      setStats({
        total_companies:128, valued_companies:47, valued_ratio:36.7,
        total_industries:12, industry_groups:6, weekly_new_companies:5, weekly_new_delta:3,
        industry_distribution:[
          {industry:'互联网',count:34},{industry:'游戏',count:18},{industry:'新能源',count:22},
          {industry:'半导体',count:15},{industry:'医药',count:12},{industry:'金融科技',count:10},
          {industry:'智能硬件',count:8},{industry:'其他',count:9},
        ],
        valuation_status:{ valued:47, not_valued:81 },
        industry_avg_pe:[
          {industry:'互联网',avg_pe:25.3},{industry:'游戏',avg_pe:32.1},{industry:'新能源',avg_pe:45.6},
          {industry:'半导体',avg_pe:38.2},{industry:'医药',avg_pe:28.9},{industry:'金融科技',avg_pe:15.4},
        ],
      })
    } finally {
      setLoading(false)
    }
  }

  function handleSearch() {
    const params = {}
    if (keyword) params.keyword = keyword
    if (industry) params.industry = industry
    loadData(params)
  }

  if (loading || !stats || !companies) {
    return (
      <div className="loading-container">
        <div className="spinner" />
        <span style={{ color: 'var(--text2)' }}>加载中…</span>
      </div>
    )
  }

  const valStatusData = [
    { name: '已估值', value: stats.valuation_status.valued },
    { name: '未估值', value: stats.valuation_status.not_valued },
  ]

  const industries = [...new Set(companies.companies.map(c => c.industry))]

  return (
    <>
      <h1 className="page-title">目标公司选择</h1>
      <p className="page-desc">按名称搜索或行业筛选，选定后进入公司详情开始估值分析</p>

      <div className="search-bar">
        <input
          type="text"
          placeholder="🔍  搜索公司名称 …"
          value={keyword}
          onChange={e => setKeyword(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSearch()}
        />
        <select value={industry} onChange={e => setIndustry(e.target.value)}>
          <option value="">全部行业</option>
          {stats.industry_distribution.map(d => (
            <option key={d.industry} value={d.industry}>{d.industry}</option>
          ))}
        </select>
        <button className="btn btn-primary" onClick={handleSearch}>搜索</button>
      </div>

      {/* Stat Cards */}
      <div className="grid-4" style={{ marginBottom: 20 }}>
        <StatCard label="公司总数" value={stats.total_companies} sub="持续更新中" delay={0} />
        <StatCard label="已有估值" value={stats.valued_companies} sub={`占比 ${stats.valued_ratio}%`} delay={0.05} />
        <StatCard label="覆盖行业" value={stats.total_industries} delay={0.1} />
        <StatCard label="本周新增" value={stats.weekly_new_companies} delay={0.15} />
      </div>

      <div className="grid-2">
        {/* Company Table */}
        <Card title={`搜索结果（共 ${companies.total} 家匹配）`} delay={0.1}>
          <table>
            <thead>
              <tr><th>公司名称</th><th>行业</th><th>估值状态</th><th>操作</th></tr>
            </thead>
            <tbody>
              {companies.companies.map((c, i) => (
                <motion.tr
                  key={c.company_id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.15 + i * 0.04 }}
                >
                  <td><strong>{c.name}</strong></td>
                  <td><span className="badge badge-blue">{c.industry}</span></td>
                  <td>
                    {c.has_valuation
                      ? <span className="badge badge-green">已估值</span>
                      : <span className="badge badge-yellow">未估值</span>}
                  </td>
                  <td>
                    <button
                      className={`btn btn-sm ${c.has_valuation ? 'btn-outline' : 'btn-primary'}`}
                      onClick={() => navigate(`/company/${c.company_id}`)}
                    >
                      {c.has_valuation ? '查看' : '选定 →'}
                    </button>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </Card>

        {/* Industry Distribution */}
        <Card title="行业分布（公司数量）" delay={0.15}>
          <ResponsiveContainer width="100%" height={320}>
            <PieChart>
              <Pie
                data={stats.industry_distribution}
                dataKey="count"
                nameKey="industry"
                cx="50%" cy="50%"
                innerRadius={60} outerRadius={110}
                paddingAngle={3}
                animationBegin={200}
                animationDuration={800}
              >
                {stats.industry_distribution.map((_, i) => (
                  <Cell key={i} fill={COLORS_PIE[i % COLORS_PIE.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Second Row Charts */}
      <div className="grid-2">
        <Card title="估值状态分布" delay={0.2}>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie
                data={valStatusData}
                dataKey="value"
                nameKey="name"
                cx="50%" cy="50%"
                outerRadius={90}
                animationBegin={400}
                animationDuration={800}
              >
                <Cell fill="#4F6BF6" />
                <Cell fill="#E2E8F0" />
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </Card>

        <Card title="各行业平均 PE 对比" delay={0.25}>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={stats.industry_avg_pe}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
              <XAxis dataKey="industry" tick={{ fontSize: 12 }} />
              <YAxis />
              <Tooltip />
              <Bar dataKey="avg_pe" name="平均 PE" fill="rgba(79,107,246,0.15)" stroke="#4F6BF6" strokeWidth={1.5} radius={[6,6,0,0]} animationDuration={1000} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>
    </>
  )
}
