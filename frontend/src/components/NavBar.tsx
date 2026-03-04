import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const links = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/influencers', label: 'Influencers' },
  { to: '/discover', label: 'Discover' },
  { to: '/campaigns', label: 'Pipeline' },
  { to: '/settings', label: 'Settings' },
]

export default function NavBar() {
  const { signOut, user } = useAuth()

  return (
    <>
      <nav className="bg-white border-b px-6 py-3 flex items-center justify-between">
        <div className="flex gap-6 text-sm font-medium">
          {links.map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                isActive ? 'text-blue-600' : 'text-gray-700 hover:text-blue-600'
              }
            >
              {label}
            </NavLink>
          ))}
        </div>
        <div className="flex items-center gap-4 text-sm">
          <span className="text-gray-500">{user?.email}</span>
          <button
            onClick={signOut}
            className="text-red-600 hover:underline cursor-pointer"
          >
            Logout
          </button>
        </div>
      </nav>
      <main className="p-6">
        <Outlet />
      </main>
    </>
  )
}
