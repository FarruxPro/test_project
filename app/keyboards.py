from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.database.models import Subscription, async_session
from sqlalchemy import select

premium = True

subscriptions_data = 'my_subscriptions' if premium else 'no_subscription'

main = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='⭐️Программы Школы', callback_data='school_programs')],
    [InlineKeyboardButton(text='✨Мои подписки', callback_data=subscriptions_data)],
    [InlineKeyboardButton(text='💬Связаться с тех.поддержкой', url="https://ChatBotStart.com")]
])

school_programs = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='📚Подписка на обучение', callback_data='school_subscription_training')],
    [InlineKeyboardButton(text='🚀Подписка для масштабирования', url="https://yotube.com")],
    [InlineKeyboardButton(text='🔙Назад', callback_data='main')]
])

my_subscriptions = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='📚Подписка на обучение', callback_data='my_subscriptions_traning')],
    [InlineKeyboardButton(text='🚀Подписка для масштабирования', url="https://yotube.com")],
    [InlineKeyboardButton(text='➕Продлить подписку', url="https://yotube.com")],
    [InlineKeyboardButton(text='🔙Назад', callback_data='main')]
])

no_subscription = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='⭐️Программы Школы', callback_data='school_programs')],
    [InlineKeyboardButton(text='💬Связаться с тех.поддержкой', url="https://ChatBotStart.com")],
    [InlineKeyboardButton(text='🔙Назад', callback_data='main')]
])

school_subscription_training = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='💬Связаться с тех.поддержкой', url="https://ChatBotStart.com")],
    [InlineKeyboardButton(text='🔙Назад', callback_data='school_programs')]
])

my_subscriptions_traning = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Канал 1', url="https://ChatBotStart.com")],
    [InlineKeyboardButton(text='Группа 1', url="https://ChatBotStart.com")],
    [InlineKeyboardButton(text='Канал 2', url="https://ChatBotStart.com")],
    [InlineKeyboardButton(text='🔙Назад', callback_data='my_subscriptions')]
])

# Admin
admin = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Управление подписками', callback_data='subscription_management')],
    [InlineKeyboardButton(text='Статистика', callback_data='static_but')],
    [InlineKeyboardButton(text='Управление пользователями', callback_data='user_management')]
])

# User
user_management = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Посмотреть список пользователей', callback_data='user_list')],
    [InlineKeyboardButton(text='Назначить подписки пользователю', callback_data='assign_subscription')],
    [InlineKeyboardButton(text='Удалить подписки у пользователя', url="https://yotube.com")],
    [InlineKeyboardButton(text='Рассылка', url="https://yotube.com")],
    [InlineKeyboardButton(text='Назад', callback_data='admin')]
])

user_list = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Назад', callback_data='user_management')]
])

# Sub
subscription_management = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Добавить подписку', callback_data='add_subscription')],
    [InlineKeyboardButton(text='Редактировать подписку', callback_data='edit_subscription')],
    [InlineKeyboardButton(text='Скрыть подписку', callback_data='hide_subscription')],
    [InlineKeyboardButton(text='Восстановить подписку', callback_data='restore_subscription')],
    [InlineKeyboardButton(text='Удалить подписку', callback_data='delete_subscription')],
    [InlineKeyboardButton(text='Назад', callback_data='admin')]
])

add_subscription = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Добавить еще одну подписку', callback_data='add_subscription')],
    [InlineKeyboardButton(text='Назад', callback_data='subscription_management')]
])


back_sub = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Назад', callback_data='subscription_management')]
])

# вывод кнопок по имени подписки.
# функции, которая возвращает объект клавиатуры
async def edit_subscription() -> InlineKeyboardMarkup:
    # создаём пустую клавиатуру
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    # Открываем асинхронную сессию подключения к базе данных
    async with async_session() as session:
        result = await session.execute(
            # выбираем все строки из таблицы
            select(Subscription)
        )
        # Преобразуем результат запроса в список объектов модели
        subscriptions = result.scalars().all()
        # Перебираем все подписки и фильтруем только те, у которых поле is_hidden — False
        for sub in subscriptions:
            if sub.is_hidden == False:
                keyboard.inline_keyboard.append(
                    [InlineKeyboardButton(text=sub.name, callback_data=f"sub_{sub.id}")])

    keyboard.inline_keyboard.append(
        [InlineKeyboardButton(text='Назад', callback_data='subscription_management')])

    return keyboard

# кнопка что редактировать
def get_subscription_detail_keyboard(sub_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Название", callback_data=f"name_{sub_id}")],
        [InlineKeyboardButton(text="Описание", callback_data=f"description_{sub_id}")],
        [InlineKeyboardButton(text="Каналы/группы", callback_data=f"channels_{sub_id}")],
        [InlineKeyboardButton(text="Назад", callback_data="subscription_management")]
    ])

#создание кнопки для скрытия подписок
async def hide_subscription() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    async with async_session() as session:
        result = await session.execute(select(Subscription))
        subscriptions = result.scalars().all()

        for sub in subscriptions:
            if sub.is_hidden == False:
                keyboard.inline_keyboard.append(
                    [InlineKeyboardButton(text=sub.name, callback_data=f"hide_{sub.id}")])

    keyboard.inline_keyboard.append(
        [InlineKeyboardButton(text='Назад', callback_data='subscription_management')])

    return keyboard

# Кнопки для востановления
async def restore_subscription() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    async with async_session() as session:
        result = await session.execute(select(Subscription))
        subscriptions = result.scalars().all()

        for sub in subscriptions:
            if sub.is_hidden == True:
                keyboard.inline_keyboard.append(
                    [InlineKeyboardButton(text=sub.name, callback_data=f"res_{sub.id}")])

    keyboard.inline_keyboard.append(
        [InlineKeyboardButton(text='Назад', callback_data='subscription_management')])

    return keyboard

# Клавиатура для удаления
async def delete_subscription() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    async with async_session() as session:
        result = await session.execute(select(Subscription))
        subscriptions = result.scalars().all()

        for sub in subscriptions:
            if sub.is_hidden == False:
                keyboard.inline_keyboard.append(
                    [InlineKeyboardButton(text=sub.name, callback_data=f"del_{sub.id}")])

    keyboard.inline_keyboard.append(
        [InlineKeyboardButton(text='Назад', callback_data='subscription_management')])

    return keyboard


async def delete__sub(del_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard = [
        [InlineKeyboardButton(text='Подтвердить удаление', callback_data=f'delete_{del_id}')],
        [InlineKeyboardButton(text='Отменить', callback_data='subscription_management')]
    ])


# Кнопка для статистики

static_but = InlineKeyboardMarkup(inline_keyboard= [
    [InlineKeyboardButton(text='Выбрать период', callback_data='date_static')],
    [InlineKeyboardButton(text='Выбрать подписку', callback_data='subscription_static')],
    [InlineKeyboardButton(text='Назад', callback_data='admin')]
])

async def subscription_static() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    async with async_session() as session:
        result = await session.execute(select(Subscription))
        subscriptions = result.scalars().all()

        for sub in subscriptions:
            if sub.is_hidden == False:
                keyboard.inline_keyboard.append(
                    [InlineKeyboardButton(text=sub.name, callback_data=f"static_{sub.id}")])

    keyboard.inline_keyboard.append(
        [InlineKeyboardButton(text='Назад', callback_data='static_but')])

    return keyboard

static_menu = InlineKeyboardMarkup(inline_keyboard= [
    [InlineKeyboardButton(text='Меню', callback_data='admin')]
])