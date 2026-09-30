import { useState, useEffect } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import { Search, CheckCircle, XCircle, AlertTriangle, Info, Clock, Award, Building2, Package, Hash } from 'lucide-react'
import api from '../../lib/api'
import { formatDate, formatDateTime, getStatusBadge, getStatusLabel } from '../../lib/utils'

export default function PublicVerify() {
  const { token } = useParams()
  const [searchParams] = useSearchParams()
  const certificateId = searchParams.get('certificate_id')
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [searched, setSearched] = useState(false)
  const [inputValue, setInputValue] = useState(certificateId || '')

  useEffect(() => {
    if (token) {
      verifyCertificate(token)
    }
  }, [token])

  const verifyCertificate = async (identifier) => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.get(`/certificates/public/verify/${identifier}`)
      setData({ ...response.data, verified_at: new Date().toISOString() })
      setSearched(true)
    } catch (err) {
      if (err.response?.status === 404) {
        setData(null)
        setError('Certificate not found')
      } else {
        setError('Verification failed. Please try again.')
      }
      setSearched(true)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = (e) => {
    e.preventDefault()
    if (inputValue.trim()) {
      verifyCertificate(inputValue.trim())
    }
  }

  const statusIcons = {
    valid: CheckCircle,
    expired: Clock,
    revoked: XCircle,
    superseded: AlertTriangle,
    not_found: XCircle,
  }

  const statusColors = {
    valid: 'text-green-600 bg-green-100',
    expired: 'text-red-600 bg-red-100',
    revoked: 'text-red-600 bg-red-100',
    superseded: 'text-purple-600 bg-purple-100',
    not_found: 'text-gray-600 bg-gray-100',
  }

  const StatusIcon = data ? statusIcons[data.status] : Search

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <div className="inline-flex items-center justify-center h-10 w-10 rounded-xl bg-primary-600">
                <Award className="h-6 w-6 text-white" />
              </div>
              <span className="ml-2 text-xl font-bold text-gray-900">Legal Metrology</span>
            </div>
            <a href="/" className="text-gray-600 hover:text-gray-900 font-medium">Home</a>
          </div>
        </div>
      </header>

      <main className="py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mx-auto">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900">Certificate Verification</h1>
            <p className="mt-2 text-gray-600">
              Scan a QR code or enter a Certificate ID to verify the current status
            </p>
          </div>

          <form onSubmit={handleSearch} className="card p-6 mb-8">
            <div className="flex gap-2">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="Enter Certificate ID or scan QR code"
                className="input flex-1"
                disabled={loading}
                autoFocus={!token && !certificateId}
              />
              <button
                type="submit"
                disabled={loading || !inputValue.trim()}
                className="btn-primary px-6"
              >
                {loading ? (
                  <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                ) : (
                  <Search className="h-5 w-5" />
                )}
              </button>
            </div>
            <p className="mt-3 text-sm text-gray-500 text-center">
              Or <a href="/verify" className="text-primary-600 hover:underline">scan a QR code</a> with your camera
            </p>
          </form>

          {searched && (
            <div className="card overflow-hidden">
              {error && !data ? (
                <div className="p-8 text-center">
                  <XCircle className="h-16 w-16 text-red-400 mx-auto mb-4" />
                  <h2 className="text-xl font-semibold text-gray-900 mb-2">Certificate Not Found</h2>
                  <p className="text-gray-600">No certificate matches the provided ID or token.</p>
                  <p className="text-sm text-gray-500 mt-2">Please check the ID and try again.</p>
                </div>
              ) : data && (
                <>
                  <div className={`px-6 py-4 border-b border-gray-200 ${statusColors[data.status] || 'bg-gray-100'}`}>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center">
                        <StatusIcon className={`h-8 w-8 ${statusColors[data.status]?.replace('bg-', 'text-') || 'text-gray-600'}`} />
                        <div className="ml-3">
                          <h2 className="text-lg font-semibold text-gray-900">
                            Status: {getStatusLabel(data.status)}
                          </h2>
                          <p className="text-sm text-gray-600">
                            Verified at {formatDateTime(data.verified_at)}
                          </p>
                        </div>
                      </div>
                      <span className={`badge ${getStatusBadge(data.status)}`}>
                        {getStatusLabel(data.status)}
                      </span>
                    </div>
                  </div>

                  <div className="p-6 space-y-6">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div>
                        <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Certificate ID</label>
                        <p className="text-sm font-mono text-gray-900 mt-1">{data.certificate_number}</p>
                      </div>
                      <div>
                        <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Instrument Category</label>
                        <p className="text-sm text-gray-900 mt-1">{data.instrument_category}</p>
                      </div>
                      <div>
                        <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Manufacturer</label>
                        <p className="text-sm text-gray-900 mt-1">{data.manufacturer}</p>
                      </div>
                      <div>
                        <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Model</label>
                        <p className="text-sm text-gray-900 mt-1">{data.model}</p>
                      </div>
                      <div>
                        <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Serial Number (Masked)</label>
                        <p className="text-sm font-mono text-gray-900 mt-1">{data.serial_number_masked}</p>
                      </div>
                      <div>
                        <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Issue Date</label>
                        <p className="text-sm text-gray-900 mt-1">{formatDate(data.issue_date)}</p>
                      </div>
                      <div>
                        <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Valid From</label>
                        <p className="text-sm text-gray-900 mt-1">{formatDate(data.valid_from)}</p>
                      </div>
                      <div>
                        <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Valid Until</label>
                        <p className="text-sm text-gray-900 mt-1">{formatDate(data.valid_until)}</p>
                      </div>
                      <div>
                        <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Issuing Authority</label>
                        <p className="text-sm text-gray-900 mt-1">{data.issuing_authority}</p>
                      </div>
                      <div>
                        <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Issuing Office</label>
                        <p className="text-sm text-gray-900 mt-1">{data.issuing_office}</p>
                      </div>
                    </div>

                    {data.status === 'revoked' && data.revocation_reason && (
                      <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                        <div className="flex items-start">
                          <AlertTriangle className="h-5 w-5 text-red-600 mr-3 flex-shrink-0" />
                          <div>
                            <h4 className="font-medium text-red-900">Revoked</h4>
                            <p className="text-sm text-red-700 mt-1">{data.revocation_reason}</p>
                          </div>
                        </div>
                      </div>
                    )}

                    {data.status === 'superseded' && (
                      <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg">
                        <div className="flex items-start">
                          <Info className="h-5 w-5 text-purple-600 mr-3 flex-shrink-0" />
                          <div>
                            <h4 className="font-medium text-purple-900">Superseded</h4>
                            <p className="text-sm text-purple-700 mt-1">This certificate has been replaced by a newer certificate.</p>
                          </div>
                        </div>
                      </div>
                    )}

                    <div className="pt-4 border-t border-gray-200">
                      <p className="text-xs text-gray-500 text-center">
                        {data.is_prototype && (
                          <span className="inline-flex items-center px-2 py-1 rounded-full bg-yellow-100 text-yellow-800 text-xs font-medium mr-2">
                            Prototype / Demo — Not an official legal metrology certificate
                          </span>
                        )}
                        This verification reflects the current server-side status.
                        Owner contact details and private documents are not displayed.
                      </p>
                    </div>
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      </main>

      <footer className="bg-gray-900 text-gray-400 py-8 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-sm">
          <p>Legal Metrology Online Verification System — Prototype for PS-26036 / SIH26036</p>
          <p className="text-xs mt-1">This is a prototype demonstration. Not an official government service.</p>
        </div>
      </footer>
    </div>
  )
}