import { useState, useEffect } from 'react'
import { List, Cell, Section, Placeholder, SegmentedControl } from '@telegram-apps/telegram-ui'
import { fetchLeaderboard } from '../api'
import './LeaderboardPage.css'

function LeaderboardPage({ tg }) {
  const [activeTab, setActiveTab] = useState('wins')
  const [leaders, setLeaders] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchLeaders(activeTab)
  }, [activeTab])

  const fetchLeaders = async (type) => {
    setLoading(true)
    setError(null)
    try {
      // Получаем данные с API
      const apiLeaders = await fetchLeaderboard(type)
      
      // Форматируем для отображения
      const formatted = apiLeaders.map((leader, index) => ({
        id: leader.userId,
        name: leader.fullName || leader.username || `User ${leader.userId}`,
        value: leader.score,
        avatar: index === 0 ? '👑' : index === 1 ? '🥈' : index === 2 ? '🥉' : '👤'
      }))
      
      setLeaders(formatted)
    } catch (error) {
      console.error('Ошибка загрузки топа:', error)
      setError('Не удалось загрузить топ')
      setLeaders([])
    } finally {
      setLoading(false)
    }
  }

  const getRankEmoji = (index) => {
    if (index === 0) return '🥇'
    if (index === 1) return '🥈'
    if (index === 2) return '🥉'
    return `#${index + 1}`
  }

  const tabs = [
    { id: 'wins', label: '🏆 Победы' },
    { id: 'referrals', label: '👥 Рефералы' },
    { id: 'contests', label: '🎯 Участие' }
  ]

  if (loading) {
    return (
      <div className="leaderboard-page">
        <Placeholder description="Загрузка топа...">
          <span style={{ fontSize: '48px' }}>🏆</span>
        </Placeholder>
      </div>
    )
  }

  if (error) {
    return (
      <div className="leaderboard-page">
        <Placeholder description={error}>
          <span style={{ fontSize: '48px' }}>⚠️</span>
        </Placeholder>
      </div>
    )
  }

  if (leaders.length === 0) {
    return (
      <div className="leaderboard-page">
        <div className="leaderboard-header">
          <h1>🏆 Топ игроков</h1>
          <p>Лучшие участники сообщества</p>
        </div>

        <div className="leaderboard-tabs">
          <SegmentedControl>
            {tabs.map(tab => (
              <SegmentedControl.Item
                key={tab.id}
                selected={activeTab === tab.id}
                onClick={() => setActiveTab(tab.id)}
              >
                {tab.label}
              </SegmentedControl.Item>
            ))}
          </SegmentedControl>
        </div>

        <Placeholder description="Пока нет данных">
          <span style={{ fontSize: '48px' }}>📊</span>
        </Placeholder>
      </div>
    )
  }

  return (
    <div className="leaderboard-page">
      <div className="leaderboard-header">
        <h1>🏆 Топ игроков</h1>
        <p>Лучшие участники сообщества</p>
      </div>

      <div className="leaderboard-tabs">
        <SegmentedControl>
          {tabs.map(tab => (
            <SegmentedControl.Item
              key={tab.id}
              selected={activeTab === tab.id}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
            </SegmentedControl.Item>
          ))}
        </SegmentedControl>
      </div>

      <List>
        <Section>
          {leaders.map((user, index) => (
            <Cell
              key={user.id}
              before={
                <div className="rank-badge">
                  <span className={`rank rank-${index + 1}`}>
                    {getRankEmoji(index)}
                  </span>
                </div>
              }
              after={
                <span className="leader-value">{user.value}</span>
              }
              subtitle={`Позиция ${index + 1}`}
            >
              {user.name}
            </Cell>
          ))}
        </Section>
      </List>
    </div>
  )
}

export default LeaderboardPage