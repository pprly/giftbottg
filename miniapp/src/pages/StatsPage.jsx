import { useState, useEffect } from 'react'
import { Card, List, Cell, Section, Button, Placeholder } from '@telegram-apps/telegram-ui'
import './StatsPage.css'

function StatsPage({ user, tg }) {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Получаем статистику пользователя из бота
    fetchStats()
  }, [user])

  const fetchStats = async () => {
    try {
      // TODO: Здесь будет запрос к твоему боту через API
      // Пока используем mock данные
      const mockStats = {
        referrals: 5,
        totalContests: 12,
        totalWins: 3,
        votingWins: 1,
        randomWins: 1,
        spamWins: 1,
        bestStreak: 2
      }
      
      // Симуляция загрузки
      setTimeout(() => {
        setStats(mockStats)
        setLoading(false)
      }, 500)
    } catch (error) {
      console.error('Ошибка загрузки статистики:', error)
      setLoading(false)
    }
  }

  const shareReferral = () => {
    // Открываем реферальную систему через бота
    if (tg) {
      const botUsername = 'твой_бот' // Из .env потом возьмем
      const referralLink = `https://t.me/${botUsername}?start=ref_${user?.id}`
      
      tg.openTelegramLink(`https://t.me/share/url?url=${encodeURIComponent(referralLink)}&text=${encodeURIComponent('Присоединяйся к конкурсам! 🎁')}`)
    }
  }

  if (loading) {
    return (
      <div className="stats-page">
        <Placeholder description="Загрузка статистики...">
          <span style={{ fontSize: '48px' }}>📊</span>
        </Placeholder>
      </div>
    )
  }

  return (
    <div className="stats-page">
      <div className="stats-header">
        <h1>Привет, {user?.first_name || 'Пользователь'}! 👋</h1>
        <p>Твоя статистика в боте</p>
      </div>

      <List>
        <Section header="📈 Основная статистика">
          <Cell 
            subtitle="Рефералов"
            after={<span className="stat-value">{stats.referrals}</span>}
          >
            👥 Приглашено друзей
          </Cell>
          <Cell 
            subtitle="Участий в конкурсах"
            after={<span className="stat-value">{stats.totalContests}</span>}
          >
            🎯 Участие
          </Cell>
          <Cell 
            subtitle="Побед"
            after={<span className="stat-value highlight">{stats.totalWins}</span>}
          >
            🏆 Победы
          </Cell>
        </Section>

        {stats.totalWins > 0 && (
          <Section header="🎖️ Победы по типам">
            <Cell after={stats.votingWins}>🗳️ Голосовательные</Cell>
            <Cell after={stats.randomWins}>🎰 Рандомайзер</Cell>
            <Cell after={stats.spamWins}>⚡ Спам-конкурс</Cell>
          </Section>
        )}

        {stats.bestStreak > 0 && (
          <Section header="🔥 Достижения">
            <Cell after={stats.bestStreak}>
              Лучшая серия побед
            </Cell>
          </Section>
        )}
      </List>

      <div className="stats-actions">
        <Card>
          <div style={{ padding: '16px' }}>
            <h3 style={{ marginBottom: '8px' }}>💡 Пригласи друзей!</h3>
            <p style={{ fontSize: '14px', opacity: 0.7, marginBottom: '12px' }}>
              Получай бонусы за каждого друга
            </p>
            <Button 
              size="l" 
              stretched 
              onClick={shareReferral}
            >
              📤 Поделиться ссылкой
            </Button>
          </div>
        </Card>
      </div>
    </div>
  )
}

export default StatsPage