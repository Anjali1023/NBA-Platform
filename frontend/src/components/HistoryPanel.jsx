
function HistoryPanel({ history, customerId }) {
  return (
    <div className="rounded-2xl border border-gray-800 bg-gray-900 p-5 shadow-xl">
      <h2 className="mb-4 text-lg font-semibold text-white">Past Interactions</h2>
      {history.length === 0 ? (
        <p className="text-sm text-gray-400">No approved history yet for {customerId}.</p>
      ) : (
        <ul className="space-y-3">
          {history.map((entry, index) => (
            <li key={`${entry.created_at}-${index}`} className="rounded-xl border border-gray-800 bg-gray-800/70 p-3 text-sm text-gray-300">
              <div className="mb-1 flex items-center justify-between">
                <span className="font-medium text-white">{entry.customer_id}</span>
                <span className="text-gray-400">{entry.created_at ? new Date(entry.created_at).toLocaleDateString() : 'Recent'}</span>
              </div>
              <p className="text-gray-400">{Array.isArray(entry.recommendations) ? entry.recommendations[0]?.action || 'Approved action' : 'Approved action'}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default HistoryPanel
