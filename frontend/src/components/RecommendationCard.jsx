
import { useMemo, useState } from 'react'

const priorityColors = {
  high: 'bg-red-500/20 text-red-300 border-red-500/30',
  medium: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
  low: 'bg-green-500/20 text-green-300 border-green-500/30',
}

function RecommendationCard({ recommendation, onApprove, onReject, isApproved, isRejected }) {
  const [animate, setAnimate] = useState(false)
  const confidence = useMemo(() => Math.round((recommendation.confidence || 0.7) * 100), [recommendation])

  const handleApprove = () => {
    setAnimate(true)
    onApprove?.()
  }

  return (
    <div className={`rounded-2xl border border-gray-700 bg-gray-800/80 p-4 shadow-lg transition-all duration-300 ${animate ? 'scale-[1.01] ring-1 ring-blue-500/40' : ''}`}>
      <div className="mb-3 flex items-start justify-between gap-3">
        <div>
          <div className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-semibold uppercase ${priorityColors[recommendation.priority] || priorityColors.medium}`}>
            {recommendation.priority || 'medium'} priority
          </div>
          <h3 className="mt-2 text-lg font-semibold text-white">{recommendation.action}</h3>
        </div>
        {isApproved && <span className="text-sm font-medium text-green-400">Approved!</span>}
        {isRejected && <span className="text-sm font-medium text-gray-400">Rejected</span>}
      </div>

      <p className="mb-3 text-sm leading-6 text-gray-400">{recommendation.reasoning}</p>

      <div className="mb-3">
        <div className="mb-1 flex items-center justify-between text-sm text-gray-400">
          <span>Confidence</span>
          <span>{confidence}%</span>
        </div>
        <div className="h-2 rounded-full bg-gray-700">
          <div className="h-2 rounded-full bg-blue-500 transition-all duration-700" style={{ width: `${confidence}%` }} />
        </div>
      </div>

      <div className="mb-4 flex flex-wrap gap-2">
        {(recommendation.evidence || []).map((item) => (
          <button key={item} className="rounded-full border border-gray-600 bg-gray-700/70 px-2.5 py-1 text-xs text-gray-300 transition hover:border-blue-500 hover:text-blue-300">
            {item}
          </button>
        ))}
      </div>

      <div className="mb-4 flex flex-wrap gap-3 text-sm text-gray-400">
        <span>Timeline: {recommendation.timeline}</span>
        <span>Owner: {recommendation.owner}</span>
      </div>

      <div className="flex gap-3">
        <button onClick={handleApprove} className="rounded-lg bg-green-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-green-700">
          Approve
        </button>
        <button onClick={onReject} className="rounded-lg bg-gray-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-gray-500">
          Reject
        </button>
      </div>
    </div>
  )
}

export default RecommendationCard
