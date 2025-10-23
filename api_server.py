"""
API сервер для Telegram Mini App
Отдаёт данные пользователей из базы данных
"""

from aiohttp import web
import json
from database_postgres import db
import hashlib
import hmac
import urllib.parse
import config


def validate_init_data(init_data: str) -> dict:
    """
    Валидация данных от Telegram Mini App
    Возвращает данные пользователя если валидны
    """
    try:
        # Парсим init_data
        parsed = dict(urllib.parse.parse_qsl(init_data))
        hash_value = parsed.pop('hash', None)
        
        if not hash_value:
            raise ValueError("Hash отсутствует")
        
        # Создаём data_check_string
        data_check_arr = []
        for key in sorted(parsed.keys()):
            data_check_arr.append(f"{key}={parsed[key]}")
        data_check_string = '\n'.join(data_check_arr)
        
        # Проверяем HMAC
        secret_key = hmac.new(
            "WebAppData".encode(),
            config.BOT_TOKEN.encode(),
            hashlib.sha256
        ).digest()
        
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if calculated_hash != hash_value:
            raise ValueError("Невалидный hash")
        
        # Парсим user данные
        user_data = json.loads(parsed.get('user', '{}'))
        return user_data
        
    except Exception as e:
        print(f"❌ Ошибка валидации init_data: {e}")
        raise


async def get_user_stats(request):
    """
    GET /api/stats?init_data=...
    Возвращает статистику пользователя
    """
    try:
        # Получаем init_data из query параметров
        init_data = request.query.get('init_data')
        if not init_data:
            return web.json_response(
                {'error': 'init_data отсутствует'},
                status=400
            )
        
        # Валидируем данные
        user_data = validate_init_data(init_data)
        user_id = user_data.get('id')
        
        if not user_id:
            return web.json_response(
                {'error': 'user_id отсутствует'},
                status=400
            )
        
        # Получаем статистику из БД
        stats = await db.get_user_stats(user_id)
        referral_count = await db.get_referral_count(user_id)
        
        return web.json_response({
            'success': True,
            'user_id': user_id,
            'stats': {
                'referrals': referral_count,
                'totalContests': stats.get('total_contests', 0),
                'totalWins': stats.get('total_wins', 0),
                'votingWins': stats.get('voting_wins', 0),
                'randomWins': stats.get('random_wins', 0),
                'spamWins': stats.get('spam_wins', 0),
                'bestStreak': stats.get('best_win_streak', 0)
            }
        })
        
    except ValueError as e:
        return web.json_response(
            {'error': f'Невалидные данные: {str(e)}'},
            status=401
        )
    except Exception as e:
        print(f"❌ Ошибка в get_user_stats: {e}")
        return web.json_response(
            {'error': 'Внутренняя ошибка сервера'},
            status=500
        )


async def get_leaderboard(request):
    """
    GET /api/leaderboard?type=wins|referrals|contests
    Возвращает топ пользователей
    """
    try:
        leaderboard_type = request.query.get('type', 'wins')
        
        # Получаем топ из БД
        if leaderboard_type == 'wins':
            leaders = await db.get_leaderboard_by_wins(limit=10)
        elif leaderboard_type == 'referrals':
            leaders = await db.get_leaderboard_by_referrals(limit=10)
        elif leaderboard_type == 'contests':
            leaders = await db.get_leaderboard_by_contests(limit=10)
        else:
            return web.json_response(
                {'error': f'Неизвестный тип: {leaderboard_type}'},
                status=400
            )
        
        # Форматируем данные для фронтенда
        formatted_leaders = []
        for leader in leaders:
            # Определяем score в зависимости от типа
            if leaderboard_type == 'wins':
                score = leader.get('total_wins', 0)
            elif leaderboard_type == 'referrals':
                score = leader.get('referral_count', 0)
            else:  # contests
                score = leader.get('total_contests', 0)
            
            formatted_leaders.append({
                'rank': leader['rank'],
                'userId': leader['user_id'],
                'username': leader.get('username'),
                'fullName': leader.get('full_name'),
                'score': score
            })
        
        return web.json_response({
            'success': True,
            'type': leaderboard_type,
            'leaders': formatted_leaders
        })
        
    except Exception as e:
        print(f"❌ Ошибка в get_leaderboard: {e}")
        import traceback
        traceback.print_exc()
        return web.json_response(
            {'error': 'Внутренняя ошибка сервера'},
            status=500
        )

