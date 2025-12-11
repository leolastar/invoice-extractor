'use client'

interface StatsProps {
  stats: {
    total_orders: number
    total_value: number
    average_order_value: number
  } | null
}

export default function Stats({ stats }: StatsProps) {
  if (!stats) {
    return null
  }

  return (
    <div className="grid" style={{ marginBottom: '2rem' }}>
      <div className="card">
        <h3 style={{ color: '#667eea', marginBottom: '0.5rem' }}>Total Orders</h3>
        <div style={{ fontSize: '2.5rem', fontWeight: '700', color: '#333' }}>
          {stats.total_orders}
        </div>
      </div>
      <div className="card">
        <h3 style={{ color: '#667eea', marginBottom: '0.5rem' }}>Total Value</h3>
        <div style={{ fontSize: '2.5rem', fontWeight: '700', color: '#333' }}>
          ${stats.total_value.toFixed(2)}
        </div>
      </div>
      <div className="card">
        <h3 style={{ color: '#667eea', marginBottom: '0.5rem' }}>Average Order</h3>
        <div style={{ fontSize: '2.5rem', fontWeight: '700', color: '#333' }}>
          ${stats.average_order_value.toFixed(2)}
        </div>
      </div>
    </div>
  )
}

