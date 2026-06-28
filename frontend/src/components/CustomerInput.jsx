
function CustomerInput({ customerId, setCustomerId, inputText, setInputText, onAnalyze, loading }) {
  return (
    <div className="space-y-4">
      <div>
        <label className="mb-2 block text-sm font-medium text-gray-300">Customer ID</label>
        <input
          value={customerId}
          onChange={(event) => setCustomerId(event.target.value)}
          className="w-full rounded-xl border border-gray-700 bg-gray-800 px-3 py-2 text-white outline-none"
          placeholder="Enter customer ID"
        />
      </div>
      <div>
        <label className="mb-2 block text-sm font-medium text-gray-300">Meeting transcript, email or CRM note</label>
        <textarea
          rows={8}
          value={inputText}
          onChange={(event) => setInputText(event.target.value)}
          className="w-full rounded-xl border border-gray-700 bg-gray-800 px-3 py-2 text-white outline-none"
          placeholder="Paste meeting transcript, email or CRM note here..."
        />
      </div>
      <button
        onClick={onAnalyze}
        disabled={loading}
        className="flex items-center justify-center rounded-xl bg-blue-600 px-4 py-2 font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-800"
      >
        {loading ? 'AI agents analyzing...' : 'Analyze'}
      </button>
    </div>
  )
}

export default CustomerInput
