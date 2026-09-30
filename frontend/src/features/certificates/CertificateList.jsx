import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Award, ChevronRight, Filter, X, Search, Clock } from 'lucide-react'
import api from '../../lib/api'
import { formatDate, getStatusBadge, getStatusLabel } from '../../lib/utils'
import { useAuth } from '../../lib/auth'

export default function CertificateList() {
  const { user, isOwner, isLMO, isGATC, isRegulator, isAdmin, canIssueCertificate } = useAuth()
  const [certificates, setCertificates] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(10)
  const [status, setStatus] = useState('')
  const [search, setSearch] = useState('')

  const statuses = ['valid', 'expired', 'revoked', 'superseded']

  useEffect(() => {
    fetchCertificates()
  }, [page, status, search])

  const fetchCertificates = async () => {
    setLoading(true)
    try {
      const params = { page, page_size: pageSize }
      if (status) params.status = status
      if (search) params.search = search
      const response = await api.get('/certificates', { params })
      setCertificates(response.data.items)
      setTotal(response.data.total)
    } catch (error) {
      console.error('Failed to fetch certificates', error)
    } finally {
      setLoading(false)
    }
  }

  const clearFilters = () => {
    setStatus('')
    setSearch('')
    setPage(1)
  }

  const hasFilters = status || search

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Certificates</h1>
          <p className="text-gray-600">View and manage issued certificates</p>
        </div>
        {canIssueCertificate && (
          <span className="text-sm text-gray-500">Use application detail page to issue certificates</span>
        )}
      </div>

      <div className="card">
        <div className="p-4 border-b border-gray-200">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search by certificate number..."
                className="input pl-10"
              />
            </div>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="input w-full sm:w-40"
            >
              <option value="">All Statuses</option>
              {statuses.map((s) => (
                <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
              ))}
            </select>
            {hasFilters && (
              <button type="button" onClick={clearFilters} className="btn-secondary">
                <X className="h-4 w-4 mr-1" />
                Clear
              </button>
            )}
          </div>
        </div>

        {loading ? (
          <div className="p-8 text-center">
            <svg className="animate-spin h-8 w-8 text-primary-600 mx-auto" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          </div>
        ) : certificates.length === 0 ? (
          <div className="p-8 text-center">
            <Award className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-1">No certificates found</h3>
            <p className="text-gray-500">No certificates match your current filters</p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Certificate Number</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Instrument</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Issued</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Valid Until</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Issuer</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {certificates.map((cert) => (
                    <tr key={cert.id} className="hover:bg-gray-50">
                      <td className="px-4 py-4 font-mono text-sm text-gray-900">{cert.certificate_number}</td>
                      <td className="px-4 py-4">
                        <Link to={`/instruments/${cert.instrument?.id}`} className="text-gray-900 hover:text-primary-600">
                          {cert.instrument?.manufacturer} {cert.instrument?.model}
                        </Link>
                        <p className="text-sm text-gray-500 font-mono">{cert.instrument?.serial_number}</p>
                      </td>
                      <td className="px-4 py-4 text-sm text-gray-500">{formatDate(cert.issue_date)}</td>
                      <td className="px-4 py-4 text-sm text-gray-500">
                        {formatDate(cert.valid_until)}
                        {new Date(cert.valid_until) < new Date() && cert.status === 'valid' && (
                          <Clock className="h-4 w-4 text-red-500 inline ml-1" title="Expired" />
                        )}
                      </td>
                      <td className="px-4 py-4">
                        <span className={`badge ${getStatusBadge(cert.status)}`}>{getStatusLabel(cert.status)}</span>
                      </td>
                      <td className="px-4 py-4 text-sm text-gray-500">{cert.issuer?.full_name}</td>
                      <td className="px-4 py-4 text-right">
                        <Link to={`/certificates/${cert.id}`} className="text-primary-600 hover:text-primary-700 text-sm font-medium flex items-center justify-end">
                          View <ChevronRight className="h-4 w-4 ml-1" />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {total > pageSize && (
              <div className="p-4 border-t border-gray-200 flex items-center justify-between">
                <p className="text-sm text-gray-500">
                  Showing {((page - 1) * pageSize) + 1} to {Math.min(page * pageSize, total)} of {total} results
                </p>
                <div className="flex gap-2">
                  <button
                    onClick={() => setPage(page - 1)}
                    disabled={page === 1}
                    className="btn-secondary px-3 py-1"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => setPage(page + 1)}
                    disabled={page * pageSize >= total}
                    className="btn-secondary px-3 py-1"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}