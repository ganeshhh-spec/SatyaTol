import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Scale, ArrowLeft } from 'lucide-react'
import api from '../../lib/api'
import { cn } from '../../lib/utils'

const categories = [
  { value: 'weighing_non_automatic', label: 'Weighing - Non-Automatic' },
  { value: 'weighing_automatic', label: 'Weighing - Automatic' },
  { value: 'measuring_length', label: 'Measuring - Length' },
  { value: 'measuring_volume', label: 'Measuring - Volume' },
  { value: 'measuring_flow', label: 'Measuring - Flow' },
  { value: 'other', label: 'Other' },
]

export default function InstrumentForm() {
  const navigate = useNavigate()
  const { id } = useParams()
  const isEditing = !!id
  const [formData, setFormData] = useState({
    category: '',
    instrument_type: '',
    manufacturer: '',
    model: '',
    serial_number: '',
    capacity: '',
    unit: '',
    location: '',
    use_context: '',
  })
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (isEditing) {
      fetchInstrument()
    }
  }, [id])

  const fetchInstrument = async () => {
    setLoading(true)
    try {
      const response = await api.get(`/instruments/${id}`)
      setFormData(response.data)
    } catch (error) {
      console.error('Failed to fetch instrument', error)
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
    if (!formData.category) newErrors.category = 'Category is required'
    if (!formData.instrument_type.trim()) newErrors.instrument_type = 'Instrument type is required'
    if (!formData.manufacturer.trim()) newErrors.manufacturer = 'Manufacturer is required'
    if (!formData.model.trim()) newErrors.model = 'Model is required'
    if (!formData.serial_number.trim()) newErrors.serial_number = 'Serial number is required'
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!validate()) return

    setSubmitting(true)
    try {
      if (isEditing) {
        await api.patch(`/instruments/${id}`, formData)
      } else {
        await api.post('/instruments', formData)
      }
      navigate('/instruments')
    } catch (error) {
      if (error.response?.data?.detail) {
        setErrors({ submit: error.response.data.detail })
      } else {
        setErrors({ submit: 'Failed to save instrument' })
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

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center">
        <button onClick={() => navigate(-1)} className="btn-ghost p-2 mr-4">
          <ArrowLeft className="h-5 w-5" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{isEditing ? 'Edit Instrument' : 'Register Instrument'}</h1>
          <p className="text-gray-600">Enter the details of the weighing or measuring instrument</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="card p-6 space-y-6">
        {errors.submit && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm" role="alert">
            {errors.submit}
          </div>
        )}

        <div>
          <label htmlFor="category" className="label">Category <span className="text-red-500">*</span></label>
          <select
            id="category"
            name="category"
            value={formData.category}
            onChange={handleChange}
            className={cn('input', errors.category && 'border-red-500 focus:border-red-500 focus:ring-red-500')}
            required
          >
            <option value="">Select category</option>
            {categories.map((c) => (
              <option key={c.value} value={c.value}>{c.label}</option>
            ))}
          </select>
          {errors.category && <p className="mt-1 text-sm text-red-600">{errors.category}</p>}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label htmlFor="instrument_type" className="label">Instrument Type <span className="text-red-500">*</span></label>
            <input
              id="instrument_type"
              name="instrument_type"
              type="text"
              value={formData.instrument_type}
              onChange={handleChange}
              className={cn('input', errors.instrument_type && 'border-red-500 focus:border-red-500 focus:ring-red-500')}
              placeholder="e.g., Weighbridge, Platform Scale"
              required
            />
            {errors.instrument_type && <p className="mt-1 text-sm text-red-600">{errors.instrument_type}</p>}
          </div>

          <div>
            <label htmlFor="manufacturer" className="label">Manufacturer <span className="text-red-500">*</span></label>
            <input
              id="manufacturer"
              name="manufacturer"
              type="text"
              value={formData.manufacturer}
              onChange={handleChange}
              className={cn('input', errors.manufacturer && 'border-red-500 focus:border-red-500 focus:ring-red-500')}
              placeholder="e.g., Avery Weigh-Tronix"
              required
            />
            {errors.manufacturer && <p className="mt-1 text-sm text-red-600">{errors.manufacturer}</p>}
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label htmlFor="model" className="label">Model <span className="text-red-500">*</span></label>
            <input
              id="model"
              name="model"
              type="text"
              value={formData.model}
              onChange={handleChange}
              className={cn('input', errors.model && 'border-red-500 focus:border-red-500 focus:ring-red-500')}
              placeholder="e.g., ZM510"
              required
            />
            {errors.model && <p className="mt-1 text-sm text-red-600">{errors.model}</p>}
          </div>

          <div>
            <label htmlFor="serial_number" className="label">Serial Number <span className="text-red-500">*</span></label>
            <input
              id="serial_number"
              name="serial_number"
              type="text"
              value={formData.serial_number}
              onChange={handleChange}
              className={cn('input', errors.serial_number && 'border-red-500 focus:border-red-500 focus:ring-red-500')}
              placeholder="e.g., SN123456789"
              required
            />
            {errors.serial_number && <p className="mt-1 text-sm text-red-600">{errors.serial_number}</p>}
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label htmlFor="capacity" className="label">Capacity</label>
            <input
              id="capacity"
              name="capacity"
              type="text"
              value={formData.capacity}
              onChange={handleChange}
              className="input"
              placeholder="e.g., 1000"
            />
          </div>

          <div>
            <label htmlFor="unit" className="label">Unit</label>
            <input
              id="unit"
              name="unit"
              type="text"
              value={formData.unit}
              onChange={handleChange}
              className="input"
              placeholder="e.g., kg, litre, m"
            />
          </div>
        </div>

        <div>
          <label htmlFor="location" className="label">Location</label>
          <textarea
            id="location"
            name="location"
            value={formData.location}
            onChange={handleChange}
            className="input"
            rows={2}
            placeholder="Physical location of the instrument"
          />
        </div>

        <div>
          <label htmlFor="use_context" className="label">Use Context</label>
          <textarea
            id="use_context"
            name="use_context"
            value={formData.use_context}
            onChange={handleChange}
            className="input"
            rows={2}
            placeholder="Description of how the instrument is used"
          />
        </div>

        <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
          <button type="button" onClick={() => navigate(-1)} className="btn-secondary">
            Cancel
          </button>
          <button type="submit" disabled={submitting} className="btn-primary">
            {submitting ? 'Saving...' : isEditing ? 'Update Instrument' : 'Register Instrument'}
          </button>
        </div>
      </form>
    </div>
  )
}