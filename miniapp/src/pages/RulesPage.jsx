import { Section, Cell, List, Card } from '@telegram-apps/telegram-ui'
import './RulesPage.css'

function RulesPage({ tg }) {
  return (
    <div className="rules-page">
      <div className="rules-header">
        <h1>📖 Правила</h1>
        <p>Полное руководство по участию в конкурсах</p>
      </div>

      <List>
        <Section header="🎯 Как участвовать">
          <Cell 
            subtitle="Обязательное требование для участия"
            multiline
          >
            1. Подпишитесь на канал
          </Cell>
          <Cell 
            subtitle="Напишите комментарий под постом конкурса"
            multiline
          >
            2. Оставьте комментарий
          </Cell>
          <Cell 
            subtitle="Бот автоматически зарегистрирует вас"
            multiline
          >
            3. Ожидайте результатов
          </Cell>
        </Section>

        <Section header="🎲 Виды конкурсов">
          <Cell 
            subtitle="Администратор выбирает победителя из участников. Может выбрать сразу нескольких победителей."
            multiline
          >
            🗳️ Голосовательный
          </Cell>
          <Cell 
            subtitle="Победитель выбирается случайным образом среди всех участников. Все имеют равные шансы."
            multiline
          >
            🎰 Рандомайзер
          </Cell>
          <Cell 
            subtitle="Победитель определяется по количеству сообщений в обсуждении. Больше активности = больше шансов выиграть."
            multiline
          >
            ⚡ Спам-конкурс
          </Cell>
        </Section>

        <Section header="👥 Условия участия">
          <Cell 
            subtitle="Только первые N человек, написавших комментарий"
            multiline
          >
            🏃 Первые N участников
          </Cell>
          <Cell 
            subtitle="Участвуют все, кто оставил комментарий"
            multiline
          >
            ♾️ Без ограничений
          </Cell>
          <Cell 
            subtitle="Только пользователи, которые привели рефералов"
            multiline
          >
            🌟 Только с рефералами
          </Cell>
        </Section>

        <Section header="🎁 Реферальная программа">
          <Cell 
            subtitle="Отправьте свою реферальную ссылку друзьям"
            multiline
          >
            📤 Пригласите друзей
          </Cell>
          <Cell 
            subtitle="Друг должен подписаться на канал"
            multiline
          >
            ✅ Друг подписывается
          </Cell>
          <Cell 
            subtitle="После подписки вам начисляется +1 реферал"
            multiline
          >
            🌟 Получите бонус
          </Cell>
          <Cell 
            subtitle="Участвуйте в специальных конкурсах для активных рефероводов"
            multiline
          >
            🏆 Участвуйте в конкурсах
          </Cell>
        </Section>

        <Section header="⭐ Достижения">
          <Cell 
            subtitle="За участие в конкурсах, победы и рефералов"
            multiline
          >
            🎯 Выполняйте задания
          </Cell>
          <Cell 
            subtitle="Собирайте уникальные бейджи за достижения"
            multiline
          >
            🏅 Получайте награды
          </Cell>
          <Cell 
            subtitle="Растите в рейтинге и получайте преимущества"
            multiline
          >
            📈 Повышайте статус
          </Cell>
        </Section>

        <Section header="📊 Статистика">
          <Cell multiline>
            📈 Отслеживайте свой прогресс в боте
          </Cell>
          <Cell multiline>
            🏆 Смотрите количество побед и участий
          </Cell>
          <Cell multiline>
            👥 Проверяйте количество приглашённых друзей
          </Cell>
          <Cell multiline>
            🔥 Следите за серией побед
          </Cell>
        </Section>

        <Section header="⚠️ Важные правила">
          <Cell 
            subtitle="Без подписки участие невозможно"
            multiline
          >
            ✅ Обязательная подписка
          </Cell>
          <Cell 
            subtitle="Использование мультиаккаунтов запрещено"
            multiline
          >
            👤 Один человек = один аккаунт
          </Cell>
          <Cell 
            subtitle="Это не считается рефералом"
            multiline
          >
            🚫 Нельзя приглашать себя
          </Cell>
          <Cell 
            subtitle="Объявляются в канале после завершения"
            multiline
          >
            📢 Результаты публикуются
          </Cell>
          <Cell 
            subtitle="Администратор имеет право отклонить участие"
            multiline
          >
            ⚖️ Модерация конкурсов
          </Cell>
        </Section>

        <Section header="❌ Запрещено">
          <Cell 
            subtitle="Ботов, накрутку, фейковые аккаунты"
            multiline
          >
            🤖 Использование автоматизации
          </Cell>
          <Cell 
            subtitle="Оскорбления, спам, реклама в обсуждениях"
            multiline
          >
            💬 Нарушение правил общения
          </Cell>
          <Cell 
            subtitle="Попытка обмана системы или администрации"
            multiline
          >
            ⚠️ Мошенничество
          </Cell>
        </Section>

        <Section header="🎖️ Преимущества активных участников">
          <Cell multiline>
            🌟 Приоритет в некоторых конкурсах
          </Cell>
          <Cell multiline>
            🎁 Специальные бонусы и призы
          </Cell>
          <Cell multiline>
            👑 Статус в сообществе
          </Cell>
          <Cell multiline>
            📊 Место в топе рейтинга
          </Cell>
        </Section>
      </List>

      <Card style={{ margin: '16px 0', padding: '16px' }}>
        <h3 style={{ fontSize: '16px', marginBottom: '8px', color: 'var(--tg-theme-text-color)' }}>
          💡 Совет
        </h3>
        <p style={{ fontSize: '14px', color: 'var(--tg-theme-hint-color)', lineHeight: '1.5' }}>
          Приглашайте друзей, активно участвуйте в конкурсах и следите за своей статистикой, 
          чтобы повысить шансы на победу и получить больше достижений!
        </p>
      </Card>

      <div className="rules-footer">
        <p>Есть вопросы? Напишите администратору!</p>
        <p style={{ marginTop: '8px', fontSize: '12px' }}>
          Администрация оставляет за собой право изменять правила
        </p>
      </div>
    </div>
  )
}

export default RulesPage