"""
Модуль работы с базой данных SQLite v2.1
Поддержка гибких условий участия и модульной архитектуры
+ спам-конкурсы
"""

import aiosqlite
import json
from typing import Optional, List, Dict, Any
import config


class Database:
    def __init__(self, db_path: str = config.DATABASE_PATH):
        self.db_path = db_path
    
    async def init_db(self):
        """Инициализация базы данных и создание таблиц"""
        async with aiosqlite.connect(self.db_path) as db:
            # Таблица конкурсов
            await db.execute("""
                CREATE TABLE IF NOT EXISTS contests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contest_type TEXT DEFAULT 'voting_contest',
                    status TEXT NOT NULL,
                    prize TEXT,
                    conditions TEXT,
                    entry_conditions TEXT,
                    participants_count INTEGER DEFAULT 10,
                    timer_minutes INTEGER DEFAULT 60,
                    announcement_message_id INTEGER,
                    discussion_message_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ended_at TIMESTAMP
                )
            """)
            
            # Таблица участников
            await db.execute("""
                CREATE TABLE IF NOT EXISTS participants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contest_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    username TEXT,
                    full_name TEXT,
                    comment_text TEXT,
                    position INTEGER,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (contest_id) REFERENCES contests (id)
                )
            """)
            
            # Таблица победителей
            await db.execute("""
                CREATE TABLE IF NOT EXISTS winners (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contest_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    position INTEGER,
                    won_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (contest_id) REFERENCES contests (id)
                )
            """)
            
            # Таблица рефералов
            await db.execute("""
                CREATE TABLE IF NOT EXISTS referrals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    referrer_id INTEGER NOT NULL,
                    referred_id INTEGER NOT NULL,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    subscribed BOOLEAN DEFAULT 0,
                    points_awarded BOOLEAN DEFAULT 0
                )
            """)
            
            # Таблица статистики пользователей
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_stats (
                    user_id INTEGER PRIMARY KEY,
                    total_contests INTEGER DEFAULT 0,
                    total_wins INTEGER DEFAULT 0,
                    referral_points INTEGER DEFAULT 0,
                    voting_wins INTEGER DEFAULT 0,
                    random_wins INTEGER DEFAULT 0,
                    spam_wins INTEGER DEFAULT 0,
                    referral_wins INTEGER DEFAULT 0,
                    activity_wins INTEGER DEFAULT 0,
                    current_win_streak INTEGER DEFAULT 0,
                    best_win_streak INTEGER DEFAULT 0,
                    best_voting_streak INTEGER DEFAULT 0,
                    best_random_streak INTEGER DEFAULT 0,
                    best_spam_streak INTEGER DEFAULT 0,
                    best_referral_streak INTEGER DEFAULT 0,
                    best_activity_streak INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблица достижений
            await db.execute("""
                CREATE TABLE IF NOT EXISTS achievements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    achievement_type TEXT NOT NULL,
                    achievement_level TEXT NOT NULL,
                    unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблица для подсчёта спамов в спам-конкурсах
            await db.execute("""
                CREATE TABLE IF NOT EXISTS spam_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contest_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    spam_count INTEGER DEFAULT 0,
                    FOREIGN KEY (contest_id) REFERENCES contests (id),
                    UNIQUE(contest_id, user_id)
                )
            """)
            
            # Добавляем новую колонку в существующую таблицу (для миграции)
            try:
                await db.execute("""
                    ALTER TABLE contests ADD COLUMN discussion_message_id INTEGER
                """)
                print("✅ Колонка discussion_message_id добавлена")
            except Exception as e:
                # Колонка уже существует, игнорируем ошибку
                pass
            
            # Добавляем spam_wins если ещё нет
            try:
                await db.execute("""
                    ALTER TABLE user_stats ADD COLUMN spam_wins INTEGER DEFAULT 0
                """)
                print("✅ Колонка spam_wins добавлена")
            except Exception as e:
                pass
            
            try:
                await db.execute("""
                    ALTER TABLE user_stats ADD COLUMN best_spam_streak INTEGER DEFAULT 0
                """)
                print("✅ Колонка best_spam_streak добавлена")
            except Exception as e:
                pass
            
            await db.commit()
            print("✅ База данных инициализирована")
    
    # ==================== КОНКУРСЫ ====================
    
    async def create_contest(
        self, 
        prize: str, 
        conditions: str,
        entry_conditions: Dict[str, Any],
        participants_count: int = 10,
        timer_minutes: int = 60,
        contest_type: str = "voting_contest"
    ) -> int:
        """Создание нового конкурса с гибкими условиями"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO contests 
                (contest_type, status, prize, conditions, entry_conditions, participants_count, timer_minutes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                contest_type, 
                "collecting", 
                prize, 
                conditions,
                json.dumps(entry_conditions),  # Сохраняем как JSON
                participants_count, 
                timer_minutes
            ))
            await db.commit()
            print(f"✅ Конкурс создан: ID={cursor.lastrowid}, тип={contest_type}")
            return cursor.lastrowid
    
    async def get_active_contest(self) -> Optional[Dict]:
        """
        Получить активный конкурс (collecting или voting)
        DEPRECATED: Используйте get_active_contests() для нескольких конкурсов
        Оставлено для обратной совместимости - возвращает последний активный
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM contests 
                WHERE status IN ('collecting', 'voting', 'running')
                ORDER BY created_at DESC LIMIT 1
            """) as cursor:
                row = await cursor.fetchone()
                if row:
                    contest = dict(row)
                    # Парсим JSON условия
                    if contest['entry_conditions']:
                        contest['entry_conditions'] = json.loads(contest['entry_conditions'])
                    return contest
                return None
    
    async def get_active_contests(self) -> List[Dict]:
        """Получить ВСЕ активные конкурсы (collecting, voting или running)"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM contests 
                WHERE status IN ('collecting', 'voting', 'running')
                ORDER BY created_at DESC
            """) as cursor:
                rows = await cursor.fetchall()
                contests = []
                for row in rows:
                    contest = dict(row)
                    if contest['entry_conditions']:
                        contest['entry_conditions'] = json.loads(contest['entry_conditions'])
                    contests.append(contest)
                return contests
    
    async def get_contest_by_announcement_id(self, message_id: int) -> Optional[Dict]:
        """Найти конкурс по ID сообщения-анонса в канале"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM contests 
                WHERE announcement_message_id = ?
            """, (message_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    contest = dict(row)
                    if contest['entry_conditions']:
                        contest['entry_conditions'] = json.loads(contest['entry_conditions'])
                    return contest
                return None
    
    async def get_contest_by_discussion_id(self, message_id: int) -> Optional[Dict]:
        """Найти конкурс по ID сообщения в группе обсуждений"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM contests 
                WHERE discussion_message_id = ?
            """, (message_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    contest = dict(row)
                    if contest['entry_conditions']:
                        contest['entry_conditions'] = json.loads(contest['entry_conditions'])
                    return contest
                return None
    
    async def get_contest_by_id(self, contest_id: int) -> Optional[Dict]:
        """Получить конкурс по ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM contests WHERE id = ?
            """, (contest_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    contest = dict(row)
                    if contest['entry_conditions']:
                        contest['entry_conditions'] = json.loads(contest['entry_conditions'])
                    return contest
                return None
    
    async def get_last_ended_contest(self) -> Optional[Dict]:
        """Получить последний завершённый конкурс"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM contests 
                WHERE status = 'ended'
                ORDER BY ended_at DESC LIMIT 1
            """) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    
    async def update_contest_status(self, contest_id: int, status: str):
        """Обновить статус конкурса"""
        async with aiosqlite.connect(self.db_path) as db:
            if status == 'ended':
                await db.execute("""
                    UPDATE contests 
                    SET status = ?, ended_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                """, (status, contest_id))
            else:
                await db.execute("""
                    UPDATE contests SET status = ? WHERE id = ?
                """, (status, contest_id))
            await db.commit()
            print(f"✅ Статус конкурса {contest_id} изменён на '{status}'")
    
    async def set_announcement_message(self, contest_id: int, message_id: int):
        """Сохранить ID сообщения-анонса в канале"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE contests SET announcement_message_id = ? WHERE id = ?
            """, (message_id, contest_id))
            await db.commit()
    
    async def set_discussion_message(self, contest_id: int, message_id: int):
        """Сохранить ID сообщения в группе обсуждений"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE contests SET discussion_message_id = ? WHERE id = ?
            """, (message_id, contest_id))
            await db.commit()
    
    # ==================== УЧАСТНИКИ ====================
    
    async def add_participant(
        self, 
        contest_id: int, 
        user_id: int,
        username: str, 
        full_name: str,
        emoji: str
    ) -> bool:
        """Добавить участника в конкурс"""
        async with aiosqlite.connect(self.db_path) as db:
            # Проверяем, не участвует ли уже этот пользователь
            async with db.execute("""
                SELECT id FROM participants 
                WHERE contest_id = ? AND user_id = ?
            """, (contest_id, user_id)) as cursor:
                if await cursor.fetchone():
                    return False
            
            # Получаем текущее количество участников
            async with db.execute("""
                SELECT COUNT(*) as count FROM participants WHERE contest_id = ?
            """, (contest_id,)) as cursor:
                row = await cursor.fetchone()
                position = row[0] + 1
            
            # Добавляем участника
            await db.execute("""
                INSERT INTO participants 
                (contest_id, user_id, username, full_name, comment_text, position)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (contest_id, user_id, username, full_name, emoji, position))
            await db.commit()
            return True
    
    async def get_participants(self, contest_id: int) -> List[Dict]:
        """Получить всех участников конкурса"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM participants 
                WHERE contest_id = ?
                ORDER BY position
            """, (contest_id,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def get_participants_count(self, contest_id: int) -> int:
        """Получить количество участников"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT COUNT(*) FROM participants WHERE contest_id = ?
            """, (contest_id,)) as cursor:
                row = await cursor.fetchone()
                return row[0]
    
    async def get_participant_by_position(self, contest_id: int, position: int) -> Optional[Dict]:
        """Получить участника по его номеру"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM participants 
                WHERE contest_id = ? AND position = ?
            """, (contest_id, position)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    
    # ==================== ПОБЕДИТЕЛИ ====================
    
    async def set_contest_winner(self, contest_id: int, user_id: int):
        """Сохранить победителя конкурса"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO winners (contest_id, user_id, position)
                VALUES (?, ?, 1)
            """, (contest_id, user_id))
            await db.commit()
            print(f"💾 Победитель сохранён: user_id={user_id}")
    
    async def get_last_winners_by_type(self, contest_type: str) -> list:
        """Получить список победителей последнего конкурса определённого типа"""
        async with aiosqlite.connect(self.db_path) as db:
            # Находим ID последнего завершённого конкурса этого типа
            async with db.execute("""
                SELECT id FROM contests 
                WHERE contest_type = ? AND status = 'ended'
                ORDER BY ended_at DESC LIMIT 1
            """, (contest_type,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return []
                last_contest_id = row[0]
            
            # Получаем всех победителей этого конкурса
            async with db.execute("""
                SELECT user_id FROM winners 
                WHERE contest_id = ?
            """, (last_contest_id,)) as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]
    
    # ==================== РЕФЕРАЛЬНАЯ СИСТЕМА ====================
    
    async def add_referral(self, referrer_id: int, referred_id: int) -> bool:
        """Добавить реферала"""
        async with aiosqlite.connect(self.db_path) as db:
            # Проверяем, не был ли уже добавлен этот реферал
            async with db.execute("""
                SELECT id FROM referrals 
                WHERE referrer_id = ? AND referred_id = ?
            """, (referrer_id, referred_id)) as cursor:
                if await cursor.fetchone():
                    return False
            
            await db.execute("""
                INSERT INTO referrals (referrer_id, referred_id)
                VALUES (?, ?)
            """, (referrer_id, referred_id))
            await db.commit()
            return True
    
    async def mark_referral_subscribed(self, referrer_id: int, referred_id: int) -> bool:
        """Отметить что реферал подписался и начислить очки"""
        async with aiosqlite.connect(self.db_path) as db:
            # Обновляем статус подписки
            await db.execute("""
                UPDATE referrals 
                SET subscribed = 1, points_awarded = 1
                WHERE referrer_id = ? AND referred_id = ? AND points_awarded = 0
            """, (referrer_id, referred_id))
            
            # Начисляем очко рефереру
            await db.execute("""
                INSERT INTO user_stats (user_id, referral_points)
                VALUES (?, 1)
                ON CONFLICT(user_id) DO UPDATE SET
                    referral_points = referral_points + 1,
                    updated_at = CURRENT_TIMESTAMP
            """, (referrer_id,))
            
            await db.commit()
            return True
    
    async def get_referral_count(self, user_id: int) -> int:
        """Получить количество успешных рефералов"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT COUNT(*) FROM referrals 
                WHERE referrer_id = ? AND subscribed = 1
            """, (user_id,)) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0
    
    async def check_referral_exists(self, referred_id: int) -> Optional[int]:
        """Проверить был ли пользователь приглашён кем-то"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT referrer_id FROM referrals 
                WHERE referred_id = ?
            """, (referred_id,)) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else None
    
    # ==================== СТАТИСТИКА ПОЛЬЗОВАТЕЛЕЙ ====================
    
    async def get_user_stats(self, user_id: int) -> Dict:
        """Получить статистику пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Создаём запись если её нет
            await db.execute("""
                INSERT OR IGNORE INTO user_stats (user_id)
                VALUES (?)
            """, (user_id,))
            await db.commit()
            
            # Получаем статистику
            async with db.execute("""
                SELECT * FROM user_stats WHERE user_id = ?
            """, (user_id,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return {
                        'user_id': user_id,
                        'total_contests': 0,
                        'total_wins': 0,
                        'referral_points': 0
                    }
                return dict(row)
    
    async def increment_user_contests(self, user_id: int):
        """Увеличить счётчик участий в конкурсах"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO user_stats (user_id, total_contests)
                VALUES (?, 1)
                ON CONFLICT(user_id) DO UPDATE SET
                    total_contests = total_contests + 1,
                    updated_at = CURRENT_TIMESTAMP
            """, (user_id,))
            await db.commit()
    
    async def increment_user_wins(self, user_id: int, contest_type: str = "voting_contest"):
        """Увеличить счётчик побед"""
        async with aiosqlite.connect(self.db_path) as db:
            # Определяем какой счётчик увеличивать
            type_field = f"{contest_type.replace('_contest', '')}_wins"
            
            await db.execute(f"""
                INSERT INTO user_stats (user_id, total_wins, {type_field})
                VALUES (?, 1, 1)
                ON CONFLICT(user_id) DO UPDATE SET
                    total_wins = total_wins + 1,
                    {type_field} = {type_field} + 1,
                    updated_at = CURRENT_TIMESTAMP
            """, (user_id,))
            await db.commit()
    
    # ==================== ДОСТИЖЕНИЯ ====================
    
    async def check_and_unlock_achievement(self, user_id: int, achievement_type: str, achievement_level: str) -> bool:
        """
        Проверить и разблокировать достижение
        
        Returns:
            True если достижение только что разблокировано (новое)
        """
        async with aiosqlite.connect(self.db_path) as db:
            # Проверяем есть ли уже это достижение
            async with db.execute("""
                SELECT id FROM achievements 
                WHERE user_id = ? AND achievement_type = ? AND achievement_level = ?
            """, (user_id, achievement_type, achievement_level)) as cursor:
                if await cursor.fetchone():
                    return False  # Уже есть
            
            # Добавляем новое достижение
            await db.execute("""
                INSERT INTO achievements (user_id, achievement_type, achievement_level)
                VALUES (?, ?, ?)
            """, (user_id, achievement_type, achievement_level))
            await db.commit()
            return True  # Новое достижение!
    
    async def get_user_achievements(self, user_id: int) -> List[Dict]:
        """Получить все достижения пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM achievements 
                WHERE user_id = ?
                ORDER BY unlocked_at DESC
            """, (user_id,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def has_achievement(self, user_id: int, achievement_type: str, achievement_level: str) -> bool:
        """Проверить наличие конкретного достижения"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT id FROM achievements 
                WHERE user_id = ? AND achievement_type = ? AND achievement_level = ?
            """, (user_id, achievement_type, achievement_level)) as cursor:
                return await cursor.fetchone() is not None
    
    # ==================== ЛИДЕРБОРДЫ ====================
    
    async def get_top_by_referrals(self, limit: int = 10) -> List[Dict]:
        """Получить ТОП по рефералам"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT user_id, referral_points
                FROM user_stats
                WHERE referral_points > 0
                ORDER BY referral_points DESC
                LIMIT ?
            """, (limit,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def get_top_by_wins(self, limit: int = 10) -> List[Dict]:
        """Получить ТОП по победам"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT user_id, total_wins
                FROM user_stats
                WHERE total_wins > 0
                ORDER BY total_wins DESC
                LIMIT ?
            """, (limit,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def get_top_by_contests(self, limit: int = 10) -> List[Dict]:
        """Получить ТОП по активности (участиям)"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT user_id, total_contests
                FROM user_stats
                WHERE total_contests > 0
                ORDER BY total_contests DESC
                LIMIT ?
            """, (limit,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def get_user_position(self, user_id: int, category: str) -> tuple[int, int]:
        """
        Получить позицию пользователя в рейтинге
        
        Args:
            user_id: ID пользователя
            category: 'referrals', 'wins', 'contests'
        
        Returns:
            tuple (position, total_count): позиция и общее количество участников
        """
        field_map = {
            'referrals': 'referral_points',
            'wins': 'total_wins',
            'contests': 'total_contests'
        }
        
        field = field_map.get(category, 'referral_points')
        
        async with aiosqlite.connect(self.db_path) as db:
            # Получаем значение пользователя
            async with db.execute(f"""
                SELECT {field} FROM user_stats WHERE user_id = ?
            """, (user_id,)) as cursor:
                row = await cursor.fetchone()
                if not row or row[0] == 0:
                    return (0, 0)
                user_value = row[0]
            
            # Считаем сколько людей лучше
            async with db.execute(f"""
                SELECT COUNT(*) FROM user_stats 
                WHERE {field} > ?
            """, (user_value,)) as cursor:
                row = await cursor.fetchone()
                position = row[0] + 1
            
            # Считаем общее количество
            async with db.execute(f"""
                SELECT COUNT(*) FROM user_stats 
                WHERE {field} > 0
            """, ()) as cursor:
                row = await cursor.fetchone()
                total = row[0]
            
            return (position, total)
    
    # ==================== СПАМ-КОНКУРС ====================
    
    async def init_spam_participant(self, contest_id: int, user_id: int):
        """Инициализировать участника спам-конкурса"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR IGNORE INTO spam_messages (contest_id, user_id, spam_count)
                VALUES (?, ?, 0)
            """, (contest_id, user_id))
            await db.commit()
    
    async def increment_spam_count(self, contest_id: int, user_id: int):
        """Увеличить счётчик спамов на 1"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO spam_messages (contest_id, user_id, spam_count)
                VALUES (?, ?, 1)
                ON CONFLICT(contest_id, user_id) DO UPDATE SET
                    spam_count = spam_count + 1
            """, (contest_id, user_id))
            await db.commit()
    
    async def get_spam_leaderboard(self, contest_id: int) -> List[Dict]:
        """Получить таблицу лидеров спам-конкурса"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT 
                    sm.user_id,
                    sm.spam_count,
                    p.username,
                    p.full_name,
                    p.comment_text,
                    p.position
                FROM spam_messages sm
                JOIN participants p ON sm.user_id = p.user_id AND sm.contest_id = p.contest_id
                WHERE sm.contest_id = ?
                ORDER BY sm.spam_count DESC, p.position ASC
            """, (contest_id,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def get_spam_count(self, contest_id: int, user_id: int) -> int:
        """Получить количество спамов конкретного участника"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT spam_count FROM spam_messages
                WHERE contest_id = ? AND user_id = ?
            """, (contest_id, user_id)) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0
    
    async def get_spam_winner(self, contest_id: int) -> Optional[Dict]:
        """Получить победителя спам-конкурса (у кого больше всего спамов)"""
        leaderboard = await self.get_spam_leaderboard(contest_id)
        return leaderboard[0] if leaderboard else None


# Глобальный экземпляр БД
db = Database()