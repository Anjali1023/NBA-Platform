
function RiskBadge({ label, value }) {
  const style = value === 'critical' || value === 'high' || value === 'opportunity'
    ? 'bg-red-500/20 text-red-300 border-red-500/30'
    : value === 'medium' || value === 'yellow'
      ? 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30'
      : 'bg-green-500/20 text-green-300 border-green-500/30'

  return <span className={`rounded-full border px-3 py-1 text-sm ${style}`}>{label}: {String(value)}</span>
}

export default RiskBadge
