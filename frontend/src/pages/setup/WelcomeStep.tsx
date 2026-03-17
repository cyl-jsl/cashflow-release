export default function WelcomeStep({ onNext }: { onNext: () => void }) {
  return (
    <div className="text-center space-y-6">
      <h1 className="text-3xl font-bold text-gray-800">歡迎使用金流儀表板</h1>
      <p className="text-gray-600 text-lg">
        只需 6 步，快速設定你的財務狀況。<br />
        設定完成後，你就能即時看到可動用金額。
      </p>
      <div className="bg-indigo-50 p-4 rounded-lg text-sm text-indigo-800 text-left space-y-1">
        <p>我們會引導你建立：</p>
        <ul className="list-disc ml-5 space-y-1">
          <li>銀行帳戶與目前餘額</li>
          <li>收入來源（薪水等）</li>
          <li>固定支出（房租、訂閱等）</li>
          <li>每月現金生活費預算</li>
          <li>信用卡（選填）</li>
        </ul>
      </div>
      <button onClick={onNext} className="bg-indigo-600 text-white px-8 py-3 rounded-lg text-lg hover:bg-indigo-700">
        開始設定
      </button>
    </div>
  )
}