async def get_achievements(request):
    """
    GET /api/achievements?init_data=...
    Возвращает достижения пользователя
    """
    try:
        init_data = request.query.get('init_data')
        if not init_data:
            return web.json_response(
                {'error': 'init_data отсутствует'},
                status=400
            )
        
        user_data = validate_init_data(init_data)
        user_id = user_data.get('id')
        
        if not user_id:
            return web.json_response(
                {'error': 'user_id отсутствует'},
                status=400
            )
        
        # Получаем статистику для подсчета прогресса
        stats = await db.get_user_stats(user_id)
        referral_count = await db.get_referral_count(user_id)
        
        # Список всех достижений с прогрессом
        all_achievements = [
            # Участие в конкурсах
            {
                'id': 'newbie',
                'name': '🎯 Новичок',
                'emoji': '🎯',
                'description': 'Участвуй в 5 конкурсах',
                'target': 5,
                'progress': min(stats.get('total_contests', 0), 5),
                'earned': stats.get('total_contests', 0) >= 5
            },
            {
                'id': 'regular',
                'name': '⭐ Постоялец',
                'emoji': '⭐',
                'description': 'Участвуй в 20 конкурсах',
                'target': 20,
                'progress': min(stats.get('total_contests', 0), 20),
                'earned': stats.get('total_contests', 0) >= 20
            },
            {
                'id': 'veteran',
                'name': '👑 Ветеран',
                'emoji': '👑',
                'description': 'Участвуй в 50 конкурсах',
                'target': 50,
                'progress': min(stats.get('total_contests', 0), 50),
                'earned': stats.get('total_contests', 0) >= 50
            },
            
            # Победы
            {
                'id': 'first_win',
                'name': '🏆 Первая победа',
                'emoji': '🏆',
                'description': 'Выиграй свой первый конкурс',
                'target': 1,
                'progress': min(stats.get('total_wins', 0), 1),
                'earned': stats.get('total_wins', 0) >= 1
            },
            {
                'id': 'winner',
                'name': '🌟 Победитель',
                'emoji': '🌟',
                'description': 'Выиграй 5 конкурсов',
                'target': 5,
                'progress': min(stats.get('total_wins', 0), 5),
                'earned': stats.get('total_wins', 0) >= 5
            },
            {
                'id': 'champion',
                'name': '💎 Чемпион',
                'emoji': '💎',
                'description': 'Выиграй 10 конкурсов',
                'target': 10,
                'progress': min(stats.get('total_wins', 0), 10),
                'earned': stats.get('total_wins', 0) >= 10
            },
            
            # Рефералы
            {
                'id': 'recruiter',
                'name': '👋 Друг',
                'emoji': '👋',
                'description': 'Пригласи 5 друзей',
                'target': 5,
                'progress': min(referral_count, 5),
                'earned': referral_count >= 5
            },
            {
                'id': 'influencer',
                'name': '🌟 Популярный',
                'emoji': '🌟',
                'description': 'Пригласи 25 друзей',
                'target': 25,
                'progress': min(referral_count, 25),
                'earned': referral_count >= 25
            },
            {
                'id': 'legend',
                'name': '🔥 Легенда',
                'emoji': '🔥',
                'description': 'Пригласи 100 друзей',
                'target': 100,
                'progress': min(referral_count, 100),
                'earned': referral_count >= 100
            },
            
            # Серии побед
            {
                'id': 'streak',
                'name': '🔥 Серия побед',
                'emoji': '🔥',
                'description': 'Выиграй 3 раза подряд',
                'target': 3,
                'progress': min(stats.get('best_win_streak', 0), 3),
                'earned': stats.get('best_win_streak', 0) >= 3
            }
        ]
        
        return web.json_response({
            'success': True,
            'achievements': all_achievements
        })
        
    except ValueError as e:
        return web.json_response(
            {'error': f'Невалидные данные: {str(e)}'},
            status=401
        )
    except Exception as e:
        print(f"❌ Ошибка в get_achievements: {e}")
        import traceback
        traceback.print_exc()
        return web.json_response(
            {'error': 'Внутренняя ошибка сервера'},
            status=500
        )


# CORS middleware (ИСПРАВЛЕНО)
@web.middleware
async def cors_middleware(request, handler):
    """Добавляет CORS заголовки"""
    # Обрабатываем preflight OPTIONS запросы
    if request.method == 'OPTIONS':
        response = web.Response()
    else:
        response = await handler(request)
    
    # Добавляем CORS заголовки
    response.headers['Access-Control-Allow-Origin'] = 'https://pprly.github.io'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Max-Age'] = '86400'
    
    return response


def create_app():
    """Создаёт aiohttp приложение"""
    app = web.Application(middlewares=[cors_middleware])
    
    # Роуты
    app.router.add_get('/api/stats', get_user_stats)
    app.router.add_get('/api/leaderboard', get_leaderboard)
    app.router.add_get('/api/achievements', get_achievements)
    
    return app


async def start_api_server():
    """Запускает API сервер"""
    app = create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8000)
    await site.start()
    print("🌐 API сервер запущен на порту 8000")
    return runner

