import { useState, useEffect } from 'react'
import { Card, Placeholder, Button } from '@telegram-apps/telegram-ui'
import { fetchAchievements } from '../api'
import './AchievementsPage.css'

function AchievementsPage({ user, tg }) {
  const [achievements, setAchievements] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadAchievements()
  }, [user])

  const loadAchievements = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await fetchAchievements()
      setAchievements(data)
    } catch (err) {
      console.error('Ошибка загрузки достижений:', err)
      setError('Не удалось загрузить достижения')
      // Временно показываем mock данные если API не работает
      setAchievements([
        { id: 'newbie', name: 'Новичок', emoji: '🎯', description: 'Участвовать в 5 конкурсах', progress: 0, target: 5, earned: false },
        { id: 'first_win', name: 'Первая победа', emoji: '🏆', description: 'Выиграть первый конкурс', progress: 0, target: 1, earned: false },
        { id: 'recruiter', name: 'Друг', emoji: '👋', description: 'Пригласить 5 друзей', progress: 0, target: 5, earned: false },
      ])
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="achievements-page">
        <Placeholder description="Загрузка достижений...">
          <span style={{ fontSize: '48px' }}>⭐</span>
        </Placeholder>
      </div>
    )
  }

  const earnedCount = achievements.filter(a => a.earned).length

  return (
    <div className="achievements-page">
      <div className="achievements-header">
        <h1>⭐ Достижения</h1>
        <p>Получено: {earnedCount} из {achievements.length}</p>
      </div>

      {error && (
        <div style={{ padding: '16px', textAlign: 'center', color: 'var(--tg-theme-hint-color)' }}>
          <p>{error}</p>
          <Button onClick={loadAchievements} style={{ marginTop: '12px' }}>
            Повторить
          </Button>
        </div>
      )}

      <div className="achievements-grid">
        {achievements.map(achievement => (
          <Card key={achievement.id} className={`achievement-card ${achievement.earned ? 'earned' : 'locked'}`}>
            <div className="achievement-icon">
              {achievement.earned ? achievement.emoji : '🔒'}
            </div>
            <h3 className="achievement-name">{achievement.name}</h3>
            <p className="achievement-description">{achievement.description}</p>
            
            {!achievement.earned && (
              <div className="achievement-progress">
                <div className="progress-bar">
                  <div 
                    className="progress-fill" 
                    style={{ width: `${(achievement.progress / achievement.target) * 100}%` }}
                  />
                </div>
                <span className="progress-text">
                  {achievement.progress} / {achievement.target}
                </span>
              </div>
            )}
            
            {achievement.earned && (
              <div className="achievement-earned">
                ✓ Получено
              </div>
            )}
          </Card>
        ))}
      </div>
    </div>
  )
}

export default AchievementsPage