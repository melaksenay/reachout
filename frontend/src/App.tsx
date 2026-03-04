import { Routes, Route, Navigate } from 'react-router-dom'
import LoginPage from './pages/LoginPage'
import SignUpPage from './pages/SignUpPage'
import InfluencersPage from './pages/InfluencersPage'
import InfluencerDetailPage from './pages/InfluencerDetailPage'
import DiscoverPage from './pages/DiscoverPage'
import CampaignsPage from './pages/CampaignsPage'
import SettingsPage from './pages/SettingsPage'
import DashboardPage from './pages/DashboardPage'
import ProtectedRoute from './components/ProtectedRoute'
import NavBar from './components/NavBar'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignUpPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<NavBar />}>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/influencers" element={<InfluencersPage />} />
          <Route path="/influencers/:id" element={<InfluencerDetailPage />} />
          <Route path="/discover" element={<DiscoverPage />} />
          <Route path="/campaigns" element={<CampaignsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Route>
      </Route>
    </Routes>
  )
}
