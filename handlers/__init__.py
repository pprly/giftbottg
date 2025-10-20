
from aiogram import Router

# Создаём главный роутер
router = Router()

def setup_routers():
    """Настройка всех роутеров"""
    
    # Импорты
    from handlers.user import main_menu, my_stats, referral, achievements, leaderboard, inline_referral
    from handlers.faq import faq_menu, contest_types, referral_info, contact_info
    from handlers.admin import admin_menu, create_contest, select_winner
    from handlers.contests import voting_contest, random_contest, spam_contest, message_handler
    from handlers.system import auto_approve
    from handlers.admin import publish_rules
    
    # ⬇️ ВАЖНО: Подключаем message_handler ПЕРВЫМ (до debug)
    router.include_router(message_handler.router)
    print("✅ Message handler подключен первым\n")
    
    # User handlers
    router.include_router(main_menu.router)
    router.include_router(my_stats.router)
    router.include_router(referral.router)
    router.include_router(inline_referral.router)
    router.include_router(achievements.router)
    router.include_router(leaderboard.router)
    
    # FAQ handlers
    router.include_router(faq_menu.router)
    router.include_router(contest_types.router)
    router.include_router(referral_info.router)
    router.include_router(contact_info.router)
    
    # Admin handlers
    router.include_router(admin_menu.router)
    router.include_router(create_contest.router)
    router.include_router(select_winner.router)
    router.include_router(publish_rules.router)
    
    # Contest handlers
    router.include_router(voting_contest.router)
    router.include_router(random_contest.router)
    router.include_router(spam_contest.router)
    
    # System handlers
    router.include_router(auto_approve.router)
    
    # ⬇️ DEBUG: Подключаем ПОСЛЕДНИМ (для отладки)
    # import test_debug
    # router.include_router(test_debug.router)
    # print("🔍 DEBUG роутер подключен последним\n")
    
    print("✅ Все роутеры подключены")

setup_routers()