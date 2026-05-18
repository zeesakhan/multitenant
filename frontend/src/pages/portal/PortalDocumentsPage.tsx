import { useQuery } from '@tanstack/react-query'
import { FolderOpen, FileText, Download } from 'lucide-react'
import { portalCustomerApi } from '../../services/portalApi'

const DOC_TYPE_LABELS: Record<string, string> = {
  POLICY_DOCUMENT: 'Policy Document',
  QUOTE_DOCUMENT: 'Quote',
  APPLICATION_FORM: 'Application Form',
  INVOICE: 'Invoice',
  ENDORSEMENT: 'Endorsement',
  RENEWAL_NOTICE: 'Renewal Notice',
  CLAIMS_FORM: 'Claims Form',
  MEDICAL_REPORT: 'Medical Report',
  ID_PROOF: 'ID Proof',
  ADDRESS_PROOF: 'Address Proof',
  INCOME_PROOF: 'Income Proof',
}

const DOC_TYPE_COLORS: Record<string, string> = {
  POLICY_DOCUMENT: 'bg-emerald-100 text-emerald-700',
  INVOICE: 'bg-blue-100 text-blue-700',
  CLAIMS_FORM: 'bg-amber-100 text-amber-700',
  ENDORSEMENT: 'bg-violet-100 text-violet-700',
  RENEWAL_NOTICE: 'bg-orange-100 text-orange-700',
}

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function fileIcon(mime: string) {
  if (mime.includes('pdf')) return '📄'
  if (mime.includes('image')) return '🖼️'
  if (mime.includes('word') || mime.includes('doc')) return '📝'
  return '📁'
}

export default function PortalDocumentsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['portal-documents'],
    queryFn: portalCustomerApi.getDocuments,
    retry: false,
  })

  const documents: Record<string, unknown>[] = data?.data?.data ?? []

  // Group by document type
  const grouped = documents.reduce<Record<string, Record<string, unknown>[]>>((acc, doc) => {
    const type = String(doc.document_type ?? 'OTHER')
    if (!acc[type]) acc[type] = []
    acc[type].push(doc)
    return acc
  }, {})

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Documents</h1>
        <p className="text-gray-500 text-sm mt-1">{documents.length} document{documents.length !== 1 ? 's' : ''} available.</p>
      </div>

      {isLoading && <p className="text-sm text-gray-400">Loading documents…</p>}

      {!isLoading && documents.length === 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
          <FolderOpen className="w-10 h-10 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500 text-sm">No documents available yet.</p>
          <p className="text-xs text-gray-400 mt-1">Documents will appear here once your insurer uploads them.</p>
        </div>
      )}

      {Object.entries(grouped).map(([type, docs]) => (
        <div key={type} className="mb-6">
          <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
            {DOC_TYPE_LABELS[type] ?? type}
          </h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
            {docs.map((doc) => (
              <div key={String(doc.id)} className="bg-white rounded-xl border border-gray-200 p-4 flex items-center gap-4 hover:border-emerald-300 transition-colors">
                <div className="text-2xl flex-shrink-0">{fileIcon(String(doc.mime_type ?? ''))}</div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">{String(doc.file_name)}</p>
                  <div className="flex items-center gap-3 mt-1">
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${DOC_TYPE_COLORS[type] ?? 'bg-gray-100 text-gray-600'}`}>
                      {DOC_TYPE_LABELS[type] ?? type}
                    </span>
                    <span className="text-xs text-gray-400">{doc.file_size ? formatSize(Number(doc.file_size)) : '—'}</span>
                    <span className="text-xs text-gray-400">
                      {doc.created_at ? new Date(String(doc.created_at)).toLocaleDateString() : ''}
                    </span>
                  </div>
                </div>
                <div className="flex-shrink-0">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    doc.validation_status === 'valid' ? 'bg-green-100 text-green-700' :
                    doc.validation_status === 'invalid' ? 'bg-red-100 text-red-700' :
                    'bg-gray-100 text-gray-500'
                  }`}>{String(doc.validation_status ?? 'pending')}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}

      {!isLoading && documents.length > 0 && (
        <div className="mt-4 p-4 bg-amber-50 border border-amber-200 rounded-xl text-sm text-amber-800">
          <strong>Note:</strong> To download a document, contact your insurance provider or log into their main portal with your agent's assistance.
        </div>
      )}
    </div>
  )
}
