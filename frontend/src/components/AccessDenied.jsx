import { Link } from 'react-router-dom'
import { Lock, ArrowLeft } from 'lucide-react'

export default function AccessDenied() {
  return (
    <div className="min-h-[60vh] flex items-center justify-center px-4">
      <div className="text-center">
        <Lock className="h-16 w-16 text-gray-300 mx-auto mb-4" />
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Access Denied</h1>
        <p className="text-gray-600 mb-8 max-w-md mx-auto">
          You don't have permission to access this page. Please contact your administrator if you believe this is an error.
        </p>
        <Link to="/dashboard" className="btn-primary">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Go to Dashboard
        </Link>
      </div>
    </div>
  )
}