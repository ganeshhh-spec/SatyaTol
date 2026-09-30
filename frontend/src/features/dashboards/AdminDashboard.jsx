import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Users, Settings, Scale, Shield, Plus } from 'lucide-react'
import api from '../../lib/api'

export default function AdminDashboard() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboard()
  }, [])

  const fetchDashboard = async () => {
    try {
      const statsRes = await api.get('/dashboards')
      setStats(statsRes.data.admin)
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
    { label: 'Active Users', value: stats?.active_users || 0, icon: Users, color: 'bg-blue-500' },
    { label: 'Configured Centres', value: stats?.centre_configuration || 0, icon: Scale, color: 'bg-green-500' },
  ]

  const roleDistribution = stats?.role_distribution || {}

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
          <p className="text-gray-600">Manage users, roles, and system configuration</p>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {statCards.map((stat, i) => (
          <Link key={i} to={i === 0 ? '/users' : '/config'} className="card p-6 hover:shadow-md transition-shadow">
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
            <h2 className="text-lg font-semibold text-gray-900">User Role Distribution</h2>
          </div>
          <div className="p-4 space-y-3">
            {Object.entries(roleDistribution).length > 0 ? (
              Object.entries(roleDistribution).map(([role, count]) => (
                <div key={role} className="flex items-center justify-between">
                  <span className="text-gray-700 capitalize">{role}</span>
                  <span className="font-semibold text-gray-900">{count}</span>
                </div>
              ))
            ) : (
              <p className="text-gray-500">No user data</p>
            )}
          </div>
        </div>

        <div className="card">
          <div className="p-4 border-b border-gray-200 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">System Status</h2>
          </div>
          <div className="p-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-gray-700">Database</span>
              <span className="badge badge-green">Connected</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-700">API</span>
              <span className="badge badge-green">Operational</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-700">File Storage</span>
              <span className="badge badge-green">Available</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-700">Prototype Mode</span>
              <span className="badge badge-yellow">Active</span>
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="p-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Quick Actions</h2>
        </div>
        <div className="p-4 grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Link to="/users" className="btn-secondary h-auto py-4 flex flex-col items-center">
            <Users className="h-8 w-8 text-gray-500 mb-2" />
            <span className="text-sm font-medium">Manage Users</span>
          </Link>
          <Link to="/users/new" className="btn-primary h-auto py-4 flex flex-col items-center">
            <Plus className="h-8 w-8 text-white mb-2" />
            <span className="text-sm font-medium">Add User</span>
          </Link>
          <Link to="/config" className="btn-secondary h-auto py-4 flex flex-col items-center">
            <Settings className="h-8 w-8 text-gray-500 mb-2" />
            <span className="text-sm font-medium">Configuration</span>
          </Link>
        </div>
      </div>
    </div>
  )
}