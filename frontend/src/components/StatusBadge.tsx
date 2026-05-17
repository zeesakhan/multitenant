import clsx from 'clsx'

const map: Record<string, string> = {
  active: 'badge-green',
  ACTIVE: 'badge-green',
  inactive: 'badge-gray',
  INACTIVE: 'badge-gray',
  suspended: 'badge-red',
  SUSPENDED: 'badge-red',
  pending: 'badge-yellow',
  PENDING: 'badge-yellow',
  approved: 'badge-green',
  APPROVED: 'badge-green',
  rejected: 'badge-red',
  REJECTED: 'badge-red',
  submitted: 'badge-blue',
  SUBMITTED: 'badge-blue',
  draft: 'badge-gray',
  DRAFT: 'badge-gray',
}

export default function StatusBadge({ status }: { status: string }) {
  return (
    <span className={clsx(map[status] ?? 'badge-gray')}>
      {status?.toLowerCase()}
    </span>
  )
}
