import { useNavigate, useLocation } from 'react-router-dom'
import { Tabbar } from '@telegram-apps/telegram-ui'
import './Navigation.css'

function Navigation() {
  const navigate = useNavigate()
  const location = useLocation()

  const tabs = [
    { path: '/', icon: '📊', label: 'Статистика' },
    { path: '/leaderboard', icon: '🏆', label: 'Топы' },
    { path: '/achievements', icon: '⭐', label: 'Достижения' },
    { path: '/rules', icon: '📖', label: 'Правила' }
  ]

  return (
    <div className="navigation">
      <Tabbar>
        {tabs.map((tab) => (
          <Tabbar.Item
            key={tab.path}
            text={tab.label}
            selected={location.pathname === tab.path}
            onClick={() => navigate(tab.path)}
          >
            <span style={{ fontSize: '24px' }}>{tab.icon}</span>
          </Tabbar.Item>
        ))}
      </Tabbar>
    </div>
  )
}

export default Navigation