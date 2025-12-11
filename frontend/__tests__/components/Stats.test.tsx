import { render, screen } from '@testing-library/react'
import Stats from '../../app/components/Stats'

describe('Stats Component', () => {
  it('renders nothing when stats is null', () => {
    const { container } = render(<Stats stats={null} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders stats correctly', () => {
    const mockStats = {
      total_orders: 10,
      total_value: 50000.50,
      average_order_value: 5000.05
    }

    render(<Stats stats={mockStats} />)

    expect(screen.getByText('Total Orders')).toBeInTheDocument()
    expect(screen.getByText('10')).toBeInTheDocument()
    expect(screen.getByText('Total Value')).toBeInTheDocument()
    expect(screen.getByText('$50000.50')).toBeInTheDocument()
    expect(screen.getByText('Average Order')).toBeInTheDocument()
    expect(screen.getByText('$5000.05')).toBeInTheDocument()
  })

  it('formats currency values correctly', () => {
    const mockStats = {
      total_orders: 1,
      total_value: 1234.56,
      average_order_value: 1234.56
    }

    render(<Stats stats={mockStats} />)

    // Both total_value and average_order_value show $1234.56
    const values = screen.getAllByText('$1234.56')
    expect(values.length).toBeGreaterThanOrEqual(1)
  })

  it('handles zero values', () => {
    const mockStats = {
      total_orders: 0,
      total_value: 0,
      average_order_value: 0
    }

    render(<Stats stats={mockStats} />)

    expect(screen.getByText('0')).toBeInTheDocument()
    // Both total_value and average_order_value show $0.00
    const zeroValues = screen.getAllByText('$0.00')
    expect(zeroValues.length).toBeGreaterThanOrEqual(1)
  })
})

