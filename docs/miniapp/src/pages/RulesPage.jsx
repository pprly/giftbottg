import { Section, Cell, List } from '@telegram-apps/telegram-ui'
import './RulesPage.css'

function RulesPage({ tg }) {
  return (
    <div className="rules-page">
      <div className="rules-header">
        <h1>📖 Правила</h1>
        <p>Как участвовать в конкурсах</p>
      </div>

      <List>
        <Section header="🎯 Виды конкурсов">
          <Cell 
            subtitle="Голосуйте за участников"
            multiline
          >
            🗳️ Голосовательный
          </Cell>
          <Cell 
            subtitle="Случайный выбор победителя"
            multiline
          >
            🎰 Рандомайзер
          </Cell>
          <Cell 
            subtitle="Больше активности = больше шансов"
            multiline
          >
            ⚡ Спам-конкурс
          </Cell>
        </Section>

        <Section header="👥 Реферальная программа">
          <Cell multiline>
            📤 Делитесь ссылкой с друзьями
          </Cell>
          <Cell multiline>
            ✅ Друг подписывается на канал
          </Cell>
          <Cell multiline>
            🌟 Вы получаете +1 очко
          </Cell>
          <Cell multiline>
            🏆 Участвуйте в реферальных конкурсах
          </Cell>
        </Section>

        <Section header="⭐ Достижения">
          <Cell multiline>
            🎯 Выполняйте задания
          </Cell>
          <Cell multiline>
            🏅 Получайте бейджи
          </Cell>
          <Cell multiline>
            📈 Повышайте свой статус
          </Cell>
        </Section>

        <Section header="❗ Важно">
          <Cell multiline>
            • Нужна подписка на канал
          </Cell>
          <Cell multiline>
            • Один человек = один участник
          </Cell>
          <Cell multiline>
            • Нельзя использовать свою реферальную ссылку
          </Cell>
          <Cell multiline>
            • Результаты публикуются после конкурса
          </Cell>
        </Section>
      </List>

      <div className="rules-footer">
        <p>Есть вопросы? Напишите администратору!</p>
      </div>
    </div>
  )
}

export default RulesPage