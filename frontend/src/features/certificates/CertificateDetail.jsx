import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Award, ChevronRight, ArrowLeft, CheckCircle, XCircle, Clock, AlertTriangle, Eye, Building2, User, Package, Hash, MapPin, Printer, Download, QrCode } from 'lucide-react'
import QRCode from 'qrcode.react'
import api from '../../lib/api'
import { formatDate, formatDateTime, getStatusBadge, getStatusLabel } from '../../lib/utils'
import { useAuth } from '../../lib/auth'
import { cn } from '../../lib/utils'

export default function CertificateDetail() {
  const { id } = useParams()
  const { user, canIssueCertificate, isOwner, isLMO, isAdmin, isRegulator } = useAuth()
  const [certificate, setCertificate] = useState(null)
  const [loading, setLoading] = useState(true)
  const [qrUrl, setQrUrl] = useState('')

  useEffect(() => {
    fetchCertificate()
  }, [id])

  const fetchCertificate = async () => {
    setLoading(true)
    try {
      const response = await api.get(`/certificates/${id}`)
      setCertificate(response.data)
      const baseUrl = window.location.origin
      setQrUrl(`${baseUrl}/verify/${response.data.verification_token}`)
    } catch (error) {
      console.error('Failed to fetch certificate', error)
    } finally {
      setLoading(false)
    }
  }

  const handleRevoke = async () => {
    const reason = prompt('Enter revocation reason:')
    if (!reason) return

    try {
      await api.post(`/certificates/${id}/revoke`, { reason })
      fetchCertificate()
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to revoke certificate')
    }
  }

  const handleSupersede = async () => {
    const newCertId = prompt('Enter new certificate ID to supersede this one:')
    const reason = prompt('Enter supersession reason:')
    if (!newCertId || !reason) return

    try {
      await api.post(`/certificates/${id}/supersede`, { new_certificate_id: parseInt(newCertId), reason })
      fetchCertificate()
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to supersede certificate')
    }
  }

  const printCertificate = () => {
    window.print()
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <svg className="animate-spin h-8 w-8 text-primary-600" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      </div>
    )
  }

  if (!certificate) {
    return (
      <div className="text-center py-12">
        <Award className="h-12 w-12 text-gray-300 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900">Certificate not found</h3>
        <Link to="/certificates" className="btn-primary mt-4 inline-flex">Back to Certificates</Link>
      </div>
    )
  }

  const canRevoke = canIssueCertificate && certificate.status === 'valid'
  const canSupersede = canIssueCertificate && certificate.status === 'valid'
  const isExpired = new Date(certificate.valid_until) < new Date() && certificate.status === 'valid'

  const statusColors = {
    valid: 'bg-green-100 text-green-800',
    expired: 'bg-red-100 text-red-800',
    revoked: 'bg-red-100 text-red-800',
    superseded: 'bg-purple-100 text-purple-800',
  }

  const statusIcons = {
    valid: CheckCircle,
    expired: Clock,
    revoked: XCircle,
    superseded: AlertTriangle,
  }

  const StatusIcon = statusIcons[certificate.status] || Award

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <button onClick={() => window.history.back()} className="btn-ghost p-2 mr-4">
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Certificate {certificate.certificate_number}</h1>
            <p className="text-gray-600">
              {certificate.instrument?.manufacturer} {certificate.instrument?.model}
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <button onClick={printCertificate} className="btn-secondary">
            <Printer className="h-4 w-4 mr-2" />
            Print
          </button>
          <button onClick={() => downloadCertificate()} className="btn-secondary">
            <Download className="h-4 w-4 mr-2" />
            Download
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="card p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-gray-900">Certificate Status</h2>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${statusColors[certificate.status] || 'bg-gray-100 text-gray-800'}`}>
                <StatusIcon className="inline h-4 w-4 mr-1" />
                {getStatusLabel(certificate.status)}
              </span>
            </div>

            {certificate.status === 'revoked' && certificate.revocation_reason && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg mb-6">
                <div className="flex items-start">
                  <XCircle className="h-5 w-5 text-red-600 mr-3 flex-shrink-0" />
                  <div>
                    <h4 className="font-medium text-red-900">Revoked</h4>
                    <p className="text-sm text-red-700 mt-1">{certificate.revocation_reason}</p>
                    <p className="text-xs text-red-500 mt-1">Revoked on {formatDateTime(certificate.revoked_at)}</p>
                  </div>
                </div>
              </div>
            )}

            {certificate.status === 'superseded' && certificate.superseded_by_id && (
              <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg mb-6">
                <div className="flex items-start">
                  <AlertTriangle className="h-5 w-5 text-purple-600 mr-3 flex-shrink-0" />
                  <div>
                    <h4 className="font-medium text-purple-900">Superseded</h4>
                    <p className="text-sm text-purple-700 mt-1">This certificate has been replaced by certificate ID: {certificate.superseded_by_id}</p>
                  </div>
                </div>
              </div>
            )}

            <dl className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <div className="sm:col-span-2">
                <dt className="text-sm text-gray-500">Certificate Number</dt>
                <dd className="font-mono text-lg text-gray-900 mt-1">{certificate.certificate_number}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Verification Token</dt>
                <dd className="font-mono text-sm text-gray-900 mt-1">{certificate.verification_token}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Issue Date</dt>
                <dd className="mt-1 text-gray-900">{formatDateTime(certificate.issue_date)}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Valid From</dt>
                <dd className="mt-1 text-gray-900">{formatDate(certificate.valid_from)}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Valid Until</dt>
                <dd className="mt-1 text-gray-900">{formatDate(certificate.valid_until)}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Status</dt>
                <dd className="mt-1">
                  <span className={`badge ${getStatusBadge(certificate.status)}`}>{getStatusLabel(certificate.status)}</span>
                </dd>
              </div>
              <div className="sm:col-span-2">
                <dt className="text-sm text-gray-500">Instrument</dt>
                <dd className="mt-1">
                  <Link to={`/instruments/${certificate.instrument?.id}`} className="text-gray-900 hover:text-primary-600">
                    {certificate.instrument?.manufacturer} {certificate.instrument?.model}
                  </Link>
                  <p className="text-sm text-gray-500">
                    Category: {certificate.instrument?.category?.replace?.('_', ' ')} • Serial: {certificate.instrument?.serial_number}
                  </p>
                </dd>
              </div>
              <div className="sm:col-span-2">
                <dt className="text-sm text-gray-500">Issuing Authority</dt>
                <dd className="mt-1 flex items-center">
                  <Building2 className="h-4 w-4 mr-1 text-gray-400" />
                  {certificate.issuer?.organization || 'Legal Metrology Department'}
                </dd>
              </div>
              <div className="sm:col-span-2">
                <dt className="text-sm text-gray-500">Issued By</dt>
                <dd className="mt-1 flex items-center">
                  <User className="h-4 w-4 mr-1 text-gray-400" />
                  {certificate.issuer?.full_name} ({certificate.issuer?.email})
                </dd>
              </div>
              <div className="sm:col-span-2">
                <dt className="text-sm text-gray-500">Linked Application</dt>
                <dd className="mt-1">
                  <Link to={`/applications/${certificate.application_id}`} className="text-primary-600 hover:text-primary-700">
                    Application #{certificate.application_id}
                  </Link>
                </dd>
              </div>
            </dl>
          </div>

          {(canRevoke || canSupersede) && (
            <div className="card p-6 border-yellow-200 bg-yellow-50">
              <h3 className="font-medium text-gray-900 mb-4">Certificate Actions (Authorized Issuer Only)</h3>
              <div className="flex flex-wrap gap-3">
                {canRevoke && (
                  <button onClick={handleRevoke} className="btn-danger">
                    <XCircle className="h-4 w-4 mr-2" />
                    Revoke Certificate
                  </button>
                )}
                {canSupersede && (
                  <button onClick={handleSupersede} className="btn-secondary border-purple-500 text-purple-700 hover:bg-purple-50">
                    <AlertTriangle className="h-4 w-4 mr-2" />
                    Supersede Certificate
                  </button>
                )}
              </div>
            </div>
          )}

          <div className="card p-6 bg-gray-50 border-yellow-200">
            <div className="flex items-start">
              <AlertTriangle className="h-5 w-5 text-yellow-600 mr-3 flex-shrink-0" />
              <div>
                <h3 className="font-medium text-gray-900">Prototype Certificate</h3>
                <p className="text-sm text-gray-600 mt-1">
                  This is a prototype certificate for PS-26036 demonstration purposes only.
                  It is not an official legal metrology certificate and has no legal validity.
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="card p-6 text-center">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">QR Code for Public Verification</h2>
            <div className="inline-block p-4 bg-white rounded-lg border border-gray-200">
              <QRCode value={qrUrl} size={128} level="M" />
            </div>
            <p className="mt-4 text-sm text-gray-500">Scan to verify on public portal</p>
            <p className="mt-2 text-xs text-gray-400 font-mono">{qrUrl}</p>
            <div className="mt-4 pt-4 border-t border-gray-200">
              <Link to={`/verify/${certificate.verification_token}`} target="_blank" className="btn-secondary inline-flex">
                <Eye className="h-4 w-4 mr-2" />
                Test Verification
              </Link>
            </div>
          </div>

          <div className="card p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Certificate Preview (Print Layout)</h2>
            <div className="border-2 border-gray-300 rounded-lg p-8 bg-white" id="certificate-preview">
              <div className="text-center mb-6">
                <div className="inline-flex items-center justify-center h-16 w-16 rounded-full bg-primary-600 mb-4">
                  <Award className="h-8 w-8 text-white" />
                </div>
                <h3 className="text-2xl font-bold text-gray-900">VERIFICATION CERTIFICATE</h3>
                <p className="text-gray-600 mt-1">Legal Metrology Department (Prototype)</p>
              </div>

              <div className="grid grid-cols-2 gap-4 mb-6 text-sm">
                <div><span className="text-gray-500">Certificate No:</span> <span className="font-mono font-medium ml-2">{certificate.certificate_number}</span></div>
                <div><span className="text-gray-500">Verification Token:</span> <span className="font-mono font-medium ml-2">{certificate.verification_token}</span></div>
                <div><span className="text-gray-500">Issue Date:</span> <span className="ml-2">{formatDate(certificate.issue_date)}</span></div>
                <div><span className="text-gray-500">Valid Until:</span> <span className="ml-2">{formatDate(certificate.valid_until)}</span></div>
                <div className="col-span-2"><span className="text-gray-500">Instrument:</span> <span className="ml-2">{certificate.instrument?.manufacturer} {certificate.instrument?.model}</span></div>
                <div className="col-span-2"><span className="text-gray-500">Serial Number:</span> <span className="font-mono font-medium ml-2">{certificate.instrument?.serial_number}</span></div>
                <div className="col-span-2"><span className="text-gray-500">Category:</span> <span className="ml-2">{certificate.instrument?.category?.replace?.('_', ' ')}</span></div>
                <div className="col-span-2"><span className="text-gray-500">Issued By:</span> <span className="ml-2">{certificate.issuer?.full_name}</span></div>
                <div className="col-span-2"><span className="text-gray-500">Office:</span> <span className="ml-2">{certificate.issuer?.organization}</span></div>
              </div>

              <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                <div className="text-center">
                  <QRCode value={qrUrl} size={64} level="M" />
                  <p className="text-xs text-gray-500 mt-1">Scan to verify</p>
                </div>
                <div className="text-right">
                  <p className="font-medium text-gray-900">Authorized Signature</p>
                  <p className="text-sm text-gray-500">{certificate.issuer?.full_name}</p>
                  <p className="text-xs text-gray-400">Legal Metrology Officer</p>
                </div>
              </div>

              <div className="mt-4 text-center text-xs text-gray-500">
                <p>PROTOTYPE — NOT AN OFFICIAL LEGAL METROLOGY CERTIFICATE</p>
                <p>PS-26036 / SIH26036 Demonstration System</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )

  function downloadCertificate() {
    const element = document.getElementById('certificate-preview')
    if (!element) return

    const printWindow = window.open('', '_blank')
    printWindow.document.write(`
      <html>
        <head>
          <title>Certificate ${certificate.certificate_number}</title>
          <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 20px; }
            @media print { .no-print { display: none; } }
          </style>
        </head>
        <body>${element.innerHTML}</body>
      </html>
    `)
    printWindow.document.close()
    printWindow.focus()
    setTimeout(() => printWindow.print(), 500)
  }
}