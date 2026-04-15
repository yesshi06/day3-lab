import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import CompanyDetail from './pages/CompanyDetail'
import ComparableSelection from './pages/ComparableSelection'
import ValuationAnalysis from './pages/ValuationAnalysis'
import ValuationResult from './pages/ValuationResult'

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/company/:id" element={<CompanyDetail />} />
        <Route path="/company/:id/comparables" element={<ComparableSelection />} />
        <Route path="/company/:id/valuation" element={<ValuationAnalysis />} />
        <Route path="/company/:id/result" element={<ValuationResult />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  )
}
