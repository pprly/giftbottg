import { useEffect, useState } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { AppRoot } from '@telegram-apps/telegram-ui'

// Импорт страниц (создадим их дальше)
import StatsPage from './pages/StatsPage'
import LeaderboardPage from './pages/LeaderboardPage'
import AchievementsPage from './pages/AchievementsPage'
import RulesPage from './pages/RulesPage'
import Navigation from './components/Navigation'

function App() {
  const [tg, setTg] = useState(null)
  const [user, setUser] = useState(null)

  useEffect(() => {
    // Инициализация Telegram WebApp
    const app = window.Telegram?.WebApp
    if (app) {
      app.ready()
      app.expand()
      app.enableClosingConfirmation() // Подтверждение при закрытии
      
      setTg(app)
      setUser(app.initDataUnsafe?.user)

      // Применяем тему Telegram
      document.documentElement.style.setProperty('--tg-viewport-height', `${app.viewportHeight}px`)
    }
  }, [])

  if (!tg) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        background: 'var(--tg-theme-bg-color)'
      }}>
        <p style={{ color: 'var(--tg-theme-text-color)' }}>Загрузка...</p>
      </div>
    )
  }

  return (
    <AppRoot>
      <Router>
        <div style={{ paddingBottom: '70px' }}>
          <Routes>
            <Route path="/" element={<StatsPage user={user} tg={tg} />} />
            <Route path="/leaderboard" element={<LeaderboardPage tg={tg} />} />
            <Route path="/achievements" element={<AchievementsPage user={user} tg={tg} />} />
            <Route path="/rules" element={<RulesPage tg={tg} />} />
          </Routes>
        </div>
        <Navigation />
      </Router>
    </AppRoot>
  )
}

export default App