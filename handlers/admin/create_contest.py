"""
Создание конкурса с гибкими условиями участия
Пошаговый процесс через FSM
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import config
from database_postgres import db
from utils.filters import ParticipantFilter


router = Router()


class ContestCreation(StatesGroup):
    """Состояния создания конкурса"""
    waiting_for_contest_type = State()
    waiting_for_prize = State()
    waiting_for_conditions = State()
    waiting_for_participants_count = State()
    waiting_for_timer = State()
    
    # Настройка условий участия
    configuring_entry_conditions = State()
    waiting_for_min_referrals = State()
    waiting_for_min_contests = State()
    waiting_for_max_contests = State()


def is_admin(user_id: int) -> bool:
    """Проверка прав администратора"""
    return user_id == config.ADMIN_ID


@router.callback_query(F.data == "create_contest")
async def create_contest_start(callback: CallbackQuery, state: FSMContext):
    """Начало создания конкурса - выбор типа"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ У вас нет доступа!", show_alert=True)
        return
    
    # Проверяем есть ли активный конкурс в статусе 'collecting'
    contests = await db.get_active_contests()
    collecting_contests = [c for c in contests if c['status'] == 'collecting']
    
    if collecting_contests:
        # Показываем предупреждение
        contest = collecting_contests[0]
        text = (
            "⚠️ **НАБОР УЖЕ ИДЁТ**\n\n"
            f"Активен конкурс #{contest['id']} в статусе 'collecting'\n"
            f"🎁 Приз: {contest['prize']}\n"
            f"👥 Участников: {await db.get_participants_count(contest['id'])}/{contest['participants_count']}\n\n"
            "❗️ Нельзя начать новый набор пока идёт текущий!\n\n"
            "**Варианты:**\n"
            "• Дождитесь завершения набора\n"
            "• Или принудительно запустите конкурс ➡️"
        )
        
        builder = InlineKeyboardBuilder()
        builder.button(text="🚀 Запустить конкурс принудительно", callback_data=f"force_start_{contest['id']}")
        builder.button(text="🔙 Назад", callback_data="admin_panel")
        builder.adjust(1)
        
        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        await callback.answer()
        return
    
    # Если нет активных в 'collecting' - разрешаем создать
    builder = InlineKeyboardBuilder()
    
    # Кнопки типов конкурсов
    for contest_type, info in config.CONTEST_TYPES.items():
        builder.button(
            text=info['name'],
            callback_data=f"contest_type_{contest_type}"
        )
    
    builder.button(text="🔙 Отмена", callback_data="admin_panel")
    builder.adjust(2, 2, 1)
    
    await callback.message.edit_text(
        "🎲 **СОЗДАНИЕ КОНКУРСА**\n\n"
        "**Шаг 1/5:** Выберите тип конкурса\n\n"
        "🗳️ **Голосовательный** - админ выбирает победителя\n"
        "🎰 **Рандомайзер** - случайный выбор (скоро)\n"
        "👥 **Реферальный** - победа по рефералам (скоро)\n"
        "⚡ **Активность** - кто больше сообщений (скоро)",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await state.set_state(ContestCreation.waiting_for_contest_type)
    await callback.answer()


@router.callback_query(ContestCreation.waiting_for_contest_type, F.data.startswith("contest_type_"))
async def process_contest_type(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора типа конкурса"""
    contest_type = callback.data.replace("contest_type_", "")
    
    # Поддерживаем voting, random и spam
    if contest_type not in ["voting_contest", "random_contest", "spam_contest"]:
        await callback.answer("🚧 Этот тип конкурса ещё в разработке!", show_alert=True)
        return
    
    await state.update_data(contest_type=contest_type)
    
    await callback.message.edit_text(
        "🎁 **Шаг 2/5:** Введите описание приза\n\n"
        "Например: Медведь за 15 звёзд"
    )
    await state.set_state(ContestCreation.waiting_for_prize)
    await callback.answer()


@router.message(ContestCreation.waiting_for_prize)
async def process_prize(message: Message, state: FSMContext):
    """Обработка ввода приза"""
    if not is_admin(message.from_user.id):
        return
    
    await state.update_data(prize=message.text)
    
    await message.answer(
        "📝 **Шаг 3/5:** Введите условия участия (для пользователей)\n\n"
        "Например: Написать комментарий, быть подписанным на канал"
    )
    await state.set_state(ContestCreation.waiting_for_conditions)


@router.message(ContestCreation.waiting_for_conditions)
async def process_conditions(message: Message, state: FSMContext):
    """Обработка условий и переход к настройке фильтров"""
    if not is_admin(message.from_user.id):
        return
    
    await state.update_data(conditions=message.text)
    
    # Инициализируем пустые условия участия
    await state.update_data(entry_conditions={})
    
    await show_entry_conditions_menu(message, state)


async def show_entry_conditions_menu(message: Message, state: FSMContext):
    """Показать меню настройки условий участия"""
    data = await state.get_data()
    entry_conditions = data.get('entry_conditions', {})
    
    # Формируем текст с текущими условиями
    conditions_text = "**Текущие условия:**\n"
    
    if 'first_n' in entry_conditions:
        conditions_text += f"✅ Первые {entry_conditions['first_n']} человек\n"
    else:
        conditions_text += "❌ Первые N человек (не задано)\n"
    
    if 'min_referrals' in entry_conditions:
        conditions_text += f"✅ Минимум {entry_conditions['min_referrals']} рефералов\n"
    else:
        conditions_text += "❌ Минимум рефералов (не задано)\n"
    
    # НОВОЕ: Показываем диапазон участий
    has_min = 'min_contests' in entry_conditions
    has_max = 'max_contests' in entry_conditions
    
    if has_min and has_max:
        conditions_text += f"✅ От {entry_conditions['min_contests']} до {entry_conditions['max_contests']} участий\n"
    elif has_min:
        conditions_text += f"✅ Минимум {entry_conditions['min_contests']} участий\n"
    elif has_max:
        conditions_text += f"✅ Максимум {entry_conditions['max_contests']} участий\n"
    else:
        conditions_text += "❌ Минимум/максимум участий (не задано)\n"
    
    if entry_conditions.get('all_subscribers'):
        conditions_text += "✅ Все подписчики канала\n"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="👥 Первые N человек", callback_data="set_first_n")
    builder.button(text="🔗 Минимум рефералов", callback_data="set_min_referrals")
    builder.button(text="🎯 Минимум участий", callback_data="set_min_contests")  # ← УБРАЛИ ЗАГЛУШКУ
    builder.button(text="🆕 Максимум участий", callback_data="set_max_contests")  # ← НОВАЯ КНОПКА
    builder.button(text="✅ Готово, продолжить", callback_data="entry_conditions_done")
    builder.adjust(2, 2, 1)
    
    text = (
        "⚙️ **НАСТРОЙКА УСЛОВИЙ УЧАСТИЯ**\n\n"
        f"{conditions_text}\n"
        "Выберите параметр для настройки:"
    )
    
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    await state.set_state(ContestCreation.configuring_entry_conditions)


@router.callback_query(ContestCreation.configuring_entry_conditions, F.data == "set_first_n")
async def set_first_n(callback: CallbackQuery, state: FSMContext):
    """Настройка количества первых участников"""
    builder = InlineKeyboardBuilder()
    builder.button(text="3 (тест)", callback_data="first_n_3")
    builder.button(text="10", callback_data="first_n_10")
    builder.button(text="15", callback_data="first_n_15")
    builder.button(text="Свой вариант", callback_data="first_n_custom")
    builder.button(text="🔙 Назад", callback_data="back_to_entry_menu")
    builder.adjust(3, 1, 1)
    
    await callback.message.edit_text(
        "👥 **Количество участников**\n\n"
        "Выберите сколько первых человек станут участниками:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(ContestCreation.configuring_entry_conditions, F.data.startswith("first_n_"))
async def process_first_n(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора количества участников"""
    value = callback.data.replace("first_n_", "")
    
    if value == "custom":
        await callback.message.edit_text(
            "👥 Введите количество участников (от 3 до 100):"
        )
        await state.set_state(ContestCreation.waiting_for_participants_count)
        await callback.answer()
        return
    
    count = int(value)
    data = await state.get_data()
    entry_conditions = data.get('entry_conditions', {})
    entry_conditions['first_n'] = count
    await state.update_data(entry_conditions=entry_conditions)
    
    await callback.answer(f"✅ Установлено: первые {count} человек")
    
    # Возвращаемся в меню настроек
    await show_entry_conditions_menu(callback.message, state)


@router.message(ContestCreation.waiting_for_participants_count)
async def process_participants_custom(message: Message, state: FSMContext):
    """Обработка ввода своего количества участников"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        count = int(message.text)
        if count < 3 or count > 100:
            await message.answer("⚠️ Количество должно быть от 3 до 100. Попробуйте снова:")
            return
        
        data = await state.get_data()
        entry_conditions = data.get('entry_conditions', {})
        entry_conditions['first_n'] = count
        await state.update_data(entry_conditions=entry_conditions)
        
        await message.answer(f"✅ Установлено: первые {count} человек")
        await show_entry_conditions_menu(message, state)
        
    except ValueError:
        await message.answer("⚠️ Введите число от 3 до 100:")


@router.callback_query(ContestCreation.configuring_entry_conditions, F.data == "set_min_referrals")
async def set_min_referrals(callback: CallbackQuery, state: FSMContext):
    """Настройка минимального количества рефералов"""
    builder = InlineKeyboardBuilder()
    builder.button(text="1 реферал", callback_data="min_refs_1")
    builder.button(text="5 рефералов", callback_data="min_refs_5")
    builder.button(text="10 рефералов", callback_data="min_refs_10")
    builder.button(text="Свой вариант", callback_data="min_refs_custom")
    builder.button(text="❌ Убрать условие", callback_data="min_refs_remove")
    builder.button(text="🔙 Назад", callback_data="back_to_entry_menu")
    builder.adjust(3, 1, 1, 1)
    
    await callback.message.edit_text(
        "🔗 **Минимум рефералов**\n\n"
        "Выберите минимальное количество рефералов для участия:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(ContestCreation.configuring_entry_conditions, F.data.startswith("min_refs_"))
async def process_min_referrals(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора минимума рефералов"""
    value = callback.data.replace("min_refs_", "")
    
    data = await state.get_data()
    entry_conditions = data.get('entry_conditions', {})
    
    if value == "custom":
        await callback.message.edit_text(
            "🔗 Введите минимальное количество рефералов (от 1 до 50):"
        )
        await state.set_state(ContestCreation.waiting_for_min_referrals)
        await callback.answer()
        return
    elif value == "remove":
        if 'min_referrals' in entry_conditions:
            del entry_conditions['min_referrals']
        await state.update_data(entry_conditions=entry_conditions)
        await callback.answer("✅ Условие убрано")
    else:
        count = int(value)
        entry_conditions['min_referrals'] = count
        await state.update_data(entry_conditions=entry_conditions)
        await callback.answer(f"✅ Установлено: минимум {count} рефералов")
    
    await show_entry_conditions_menu(callback.message, state)


@router.message(ContestCreation.waiting_for_min_referrals)
async def process_min_referrals_custom(message: Message, state: FSMContext):
    """Обработка ввода своего минимума рефералов"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        count = int(message.text)
        if count < 1 or count > 50:
            await message.answer("⚠️ Количество должно быть от 1 до 50. Попробуйте снова:")
            return
        
        data = await state.get_data()
        entry_conditions = data.get('entry_conditions', {})
        entry_conditions['min_referrals'] = count
        await state.update_data(entry_conditions=entry_conditions)
        
        await message.answer(f"✅ Установлено: минимум {count} рефералов")
        await show_entry_conditions_menu(message, state)
        
    except ValueError:
        await message.answer("⚠️ Введите число от 1 до 50:")


@router.callback_query(ContestCreation.configuring_entry_conditions, F.data == "set_min_contests")
async def set_min_contests(callback: CallbackQuery, state: FSMContext):
    """Настройка минимального количества участий"""
    builder = InlineKeyboardBuilder()
    builder.button(text="3 участия", callback_data="min_contests_3")
    builder.button(text="5 участий", callback_data="min_contests_5")
    builder.button(text="10 участий", callback_data="min_contests_10")
    builder.button(text="20 участий", callback_data="min_contests_20")
    builder.button(text="Свой вариант", callback_data="min_contests_custom")
    builder.button(text="❌ Убрать условие", callback_data="min_contests_remove")
    builder.button(text="🔙 Назад", callback_data="back_to_entry_menu")
    builder.adjust(2, 2, 1, 1, 1)
    
    await callback.message.edit_text(
        "🎯 **Минимум участий**\n\n"
        "Выберите минимальное количество участий в конкурсах:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(ContestCreation.configuring_entry_conditions, F.data.startswith("min_contests_"))
async def process_min_contests(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора минимума участий"""
    value = callback.data.replace("min_contests_", "")
    
    data = await state.get_data()
    entry_conditions = data.get('entry_conditions', {})
    
    if value == "custom":
        await callback.message.edit_text(
            "🎯 Введите минимальное количество участий (от 1 до 100):"
        )
        await state.set_state(ContestCreation.waiting_for_min_contests)
        await callback.answer()
        return
    elif value == "remove":
        if 'min_contests' in entry_conditions:
            del entry_conditions['min_contests']
        await state.update_data(entry_conditions=entry_conditions)
        await callback.answer("✅ Условие убрано")
    else:
        count = int(value)
        entry_conditions['min_contests'] = count
        await state.update_data(entry_conditions=entry_conditions)
        await callback.answer(f"✅ Установлено: минимум {count} участий")
    
    await show_entry_conditions_menu(callback.message, state)


@router.message(ContestCreation.waiting_for_min_contests)
async def process_min_contests_custom(message: Message, state: FSMContext):
    """Обработка ввода своего минимума участий"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        count = int(message.text)
        if count < 1 or count > 100:
            await message.answer("⚠️ Количество должно быть от 1 до 100. Попробуйте снова:")
            return
        
        data = await state.get_data()
        entry_conditions = data.get('entry_conditions', {})
        entry_conditions['min_contests'] = count
        await state.update_data(entry_conditions=entry_conditions)
        
        await message.answer(f"✅ Установлено: минимум {count} участий")
        await show_entry_conditions_menu(message, state)
        
    except ValueError:
        await message.answer("⚠️ Введите число от 1 до 100:")

@router.callback_query(ContestCreation.configuring_entry_conditions, F.data == "set_max_contests")
async def set_max_contests(callback: CallbackQuery, state: FSMContext):
    """Настройка максимального количества участий"""
    builder = InlineKeyboardBuilder()
    builder.button(text="0 (совсем новички)", callback_data="max_contests_0")
    builder.button(text="1 (0-1 участие)", callback_data="max_contests_1")
    builder.button(text="3 участия", callback_data="max_contests_3")
    builder.button(text="5 участий", callback_data="max_contests_5")
    builder.button(text="10 участий", callback_data="max_contests_10")
    builder.button(text="Свой вариант", callback_data="max_contests_custom")
    builder.button(text="❌ Убрать условие", callback_data="max_contests_remove")
    builder.button(text="🔙 Назад", callback_data="back_to_entry_menu")
    builder.adjust(2, 2, 2, 1, 1, 1)
    
    await callback.message.edit_text(
        "🆕 **Максимум участий**\n\n"
        "Выберите максимальное количество участий:\n"
        "(например, max=1 → только для новичков)",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(ContestCreation.configuring_entry_conditions, F.data.startswith("max_contests_"))
async def process_max_contests(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора максимума участий"""
    value = callback.data.replace("max_contests_", "")
    
    data = await state.get_data()
    entry_conditions = data.get('entry_conditions', {})
    
    if value == "custom":
        await callback.message.edit_text(
            "🆕 Введите максимальное количество участий (от 0 до 100):"
        )
        await state.set_state(ContestCreation.waiting_for_max_contests)
        await callback.answer()
        return
    elif value == "remove":
        if 'max_contests' in entry_conditions:
            del entry_conditions['max_contests']
        await state.update_data(entry_conditions=entry_conditions)
        await callback.answer("✅ Условие убрано")
    else:
        count = int(value)
        entry_conditions['max_contests'] = count
        await state.update_data(entry_conditions=entry_conditions)
        
        if count == 0:
            await callback.answer("✅ Установлено: только совсем новички (0 участий)")
        elif count == 1:
            await callback.answer("✅ Установлено: только новички (0-1 участие)")
        else:
            await callback.answer(f"✅ Установлено: максимум {count} участий")
    
    await show_entry_conditions_menu(callback.message, state)


@router.message(ContestCreation.waiting_for_max_contests)
async def process_max_contests_custom(message: Message, state: FSMContext):
    """Обработка ввода своего максимума участий"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        count = int(message.text)
        if count < 0 or count > 100:
            await message.answer("⚠️ Количество должно быть от 0 до 100. Попробуйте снова:")
            return
        
        data = await state.get_data()
        entry_conditions = data.get('entry_conditions', {})
        entry_conditions['max_contests'] = count
        await state.update_data(entry_conditions=entry_conditions)
        
        if count == 0:
            await message.answer("✅ Установлено: только совсем новички (0 участий)")
        elif count == 1:
            await message.answer("✅ Установлено: только новички (0-1 участие)")
        else:
            await message.answer(f"✅ Установлено: максимум {count} участий")
        
        await show_entry_conditions_menu(message, state)
        
    except ValueError:
        await message.answer("⚠️ Введите число от 0 до 100:")


@router.callback_query(ContestCreation.configuring_entry_conditions, F.data == "back_to_entry_menu")
async def back_to_entry_menu(callback: CallbackQuery, state: FSMContext):
    """Вернуться в меню настройки условий"""
    await show_entry_conditions_menu(callback.message, state)
    await callback.answer()


@router.callback_query(ContestCreation.configuring_entry_conditions, F.data == "entry_conditions_done")
async def entry_conditions_done(callback: CallbackQuery, state: FSMContext):
    """Завершение настройки условий участия"""
    data = await state.get_data()
    entry_conditions = data.get('entry_conditions', {})
    
    # Проверяем что хоть что-то настроено
    if not entry_conditions or 'first_n' not in entry_conditions:
        await callback.answer(
            "⚠️ Нужно задать хотя бы количество участников!",
            show_alert=True
        )
        return
    
    # Разный текст и варианты таймера в зависимости от типа
    contest_type = data.get('contest_type', 'voting_contest')
    
    builder = InlineKeyboardBuilder()
    
    if contest_type == "voting_contest":
        # Голосование: короткий таймер
        text = "⏰ **Шаг 5/5:** Длительность голосования"
        builder.button(text="5 минут (тест)", callback_data="timer_5")
        builder.button(text="30 минут", callback_data="timer_30")
        builder.button(text="1 час", callback_data="timer_60")
        builder.button(text="2 часа", callback_data="timer_120")
        builder.button(text="Свой вариант", callback_data="timer_custom")
        builder.adjust(2, 2, 1)
    
    elif contest_type == "random_contest":
        # Рандомайзер: время сбора участников
        text = "⏰ **Шаг 5/5:** Время сбора участников"
        builder.button(text="5 минут (тест)", callback_data="timer_5")
        builder.button(text="30 минут", callback_data="timer_30")
        builder.button(text="1 час", callback_data="timer_60")
        builder.button(text="6 часов", callback_data="timer_360")
        builder.button(text="24 часа", callback_data="timer_1440")
        builder.button(text="Свой вариант", callback_data="timer_custom")
        builder.adjust(2, 2, 2, 1)
    
    elif contest_type == "spam_contest":
        # Спам-конкурс: только время РЕГИСТРАЦИИ (первый таймер)
        # Второй таймер (конкурс) спросим на следующем шаге
        text = "⏰ **Шаг 5а/6:** Время регистрации участников"
        builder.button(text="5 минут (тест)", callback_data="timer_5")
        builder.button(text="10 минут", callback_data="timer_10")
        builder.button(text="30 минут", callback_data="timer_30")
        builder.button(text="Свой вариант", callback_data="timer_custom")
        builder.adjust(3, 1)
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await state.set_state(ContestCreation.waiting_for_timer)
    await callback.answer()


@router.callback_query(ContestCreation.waiting_for_timer, F.data.startswith("timer_"))
async def process_timer(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора таймера"""
    value = callback.data.replace("timer_", "")
    
    if value == "custom":
        await callback.message.edit_text(
            "⏰ Введите длительность в минутах (от 5 до 300):"
        )
        await callback.answer()
        return
    
    timer_minutes = int(value)
    data = await state.get_data()
    contest_type = data.get('contest_type', 'voting_contest')
    
    # Для спам-конкурса нужен ВТОРОЙ таймер
    if contest_type == "spam_contest":
        # Сохраняем первый таймер (регистрация)
        await state.update_data(registration_time=timer_minutes)
        
        # Спрашиваем второй таймер (длительность конкурса)
        builder = InlineKeyboardBuilder()
        builder.button(text="5 минут (тест)", callback_data="contest_timer_5")
        builder.button(text="30 минут", callback_data="contest_timer_30")
        builder.button(text="1 час", callback_data="contest_timer_60")
        builder.button(text="2 часа", callback_data="contest_timer_120")
        builder.button(text="Свой вариант", callback_data="contest_timer_custom")
        builder.adjust(2, 2, 1)
        
        await callback.message.edit_text(
            "⏰ **Шаг 5б/6:** Длительность самого конкурса",
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        await callback.answer()
        return
    
    # Для остальных типов - сразу финализируем
    await finalize_contest(callback.message, state, timer_minutes)
    await callback.answer()

@router.callback_query(ContestCreation.waiting_for_timer, F.data.startswith("contest_timer_"))
async def process_contest_timer(callback: CallbackQuery, state: FSMContext):
    """Обработка второго таймера для спам-конкурса"""
    value = callback.data.replace("contest_timer_", "")
    
    if value == "custom":
        await callback.message.edit_text(
            "⏰ Введите длительность конкурса в минутах (от 5 до 300):"
        )
        # Переключаем состояние на ожидание custom таймера конкурса
        await state.update_data(waiting_contest_timer=True)
        await callback.answer()
        return
    
    contest_timer = int(value)
    await finalize_contest(callback.message, state, contest_timer)
    await callback.answer()


@router.message(ContestCreation.waiting_for_timer)
async def process_timer_custom(message: Message, state: FSMContext):
    """Обработка ввода своего таймера"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        timer = int(message.text)
        if timer < 5 or timer > 300:
            await message.answer("⚠️ Длительность должна быть от 5 до 300 минут. Попробуйте снова:")
            return
        
        await finalize_contest(message, state, timer)
    except ValueError:
        await message.answer("⚠️ Введите число от 5 до 300:")


async def finalize_contest(message: Message, state: FSMContext, timer_minutes: int):
    """Финализация и создание конкурса"""
    data = await state.get_data()
    await state.clear()
    
    entry_conditions = data.get('entry_conditions', {})
    contest_type = data.get("contest_type", "voting_contest")
    
    # Для спам-конкурса используем registration_time как timer_minutes в БД
    # А timer_minutes (параметр функции) - это длительность конкурса
    if contest_type == "spam_contest":
        registration_time = data.get('registration_time', 10)
        contest_duration = timer_minutes
        
        # В БД сохраняем registration_time как timer_minutes
        # А contest_duration передадим через условия или отдельно
        timer_to_save = registration_time
        
        # Сохраняем длительность конкурса в entry_conditions (временное решение)
        entry_conditions['contest_duration'] = contest_duration
    else:
        timer_to_save = timer_minutes
    
    # Сохраняем конкурс в БД
    contest_id = await db.create_contest(
        prize=data["prize"],
        conditions=data["conditions"],
        entry_conditions=entry_conditions,
        participants_count=entry_conditions.get('first_n', 10),
        timer_minutes=timer_to_save,
        contest_type=contest_type
    )
    
    # Форматируем условия для отображения
    conditions_display = ParticipantFilter.format_conditions(entry_conditions)
    
    # Разное подтверждение в зависимости от типа
    if contest_type == "voting_contest":
        confirm_text = (
            f"✅ **Голосовательный конкурс создан!**\n\n"
            f"🎁 Приз: {data['prize']}\n"
            f"📝 Условия: {data['conditions']}\n\n"
            f"**Фильтры участия:**\n{conditions_display}\n\n"
            f"⏰ Длительность голосования: {timer_minutes} мин\n\n"
            f"🚀 Публикую анонс в канале..."
        )
    elif contest_type == "random_contest":
        confirm_text = (
            f"✅ **Рандомайзер создан!**\n\n"
            f"🎁 Приз: {data['prize']}\n"
            f"📝 Условия: {data['conditions']}\n\n"
            f"**Фильтры участия:**\n{conditions_display}\n\n"
            f"⏰ Время сбора: {timer_minutes} мин\n"
            f"🎲 Автоматический розыгрыш после набора\n\n"
            f"🚀 Публикую анонс в канале..."
        )
    elif contest_type == "spam_contest":
        confirm_text = (
            f"✅ **Спам-конкурс создан!**\n\n"
            f"🎁 Приз: {data['prize']}\n"
            f"📝 Условия: {data['conditions']}\n\n"
            f"**Фильтры участия:**\n{conditions_display}\n\n"
            f"⏰ Регистрация: {registration_time} мин\n"
            f"⚡ Конкурс: {contest_duration} мин\n"
            f"💬 Победитель = кто больше написал\n\n"
            f"🚀 Публикую анонс в канале..."
        )
    
    # Отправляем подтверждение
    await message.answer(confirm_text, parse_mode="Markdown")
    
    # Импортируем и запускаем публикацию в зависимости от типа
    if contest_type == "voting_contest":
        from handlers.contests.voting_contest import publish_contest_announcement
        await publish_contest_announcement(message.bot, contest_id)
    
    elif contest_type == "random_contest":
        from handlers.contests.random_contest import publish_random_contest_announcement
        await publish_random_contest_announcement(message.bot, contest_id)
    
    elif contest_type == "spam_contest":
        from handlers.contests.spam_contest import publish_spam_contest_announcement
        await publish_spam_contest_announcement(message.bot, contest_id)

@router.callback_query(F.data.startswith("force_start_"))
async def force_start_contest(callback: CallbackQuery):
    """Принудительный запуск конкурса (закрытие набора)"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ У вас нет доступа!", show_alert=True)
        return
    
    # Извлекаем ID конкурса
    contest_id = int(callback.data.replace("force_start_", ""))
    
    # Получаем конкурс
    contest = await db.get_contest_by_id(contest_id)
    
    if not contest:
        await callback.answer("❌ Конкурс не найден", show_alert=True)
        return
    
    # Проверяем статус
    if contest['status'] != 'collecting':
        await callback.answer("ℹ️ Конкурс уже не в статусе 'collecting'", show_alert=True)
        return
    
    # Проверяем есть ли хоть кто-то
    participants_count = await db.get_participants_count(contest_id)
    
    if participants_count == 0:
        await callback.answer("❌ Нельзя запустить конкурс без участников!", show_alert=True)
        return
    
    # ⚡ ВАЖНО: Отменяем задачу сбора комментариев
    from handlers.contests.voting_contest import cancel_collect_task, publish_participants_list, start_timer, active_tasks
    await cancel_collect_task(contest_id)
    
    # Закрываем набор - меняем статус на 'voting'
    await db.update_contest_status(contest_id, 'voting')
    print(f"🔒 [{contest_id}] Регистрация закрыта принудительно")
    
    # Публикуем список участников
    await publish_participants_list(callback.bot, contest_id)
    
    # Запускаем таймер с сохранением задачи
    import asyncio
    task = asyncio.create_task(start_timer(callback.bot, contest_id, contest['timer_minutes']))
    active_tasks[f"timer_{contest_id}"] = task
    
    # Уведомляем админа
    text = (
        "✅ **КОНКУРС ЗАПУЩЕН ПРИНУДИТЕЛЬНО**\n\n"
        f"🆔 ID: {contest_id}\n"
        f"🎁 Приз: {contest['prize']}\n"
        f"👥 Участников: {participants_count}/{contest['participants_count']}\n"
        "Список участников опубликован в канале.\n"
        "Таймер запущен!"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 В админ-панель", callback_data="admin_panel")
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()
