import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Package, FileText, Calendar, Award, AlertTriangle, Clock, Plus, Search, Filter } from 'lucide-react'
import api from '../../lib/api'
import { formatDate, getStatusBadge, getStatusLabel } from '../../lib/utils'

export default function OwnerDashboard() {
  const [stats, setStats] = useState(null)
  const [recentApplications, setRecentApplications] = useState([])
  const [expiringCertificates, setExpiringCertificates] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboard()
  }, [])

  const fetchDashboard = async () => {
    try {
      const [statsRes, appsRes, certsRes] = await Promise.all([
        api.get('/dashboards'),
        api.get('/applications', { params: { page_size: 5 } }),
        api.get('/certificates', { params: { page_size: 5 } }),
      ])
      setStats(statsRes.data.owner)
      setRecentApplications(appsRes.data.items)
      const expiring = certsRes.data.items.filter(c => {
        const validUntil = new Date(c.valid_until)
        const now = new Date()
        const diff = (validUntil - now) / (1000 * 60 * 60 * 24)
        return diff <= 30 && diff > 0
      })
      setExpiringCertificates(expiring)
    } catch (error) {
      console.error('Failed to fetch dashboard', error)
    } finally {
      setLoading(false)
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

  const statCards = [
    { label: 'Total Instruments', value: stats?.total_instruments || 0, icon: Package, color: 'bg-blue-500' },
    { label: 'Active Applications', value: stats?.active_applications || 0, icon: FileText, color: 'bg-yellow-500' },
    { label: 'Upcoming Appointments', value: stats?.upcoming_appointments || 0, icon: Calendar, color: 'bg-purple-500' },
    { label: 'Active Certificates', value: stats?.active_certificates || 0, icon: Award, color: 'bg-green-500' },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600">Overview of your instruments and verification activities</p>
        </div>
        <Link to="/instruments/new" className="btn-primary">
          <Plus className="h-4 w-4 mr-2" />
          Register Instrument
        </Link>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((stat, i) => (
          <Link key={i} to={i === 0 ? '/instruments' : i === 1 ? '/applications' : i === 2 ? '/appointments' : '/certificates'} className="card p-6 hover:shadow-md transition-shadow">
            <div className="flex items-center">
              <div className={`p-3 rounded-lg ${stat.color}`}>
                <stat.icon className="h-6 w-6 text-white" />
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-500">{stat.label}</p>
                <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
              </div>
            </div>
          </Link>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <div className="p-4 border-b border-gray-200 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Recent Applications</h2>
            <Link to="/applications" className="text-sm text-primary-600 hover:text-primary-700">View all</Link>
          </div>
          <div className="divide-y divide-gray-100">
            {recentApplications.length === 0 ? (
              <div className="p-6 text-center text-gray-500">No applications yet</div>
            ) : (
              recentApplications.map((app) => (
                <Link key={app.id} to={`/applications/${app.id}`} className="p-4 hover:bg-gray-50 flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-900">Application #{app.id}</p>
                    <p className="text-sm text-gray-500">
                      {app.verification_type === 'initial' ? 'Initial' : 'Re-verification'} • {formatDate(app.submitted_at || app.created_at)}
                    </p>
                  </div>
                  <span className={`badge ${getStatusBadge(app.status)}`}>{getStatusLabel(app.status)}</span>
                </Link>
              ))
            )}
          </div>
        </div>

        <div className="card">
          <div className="p-4 border-b border-gray-200 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Certificates Expiring Soon</h2>
            <Link to="/certificates" className="text-sm text-primary-600 hover:text-primary-700">View all</Link>
          </div>
          <div className="divide-y divide-gray-100">
            {expiringCertificates.length === 0 ? (
              <div className="p-6 text-center text-gray-500">No certificates expiring soon</div>
            ) : (
              expiringCertificates.map((cert) => (
                <Link key={cert.id} to={`/certificates/${cert.id}`} className="p-4 hover:bg-gray-50 flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-900">{cert.certificate_number}</p>
                    <p className="text-sm text-gray-500">Expires {formatDate(cert.valid_until)}</p>
                  </div>
                  <span className={`badge ${getStatusBadge(cert.status)}`}>{getStatusLabel(cert.status)}</span>
                </Link>
              ))
            )}
          </div>
        </div>
      </div>

      <div className="card">
        <div className="p-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Quick Actions</h2>
        </div>
        <div className="p-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Link to="/instruments/new" className="btn-secondary h-auto py-4 flex flex-col items-center">
            <Package className="h-8 w-8 text-gray-500 mb-2" />
            <span className="text-sm font-medium">Register Instrument</span>
          </Link>
          <Link to="/applications/new" className="btn-secondary h-auto py-4 flex flex-col items-center">
            <FileText className="h-8 w-8 text-gray-500 mb-2" />
            <span className="text-sm font-medium">New Application</span>
          </Link>
          <Link to="/appointments" className="btn-secondary h-auto py-4 flex flex-col items-center">
            <Calendar className="h-8 w-8 text-gray-500 mb-2" />
            <span className="text-sm font-medium">View Appointments</span>
          </Link>
          <Link to="/certificates" className="btn-secondary h-auto py-4 flex flex-col items-center">
            <Award className="h-8 w-8 text-gray-500 mb-2" />
            <span className="text-sm font-medium">View Certificates</span>
          </Link>
        </div>
      </div>
    </div>
  )
}