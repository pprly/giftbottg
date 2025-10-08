"""
PostgreSQL база данных для Contest Bot v2.4
Замена SQLite для улучшения производительности
"""

import asyncpg
import json
from datetime import datetime
from typing import Optional, Dict, List, Any


class DatabasePostgres:
    def __init__(self, dsn: str):
        """
        dsn - строка подключения
        Пример: postgresql://user:password@localhost/contest_bot
        """
        self.dsn = dsn
        self.pool = None
    
    async def init_pool(self):
        """Создание пула соединений"""
        self.pool = await asyncpg.create_pool(
            self.dsn, 
            min_size=5, 
            max_size=20,
            command_timeout=60
        )
        print("✅ PostgreSQL пул соединений создан")
    
    async def close_pool(self):
        """Закрытие пула"""
        if self.pool:
            await self.pool.close()
            print("✅ PostgreSQL пул закрыт")
    
    async def init_db(self):
        """Создание всех таблиц с индексами"""
        async with self.pool.acquire() as conn:
            # Таблица contests
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS contests (
                    id SERIAL PRIMARY KEY,
                    contest_type VARCHAR(50) DEFAULT 'voting_contest',
                    status VARCHAR(20) NOT NULL,
                    prize TEXT,
                    conditions TEXT,
                    entry_conditions JSONB,
                    participants_count INTEGER DEFAULT 10,
                    timer_minutes INTEGER DEFAULT 60,
                    announcement_message_id BIGINT,
                    discussion_message_id BIGINT,
                    created_at TIMESTAMP DEFAULT NOW(),
                    ended_at TIMESTAMP
                )
            ''')
            
            # Индексы для contests
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_contests_status ON contests(status)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_contests_type ON contests(contest_type)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_contests_created ON contests(created_at DESC)')
            
            # Таблица participants
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS participants (
                    id SERIAL PRIMARY KEY,
                    contest_id INTEGER REFERENCES contests(id) ON DELETE CASCADE,
                    user_id BIGINT NOT NULL,
                    username VARCHAR(100),
                    full_name VARCHAR(200),
                    comment_text TEXT,
                    position INTEGER,
                    added_at TIMESTAMP DEFAULT NOW()
                )
            ''')
            
            # Индексы для participants
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_participants_contest ON participants(contest_id)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_participants_user ON participants(user_id)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_participants_position ON participants(contest_id, position)')
            
            # Таблица winners
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS winners (
                    id SERIAL PRIMARY KEY,
                    contest_id INTEGER REFERENCES contests(id) ON DELETE CASCADE,
                    user_id BIGINT NOT NULL,
                    position INTEGER,
                    won_at TIMESTAMP DEFAULT NOW()
                )
            ''')
            
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_winners_user ON winners(user_id)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_winners_contest ON winners(contest_id)')
            
            # Таблица referrals
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS referrals (
                    id SERIAL PRIMARY KEY,
                    referrer_id BIGINT NOT NULL,
                    referred_id BIGINT NOT NULL,
                    joined_at TIMESTAMP DEFAULT NOW(),
                    subscribed BOOLEAN DEFAULT FALSE,
                    points_awarded BOOLEAN DEFAULT FALSE,
                    UNIQUE(referrer_id, referred_id)
                )
            ''')
            
            # Индексы для referrals
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_referrals_referrer ON referrals(referrer_id)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_referrals_referred ON referrals(referred_id)')
            
            # Таблица user_stats
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS user_stats (
                    user_id BIGINT PRIMARY KEY,
                    total_contests INTEGER DEFAULT 0,
                    total_wins INTEGER DEFAULT 0,
                    referral_points INTEGER DEFAULT 0,
                    voting_wins INTEGER DEFAULT 0,
                    random_wins INTEGER DEFAULT 0,
                    spam_wins INTEGER DEFAULT 0,
                    current_win_streak INTEGER DEFAULT 0,
                    best_win_streak INTEGER DEFAULT 0,
                    best_voting_streak INTEGER DEFAULT 0,
                    best_random_streak INTEGER DEFAULT 0,
                    best_spam_streak INTEGER DEFAULT 0,
                    best_referral_streak INTEGER DEFAULT 0,
                    best_activity_streak INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            ''')
            
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_user_stats_total_wins ON user_stats(total_wins DESC)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_user_stats_referrals ON user_stats(referral_points DESC)')
            
            # Таблица achievements
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS achievements (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    achievement_type VARCHAR(50) NOT NULL,
                    achievement_level VARCHAR(50) NOT NULL,
                    unlocked_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(user_id, achievement_type, achievement_level)
                )
            ''')
            
            # Индексы для achievements
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_achievements_user ON achievements(user_id)')
            
            # Таблица spam_messages
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS spam_messages (
                    id SERIAL PRIMARY KEY,
                    contest_id INTEGER REFERENCES contests(id) ON DELETE CASCADE,
                    user_id BIGINT NOT NULL,
                    spam_count INTEGER DEFAULT 0,
                    UNIQUE(contest_id, user_id)
                )
            ''')
            
            # Индексы для spam_messages
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_spam_contest ON spam_messages(contest_id)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_spam_leaderboard ON spam_messages(contest_id, spam_count DESC)')
            
            print("✅ PostgreSQL база данных инициализирована!")
    
# ==================== CONTESTS ====================

    async def create_contest(self, prize: str, conditions: str,
                        entry_conditions: Dict, participants_count: int, 
                        timer_minutes: int, contest_type: str = 'voting_contest') -> int:
        """Создать новый конкурс"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('''
                INSERT INTO contests 
                (contest_type, status, prize, conditions, entry_conditions, 
                participants_count, timer_minutes)
                VALUES ($1::VARCHAR(50), $2::VARCHAR(20), $3::TEXT, $4::TEXT, $5::JSONB, $6::INTEGER, $7::INTEGER)
                RETURNING id
            ''', contest_type, 'collecting', prize, conditions, json.dumps(entry_conditions),
                participants_count, timer_minutes)
            
            return row['id']

    async def get_active_contests(self) -> List[Dict]:
        """Получить все активные конкурсы"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT *, 
                    entry_conditions::text as entry_conditions_json
                FROM contests 
                WHERE status IN ('collecting', 'voting', 'running', 'ready_to_start')
                ORDER BY created_at DESC
            ''')
            
            result = []
            for row in rows:
                contest = dict(row)
                # Парсим JSON обратно
                if contest.get('entry_conditions_json'):
                    contest['entry_conditions'] = json.loads(contest['entry_conditions_json'])
                result.append(contest)
            
            return result
    
    async def get_contest_by_id(self, contest_id: int) -> Optional[Dict]:
        """Получить конкурс по ID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('''
                SELECT *, entry_conditions::text as entry_conditions_json
                FROM contests WHERE id = $1
            ''', contest_id)
            
            if not row:
                return None
            
            contest = dict(row)
            if contest.get('entry_conditions_json'):
                contest['entry_conditions'] = json.loads(contest['entry_conditions_json'])
            return contest
    
    async def get_contest_by_announcement_id(self, message_id: int) -> Optional[Dict]:
        """Получить конкурс по ID анонса"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('''
                SELECT *, entry_conditions::text as entry_conditions_json
                FROM contests WHERE announcement_message_id = $1
            ''', message_id)
            
            if not row:
                return None
            
            contest = dict(row)
            if contest.get('entry_conditions_json'):
                contest['entry_conditions'] = json.loads(contest['entry_conditions_json'])
            return contest
    
    async def get_contest_by_discussion_id(self, message_id: int) -> Optional[Dict]:
        """Получить конкурс по ID сообщения в группе"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('''
                SELECT *, entry_conditions::text as entry_conditions_json
                FROM contests WHERE discussion_message_id = $1
            ''', message_id)
            
            if not row:
                return None
            
            contest = dict(row)
            if contest.get('entry_conditions_json'):
                contest['entry_conditions'] = json.loads(contest['entry_conditions_json'])
            return contest
    
    async def update_contest_status(self, contest_id: int, status: str):
        """Обновить статус конкурса"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                UPDATE contests 
                SET status = $1::VARCHAR(20), 
                    ended_at = CASE 
                        WHEN $1::VARCHAR(20) = 'ended' 
                        THEN NOW() 
                        ELSE ended_at 
                    END
                WHERE id = $2
            ''', status, contest_id)
    
    async def set_announcement_message(self, contest_id: int, message_id: int):
        """Сохранить ID сообщения анонса"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                UPDATE contests SET announcement_message_id = $1 WHERE id = $2
            ''', message_id, contest_id)
    
    async def set_discussion_message(self, contest_id: int, message_id: int):
        """Сохранить ID сообщения в группе"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                UPDATE contests SET discussion_message_id = $1 WHERE id = $2
            ''', message_id, contest_id)
    
    # ==================== PARTICIPANTS ====================
    
    async def add_participant(self, contest_id: int, user_id: int, 
                            username: str, full_name: str, emoji: str) -> bool:
        """Добавить участника с проверкой уникальности"""
        async with self.pool.acquire() as conn:
            # Проверяем существование
            exists = await conn.fetchval('''
                SELECT EXISTS(
                    SELECT 1 FROM participants 
                    WHERE contest_id = $1::INTEGER AND user_id = $2::BIGINT
                )
            ''', contest_id, user_id)
            
            if exists:
                return False
            
            # Получаем позицию
            position = await conn.fetchval('''
                SELECT COALESCE(MAX(position), 0) + 1 
                FROM participants WHERE contest_id = $1::INTEGER
            ''', contest_id)
            
            # Добавляем
            await conn.execute('''
                INSERT INTO participants 
                (contest_id, user_id, username, full_name, comment_text, position)
                VALUES ($1::INTEGER, $2::BIGINT, $3::VARCHAR(100), $4::VARCHAR(200), $5::TEXT, $6::INTEGER)
            ''', contest_id, user_id, username or 'noname', full_name, emoji, position)
            
            return True


    async def get_participants(self, contest_id: int) -> List[Dict]:
        """Получить всех участников конкурса"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT * FROM participants 
                WHERE contest_id = $1 
                ORDER BY position
            ''', contest_id)
            
            return [dict(row) for row in rows]
    
    async def get_participants_count(self, contest_id: int) -> int:
        """Получить количество участников"""
        async with self.pool.acquire() as conn:
            count = await conn.fetchval('''
                SELECT COUNT(*) FROM participants WHERE contest_id = $1
            ''', contest_id)
            return count or 0
    
    async def get_participant_by_position(self, contest_id: int, position: int) -> Optional[Dict]:
        """Получить участника по позиции"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('''
                SELECT * FROM participants 
                WHERE contest_id = $1 AND position = $2
            ''', contest_id, position)
            
            return dict(row) if row else None
    
    # ==================== WINNERS ====================
    
    async def set_contest_winner(self, contest_id: int, user_id: int, position: int = 1):
        """Сохранить победителя"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO winners (contest_id, user_id, position)
                VALUES ($1, $2, $3)
            ''', contest_id, user_id, position)
    
    async def get_last_winners_by_type(self, contest_type: str, limit: int = 10) -> List[int]:
        """Получить последних победителей определенного типа конкурса"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT w.user_id 
                FROM winners w
                JOIN contests c ON w.contest_id = c.id
                WHERE c.contest_type = $1
                ORDER BY w.won_at DESC
                LIMIT $2
            ''', contest_type, limit)
            
            return [row['user_id'] for row in rows]
    
    # ==================== REFERRALS ====================
    
    async def add_referral(self, referrer_id: int, referred_id: int):
        """Добавить реферала"""
        async with self.pool.acquire() as conn:
            try:
                await conn.execute('''
                    INSERT INTO referrals (referrer_id, referred_id)
                    VALUES ($1, $2)
                    ON CONFLICT DO NOTHING
                ''', referrer_id, referred_id)
            except:
                pass
    
    async def mark_referral_subscribed(self, referrer_id: int, referred_id: int):
        """Отметить что реферал подписался"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                UPDATE referrals 
                SET subscribed = TRUE, points_awarded = TRUE
                WHERE referrer_id = $1 AND referred_id = $2
            ''', referrer_id, referred_id)
            
            # Начислить очко рефереру
            await conn.execute('''
                INSERT INTO user_stats (user_id, referral_points)
                VALUES ($1, 1)
                ON CONFLICT (user_id) DO UPDATE
                SET referral_points = user_stats.referral_points + 1,
                    updated_at = NOW()
            ''', referrer_id)
    
    async def get_referral_count(self, user_id: int) -> int:
        """Получить количество рефералов"""
        async with self.pool.acquire() as conn:
            count = await conn.fetchval('''
                SELECT COUNT(*) FROM referrals 
                WHERE referrer_id = $1 AND subscribed = TRUE
            ''', user_id)
            return count or 0
    
    async def check_referral_exists(self, referrer_id: int, referred_id: int) -> bool:
        """Проверить существует ли реферал"""
        async with self.pool.acquire() as conn:
            exists = await conn.fetchval('''
                SELECT EXISTS(SELECT 1 FROM referrals 
                WHERE referrer_id = $1 AND referred_id = $2)
            ''', referrer_id, referred_id)
            return exists
    
    # ==================== USER STATS ====================
    
    async def get_user_stats(self, user_id: int) -> Dict:
        """Получить статистику пользователя"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('''
                SELECT * FROM user_stats WHERE user_id = $1
            ''', user_id)
            
            if not row:
                # Создать если нет
                await conn.execute('''
                    INSERT INTO user_stats (user_id) VALUES ($1)
                ''', user_id)
                row = await conn.fetchrow('''
                    SELECT * FROM user_stats WHERE user_id = $1
                ''', user_id)
            
            return dict(row)
    
    async def increment_user_contests(self, user_id: int):
        """Увеличить счетчик участий"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO user_stats (user_id, total_contests)
                VALUES ($1, 1)
                ON CONFLICT (user_id) DO UPDATE
                SET total_contests = user_stats.total_contests + 1,
                    updated_at = NOW()
            ''', user_id)
    
    async def increment_user_wins(self, user_id: int, contest_type: str):
        """Увеличить счетчик побед"""
        type_column = f"{contest_type.replace('_contest', '')}_wins"
        
        async with self.pool.acquire() as conn:
            query = f'''
                INSERT INTO user_stats (user_id, total_wins, {type_column}, current_win_streak)
                VALUES ($1, 1, 1, 1)
                ON CONFLICT (user_id) DO UPDATE
                SET total_wins = user_stats.total_wins + 1,
                    {type_column} = user_stats.{type_column} + 1,
                    current_win_streak = user_stats.current_win_streak + 1,
                    best_win_streak = GREATEST(user_stats.best_win_streak, user_stats.current_win_streak + 1),
                    updated_at = NOW()
            '''
            await conn.execute(query, user_id)
    
    async def get_top_by_referrals(self, limit: int = 10) -> List[Dict]:
        """Топ по рефералам"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT user_id, referral_points
                FROM user_stats
                WHERE referral_points > 0
                ORDER BY referral_points DESC
                LIMIT $1
            ''', limit)
            
            return [dict(row) for row in rows]
    
    async def get_top_by_wins(self, limit: int = 10) -> List[Dict]:
        """Топ по победам"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT user_id, total_wins
                FROM user_stats
                WHERE total_wins > 0
                ORDER BY total_wins DESC
                LIMIT $1
            ''', limit)
            
            return [dict(row) for row in rows]
    
    async def get_top_by_contests(self, limit: int = 10) -> List[Dict]:
        """Топ по активности"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT user_id, total_contests
                FROM user_stats
                WHERE total_contests > 0
                ORDER BY total_contests DESC
                LIMIT $1
            ''', limit)
            
            return [dict(row) for row in rows]
    
    async def get_user_position(self, user_id: int, leaderboard_type: str) -> int:
        """Получить позицию в рейтинге"""
        column_map = {
            'referrals': 'referral_points',
            'wins': 'total_wins',
            'contests': 'total_contests'
        }
        
        column = column_map.get(leaderboard_type, 'total_wins')
        
        async with self.pool.acquire() as conn:
            position = await conn.fetchval(f'''
                SELECT COUNT(*) + 1
                FROM user_stats
                WHERE {column} > (
                    SELECT {column} FROM user_stats WHERE user_id = $1
                )
            ''', user_id)
            
            return position or 0
    
    # ==================== ACHIEVEMENTS ====================
    
    async def check_and_unlock_achievement(self, user_id: int, achievement_type: str, 
                                         achievement_level: str):
        """Проверить и разблокировать достижение"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO achievements (user_id, achievement_type, achievement_level)
                VALUES ($1, $2, $3)
                ON CONFLICT DO NOTHING
            ''', user_id, achievement_type, achievement_level)
    
    async def get_user_achievements(self, user_id: int) -> List[Dict]:
        """Получить все достижения пользователя"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT * FROM achievements 
                WHERE user_id = $1
                ORDER BY unlocked_at DESC
            ''', user_id)
            
            return [dict(row) for row in rows]
    
    async def has_achievement(self, user_id: int, achievement_type: str, 
                            achievement_level: str) -> bool:
        """Проверить наличие достижения"""
        async with self.pool.acquire() as conn:
            exists = await conn.fetchval('''
                SELECT EXISTS(SELECT 1 FROM achievements 
                WHERE user_id = $1 AND achievement_type = $2 AND achievement_level = $3)
            ''', user_id, achievement_type, achievement_level)
            return exists
    
    # ==================== SPAM ====================
    
    async def init_spam_participant(self, contest_id: int, user_id: int):
        """Инициализировать участника спам-конкурса"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO spam_messages (contest_id, user_id, spam_count)
                VALUES ($1, $2, 0)
                ON CONFLICT DO NOTHING
            ''', contest_id, user_id)
    
    async def increment_spam_count(self, contest_id: int, user_id: int):
        """Увеличить счётчик спама"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO spam_messages (contest_id, user_id, spam_count)
                VALUES ($1, $2, 1)
                ON CONFLICT (contest_id, user_id) 
                DO UPDATE SET spam_count = spam_messages.spam_count + 1
            ''', contest_id, user_id)
    
    async def get_spam_leaderboard(self, contest_id: int) -> List[Dict]:
        """Получить таблицу лидеров спам-конкурса"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT s.*, p.username, p.full_name
                FROM spam_messages s
                JOIN participants p ON s.contest_id = p.contest_id AND s.user_id = p.user_id
                WHERE s.contest_id = $1
                ORDER BY s.spam_count DESC
            ''', contest_id)
            
            return [dict(row) for row in rows]
    
    async def get_spam_count(self, contest_id: int, user_id: int) -> int:
        """Получить количество спамов участника"""
        async with self.pool.acquire() as conn:
            count = await conn.fetchval('''
                SELECT spam_count FROM spam_messages 
                WHERE contest_id = $1 AND user_id = $2
            ''', contest_id, user_id)
            return count or 0
    
    async def get_spam_winner(self, contest_id: int) -> Optional[Dict]:
        """Получить победителя спам-конкурса"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('''
                SELECT s.*, p.username, p.full_name
                FROM spam_messages s
                JOIN participants p ON s.contest_id = p.contest_id AND s.user_id = p.user_id
                WHERE s.contest_id = $1 AND s.spam_count > 0
                ORDER BY s.spam_count DESC
                LIMIT 1
            ''', contest_id)
            
            return dict(row) if row else None

    async def get_last_ended_contest(self) -> Optional[Dict]:
        """Получить последний завершённый конкурс"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('''
                SELECT *, entry_conditions::text as entry_conditions_json
                FROM contests 
                WHERE status = 'ended'
                ORDER BY ended_at DESC
                LIMIT 1
            ''')
            
            if not row:
                return None
            
            contest = dict(row)
            if contest.get('entry_conditions_json'):
                contest['entry_conditions'] = json.loads(contest['entry_conditions_json'])
            return contest



# Глобальный экземпляр (инициализируется в bot.py)
db = None
