import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Search, ArrowLeft, CheckCircle, XCircle, AlertTriangle, Camera, Save, Flag } from 'lucide-react'
import api from '../../lib/api'
import { cn } from '../../lib/utils'
import { useAuth } from '../../lib/auth'

export default function InspectionForm() {
  const navigate = useNavigate()
  const { id, applicationId } = useParams()
  const { user, isLMO, isGATC } = useAuth()
  const isEditing = !!id
  const [application, setApplication] = useState(null)
  const [formData, setFormData] = useState({
    application_id: applicationId || '',
    appointment_id: '',
    result: '',
    observations: '',
    checklist: '',
    condition_notes: '',
    photos: '',
    signature_metadata: '',
    is_finalized: false,
  })
  const [appointments, setAppointments] = useState([])
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [finalizing, setFinalizing] = useState(false)

  useEffect(() => {
    if (applicationId) {
      formData.application_id = applicationId
      fetchApplication()
      fetchAppointments()
    }
    if (isEditing) {
      fetchInspection()
    }
  }, [applicationId, id])

  const fetchApplication = async () => {
    try {
      const response = await api.get(`/applications/${applicationId}`)
      setApplication(response.data)
    } catch (error) {
      console.error('Failed to fetch application', error)
    }
  }

  const fetchAppointments = async () => {
    try {
      const response = await api.get('/appointments', { params: { page_size: 50 } })
      setAppointments(response.data.items.filter(a => a.application_id === parseInt(applicationId)))
    } catch (error) {
      console.error('Failed to fetch appointments', error)
    }
  }

  const fetchInspection = async () => {
    setLoading(true)
    try {
      const response = await api.get(`/inspections/${id}`)
      setFormData({
        application_id: response.data.application_id,
        appointment_id: response.data.appointment_id || '',
        result: response.data.result,
        observations: response.data.observations || '',
        checklist: response.data.checklist || '',
        condition_notes: response.data.condition_notes || '',
        photos: response.data.photos || '',
        signature_metadata: response.data.signature_metadata || '',
        is_finalized: response.data.is_finalized || false,
      })
    } catch (error) {
      console.error('Failed to fetch inspection', error)
    } finally {
      setLoading(false)
    }
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
    if (!formData.application_id) newErrors.application_id = 'Application is required'
    if (!formData.result) newErrors.result = 'Inspection result is required'
    if (!formData.observations.trim()) newErrors.observations = 'Observations are required'
    if (['fail', 'needs_follow_up'].includes(formData.result) && !formData.condition_notes.trim()) {
      newErrors.condition_notes = 'Reason is required for Fail or Needs Follow-up result'
    }
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSaveDraft = async (e) => {
    e.preventDefault()
    if (!formData.application_id) {
      setErrors({ application_id: 'Application is required' })
      return
    }

    setSubmitting(true)
    try {
      if (isEditing) {
        await api.patch(`/inspections/${id}`, { ...formData, is_finalized: false })
      } else {
        await api.post('/inspections', { ...formData, is_finalized: false })
      }
      navigate(`/applications/${formData.application_id}`)
    } catch (error) {
      if (error.response?.data?.detail) {
        setErrors({ submit: error.response.data.detail })
      } else {
        setErrors({ submit: 'Failed to save inspection draft' })
      }
    } finally {
      setSubmitting(false)
    }
  }

  const handleFinalize = async (e) => {
    e.preventDefault()
    if (!validate()) return

    setFinalizing(true)
    try {
      if (isEditing) {
        await api.post(`/inspections/${id}/finalize`, formData)
      } else {
        await api.post('/inspections', { ...formData, is_finalized: true })
      }
      navigate(`/applications/${formData.application_id}`)
    } catch (error) {
      if (error.response?.data?.detail) {
        setErrors({ submit: error.response.data.detail })
      } else {
        setErrors({ submit: 'Failed to finalize inspection' })
      }
    } finally {
      setFinalizing(false)
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

  const canEdit = isEditing && formData.is_finalized && !['admin', 'regulator'].includes(user?.role)
  const showFinalize = !formData.is_finalized

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center">
        <button onClick={() => navigate(-1)} className="btn-ghost p-2 mr-4">
          <ArrowLeft className="h-5 w-5" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{isEditing ? 'Edit Inspection' : 'Record Inspection'}</h1>
          <p className="text-gray-600">Document the inspection findings and result</p>
        </div>
      </div>

      {application && (
        <div className="card p-4 bg-gray-50 border-blue-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-900">Application #{application.id}</p>
              <p className="text-sm text-gray-500">
                {application.instrument?.manufacturer} {application.instrument?.model} ({application.instrument?.serial_number})
              </p>
            </div>
            <span className={`badge ${getStatusBadge(application.status)}`}>{getStatusLabel(application.status)}</span>
          </div>
        </div>
      )}

      <form onSubmit={showFinalize ? handleFinalize : handleSaveDraft} className="card p-6 space-y-6">
        {errors.submit && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm" role="alert">
            {errors.submit}
          </div>
        )}

        <div>
          <label htmlFor="application_id" className="label">Application <span className="text-red-500">*</span></label>
          <select
            id="application_id"
            name="application_id"
            value={formData.application_id}
            onChange={handleChange}
            className={cn('input', errors.application_id && 'border-red-500 focus:border-red-500 focus:ring-red-500')}
            required
            disabled={isEditing}
          >
            <option value="">Select application</option>
            {application && <option value={application.id}>Application #{application.id} - {application.instrument?.manufacturer} {application.instrument?.model}</option>}
          </select>
          {errors.application_id && <p className="mt-1 text-sm text-red-600">{errors.application_id}</p>}
        </div>

        <div>
          <label htmlFor="appointment_id" className="label">Appointment (optional)</label>
          <select
            id="appointment_id"
            name="appointment_id"
            value={formData.appointment_id}
            onChange={handleChange}
            className="input"
            disabled={canEdit}
          >
            <option value="">Select appointment</option>
            {appointments.map((appt) => (
              <option key={appt.id} value={appt.id}>
                #{appt.id} - {new Date(appt.scheduled_start).toLocaleString()}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="label">Inspection Result <span className="text-red-500">*</span></label>
          <div className="grid grid-cols-3 gap-3">
            {[
              { value: 'pass', label: 'Pass', icon: CheckCircle, color: 'border-green-500 bg-green-50' },
              { value: 'fail', label: 'Fail', icon: XCircle, color: 'border-red-500 bg-red-50' },
              { value: 'needs_follow_up', label: 'Needs Follow-up', icon: AlertTriangle, color: 'border-yellow-500 bg-yellow-50' },
            ].map((option) => (
              <label
                key={option.value}
                className={cn(
                  'relative flex flex-col items-center p-4 border-2 rounded-lg cursor-pointer transition-colors',
                  formData.result === option.value ? option.color.replace('border-', 'border-').replace('bg-', 'bg-') : 'border-gray-200 hover:border-gray-300'
                )}
              >
                <input
                  type="radio"
                  name="result"
                  value={option.value}
                  checked={formData.result === option.value}
                  onChange={handleChange}
                  className="sr-only"
                  disabled={canEdit}
                />
                <option.icon className="h-6 w-6 mb-2" style={{ color: option.value === 'pass' ? 'green' : option.value === 'fail' ? 'red' : 'yellow' }} />
                <span className="text-sm font-medium text-gray-700">{option.label}</span>
              </label>
            ))}
          </div>
          {errors.result && <p className="mt-1 text-sm text-red-600">{errors.result}</p>}
        </div>

        <div>
          <label htmlFor="observations" className="label">Observations <span className="text-red-500">*</span></label>
          <textarea
            id="observations"
            name="observations"
            value={formData.observations}
            onChange={handleChange}
            className={cn('input', errors.observations && 'border-red-500 focus:border-red-500 focus:ring-red-500')}
            rows={4}
            placeholder="Describe the inspection findings, measurements taken, and any deviations observed"
            required
            disabled={canEdit}
          />
          {errors.observations && <p className="mt-1 text-sm text-red-600">{errors.observations}</p>}
        </div>

        <div>
          <label htmlFor="checklist" className="label">Checklist (optional)</label>
          <textarea
            id="checklist"
            name="checklist"
            value={formData.checklist}
            onChange={handleChange}
            className="input"
            rows={4}
            placeholder="Standard checklist items verified during inspection"
            disabled={canEdit}
          />
        </div>

        <div>
          <label htmlFor="condition_notes" className="label">Condition Notes / Reason <span className="text-red-500">{['fail', 'needs_follow_up'].includes(formData.result) ? '*' : ''}</span></label>
          <textarea
            id="condition_notes"
            name="condition_notes"
            value={formData.condition_notes}
            onChange={handleChange}
            className={cn('input', errors.condition_notes && 'border-red-500 focus:border-red-500 focus:ring-red-500')}
            rows={3}
            placeholder="Notes on instrument condition, wear, damage, etc. Required for Fail or Needs Follow-up"
            disabled={canEdit}
          />
          {errors.condition_notes && <p className="mt-1 text-sm text-red-600">{errors.condition_notes}</p>}
          {['fail', 'needs_follow_up'].includes(formData.result) && (
            <p className="mt-1 text-xs text-yellow-600"><AlertTriangle className="h-3 w-3 inline mr-1" />Reason required for this result</p>
          )}
        </div>

        <div>
          <label htmlFor="photos" className="label">Photo References (optional)</label>
          <textarea
            id="photos"
            name="photos"
            value={formData.photos}
            onChange={handleChange}
            className="input"
            rows={2}
            placeholder="References to uploaded photos (e.g., filenames, storage paths)"
            disabled={canEdit}
          />
          <p className="mt-1 text-xs text-gray-500">Upload photos via the application attachments section</p>
        </div>

        <div>
          <label htmlFor="signature_metadata" className="label">Signature Metadata (optional)</label>
          <textarea
            id="signature_metadata"
            name="signature_metadata"
            value={formData.signature_metadata}
            onChange={handleChange}
            className="input"
            rows={2}
            placeholder="Digital signature or verification metadata"
            disabled={canEdit}
          />
        </div>

        {canEdit && (
          <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <p className="text-sm text-yellow-800">
              <AlertTriangle className="h-4 w-4 inline mr-1" />
              This inspection has been finalized and cannot be edited.
            </p>
          </div>
        )}

        {formData.is_finalized && (
          <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
            <p className="text-sm text-green-800 flex items-center">
              <CheckCircle className="h-4 w-4 inline mr-1" />
              This inspection has been finalized. Result: <strong>{getStatusLabel(formData.result)}</strong>
            </p>
          </div>
        )}

        <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
          <button type="button" onClick={() => navigate(-1)} className="btn-secondary" disabled={submitting || finalizing}>
            Cancel
          </button>
          {showFinalize ? (
            <>
              <button type="button" onClick={handleSaveDraft} disabled={submitting || finalizing || canEdit} className="btn-secondary">
                <Save className="h-4 w-4 mr-2" />
                Save as Draft
              </button>
              <button type="submit" disabled={submitting || finalizing || canEdit} className="btn-primary">
                <Flag className="h-4 w-4 mr-2" />
                {finalizing ? 'Finalizing...' : 'Finalize Inspection'}
              </button>
            </>
          ) : (
            <button type="submit" disabled={submitting || finalizing || canEdit} className="btn-primary">
              {submitting ? 'Saving...' : 'Update Inspection'}
            </button>
          )}
        </div>
      </form>
    </div>
  )
}

function getStatusBadge(status) {
  const statusMap = {
    pass: 'badge-green',
    fail: 'badge-red',
    needs_follow_up: 'badge-yellow',
  }
  return statusMap[status] || 'badge-gray'
}

function getStatusLabel(status) {
  const labels = {
    pass: 'Pass',
    fail: 'Fail',
    needs_follow_up: 'Needs Follow-up',
  }
  return labels[status] || status
}