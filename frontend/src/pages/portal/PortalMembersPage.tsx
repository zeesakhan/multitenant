import { useQuery } from '@tanstack/react-query'
import { User, Users } from 'lucide-react'
import { portalCustomerApi } from '../../services/portalApi'

const RELATIONSHIP_LABELS: Record<string, string> = {
  self: 'Primary Insured', spouse: 'Spouse', child: 'Child',
  parent: 'Parent', sibling: 'Sibling', dependent: 'Dependent',
}

const RELATIONSHIP_COLORS: Record<string, string> = {
  self: 'bg-emerald-100 text-emerald-700',
  spouse: 'bg-blue-100 text-blue-700',
  child: 'bg-violet-100 text-violet-700',
  parent: 'bg-amber-100 text-amber-700',
  sibling: 'bg-pink-100 text-pink-700',
  dependent: 'bg-gray-100 text-gray-600',
}

const GENDER_LABELS: Record<string, string> = { M: 'Male', F: 'Female', O: 'Other', U: 'Undisclosed' }

function age(dob: string) {
  const diff = Date.now() - new Date(dob).getTime()
  return Math.floor(diff / (1000 * 60 * 60 * 24 * 365.25))
}

export default function PortalMembersPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['portal-members'],
    queryFn: portalCustomerApi.getMembers,
    retry: false,
  })
  const members: Record<string, unknown>[] = data?.data?.data ?? []

  const primary = members.find((m) => m.relationship === 'self')
  const dependents = members.filter((m) => m.relationship !== 'self')

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Covered Members</h1>
        <p className="text-gray-500 text-sm mt-1">{members.length} {members.length === 1 ? 'person' : 'people'} covered under this policy.</p>
      </div>

      {isLoading && <p className="text-sm text-gray-400">Loading members…</p>}

      {!isLoading && members.length === 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-10 text-center text-gray-500">
          No members found for this policy.
        </div>
      )}

      {primary && (
        <div className="mb-6">
          <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Primary Insured</h2>
          <MemberCard member={primary} />
        </div>
      )}

      {dependents.length > 0 && (
        <div>
          <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
            Dependents ({dependents.length})
          </h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {dependents.map((m) => <MemberCard key={String(m.id)} member={m} />)}
          </div>
        </div>
      )}
    </div>
  )
}

function MemberCard({ member: m }: { member: Record<string, unknown> }) {
  const GENDER_LABELS: Record<string, string> = { M: 'Male', F: 'Female', O: 'Other', U: 'Undisclosed' }
  const rel = String(m.relationship ?? '')

  function age(dob: string) {
    const diff = Date.now() - new Date(dob).getTime()
    return Math.floor(diff / (1000 * 60 * 60 * 24 * 365.25))
  }

  const RELATIONSHIP_LABELS: Record<string, string> = {
    self: 'Primary Insured', spouse: 'Spouse', child: 'Child',
    parent: 'Parent', sibling: 'Sibling', dependent: 'Dependent',
  }
  const RELATIONSHIP_COLORS: Record<string, string> = {
    self: 'bg-emerald-100 text-emerald-700',
    spouse: 'bg-blue-100 text-blue-700',
    child: 'bg-violet-100 text-violet-700',
    parent: 'bg-amber-100 text-amber-700',
    sibling: 'bg-pink-100 text-pink-700',
    dependent: 'bg-gray-100 text-gray-600',
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 flex items-start gap-4">
      <div className={`w-11 h-11 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0 ${
        rel === 'self' ? 'bg-emerald-600 text-white' : 'bg-gray-100 text-gray-600'
      }`}>
        {String(m.first_name ?? '?')[0]}{String(m.last_name ?? '?')[0]}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <p className="font-semibold text-gray-900">{String(m.first_name)} {String(m.last_name)}</p>
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${RELATIONSHIP_COLORS[rel] ?? 'bg-gray-100 text-gray-600'}`}>
            {RELATIONSHIP_LABELS[rel] ?? rel}
          </span>
        </div>
        <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-gray-500">
          <span>DOB: {m.date_of_birth ? new Date(String(m.date_of_birth)).toLocaleDateString() : '—'}</span>
          <span>Age: {m.date_of_birth ? `${age(String(m.date_of_birth))} yrs` : '—'}</span>
          <span>Gender: {GENDER_LABELS[String(m.gender ?? '')] ?? String(m.gender ?? '—')}</span>
          <span className="capitalize">Status: {String(m.status ?? '—')}</span>
          {m.email ? <span className="col-span-2 truncate">{String(m.email)}</span> : null}
          {m.phone ? <span>{String(m.phone)}</span> : null}
        </div>
      </div>
    </div>
  )
}
