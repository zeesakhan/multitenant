import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import Modal from '../src/components/Modal'

describe('Modal', () => {
  it('renders nothing when closed', () => {
    render(<Modal open={false} onClose={() => {}} title="Test"><p>Content</p></Modal>)
    expect(screen.queryByText('Test')).not.toBeInTheDocument()
    expect(screen.queryByText('Content')).not.toBeInTheDocument()
  })

  it('renders title and children when open', () => {
    render(<Modal open={true} onClose={() => {}} title="Confirm action"><p>Are you sure?</p></Modal>)
    expect(screen.getByText('Confirm action')).toBeInTheDocument()
    expect(screen.getByText('Are you sure?')).toBeInTheDocument()
  })

  it('calls onClose when the X button is clicked', () => {
    const onClose = vi.fn()
    render(<Modal open={true} onClose={onClose} title="Confirm"><p>body</p></Modal>)
    fireEvent.click(screen.getByRole('button'))
    expect(onClose).toHaveBeenCalledOnce()
  })

  it('calls onClose when the backdrop is clicked', () => {
    const onClose = vi.fn()
    const { container } = render(
      <Modal open={true} onClose={onClose} title="Confirm"><p>body</p></Modal>
    )
    const backdrop = container.querySelector('.absolute.inset-0') as HTMLElement
    fireEvent.click(backdrop)
    expect(onClose).toHaveBeenCalledOnce()
  })

  it('calls onClose on Escape key', () => {
    const onClose = vi.fn()
    render(<Modal open={true} onClose={onClose} title="Confirm"><p>body</p></Modal>)
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(onClose).toHaveBeenCalledOnce()
  })

  it('does not call onClose on other keys', () => {
    const onClose = vi.fn()
    render(<Modal open={true} onClose={onClose} title="Confirm"><p>body</p></Modal>)
    fireEvent.keyDown(document, { key: 'Enter' })
    expect(onClose).not.toHaveBeenCalled()
  })

  it('applies xl width class when size=xl', () => {
    const { container } = render(
      <Modal open={true} onClose={() => {}} title="Big modal" size="xl"><p>big</p></Modal>
    )
    expect(container.querySelector('.max-w-4xl')).toBeInTheDocument()
  })
})
