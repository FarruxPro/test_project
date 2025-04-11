from aiogram import F, Router, types
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from datetime import date, datetime, timedelta
from app.database.models import User, Subscription, async_session
from sqlalchemy import select, delete, func, distinct, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
import app.keyboards as kb

from sqlalchemy import select, delete, func, distinct, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

import os
import re
import app.keyboards as kb

today = date.today()

router = Router()

class AssignSubscriptionState(StatesGroup):
    input_user = State()
    select_subscription = State()
    input_duration = State()

@router.callback_query(F.data == "assign_subscription")
async def assign_subscription(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer("Ведите ID пользователя или его username:")
    await state.set_state(AssignSubscriptionState.input_user)

@router.message(AssignSubscriptionState.input_user)
async def assign_get_user(message: Message, state: FSMContext):
    user_input  = message.text.strip()

    async with async_session() as session:
        try:
            user_id = int(user_input)
        except ValueError:
            user_id = None

        stmt = select(User).filter((User.user_id == user_id) | (User.user_name == user_input))
        result = await session.execute(stmt)
        user = result.scalar()

        if not user:
            await message.answer("Пользователь не найден. Попробуйте снова.")
            return
        
        await state.update_data(user_id=user_id, user=user)
        await message.answer("Выберите подписку:", reply_markup=await kb.assign_subscription())
        await state.set_state(AssignSubscriptionState.select_subscription)
        
@router.callback_query(F.data.startswith("assign_"), AssignSubscriptionState.select_subscription)
async def handle_subscription_selection(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split("_")[1]
    
    if action == "done":
        data = await state.get_data()
        selected_subs = data.get("selected_subs", [])

        if not selected_subs:
                await callback.answer("Вы не выбрали подписки.")
                return

        # Переход к выбору срока подписки
        await callback.message.edit_text("Выберите срок подписки:", reply_markup=kb.choice_of_deadline)
        await state.set_state(AssignSubscriptionState.input_duration)
        return
    
    # Обработка других кнопок подписки
    try:
        sub_id = int(action)  # Преобразуем в число
    except ValueError:
        await callback.answer("Некорректный формат данных.")
        return
    
    data = await state.get_data()
    selected_subs = data.get("selected_subs", [])

    if sub_id in selected_subs:
        selected_subs.remove(sub_id)
    else:
        selected_subs.append(sub_id)

    await state.update_data(selected_subs=selected_subs)

    new_markup = await kb.assign_subscription(selected_subs)
    if callback.message.reply_markup != new_markup:
        await callback.message.edit_reply_markup(reply_markup=new_markup)
    else:
        await callback.answer()



@router.callback_query(F.data == "assign_done", AssignSubscriptionState.select_subscription)
async def choose_duration(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected_subs = data.get('selected_subs', [])

    if not selected_subs:
        await callback.answer("Вы не выбрали подписку")
        return
    
    await callback.message.edit_text("Выберите срок подписки:", reply_markup=kb.choice_of_deadline)
    await state.set_state(AssignSubscriptionState.input_duration)

@router.callback_query(AssignSubscriptionState.input_duration, F.data.endswith("_day"))
async def apply_subscription_duration(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user: User = data["user"]
    selected_subs = data["selected_subs"]
    duration_days = int(callback.data.split("_")[0])

    start = today
    end =start + timedelta(days=duration_days)

    async with async_session() as session:
        user = await session.get(User, user.id)
        for sub_id in selected_subs:
            sub = await session.get(Subscription, sub_id)
            if sub:
                sub.start_date = start
                sub.end_date = end
                user.subscriptions.append(sub)
        await session.commit()

    await callback.message.edit_text("Подписки успешно назначены!")

    await state.clear()

@router.message(AssignSubscriptionState.input_duration)
async def handle_manual_duration(message: Message, state: FSMContext):
    text = message.text.strip()

    if not text.isdigit():
        await message.answer("Пожалуйста, введите число — количество дней подписки.")
        return

    duration_days = int(text)
    data = await state.get_data()
    user: User = data["user"]
    selected_subs = data["selected_subs"]

    start = today
    end = start + timedelta(days=duration_days)

    async with async_session() as session:
        user = await session.get(User, user.id)
        for sub_id in selected_subs:
            sub = await session.get(Subscription, sub_id)
            if sub:
                sub.start_date = start
                sub.end_date = end
                user.subscriptions.append(sub)
        await session.commit()

    await message.answer("Подписки успешно назначены!")
    await state.clear()