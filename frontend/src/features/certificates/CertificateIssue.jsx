import { useEffect, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { ArrowLeft, Award, Calendar, AlertTriangle, XCircle, CheckCircle } from 'lucide-react'
import api from '../../lib/api'
import { formatDate, formatDateTime, getStatusBadge, getStatusLabel } from '../../lib/utils'
import { useAuth } from '../../lib/auth'
import { cn } from '../../lib/utils'

export default function CertificateIssue() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { user, canIssueCertificate, isLMO } = useAuth()
  const [application, setApplication] = useState(null)
  const [inspection, setInspection] = useState(null)
  const [formData, setFormData] = useState({
    valid_from: '',
    valid_until: '',
  })
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    fetchData()
  }, [id])

  const fetchData = async () => {
    setLoading(true)
    try {
      const [appRes, inspRes] = await Promise.all([
        api.get(`/applications/${id}`),
        api.get(`/inspections`, { params: { application_id: id, page_size: 10 } }),
      ])
      setApplication(appRes.data)
      
      const finalizedInspections = inspRes.data.items.filter(i => i.is_finalized)
      const passingInspection = finalizedInspections.find(i => i.result === 'pass')
      setInspection(passingInspection || finalizedInspections[0] || null)

      const now = new Date()
      const oneYear = new Date(now.getFullYear() + 1, now.getMonth(), now.getDate())
      setFormData({
        valid_from: formatDateForInput(now),
        valid_until: formatDateForInput(oneYear),
      })
    } catch (error) {
      console.error('Failed to fetch data', error)
    } finally {
      setLoading(false)
    }
  }

  const formatDateForInput = (date) => {
    const d = new Date(date)
    return d.toISOString().split('T')[0]
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }))
    }
  }

  const validate = () => {
    const newErrors = {}
    if (!formData.valid_from) newErrors.valid_from = 'Valid from date is required'
    if (!formData.valid_until) newErrors.valid_until = 'Valid until date is required'
    if (formData.valid_from && formData.valid_until && new Date(formData.valid_from) >= new Date(formData.valid_until)) {
      newErrors.valid_until = 'Valid until must be after valid from'
    }
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const canIssue = canIssueCertificate && 
    application?.status === 'decision_pending' && 
    inspection?.result === 'pass' && 
    inspection?.is_finalized

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!validate()) return
    if (!canIssue) {
      setErrors({ submit: 'Certificate cannot be issued: prerequisites not met' })
      return
    }

    setSubmitting(true)
    try {
      await api.post(`/certificates/${id}/issue`, {
        valid_from: new Date(formData.valid_from).toISOString(),
        valid_until: new Date(formData.valid_until).toISOString(),
      })
      navigate(`/applications/${id}`)
    } catch (error) {
      if (error.response?.data?.detail) {
        setErrors({ submit: error.response.data.detail })
      } else {
        setErrors({ submit: 'Failed to issue certificate' })
      }
    } finally {
      setSubmitting(false)
    }
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

  if (!application) {
    return (
      <div className="text-center py-12">
        <Award className="h-12 w-12 text-gray-300 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900">Application not found</h3>
        <Link to="/applications" className="btn-primary mt-4 inline-flex">Back to Applications</Link>
      </div>
    )
  }

  const isIneligible = application.status !== 'decision_pending' ||
    !inspection ||
    inspection.result !== 'pass' ||
    !inspection.is_finalized

  const ineligibilityReasons = []
  if (application.status !== 'decision_pending') {
    ineligibilityReasons.push(`Application status is "${getStatusLabel(application.status)}", must be "Decision Pending"`)
  }
  if (!inspection) {
    ineligibilityReasons.push('No inspection recorded for this application')
  } else if (!inspection.is_finalized) {
    ineligibilityReasons.push('Inspection is not finalized')
  } else if (inspection.result !== 'pass') {
    ineligibilityReasons.push(`Inspection result is "${getStatusLabel(inspection.result)}", must be "Pass"`)
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center">
        <button onClick={() => navigate(-1)} className="btn-ghost p-2 mr-4">
          <ArrowLeft className="h-5 w-5" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Issue Certificate</h1>
          <p className="text-gray-600">Application #{application.id} - {application.instrument?.manufacturer} {application.instrument?.model}</p>
        </div>
      </div>

      <div className="card p-4 bg-gray-50 border-blue-200">
        <div className="flex items-center justify-between">
          <div>
            <p className="font-medium text-gray-900">Application #{application.id}</p>
            <p className="text-sm text-gray-500">
              {application.verification_type === 'initial' ? 'Initial' : 'Re-verification'} • 
              {application.instrument?.manufacturer} {application.instrument?.model} ({application.instrument?.serial_number})
            </p>
          </div>
          <span className={`badge ${getStatusBadge(application.status)}`}>{getStatusLabel(application.status)}</span>
        </div>
      </div>

      {inspection && (
        <div className="card p-4 bg-gray-50 border-green-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-900 flex items-center">
                Inspection #{inspection.id}
                {inspection.is_finalized ? (
                  <span className="ml-2 px-2 py-0.5 text-xs bg-green-100 text-green-800 rounded">Finalized</span>
                ) : (
                  <span className="ml-2 px-2 py-0.5 text-xs bg-yellow-100 text-yellow-800 rounded">Draft</span>
                )}
              </p>
              <p className="text-sm text-gray-500">
                By {inspection.inspector?.full_name} on {formatDateTime(inspection.inspection_date)}
              </p>
            </div>
            <span className={`badge ${getStatusBadge(inspection.result)}`}>{getStatusLabel(inspection.result)}</span>
          </div>
          {inspection.observations && <p className="text-sm text-gray-600 mt-1">{inspection.observations}</p>}
        </div>
      )}

      {!inspection && (
        <div className="card p-4 bg-yellow-50 border-yellow-200">
          <p className="text-sm text-yellow-800 flex items-center">
            <AlertTriangle className="h-4 w-4 inline mr-1" />
            No inspection found for this application
          </p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="card p-6 space-y-6">
        {errors.submit && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm" role="alert">
            {errors.submit}
          </div>
        )}

        {isIneligible && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-start">
              <XCircle className="h-5 w-5 text-red-600 mr-3 flex-shrink-0" />
              <div>
                <h3 className="font-medium text-red-900">Certificate cannot be issued</h3>
                <ul className="text-sm text-red-700 mt-2 list-disc list-inside space-y-1">
                  {ineligibilityReasons.map((reason, idx) => (
                    <li key={idx}>{reason}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {!isIneligible && (
          <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-start">
              <CheckCircle className="h-5 w-5 text-green-600 mr-3 flex-shrink-0" />
              <div>
                <h3 className="font-medium text-green-900">All prerequisites satisfied</h3>
                <p className="text-sm text-green-700 mt-1">Certificate can be issued for this application</p>
              </div>
            </div>
          </div>
        )}

        <div>
          <label htmlFor="valid_from" className="label">Valid From <span className="text-red-500">*</span></label>
          <input
            id="valid_from"
            name="valid_from"
            type="date"
            value={formData.valid_from}
            onChange={handleChange}
            className={cn('input', errors.valid_from && 'border-red-500 focus:border-red-500 focus:ring-red-500')}
            required
            disabled={isIneligible}
          />
          {errors.valid_from && <p className="mt-1 text-sm text-red-600">{errors.valid_from}</p>}
        </div>

        <div>
          <label htmlFor="valid_until" className="label">Valid Until <span className="text-red-500">*</span></label>
          <input
            id="valid_until"
            name="valid_until"
            type="date"
            value={formData.valid_until}
            onChange={handleChange}
            className={cn('input', errors.valid_until && 'border-red-500 focus:border-red-500 focus:ring-red-500')}
            required
            disabled={isIneligible}
          />
          {errors.valid_until && <p className="mt-1 text-sm text-red-600">{errors.valid_until}</p>}
        </div>

        <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
          <Link to={`/applications/${id}`} className="btn-secondary" disabled={submitting}>
            Cancel
          </Link>
          <button type="submit" disabled={submitting || isIneligible} className="btn-primary">
            {submitting ? 'Issuing...' : 'Issue Certificate'}
          </button>
        </div>
      </form>

      <div className="card p-6 bg-gray-50 border-yellow-200">
        <div className="flex items-start">
          <AlertTriangle className="h-5 w-5 text-yellow-600 mr-3 flex-shrink-0" />
          <div>
            <h3 className="font-medium text-gray-900">Prototype System</h3>
            <p className="text-sm text-gray-600 mt-1">
              This is a prototype for PS-26036. Certificates issued here are for demonstration only and have no legal validity.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}