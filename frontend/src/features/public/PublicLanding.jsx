import { Link } from 'react-router-dom'
import { Scale, Search, Shield, Clock, Users, ArrowRight } from 'lucide-react'

export default function PublicLanding() {
  const features = [
    {
      icon: Search,
      title: 'Certificate Verification',
      description: 'Scan QR codes or enter certificate IDs to instantly verify the status of weighing and measuring instruments.',
    },
    {
      icon: Shield,
      title: 'Secure & Transparent',
      description: 'Role-based access control ensures only authorized personnel can issue or revoke certificates. All actions are audited.',
    },
    {
      icon: Clock,
      title: 'Lifecycle Management',
      description: 'Track instruments from registration through verification, inspection, and certificate expiry with automated reminders.',
    },
    {
      icon: Users,
      title: 'Multi-Stakeholder Workflow',
      description: 'Designed for instrument owners, legal metrology officers, test centres, regulators, and administrators.',
    },
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <div className="inline-flex items-center justify-center h-10 w-10 rounded-xl bg-primary-600">
                <Scale className="h-6 w-6 text-white" />
              </div>
              <span className="ml-2 text-xl font-bold text-gray-900">Legal Metrology</span>
            </div>
            <nav className="hidden md:flex items-center space-x-8">
              <Link to="/verify" className="text-gray-600 hover:text-gray-900 font-medium">Verify Certificate</Link>
              <Link to="/login" className="btn-primary">Sign In</Link>
            </nav>
          </div>
        </div>
      </header>

      <main>
        <section className="relative bg-gradient-to-b from-primary-50 to-white py-20 sm:py-32">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="max-w-3xl">
              <h1 className="text-4xl sm:text-5xl font-bold text-gray-900 tracking-tight">
                Online Verification System for{' '}
                <span className="text-primary-600">Weighing & Measuring Instruments</span>
              </h1>
              <p className="mt-6 text-lg text-gray-600">
                A secure, digital platform for managing the complete lifecycle of instrument verification:
                registration, application, inspection, certification, and public verification.
              </p>
              <div className="mt-8 flex flex-wrap items-center gap-4">
                <Link to="/verify" className="btn-primary text-lg px-8 py-3">
                  <Search className="h-5 w-5 mr-2" />
                  Verify Certificate
                </Link>
                <Link to="/login" className="btn-secondary text-lg px-8 py-3">
                  Sign In to Dashboard
                  <ArrowRight className="h-5 w-5 ml-2" />
                </Link>
              </div>
              <p className="mt-6 text-sm text-gray-500">
                Prototype for PS-26036 / SIH26036 — Not an official government deployment
              </p>
            </div>
          </div>
        </section>

        <section className="py-16 sm:py-24 bg-white">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold text-gray-900">Key Capabilities</h2>
              <p className="mt-4 text-lg text-gray-600 max-w-2xl mx-auto">
                Built for the complete verification workflow with role-based access and audit trails
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {features.map((feature, index) => (
                <div key={index} className="card p-6 hover:shadow-md transition-shadow">
                  <div className="inline-flex items-center justify-center h-12 w-12 rounded-lg bg-primary-100 text-primary-600 mb-4">
                    <feature.icon className="h-6 w-6" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">{feature.title}</h3>
                  <p className="text-gray-600">{feature.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="py-16 sm:py-24 bg-gray-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="grid md:grid-cols-3 gap-8">
              <div className="md:col-span-2">
                <h2 className="text-2xl font-bold text-gray-900 mb-4">Workflow Overview</h2>
                <div className="space-y-4">
                  {[
                    'Owner registers instrument and submits verification application with documents',
                    'LMO reviews application, requests corrections or approves for scheduling',
                    'Appointment scheduled with officer or GATC centre',
                    'Inspector records inspection result (pass/fail/follow-up)',
                    'Authorized LMO issues certificate with QR code',
                    'Public verifies certificate status via QR scan or certificate ID',
                  ].map((step, i) => (
                    <div key={i} className="flex items-start">
                      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary-600 text-white flex items-center justify-center text-sm font-medium">
                        {i + 1}
                      </div>
                      <div className="ml-4 pt-1">
                        <p className="text-gray-700">{step}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="card p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Demo Accounts</h3>
                <p className="text-sm text-gray-600 mb-4">All demo accounts use password: <code className="bg-gray-100 px-1.5 py-0.5 rounded">demo1234</code></p>
                <ul className="space-y-2 text-sm">
                  <li className="flex justify-between"><span>owner1@demo.com</span><span className="text-gray-500">Owner</span></li>
                  <li className="flex justify-between"><span>lmo1@demo.com</span><span className="text-gray-500">LMO</span></li>
                  <li className="flex justify-between"><span>gatc1@demo.com</span><span className="text-gray-500">GATC</span></li>
                  <li className="flex justify-between"><span>regulator1@demo.com</span><span className="text-gray-500">Regulator</span></li>
                  <li className="flex justify-between"><span>admin@demo.com</span><span className="text-gray-500">Admin</span></li>
                </ul>
                <Link to="/login" className="mt-4 btn-primary w-full text-center">
                  Try Demo
                </Link>
              </div>
            </div>
          </div>
        </section>

        <section className="py-16 bg-white border-t border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Public Certificate Verification</h2>
            <p className="text-gray-600 mb-6 max-w-2xl mx-auto">
              Anyone can verify a certificate by scanning its QR code or entering the certificate ID.
              No login required. Only approved public fields are displayed.
            </p>
            <Link to="/verify" className="btn-primary inline-flex items-center">
              <Search className="h-5 w-5 mr-2" />
              Verify a Certificate
            </Link>
          </div>
        </section>
      </main>

      <footer className="bg-gray-900 text-gray-400 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <p className="text-sm">
            Legal Metrology Online Verification System — Prototype for PS-26036 / SIH26036
          </p>
          <p className="text-xs mt-2">
            This is a prototype demonstration. Not an official government service. Do not rely on prototype certificates for legal purposes.
          </p>
        </div>
      </footer>
    </div>
  )
}