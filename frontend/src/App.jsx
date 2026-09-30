import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './lib/auth'
import Layout from './app/Layout'
import Login from './features/auth/Login'
import Register from './features/auth/Register'
import PublicLanding from './features/public/PublicLanding'
import PublicVerify from './features/public/PublicVerify'
import OwnerDashboard from './features/dashboards/OwnerDashboard'
import LMOOwnDashboard from './features/dashboards/LMODashboard'
import GATCDashboard from './features/dashboards/GATCDashboard'
import RegulatorDashboard from './features/dashboards/RegulatorDashboard'
import AdminDashboard from './features/dashboards/AdminDashboard'
import InstrumentList from './features/instruments/InstrumentList'
import InstrumentForm from './features/instruments/InstrumentForm'
import InstrumentDetail from './features/instruments/InstrumentDetail'
import InstrumentHistory from './features/instruments/InstrumentHistory'
import ApplicationList from './features/applications/ApplicationList'
import ApplicationForm from './features/applications/ApplicationForm'
import ApplicationDetail from './features/applications/ApplicationDetail'
import AppointmentList from './features/scheduling/AppointmentList'
import AppointmentDetail from './features/scheduling/AppointmentDetail'
import InspectionForm from './features/inspections/InspectionForm'
import InspectionList from './features/inspections/InspectionList'
import CertificateDetail from './features/certificates/CertificateDetail'
import CertificateList from './features/certificates/CertificateList'
import CertificateIssue from './features/certificates/CertificateIssue'
import NotFound from './components/NotFound'
import AccessDenied from './components/AccessDenied'

function ProtectedRoute({ children, allowedRoles }) {
  const { user, loading, isAuthenticated } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-600 border-t-transparent"></div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <AccessDenied />
  }

  return children
}

function PublicRoute({ children }) {
  const { isAuthenticated, loading } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-600 border-t-transparent"></div>
      </div>
    )
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }

  return children
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
      <Route path="/register" element={<PublicRoute><Register /></PublicRoute>} />
      <Route path="/verify/:token" element={<PublicVerify />} />
      <Route path="/verify" element={<PublicVerify />} />

      <Route element={<Layout />}>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={
          <ProtectedRoute>
            <DashboardRouter />
          </ProtectedRoute>
        } />
        <Route path="/instruments" element={
          <ProtectedRoute allowedRoles={['owner', 'lmo', 'gatc', 'regulator', 'admin']}>
            <InstrumentList />
          </ProtectedRoute>
        } />
        <Route path="/instruments/new" element={
          <ProtectedRoute allowedRoles={['owner']}>
            <InstrumentForm />
          </ProtectedRoute>
        } />
        <Route path="/instruments/:id" element={
          <ProtectedRoute allowedRoles={['owner', 'lmo', 'gatc', 'regulator', 'admin']}>
            <InstrumentDetail />
          </ProtectedRoute>
        } />
        <Route path="/instruments/:id/history" element={
          <ProtectedRoute allowedRoles={['owner', 'lmo', 'gatc', 'regulator', 'admin']}>
            <InstrumentHistory />
          </ProtectedRoute>
        } />
        <Route path="/instruments/:id/edit" element={
          <ProtectedRoute allowedRoles={['owner']}>
            <InstrumentForm />
          </ProtectedRoute>
        } />
        <Route path="/applications" element={
          <ProtectedRoute allowedRoles={['owner', 'lmo', 'gatc', 'regulator', 'admin']}>
            <ApplicationList />
          </ProtectedRoute>
        } />
        <Route path="/applications/new" element={
          <ProtectedRoute allowedRoles={['owner']}>
            <ApplicationForm />
          </ProtectedRoute>
        } />
        <Route path="/applications/:id" element={
          <ProtectedRoute allowedRoles={['owner', 'lmo', 'gatc', 'regulator', 'admin']}>
            <ApplicationDetail />
          </ProtectedRoute>
        } />
        <Route path="/appointments" element={
          <ProtectedRoute allowedRoles={['owner', 'lmo', 'gatc', 'regulator', 'admin']}>
            <AppointmentList />
          </ProtectedRoute>
        } />
        <Route path="/appointments/:id" element={
          <ProtectedRoute allowedRoles={['owner', 'lmo', 'gatc', 'regulator', 'admin']}>
            <AppointmentDetail />
          </ProtectedRoute>
        } />
        <Route path="/inspections" element={
          <ProtectedRoute allowedRoles={['lmo', 'gatc', 'regulator', 'admin']}>
            <InspectionList />
          </ProtectedRoute>
        } />
        <Route path="/inspections/new/:applicationId" element={
          <ProtectedRoute allowedRoles={['lmo', 'gatc']}>
            <InspectionForm />
          </ProtectedRoute>
        } />
        <Route path="/inspections/:id/:applicationId?" element={
          <ProtectedRoute allowedRoles={['lmo', 'gatc', 'regulator', 'admin']}>
            <InspectionForm />
          </ProtectedRoute>
        } />
        <Route path="/certificates" element={
          <ProtectedRoute allowedRoles={['owner', 'lmo', 'gatc', 'regulator', 'admin']}>
            <CertificateList />
          </ProtectedRoute>
        } />
        <Route path="/certificates/:id" element={
          <ProtectedRoute allowedRoles={['owner', 'lmo', 'gatc', 'regulator', 'admin']}>
            <CertificateDetail />
          </ProtectedRoute>
        } />
        <Route path="/certificates/issue/:applicationId" element={
          <ProtectedRoute allowedRoles={['lmo']}>
            <CertificateIssue />
          </ProtectedRoute>
        } />
      </Route>

      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}

function DashboardRouter() {
  const { user } = useAuth()

  switch (user?.role) {
    case 'owner':
      return <OwnerDashboard />
    case 'lmo':
      return <LMOOwnDashboard />
    case 'gatc':
      return <GATCDashboard />
    case 'regulator':
      return <RegulatorDashboard />
    case 'admin':
      return <AdminDashboard />
    default:
      return <div className="p-8 text-center">Unknown role</div>
  }
}

export default App