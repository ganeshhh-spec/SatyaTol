import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { FileText, ArrowLeft, Paperclip, X } from 'lucide-react'
import api from '../../lib/api'
import { cn } from '../../lib/utils'
import { useAuth } from '../../lib/auth'

export default function ApplicationForm() {
  const navigate = useNavigate()
  const { id } = useParams()
  const { user, isOwner } = useAuth()
  const isEditing = !!id
  const [instruments, setInstruments] = useState([])
  const [formData, setFormData] = useState({
    instrument_id: '',
    verification_type: 'initial',
    jurisdiction: '',
    requested_appointment: '',
    remarks: '',
  })
  const [attachments, setAttachments] = useState([])
  const [uploading, setUploading] = useState(false)
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    fetchInstruments()
  }, [])

  useEffect(() => {
    if (isEditing) {
      fetchApplication()
    }
  }, [id])

  const fetchInstruments = async () => {
    try {
      const response = await api.get('/instruments', { params: { page_size: 100 } })
      setInstruments(response.data.items.filter(inst => inst.status !== 'rejected'))
    } catch (error) {
      console.error('Failed to fetch instruments', error)
    }
  }

  const fetchApplication = async () => {
    setLoading(true)
    try {
      const response = await api.get(`/applications/${id}`)
      setFormData({
        instrument_id: response.data.instrument_id,
        verification_type: response.data.verification_type,
        jurisdiction: response.data.jurisdiction || '',
        requested_appointment: response.data.requested_appointment ? response.data.requested_appointment.slice(0, 16) : '',
        remarks: response.data.remarks || '',
      })
      setAttachments(response.data.attachments || [])
    } catch (error) {
      console.error('Failed to fetch application', error)
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

  const handleFileUpload = async (e) => {
    const files = Array.from(e.target.files)
    if (files.length === 0) return

    setUploading(true)
    try {
      for (const file of files) {
        const formData = new FormData()
        formData.append('file', file)
        const response = await api.post(`/applications/${id}/attachments`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        })
        setAttachments(prev => [...prev, response.data])
      }
      e.target.value = ''
    } catch (error) {
      console.error('Failed to upload attachment', error)
      setErrors({ upload: error.response?.data?.detail || 'Failed to upload file' })
    } finally {
      setUploading(false)
    }
  }

  const removeAttachment = async (attachmentId) => {
    try {
      setAttachments(prev => prev.filter(a => a.id !== attachmentId))
    } catch (error) {
      console.error('Failed to remove attachment', error)
    }
  }

  const validate = () => {
    const newErrors = {}
    if (!formData.instrument_id) newErrors.instrument_id = 'Instrument is required'
    if (!formData.verification_type) newErrors.verification_type = 'Verification type is required'
    if (!isEditing && attachments.length === 0) newErrors.attachments = 'At least one attachment is required'
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!validate()) return

    setSubmitting(true)
    try {
      if (isEditing) {
        await api.patch(`/applications/${id}`, formData)
      } else {
        const response = await api.post('/applications', formData)
        navigate(`/applications/${response.data.id}`)
      }
    } catch (error) {
      if (error.response?.data?.detail) {
        setErrors({ submit: error.response.data.detail })
      } else {
        setErrors({ submit: 'Failed to save application' })
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

  const selectedInstrument = instruments.find(i => i.id === parseInt(formData.instrument_id))

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center">
        <button onClick={() => navigate(-1)} className="btn-ghost p-2 mr-4">
          <ArrowLeft className="h-5 w-5" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{isEditing ? 'Edit Application' : 'New Verification Application'}</h1>
          <p className="text-gray-600">Select an instrument and submit a verification request</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="card p-6 space-y-6">
        {errors.submit && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm" role="alert">
            {errors.submit}
          </div>
        )}

        <div>
          <label htmlFor="instrument_id" className="label">Instrument <span className="text-red-500">*</span></label>
          <select
            id="instrument_id"
            name="instrument_id"
            value={formData.instrument_id}
            onChange={handleChange}
            className={cn('input', errors.instrument_id && 'border-red-500 focus:border-red-500 focus:ring-red-500')}
            required
            disabled={isEditing}
          >
            <option value="">Select an instrument</option>
            {instruments.map((inst) => (
              <option key={inst.id} value={inst.id}>
                {inst.manufacturer} {inst.model} ({inst.serial_number})
              </option>
            ))}
          </select>
          {errors.instrument_id && <p className="mt-1 text-sm text-red-600">{errors.instrument_id}</p>}
          {selectedInstrument && (
            <p className="mt-2 text-sm text-gray-500">
              Category: {selectedInstrument.category.replace(/_/g, ' ')} • Type: {selectedInstrument.instrument_type}
            </p>
          )}
        </div>

        <div>
          <label className="label">Verification Type <span className="text-red-500">*</span></label>
          <div className="flex space-x-4">
            <label className="flex items-center">
              <input
                type="radio"
                name="verification_type"
                value="initial"
                checked={formData.verification_type === 'initial'}
                onChange={handleChange}
                className="h-4 w-4 text-primary-600 border-gray-300 focus:ring-primary-500"
              />
              <span className="ml-2 text-sm text-gray-700">Initial Verification</span>
            </label>
            <label className="flex items-center">
              <input
                type="radio"
                name="verification_type"
                value="reverification"
                checked={formData.verification_type === 'reverification'}
                onChange={handleChange}
                className="h-4 w-4 text-primary-600 border-gray-300 focus:ring-primary-500"
              />
              <span className="ml-2 text-sm text-gray-700">Re-verification</span>
            </label>
          </div>
          {errors.verification_type && <p className="mt-1 text-sm text-red-600">{errors.verification_type}</p>}
        </div>

        <div>
          <label htmlFor="jurisdiction" className="label">Jurisdiction</label>
          <input
            id="jurisdiction"
            name="jurisdiction"
            type="text"
            value={formData.jurisdiction}
            onChange={handleChange}
            className="input"
            placeholder="e.g., North Zone, Delhi Region"
          />
        </div>

        <div>
          <label htmlFor="requested_appointment" className="label">Requested Appointment (optional)</label>
          <input
            id="requested_appointment"
            name="requested_appointment"
            type="datetime-local"
            value={formData.requested_appointment}
            onChange={handleChange}
            className="input"
          />
        </div>

        <div>
          <label htmlFor="remarks" className="label">Remarks (optional)</label>
          <textarea
            id="remarks"
            name="remarks"
            value={formData.remarks}
            onChange={handleChange}
            className="input"
            rows={3}
            placeholder="Any additional information for the reviewing officer"
          />
        </div>

        {!isEditing && (
          <div>
            <label className="label">Attachments <span className="text-red-500">*</span></label>
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6">
              <input
                type="file"
                id="attachments"
                multiple
                accept=".pdf,.jpg,.jpeg,.png"
                onChange={handleFileUpload}
                className="hidden"
                disabled={uploading}
              />
              <label htmlFor="attachments" className="cursor-pointer flex flex-col items-center">
                <Paperclip className="h-10 w-10 text-gray-400 mb-2" />
                <p className="text-gray-600">Click or drag files here (PDF, JPG, PNG - max 10MB each)</p>
                <p className="text-xs text-gray-500 mt-1">At least one attachment required</p>
              </label>
            </div>
            {attachments.length > 0 && (
              <div className="mt-3 space-y-2">
                {attachments.map((att) => (
                  <div key={att.id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span className="text-sm text-gray-700 flex items-center">
                      <Paperclip className="h-4 w-4 mr-2 text-gray-400" />
                      {att.filename}
                    </span>
                    <button
                      type="button"
                      onClick={() => removeAttachment(att.id)}
                      className="text-red-500 hover:text-red-700"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
            {errors.attachments && <p className="mt-1 text-sm text-red-600">{errors.attachments}</p>}
          </div>
        )}

        <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
          <button type="button" onClick={() => navigate(-1)} className="btn-secondary">
            Cancel
          </button>
          <button type="submit" disabled={submitting} className="btn-primary">
            {submitting ? 'Saving...' : isEditing ? 'Update Application' : 'Create Application'}
          </button>
        </div>
      </form>
    </div>
  )
}