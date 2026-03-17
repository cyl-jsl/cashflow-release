import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, NavLink, useNavigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Dashboard from './pages/Dashboard'
import Accounts from './pages/Accounts'
import Incomes from './pages/Incomes'
import Obligations from './pages/Obligations'
import CreditCards from './pages/CreditCards'
import Planning from './pages/Planning'
import Simulate from './pages/Simulate'
import Transactions from './pages/Transactions'
import SetupWizard from './pages/setup/SetupWizard'
import { useIsFirstTimeUser } from './hooks/useSystem'

const queryClient = new QueryClient()

function Nav() {
  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `px-3 py-2 rounded-md text-sm font-medium ${
      isActive ? 'bg-indigo-700 text-white' : 'text-indigo-200 hover:bg-indigo-600'
    }`

  return (
    <nav className="bg-indigo-800 px-4 py-3">
      <div className="max-w-5xl mx-auto flex items-center gap-2">
        <span className="text-white font-bold mr-4">金流儀表板</span>
        <NavLink to="/" className={linkClass} end>首頁</NavLink>
        <NavLink to="/accounts" className={linkClass}>帳戶</NavLink>
        <NavLink to="/incomes" className={linkClass}>收入</NavLink>
        <NavLink to="/obligations" className={linkClass}>義務</NavLink>
        <NavLink to="/credit-cards" className={linkClass}>信用卡</NavLink>
        <NavLink to="/planning" className={linkClass}>試算</NavLink>
        <NavLink to="/simulate" className={linkClass}>模擬</NavLink>
        <NavLink to="/transactions" className={linkClass}>匯入</NavLink>
      </div>
    </nav>
  )
}

function DashboardOrSetup() {
  const { isFirstTime, isLoading } = useIsFirstTimeUser()
  const navigate = useNavigate()

  useEffect(() => {
    if (!isLoading && isFirstTime) {
      navigate('/setup', { replace: true })
    }
  }, [isFirstTime, isLoading, navigate])

  if (isLoading) return <div className="p-8 text-center text-gray-500">載入中...</div>
  return <Dashboard />
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Nav />
        <main className="max-w-5xl mx-auto p-4">
          <Routes>
            <Route path="/" element={<DashboardOrSetup />} />
            <Route path="/setup" element={<SetupWizard />} />
            <Route path="/accounts" element={<Accounts />} />
            <Route path="/incomes" element={<Incomes />} />
            <Route path="/obligations" element={<Obligations />} />
            <Route path="/credit-cards" element={<CreditCards />} />
            <Route path="/planning" element={<Planning />} />
            <Route path="/simulate" element={<Simulate />} />
            <Route path="/transactions" element={<Transactions />} />
          </Routes>
        </main>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
