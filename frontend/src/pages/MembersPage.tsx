import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search, ChevronLeft, ChevronRight } from 'lucide-react'
import { membersApi } from '../services/api'
import { Member } from '../types'
import PageHeader from '../components/PageHeader'
import StatusBadge from '../components/StatusBadge'

export default function MembersPage() {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['members', page],
    queryFn: () => membersApi.listAll(page).then(r => r.data),
  })

  const members: Member[] = data?.data ?? []
  const pagination = data?.pagination ?? { total: 0, page: 1, per_page: 20, total_pages: 1 }

  const filtered = search
    ? members.filter(m =>
        `${m.first_name} ${m.last_name}`.toLowerCase().includes(search.toLowerCase()) ||
        m.email?.toLowerCase().includes(search.toLowerCase()) ||
        m.relationship.toLowerCase().includes(search.toLowerCase())
      )
    : members

  return (
    <div className="p-6">
      <PageHeader
        title="Members"
        subtitle={`${pagination.total} members across all applications`}
      />

      {/* Search */}
      <div className="mb-4">
        <div className="relative max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search by name, email, or relationship…"
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Name</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Relationship</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Date of Birth</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Gender</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Contact</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {isLoading ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-400">Loading…</td>
              </tr>
            ) : filtered.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-400">No members found</td>
              </tr>
            ) : filtered.map(member => (
              <tr key={member.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-4 py-3">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center text-xs font-bold text-primary-700">
                      {member.first_name[0]}{member.last_name[0]}
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{member.first_name} {member.last_name}</p>
                      {member.national_id && (
                        <p className="text-xs text-gray-400">ID: {member.national_id}</p>
                      )}
                    </div>
                  </div>
                </td>
                <td className="px-4 py-3 capitalize text-gray-700">{member.relationship}</td>
                <td className="px-4 py-3 text-gray-600">
                  {new Date(member.date_of_birth).toLocaleDateString()}
                </td>
                <td className="px-4 py-3 capitalize text-gray-600">{member.gender}</td>
                <td className="px-4 py-3">
                  <div className="text-xs">
                    {member.email && <p className="text-gray-700">{member.email}</p>}
                    {member.phone && <p className="text-gray-400">{member.phone}</p>}
                    {!member.email && !member.phone && <span className="text-gray-300">—</span>}
                  </div>
                </td>
                <td className="px-4 py-3">
                  <StatusBadge status={member.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* Pagination */}
        {pagination.total_pages > 1 && (
          <div className="px-4 py-3 border-t border-gray-200 flex items-center justify-between text-sm text-gray-600">
            <span>Page {pagination.page} of {pagination.total_pages} · {pagination.total} total</span>
            <div className="flex gap-2">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={pagination.page === 1}
                className="p-1 rounded hover:bg-gray-100 disabled:opacity-40"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                onClick={() => setPage(p => Math.min(pagination.total_pages, p + 1))}
                disabled={pagination.page === pagination.total_pages}
                className="p-1 rounded hover:bg-gray-100 disabled:opacity-40"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
