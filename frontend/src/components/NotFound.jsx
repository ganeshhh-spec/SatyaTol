import { Link } from 'react-router-dom'
import { Home, Search } from 'lucide-react'

export default function NotFound() {
  return (
    <div className="min-h-[60vh] flex items-center justify-center px-4">
      <div className="text-center">
        <h1 className="text-6xl font-bold text-gray-900 mb-4">404</h1>
        <p className="text-xl text-gray-600 mb-8">Page not found</p>
        <p className="text-gray-500 mb-8 max-w-md mx-auto">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <div className="flex items-center justify-center space-x-4">
          <Link to="/" className="btn-primary">
            <Home className="h-4 w-4 mr-2" />
            Go Home
          </Link>
          <Link to="/verify" className="btn-secondary">
            <Search className="h-4 w-4 mr-2" />
            Verify Certificate
          </Link>
        </div>
      </div>
    </div>
  )
}