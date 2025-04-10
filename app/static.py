from aiogram import F, Router, types
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from datetime import date, datetime
from app.database.models import User, Subscription, async_session

from sqlalchemy import select, delete, func, distinct, and_
from sqlalchemy.ext.asyncio import AsyncSession

import os
import re
import app.keyboards as kb

today = date.today()

router = Router()

@router.callback_query(F.data == 'static_but')
async def static(callback: CallbackQuery):
    async with async_session() as session:
        # Подсчитываем количество пользователей
        result = await session.execute(select(func.count(User.id)))
        users = result.scalar()

        # Подсчитываем количество активных подписок
        stmt = select(func.count(func.distinct(Subscription.user_id))).filter(
            and_(
                Subscription.start_date <= today,
                Subscription.end_date >= today
            )
        )
        result = await session.execute(stmt)
        active_subscriptions = result.scalar()

        # Ты также можешь подсчитать завершенные и продленные подписки, если у тебя есть нужные фильтры
        # Пример:
        # Завершающиеся подписки
        stmt_ending = select(func.count(Subscription.id)).filter(
            Subscription.end_date == today
        )
        result_ending = await session.execute(stmt_ending)
        ending_subscriptions = result_ending.scalar()

        # Завершенные подписки (с истекшими датами)
        stmt_ended = select(func.count(Subscription.id)).filter(
            Subscription.end_date < today
        )
        result_ended = await session.execute(stmt_ended)
        ended_subscriptions = result_ended.scalar()

        # Пример: Подписки, которые были продлены
        stmt_renewed = select(func.count(Subscription.id)).filter(
            Subscription.end_date > Subscription.start_date
        )
        result_renewed = await session.execute(stmt_renewed)
        renewed_subscriptions = result_renewed.scalar()

    await callback.message.delete()
    await callback.answer('')
    await callback.message.answer(f"""
Количество пользователей: {users} 
Количество подписчиков: {active_subscriptions} 
Количество завершающих подписку: {ending_subscriptions}
Количество завершенных подписок: {ended_subscriptions}
Количество продленных подписок: {renewed_subscriptions}

Выберите параметры расширенной статистики за период:
""", reply_markup=kb.static_but)
    
