import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { BarChart, AlertTriangle, Users, Clock, FileText, Scale } from 'lucide-react'
import api from '../../lib/api'
import { formatDate, getStatusBadge, getStatusLabel } from '../../lib/utils'

export default function RegulatorDashboard() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboard()
  }, [])

  const fetchDashboard = async () => {
    try {
      const statsRes = await api.get('/dashboards')
      setStats(statsRes.data.regulator)
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

  const expiryCards = [
    { label: 'Valid Certificates', value: stats?.expiry_summaries?.valid || 0, color: 'bg-green-500', icon: CheckCircle },
    { label: 'Expiring in 7 Days', value: stats?.expiry_summaries?.expiring_7_days || 0, color: 'bg-yellow-500', icon: Clock },
    { label: 'Expiring in 30 Days', value: stats?.expiry_summaries?.expiring_30_days || 0, color: 'bg-orange-500', icon: AlertTriangle },
    { label: 'Expired', value: stats?.expiry_summaries?.expired || 0, color: 'bg-red-500', icon: XCircle },
  ]

  const { CheckCircle, XCircle } = require('lucide-react')

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Regulator Dashboard</h1>
          <p className="text-gray-600">Monitor jurisdiction-level pendency, workload, and certificate validity</p>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {expiryCards.map((stat, i) => {
          const Icon = stat.icon
          return (
            <div key={i} className="card p-6 hover:shadow-md transition-shadow">
              <div className="flex items-center">
                <div className={`p-3 rounded-lg ${stat.color}`}>
                  <Icon className="h-6 w-6 text-white" />
                </div>
                <div className="ml-4">
                  <p className="text-sm text-gray-500">{stat.label}</p>
                  <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <div className="p-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Applications by Stage</h2>
          </div>
          <div className="p-4 space-y-3">
            {stats?.pending_by_stage && Object.entries(stats.pending_by_stage).length > 0 ? (
              Object.entries(stats.pending_by_stage).map(([stage, count]) => (
                <div key={stage} className="flex items-center justify-between">
                  <span className="text-gray-700 capitalize">{stage.replace(/_/g, ' ')}</span>
                  <span className="font-semibold text-gray-900">{count}</span>
                </div>
              ))
            ) : (
              <p className="text-gray-500">No pending applications</p>
            )}
          </div>
        </div>

        <div className="card">
          <div className="p-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Workload by Officer</h2>
          </div>
          <div className="p-4 space-y-3">
            {stats?.workload_by_office && Object.entries(stats.workload_by_office).length > 0 ? (
              Object.entries(stats.workload_by_office).map(([officer, count]) => (
                <div key={officer} className="flex items-center justify-between">
                  <span className="text-gray-700">{officer}</span>
                  <span className="font-semibold text-gray-900">{count} active cases</span>
                </div>
              ))
            ) : (
              <p className="text-gray-500">No active workload data</p>
            )}
          </div>
        </div>
      </div>

      <div className="card">
        <div className="p-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Quick Links</h2>
        </div>
        <div className="p-4 grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Link to="/search/applications" className="btn-secondary h-auto py-4 flex flex-col items-center">
            <FileText className="h-8 w-8 text-gray-500 mb-2" />
            <span className="text-sm font-medium">Search Applications</span>
          </Link>
          <Link to="/search/certificates" className="btn-secondary h-auto py-4 flex flex-col items-center">
            <Scale className="h-8 w-8 text-gray-500 mb-2" />
            <span className="text-sm font-medium">Certificate Validity</span>
          </Link>
          <Link to="/audit" className="btn-secondary h-auto py-4 flex flex-col items-center">
            <Users className="h-8 w-8 text-gray-500 mb-2" />
            <span className="text-sm font-medium">Audit Activity</span>
          </Link>
        </div>
      </div>
    </div>
  )
}