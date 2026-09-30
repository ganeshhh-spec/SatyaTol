import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Search, ChevronRight, Filter, X, CheckCircle, XCircle, AlertTriangle } from 'lucide-react'
import api from '../../lib/api'
import { formatDateTime, getStatusBadge, getStatusLabel } from '../../lib/utils'
import { useAuth } from '../../lib/auth'

export default function InspectionList() {
  const { user, isLMO, isGATC, isRegulator, isAdmin } = useAuth()
  const [inspections, setInspections] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(10)
  const [result, setResult] = useState('')

  const results = ['pass', 'fail', 'needs_follow_up']

  useEffect(() => {
    fetchInspections()
  }, [page, result])

  const fetchInspections = async () => {
    setLoading(true)
    try {
      const params = { page, page_size: pageSize }
      if (result) params.result = result
      const response = await api.get('/inspections', { params })
      setInspections(response.data.items)
      setTotal(response.data.total)
    } catch (error) {
      console.error('Failed to fetch inspections', error)
    } finally {
      setLoading(false)
    }
  }

  const clearFilters = () => {
    setResult('')
    setPage(1)
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Inspections</h1>
          <p className="text-gray-600">View and manage inspection records</p>
        </div>
        <Link to="/inspections/new" className="btn-primary">
          <Search className="h-4 w-4 mr-2" />
          New Inspection
        </Link>
      </div>

      <div className="card">
        <div className="p-4 border-b border-gray-200">
          <div className="flex flex-col sm:flex-row gap-4">
            <select
              value={result}
              onChange={(e) => setResult(e.target.value)}
              className="input w-full sm:w-40"
            >
              <option value="">All Results</option>
              {results.map((r) => (
                <option key={r} value={r}>{r === 'pass' ? 'Pass' : r === 'fail' ? 'Fail' : 'Needs Follow-up'}</option>
              ))}
            </select>
            {result && (
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
        ) : inspections.length === 0 ? (
          <div className="p-8 text-center">
            <Search className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-1">No inspections found</h3>
            <p className="text-gray-500 mb-4">No inspection records match your current filters</p>
            <Link to="/inspections/new" className="btn-primary inline-flex">
              <Search className="h-4 w-4 mr-2" />
              New Inspection
            </Link>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Inspection</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Application</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Inspector</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Result</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {inspections.map((insp) => (
                    <tr key={insp.id} className="hover:bg-gray-50">
                      <td className="px-4 py-4 font-medium text-gray-900">#{insp.id}</td>
                      <td className="px-4 py-4">
                        <Link to={`/applications/${insp.application_id}`} className="text-gray-900 hover:text-primary-600">
                          Application #{insp.application_id}
                        </Link>
                      </td>
                      <td className="px-4 py-4 text-sm text-gray-500">{insp.inspector?.full_name}</td>
                      <td className="px-4 py-4 text-sm text-gray-500">{formatDateTime(insp.inspection_date)}</td>
                      <td className="px-4 py-4">
                        <span className={`badge ${getStatusBadge(insp.result)}`}>
                          {insp.result === 'pass' && <CheckCircle className="h-3 w-3 mr-1" />}
                          {insp.result === 'fail' && <XCircle className="h-3 w-3 mr-1" />}
                          {insp.result === 'needs_follow_up' && <AlertTriangle className="h-3 w-3 mr-1" />}
                          {getStatusLabel(insp.result)}
                        </span>
                      </td>
                      <td className="px-4 py-4 text-right">
                        <Link to={`/inspections/${insp.id}`} className="text-primary-600 hover:text-primary-700 text-sm font-medium flex items-center justify-end">
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