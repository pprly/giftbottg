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
        
        # TODO: Добавить методы в database_postgres.py
        # Пока возвращаем заглушку
        return web.json_response({
            'success': True,
            'type': leaderboard_type,
            'leaders': []
        })
        
    except Exception as e:
        print(f"❌ Ошибка в get_leaderboard: {e}")
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
        
        # TODO: Получить достижения из БД
        # Пока возвращаем заглушку
        return web.json_response({
            'success': True,
            'achievements': []
        })
        
    except Exception as e:
        print(f"❌ Ошибка в get_achievements: {e}")
        return web.json_response(
            {'error': 'Внутренняя ошибка сервера'},
            status=500
        )


# CORS для разработки
async def add_cors_headers(request, response):
    """Добавляет CORS заголовки"""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response


def create_app():
    """Создаёт aiohttp приложение"""
    app = web.Application()
    
    # Роуты
    app.router.add_get('/api/stats', get_user_stats)
    app.router.add_get('/api/leaderboard', get_leaderboard)
    app.router.add_get('/api/achievements', get_achievements)
    
    # CORS middleware
    app.middlewares.append(lambda app, handler: 
        lambda request: add_cors_headers(request, handler(request))
    )
    
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