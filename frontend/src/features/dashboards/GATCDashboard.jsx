import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Calendar, Search, FileText, Scale, ClipboardCheck } from 'lucide-react'
import api from '../../lib/api'
import { formatDate, getStatusBadge, getStatusLabel } from '../../lib/utils'

export default function GATCDashboard() {
  const [stats, setStats] = useState(null)
  const [assignedApplications, setAssignedApplications] = useState([])
  const [upcomingSlots, setUpcomingSlots] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboard()
  }, [])

  const fetchDashboard = async () => {
    try {
      const [statsRes, appsRes, apptsRes] = await Promise.all([
        api.get('/dashboards'),
        api.get('/applications', { params: { page_size: 5 } }),
        api.get('/appointments', { params: { status: 'scheduled', page_size: 5 } }),
      ])
      setStats(statsRes.data.gatc)
      setAssignedApplications(appsRes.data.items)
      setUpcomingSlots(apptsRes.data.items)
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
    { label: 'Assigned Applications', value: stats?.assigned_applications || 0, icon: FileText, color: 'bg-blue-500' },
    { label: 'Upcoming Slots', value: stats?.upcoming_slots || 0, icon: Calendar, color: 'bg-green-500' },
    { label: 'Pending Test Records', value: stats?.pending_test_records || 0, icon: Search, color: 'bg-yellow-500' },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">GATC Dashboard</h1>
          <p className="text-gray-600">Manage centre appointments and test records</p>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {statCards.map((stat, i) => (
          <Link key={i} to={i === 0 ? '/applications' : i === 1 ? '/appointments' : '/inspections'} className="card p-6 hover:shadow-md transition-shadow">
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
            <h2 className="text-lg font-semibold text-gray-900">Assigned Applications</h2>
            <Link to="/applications" className="text-sm text-primary-600 hover:text-primary-700">View all</Link>
          </div>
          <div className="divide-y divide-gray-100">
            {assignedApplications.length === 0 ? (
              <div className="p-6 text-center text-gray-500">No assigned applications</div>
            ) : (
              assignedApplications.map((app) => (
                <Link key={app.id} to={`/applications/${app.id}`} className="p-4 hover:bg-gray-50 flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-900">Application #{app.id}</p>
                    <p className="text-sm text-gray-500">
                      {app.instrument?.manufacturer} {app.instrument?.model} • {formatDate(app.submitted_at)}
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
            <h2 className="text-lg font-semibold text-gray-900">Upcoming Appointments</h2>
            <Link to="/appointments" className="text-sm text-primary-600 hover:text-primary-700">View all</Link>
          </div>
          <div className="divide-y divide-gray-100">
            {upcomingSlots.length === 0 ? (
              <div className="p-6 text-center text-gray-500">No upcoming appointments</div>
            ) : (
              upcomingSlots.map((appt) => (
                <Link key={appt.id} to={`/applications/${appt.application_id}`} className="p-4 hover:bg-gray-50 flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-900">Appointment #{appt.id}</p>
                    <p className="text-sm text-gray-500">
                      {formatDate(appt.scheduled_start)} at {appt.location || 'TBD'}
                    </p>
                  </div>
                  <span className={`badge ${getStatusBadge(appt.status)}`}>{getStatusLabel(appt.status)}</span>
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
        <div className="p-4 grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Link to="/applications" className="btn-secondary h-auto py-4 flex flex-col items-center">
            <FileText className="h-8 w-8 text-gray-500 mb-2" />
            <span className="text-sm font-medium">View Applications</span>
          </Link>
          <Link to="/appointments" className="btn-secondary h-auto py-4 flex flex-col items-center">
            <Calendar className="h-8 w-8 text-gray-500 mb-2" />
            <span className="text-sm font-medium">Manage Calendar</span>
          </Link>
          <Link to="/inspections" className="btn-secondary h-auto py-4 flex flex-col items-center">
            <ClipboardCheck className="h-8 w-8 text-gray-500 mb-2" />
            <span className="text-sm font-medium">Record Test Results</span>
          </Link>
        </div>
      </div>
    </div>
  )
}