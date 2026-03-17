import { useState } from 'react'
import { useTransactions, useImportTransactions, useDeleteTransactions } from '../hooks/useTransactions'
import { useCreditCards } from '../hooks/useCreditCards'
import type { ImportResponse } from '../api/types'

export default function Transactions() {
  const { data: transactions, isLoading } = useTransactions()
  const { data: cards } = useCreditCards()
  const importMut = useImportTransactions()
  const deleteMut = useDeleteTransactions()

  const [file, setFile] = useState<File | null>(null)
  const [dateCol, setDateCol] = useState('date')
  const [descCol, setDescCol] = useState('description')
  const [amountCol, setAmountCol] = useState('amount')
  const [cardId, setCardId] = useState<number | undefined>(undefined)
  const [importResult, setImportResult] = useState<ImportResponse | null>(null)

  const handleImport = async () => {
    if (!file) return
    try {
      const result = await importMut.mutateAsync({
        file,
        dateColumn: dateCol,
        descriptionColumn: descCol,
        amountColumn: amountCol,
        creditCardId: cardId,
      })
      setImportResult(result)
      setFile(null)
    } catch {
      // error handled by mutation state
    }
  }

  // Group transactions by source_file
  const sourceFiles = [...new Set((transactions || []).map((t) => t.source_file))]

  const fmt = (n: number) =>
    n.toLocaleString('zh-TW', { style: 'currency', currency: 'TWD', minimumFractionDigits: 0 })

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">交易匯入</h1>

      {/* Import form */}
      <div className="bg-white p-4 rounded-lg shadow space-y-3">
        <h2 className="font-semibold">匯入 CSV / Excel</h2>

        <input
          type="file"
          accept=".csv,.xlsx,.xls"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
        />

        <div className="grid grid-cols-3 gap-2">
          <div>
            <label className="text-xs text-gray-500">日期欄位名</label>
            <input className="w-full border rounded px-2 py-1 text-sm" value={dateCol} onChange={(e) => setDateCol(e.target.value)} />
          </div>
          <div>
            <label className="text-xs text-gray-500">描述欄位名</label>
            <input className="w-full border rounded px-2 py-1 text-sm" value={descCol} onChange={(e) => setDescCol(e.target.value)} />
          </div>
          <div>
            <label className="text-xs text-gray-500">金額欄位名</label>
            <input className="w-full border rounded px-2 py-1 text-sm" value={amountCol} onChange={(e) => setAmountCol(e.target.value)} />
          </div>
        </div>

        <div>
          <label className="text-xs text-gray-500">關聯信用卡（選填）</label>
          <select className="w-full border rounded px-2 py-1 text-sm" value={cardId || ''} onChange={(e) => setCardId(e.target.value ? Number(e.target.value) : undefined)}>
            <option value="">無</option>
            {(cards || []).map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </div>

        <button
          onClick={handleImport}
          disabled={!file || importMut.isPending}
          className="bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700 disabled:opacity-50"
        >
          {importMut.isPending ? '匯入中...' : '匯入'}
        </button>

        {importMut.isError && (
          <p className="text-red-600 text-sm">{importMut.error.message}</p>
        )}

        {importResult && (
          <div className="bg-green-50 p-3 rounded text-sm text-green-800">
            成功匯入 {importResult.transactions_created} 筆交易，支出合計 {fmt(importResult.total_spending)}
          </div>
        )}
      </div>

      {/* Transaction list by source file */}
      {isLoading ? (
        <p className="text-gray-500">載入中...</p>
      ) : sourceFiles.length === 0 ? (
        <p className="text-gray-400">尚無匯入紀錄</p>
      ) : (
        sourceFiles.map((sf) => {
          const items = (transactions || []).filter((t) => t.source_file === sf)
          const total = items.reduce((s, t) => s + t.amount, 0)
          return (
            <div key={sf} className="bg-white p-4 rounded-lg shadow">
              <div className="flex justify-between items-center mb-2">
                <h3 className="font-semibold text-sm">{sf} ({items.length} 筆，合計 {fmt(total)})</h3>
                <button
                  onClick={() => deleteMut.mutate(sf)}
                  className="text-red-500 text-xs hover:underline"
                >
                  刪除此批匯入
                </button>
              </div>
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-gray-500 border-b">
                    <th className="py-1">日期</th>
                    <th>描述</th>
                    <th className="text-right">金額</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((t) => (
                    <tr key={t.id} className="border-b last:border-0">
                      <td className="py-1">{t.date}</td>
                      <td>{t.description}</td>
                      <td className={`text-right ${t.amount < 0 ? 'text-green-600' : ''}`}>
                        {fmt(t.amount)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )
        })
      )}
    </div>
  )
}
