import { useState, useEffect } from 'react'
import { List, Cell, Section, Placeholder, SegmentedControl } from '@telegram-apps/telegram-ui'
import './LeaderboardPage.css'

function LeaderboardPage({ tg }) {
  const [activeTab, setActiveTab] = useState('wins')
  const [leaders, setLeaders] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchLeaders(activeTab)
  }, [activeTab])

  const fetchLeaders = async (type) => {
    setLoading(true)
    try {
      // TODO: Запрос к API бота
      // Пока mock данные
      const mockData = {
        wins: [
          { id: 1, name: 'Алексей', value: 15, avatar: '👑' },
          { id: 2, name: 'Мария', value: 12, avatar: '🥈' },
          { id: 3, name: 'Дмитрий', value: 10, avatar: '🥉' },
          { id: 4, name: 'Анна', value: 8, avatar: '👤' },
          { id: 5, name: 'Иван', value: 7, avatar: '👤' }
        ],
        referrals: [
          { id: 1, name: 'Елена', value: 25, avatar: '👑' },
          { id: 2, name: 'Петр', value: 18, avatar: '🥈' },
          { id: 3, name: 'Ольга', value: 15, avatar: '🥉' },
          { id: 4, name: 'Сергей', value: 12, avatar: '👤' },
          { id: 5, name: 'Наталья', value: 10, avatar: '👤' }
        ],
        contests: [
          { id: 1, name: 'Владимир', value: 45, avatar: '👑' },
          { id: 2, name: 'Татьяна', value: 38, avatar: '🥈' },
          { id: 3, name: 'Андрей', value: 32, avatar: '🥉' },
          { id: 4, name: 'Юлия', value: 28, avatar: '👤' },
          { id: 5, name: 'Максим', value: 25, avatar: '👤' }
        ]
      }

      setTimeout(() => {
        setLeaders(mockData[type] || [])
        setLoading(false)
      }, 300)
    } catch (error) {
      console.error('Ошибка загрузки топа:', error)
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