import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import PageHeader from '../src/components/PageHeader'

describe('PageHeader', () => {
  it('renders the title', () => {
    render(<PageHeader title="Applications" />)
    expect(screen.getByRole('heading', { name: 'Applications' })).toBeInTheDocument()
  })

  it('renders subtitle when provided', () => {
    render(<PageHeader title="Applications" subtitle="12 total" />)
    expect(screen.getByText('12 total')).toBeInTheDocument()
  })

  it('does not render subtitle when omitted', () => {
    render(<PageHeader title="Applications" />)
    expect(screen.queryByText('12 total')).not.toBeInTheDocument()
  })

  it('renders action content', () => {
    render(<PageHeader title="Applications" action={<button>New Application</button>} />)
    expect(screen.getByRole('button', { name: 'New Application' })).toBeInTheDocument()
  })

  it('does not render action slot when omitted', () => {
    const { container } = render(<PageHeader title="Applications" />)
    expect(container.querySelectorAll('button')).toHaveLength(0)
  })
})
