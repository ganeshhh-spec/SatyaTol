import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Plus, Search, Filter, X, Scale, ChevronRight } from 'lucide-react'
import api from '../../lib/api'
import { formatDate, getStatusBadge, getStatusLabel } from '../../lib/utils'

export default function InstrumentList() {
  const [instruments, setInstruments] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(10)
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('')
  const [status, setStatus] = useState('')
  const [showFilters, setShowFilters] = useState(false)

  const categories = [
    'weighing_non_automatic',
    'weighing_automatic',
    'measuring_length',
    'measuring_volume',
    'measuring_flow',
    'other',
  ]

  const statuses = ['registered', 'under_verification', 'verified', 'expired', 'rejected']

  useEffect(() => {
    fetchInstruments()
  }, [page, search, category, status])

  const fetchInstruments = async () => {
    setLoading(true)
    try {
      const params = { page, page_size: pageSize }
      if (search) params.search = search
      if (category) params.category = category
      if (status) params.status = status
      const response = await api.get('/instruments', { params })
      setInstruments(response.data.items)
      setTotal(response.data.total)
    } catch (error) {
      console.error('Failed to fetch instruments', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = (e) => {
    e.preventDefault()
    setPage(1)
  }

  const clearFilters = () => {
    setSearch('')
    setCategory('')
    setStatus('')
    setPage(1)
  }

  const hasFilters = search || category || status

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">My Instruments</h1>
          <p className="text-gray-600">Manage your registered weighing and measuring instruments</p>
        </div>
        <Link to="/instruments/new" className="btn-primary">
          <Plus className="h-4 w-4 mr-2" />
          Register Instrument
        </Link>
      </div>

      <div className="card">
        <form onSubmit={handleSearch} className="p-4 border-b border-gray-200">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search by serial, manufacturer, model..."
                className="input pl-10"
              />
            </div>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="input w-full sm:w-48"
            >
              <option value="">All Categories</option>
              {categories.map((c) => (
                <option key={c} value={c}>{c.replace(/_/g, ' ')}</option>
              ))}
            </select>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="input w-full sm:w-40"
            >
              <option value="">All Statuses</option>
              {statuses.map((s) => (
                <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>
              ))}
            </select>
            {hasFilters && (
              <button type="button" onClick={clearFilters} className="btn-secondary">
                <X className="h-4 w-4 mr-1" />
                Clear
              </button>
            )}
          </div>
        </form>

        {loading ? (
          <div className="p-8 text-center">
            <svg className="animate-spin h-8 w-8 text-primary-600 mx-auto" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          </div>
        ) : instruments.length === 0 ? (
          <div className="p-8 text-center">
            <Scale className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-1">No instruments found</h3>
            <p className="text-gray-500 mb-4">Register your first instrument to get started</p>
            <Link to="/instruments/new" className="btn-primary inline-flex">
              <Plus className="h-4 w-4 mr-2" />
              Register Instrument
            </Link>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Instrument</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Category</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Serial Number</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Registered</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {instruments.map((instrument) => (
                    <tr key={instrument.id} className="hover:bg-gray-50">
                      <td className="px-4 py-4">
                        <Link to={`/instruments/${instrument.id}`} className="font-medium text-gray-900 hover:text-primary-600">
                          {instrument.manufacturer} {instrument.model}
                        </Link>
                        <p className="text-sm text-gray-500">{instrument.instrument_type}</p>
                      </td>
                      <td className="px-4 py-4">
                        <span className="badge badge-gray">{instrument.category.replace(/_/g, ' ')}</span>
                      </td>
                      <td className="px-4 py-4 font-mono text-sm text-gray-900">{instrument.serial_number}</td>
                      <td className="px-4 py-4">
                        <span className={`badge ${getStatusBadge(instrument.status)}`}>{getStatusLabel(instrument.status)}</span>
                      </td>
                      <td className="px-4 py-4 text-sm text-gray-500">{formatDate(instrument.registration_date)}</td>
                      <td className="px-4 py-4 text-right">
                        <Link to={`/instruments/${instrument.id}`} className="text-primary-600 hover:text-primary-700 text-sm font-medium flex items-center justify-end">
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