@router.callback_query(F.data == "subscription_static")
async def subscription_static(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer('')
    await callback.message.answer('Выберите параметры расширенной статистики за период:',
                                  reply_markup=await kb.subscription_static())
    

class PeriodState(StatesGroup):
    start_date = State()
    end_date = State()

@router.callback_query(F.data == 'date_static')
async def choose_start_date(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer('Выберете первую дату:')
    await state.set_state(PeriodState.start_date)


@router.message(PeriodState.start_date)
async def set_start_date(message: Message, state:FSMContext):
    try:
        start_date = datetime.strptime(message.text, "%Y-%m-%d").date()
        await state.update_data(start_date=start_date)
        await message.answer('Выберете вторую дату:')
        await state.set_state(PeriodState.end_date)
    except ValueError:
        await message.answer("Неверный формат даты. Пожалуйста, введите в формате ГГГГ-ММ-ДД.")

@router.message(PeriodState.end_date)
async def set_end_date(message: Message, state:FSMContext):
    try:
        end_date = datetime.strptime(message.text, "%Y-%m-%d").date()
        data = await state.get_data()
        start_date = data.get('start_date')
        
        if end_date < start_date:
            await message.answer("Конечная дата не может быть раньше начальной. Попробуйте снова.")
            return
        
        async with async_session() as session:
            # Количество пользователей, у которых есть хотя бы одна подписка в выбранном периоде
            # Количество пользователей, зарегистрированных в выбранный период
            stmt_new_users = select(func.count(User.id)).filter(
                and_(
                    User.created_at >= start_date,
                    User.created_at <= end_date
                )
            )
            result_new_users = await session.execute(stmt_new_users)
            users = result_new_users.scalar()

            # Количество активных подписчиков в этот период
            stmt_active = select(func.count(distinct(Subscription.user_id))).filter(
                and_(
                    Subscription.start_date <= end_date,
                    Subscription.end_date >= start_date
                )
            )
            result_active = await session.execute(stmt_active)
            active_subscriptions = result_active.scalar()

            # Завершающиеся подписки (end_date ровно в последний день периода)
            stmt_ending = select(func.count(Subscription.id)).filter(
                Subscription.end_date == end_date
            )
            result_ending = await session.execute(stmt_ending)
            ending_subscriptions = result_ending.scalar()

            # Завершенные подписки (end_date в пределах периода и уже закончились)
            stmt_ended = select(func.count(Subscription.id)).filter(
                and_(
                    Subscription.end_date >= start_date,
                    Subscription.end_date <= end_date
                )
            )
            result_ended = await session.execute(stmt_ended)
            ended_subscriptions = result_ended.scalar()

            # Продленные подписки (end_date больше start_date + не равны друг другу)
            stmt_renewed = select(func.count(Subscription.id)).filter(
                and_(
                    Subscription.start_date <= end_date,
                    Subscription.end_date >= start_date,
                    Subscription.end_date > Subscription.start_date
                )
            )
            result_renewed = await session.execute(stmt_renewed)
            renewed_subscriptions = result_renewed.scalar()


        await message.answer(f"""
Данные за этот период:
Количество пользователей: {users} 
Количество подписчиков: {active_subscriptions} 
Количество завершающих подписку: {ending_subscriptions} 
Количество завершенных подписок: {ended_subscriptions} 
Количество продленных подписок: {renewed_subscriptions}                             
""", reply_markup=kb.static_menu)
        await state.clear()
        
    except ValueError:
        await message.answer("Неверный формат даты. Пожалуйста, введите в формате ГГГГ-ММ-ДД.")

class SubscriptionPeriodState(StatesGroup):
    sub_id = State()
    start_date = State()
    end_date = State()

@router.callback_query(F.data.startswith("static_"))
async def choose_subscription_period(callback: CallbackQuery, state: FSMContext):
    sub_id = int(callback.data.split("_")[1])
    await state.update_data(sub_id=sub_id)
    await callback.message.delete()
    await callback.message.answer("Выберете первую дату:")
    await state.set_state(SubscriptionPeriodState.start_date)

@router.message(SubscriptionPeriodState.start_date)
async def get_subscription_start_date(message: Message, state: FSMContext):
    try:
        start_date = datetime.strptime(message.text, "%Y-%m-%d").date()
        await state.update_data(start_date=start_date)
        await message.answer("Выберете вторую дату:")
        await state.set_state(SubscriptionPeriodState.end_date)
    except ValueError:
        await message.answer("Неверный формат даты. Пожалуйста, введите в формате ГГГГ-ММ-ДД.")

@router.message(SubscriptionPeriodState.end_date)
async def get_subscription_end_date(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        start_date = data.get('start_date')
        end_date = datetime.strptime(message.text, "%Y-%m-%d").date()
        sub_id = data.get('sub_id')

        if end_date < start_date:
            await message.answer("Конечная дата не может быть раньше начальной.")
            return
        
        async with async_session() as session:
            stmt_users = select(func.count(distinct(User.id))).join(Subscription).filter(
                Subscription.id == sub_id,
                and_(
                    Subscription.start_date <= end_date,
                    Subscription.end_date >= start_date
                )
            )
            result_users = await session.execute(stmt_users)
            users_count = result_users.scalar()

            # Кол-во активных подписчиков на период
            stmt_active = select(func.count(distinct(Subscription.user_id))).filter(
                Subscription.id == sub_id,
                Subscription.start_date <= end_date,
                Subscription.end_date >= start_date
            )
            result_active = await session.execute(stmt_active)
            active_count = result_active.scalar()

            # Завершающиеся подписки (конец — последний день периода)
            stmt_ending = select(func.count(Subscription.id)).filter(
                Subscription.id == sub_id,
                Subscription.end_date == end_date
            )
            result_ending = await session.execute(stmt_ending)
            ending_count = result_ending.scalar()

            # Завершенные подписки
            stmt_ended = select(func.count(Subscription.id)).filter(
                Subscription.id == sub_id,
                Subscription.end_date >= start_date,
                Subscription.end_date <= end_date
            )
            result_ended = await session.execute(stmt_ended)
            ended_count = result_ended.scalar()

            # Продленные подписки
            stmt_renewed = select(func.count(Subscription.id)).filter(
                Subscription.id == sub_id,
                Subscription.start_date <= end_date,
                Subscription.end_date >= start_date,
                Subscription.end_date > Subscription.start_date
            )
            result_renewed = await session.execute(stmt_renewed)
            renewed_count = result_renewed.scalar()

            await message.answer(f'''
Данные за этот период:
                                 
Количество пользователей:{users_count}
Количество подписчиков:{active_count}
Количество завершающих подписку:{ending_count}
Количество завершенных подписок:{ended_count}
Количество продленных подписок:{renewed_count}
''')
        await state.clear()

    except ValueError:
        await message.answer("Неверный формат даты. Пожалуйста, введите в формате ГГГГ-ММ-ДД.")