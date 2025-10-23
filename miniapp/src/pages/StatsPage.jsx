import { useState, useEffect } from 'react'
import { Button, Placeholder, Card } from '@telegram-apps/telegram-ui'
import { fetchUserStats } from '../api'
import './StatsPage.css'

function StatsPage({ user, tg }) {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadStats()
  }, [user])

  const loadStats = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await fetchUserStats()
      setStats(data)
    } catch (err) {
      console.error('Ошибка загрузки статистики:', err)
      setError('Не удалось загрузить статистику')
    } finally {
      setLoading(false)
    }
  }

  const shareReferral = () => {
    if (tg) {
      const botUsername = import.meta.env.VITE_BOT_USERNAME || 'your_bot'
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

  if (error) {
    return (
      <div className="stats-page">
        <Placeholder 
          description={error}
          action={<Button onClick={loadStats}>Повторить</Button>}
        >
          <span style={{ fontSize: '48px' }}>⚠️</span>
        </Placeholder>
      </div>
    )
  }

  return (
    <div className="stats-page">
      {/* Hero секция */}
      <div className="stats-hero">
        <div className="stats-hero-content">
          <h1 className="stats-hero-title">
            Привет, {user?.first_name || 'Пользователь'}! 👋
          </h1>
          <p className="stats-hero-subtitle">
            Твоя статистика в Gift Bot
          </p>
        </div>
      </div>

      {/* Главные метрики */}
      <div className="stats-grid">
        <Card className="stat-card stat-card-primary">
          <div className="stat-icon">🏆</div>
          <div className="stat-value">{stats.totalWins}</div>
          <div className="stat-label">Побед</div>
        </Card>

        <Card className="stat-card stat-card-secondary">
          <div className="stat-icon">🎯</div>
          <div className="stat-value">{stats.totalContests}</div>
          <div className="stat-label">Участий</div>
        </Card>

        <Card className="stat-card stat-card-accent">
          <div className="stat-icon">👥</div>
          <div className="stat-value">{stats.referrals}</div>
          <div className="stat-label">Рефералов</div>
        </Card>

        {stats.bestStreak > 0 && (
          <Card className="stat-card stat-card-fire">
            <div className="stat-icon">🔥</div>
            <div className="stat-value">{stats.bestStreak}</div>
            <div className="stat-label">Лучшая серия</div>
          </Card>
        )}
      </div>

      {/* Детальная статистика побед */}
      {stats.totalWins > 0 && (
        <div className="stats-section">
          <h2 className="section-title">🎖️ Твои победы</h2>
          <Card className="stats-detailed-card">
            <div className="detailed-stat-row">
              <div className="detailed-stat-item">
                <span className="detailed-stat-emoji">🗳️</span>
                <div className="detailed-stat-info">
                  <div className="detailed-stat-label">Голосовательные</div>
                  <div className="detailed-stat-value">{stats.votingWins}</div>
                </div>
              </div>
            </div>
            
            <div className="detailed-stat-divider"></div>
            
            <div className="detailed-stat-row">
              <div className="detailed-stat-item">
                <span className="detailed-stat-emoji">🎰</span>
                <div className="detailed-stat-info">
                  <div className="detailed-stat-label">Рандомайзер</div>
                  <div className="detailed-stat-value">{stats.randomWins}</div>
                </div>
              </div>
            </div>
            
            <div className="detailed-stat-divider"></div>
            
            <div className="detailed-stat-row">
              <div className="detailed-stat-item">
                <span className="detailed-stat-emoji">⚡</span>
                <div className="detailed-stat-info">
                  <div className="detailed-stat-label">Спам-конкурс</div>
                  <div className="detailed-stat-value">{stats.spamWins}</div>
                </div>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Реферальная карточка */}
      <div className="stats-section">
        <Card className="referral-card">
          <div className="referral-card-content">
            <div className="referral-icon">🎁</div>
            <h3 className="referral-title">Пригласи друзей!</h3>
            <p className="referral-description">
              Получай бонусы за каждого приглашённого друга
            </p>
            <Button 
              size="l" 
              stretched 
              onClick={shareReferral}
              className="referral-button"
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

