import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import WelcomeStep from './WelcomeStep'
import AccountStep from './AccountStep'
import IncomeStep from './IncomeStep'
import FixedObligationStep from './FixedObligationStep'
import BudgetStep from './BudgetStep'
import CreditCardStep from './CreditCardStep'

const STEPS = ['歡迎', '帳戶', '收入', '固定支出', '生活費預算', '信用卡'] as const
type StepIndex = 0 | 1 | 2 | 3 | 4 | 5

export default function SetupWizard() {
  const [step, setStep] = useState<StepIndex>(0)
  const navigate = useNavigate()
  const qc = useQueryClient()

  const next = () => setStep((s) => Math.min(s + 1, 5) as StepIndex)
  const prev = () => setStep((s) => Math.max(s - 1, 0) as StepIndex)
  const finish = () => {
    qc.invalidateQueries()
    navigate('/', { replace: true })
  }

  return (
    <div className="max-w-2xl mx-auto py-8">
      {/* Progress bar */}
      <div className="mb-8">
        <div className="flex justify-between mb-2">
          {STEPS.map((label, i) => (
            <span
              key={label}
              className={`text-xs font-medium ${
                i <= step ? 'text-indigo-600' : 'text-gray-400'
              }`}
            >
              {label}
            </span>
          ))}
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-indigo-600 h-2 rounded-full transition-all"
            style={{ width: `${((step + 1) / STEPS.length) * 100}%` }}
          />
        </div>
      </div>

      {/* Step content */}
      {step === 0 && <WelcomeStep onNext={next} />}
      {step === 1 && <AccountStep onNext={next} onPrev={prev} />}
      {step === 2 && <IncomeStep onNext={next} onPrev={prev} />}
      {step === 3 && <FixedObligationStep onNext={next} onPrev={prev} />}
      {step === 4 && <BudgetStep onNext={next} onPrev={prev} />}
      {step === 5 && <CreditCardStep onFinish={finish} onPrev={prev} />}
    </div>
  )
}
