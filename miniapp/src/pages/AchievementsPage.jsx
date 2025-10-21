import { useState, useEffect } from 'react'
import { Card } from '@telegram-apps/telegram-ui'
import './AchievementsPage.css'

function AchievementsPage({ user, tg }) {
  const [achievements, setAchievements] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchAchievements()
  }, [user])

  const fetchAchievements = async () => {
    try {
      // TODO: Запрос к API бота
      // Mock данные
      const mockAchievements = [
        { id: 1, name: 'Новичок', emoji: '🎯', description: 'Участвовать в 5 конкурсах', progress: 5, target: 5, earned: true },
        { id: 2, name: 'Везунчик', emoji: '🍀', description: 'Выиграть 5 раз', progress: 3, target: 5, earned: false },
        { id: 3, name: 'Друг', emoji: '👋', description: 'Пригласить 5 друзей', progress: 5, target: 5, earned: true },
        { id: 4, name: 'Популярный', emoji: '🌟', description: 'Пригласить 25 друзей', progress: 5, target: 25, earned: false },
        { id: 5, name: 'Серия побед', emoji: '🔥', description: 'Выиграть 3 раза подряд', progress: 2, target: 3, earned: false },
        { id: 6, name: 'Продвинутый', emoji: '⭐', description: 'Участвовать в 50 конкурсах', progress: 12, target: 50, earned: false }
      ]

      setTimeout(() => {
        setAchievements(mockAchievements)
        setLoading(false)
      }, 300)
    } catch (error) {
      console.error('Ошибка загрузки достижений:', error)
      setLoading(false)
    }
  }

  const earnedCount = achievements.filter(a => a.earned).length

  return (
    <div className="achievements-page">
      <div className="achievements-header">
        <h1>⭐ Достижения</h1>
        <p>Получено: {earnedCount} из {achievements.length}</p>
      </div>

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