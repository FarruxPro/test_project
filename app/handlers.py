from aiogram import F, Router, types
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from dotenv import load_dotenv
from sqlalchemy import select, delete
from app.database.models import User, Subscription, async_session

import os
import re
import app.keyboards as kb

load_dotenv()
ADMIN_IDS = list(map(int, os.getenv('ADMIN_IDS').split(',')))
router = Router()

class Reg(StatesGroup):
     user = State()
     email = State()
     number = State()

class SubscriptionForm(StatesGroup):
    name = State()
    description = State()
    id_channels = State()


@router.message(CommandStart())
async def reg_start(message: types.Message, state: FSMContext):
     user_id = message.from_user.id
     # проверяю пользователя по id
     async with async_session() as session:
        result = await session.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()


     if user:
          # удл передпоследнее сообщение
          try:
               await message.bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 1)
          except Exception as e:
               print(f"Не удалось удалить сообщение: {e}")
               
          # 
          await message.answer('👋 Добро пожаловать! Здесь вы можете узнать о подписках на наши программы и связаться с техподдержкой для их приобретения. Выберите нужное действие:',
                               reply_markup=kb.main)
          return
     # если пользователя нет регистрирую
     await state.set_state(Reg.user)
     await message.answer('Привет! 👋 Для начала работы нам нужно собрать некоторые ваши данные. Пожалуйста, введите ваше полное имя (Ф.И.О.):')


@router.message(Reg.user)
async def reg_full_name(message: Message, state:FSMContext):
     full_name = message.text.strip()

     if not re.fullmatch(r"[A-Za-zА-Яа-яЁё]+ [A-Za-zА-Яа-яЁё]+ [A-Za-zА-Яа-яЁё]+", full_name):
          await message.answer('Привет! 👋 Для начала работы нам нужно собрать некоторые ваши данные. Пожалуйста, введите ваше полное имя (Ф.И.О.):')
          return
     
     await state.update_data(user=full_name)
     await state.set_state(Reg.email)
     await message.answer('Спасибо! Теперь, пожалуйста, укажите ваш Email-адрес для связи:')

@router.message(Reg.email)
async def reg_email(message: Message, state: FSMContext):
     email = message.text.strip()

     if not re.fullmatch(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
          await message.answer('Пожалуйста, укажите ваш Email-адрес для связи:')
          return
     
     await state.update_data(email=email)
     await state.set_state(Reg.number)
     await message.answer('Отлично! Наконец, укажите ваш номер телефона')


@router.message(Reg.number)
async def reg_number(message: Message, state: FSMContext):
     number = message.text.strip()

     if not re.fullmatch(r"^\+\d+$", number):
          await message.answer('Укажите ваш номер телефона c +')
          return

     await state.update_data(number=number)
     data = await state.get_data()

     async with async_session() as session:
          new_user = User(
               user_name=message.from_user.username,
               user_id=message.from_user.id,
               user_phone=int(data['number'].replace('+', '')),
               user_email=data['email']
          )

          session.add(new_user)
          await session.commit()

     await message.answer('👋 Добро пожаловать! Здесь вы можете узнать о подписках на наши программы и связаться с техподдержкой для их приобретения. Выберите нужное действие:',
                          reply_markup=kb.main)
     await state.clear()



@router.callback_query(F.data == 'school_programs')
async def school_programs(callback: CallbackQuery):
     await callback.message.delete()
     await callback.answer('')
     await callback.message.answer('Вот доступные подписки:\n1. 📚 Подписка на обучение\n2. 🚀 Подписка для масштабирования\nВыберите интересующую вас подписку, чтобы узнать подробности.',
                                   reply_markup=kb.school_programs)
     
@router.callback_query(F.data == 'main')
async def school_programs(callback: CallbackQuery):
     await callback.message.delete()
     await callback.answer('')
     await callback.message.answer('👋 Добро пожаловать! Здесь вы можете узнать о подписках на наши программы и связаться с техподдержкой для их приобретения. Выберите нужное действие:',
                                   reply_markup=kb.main)
     

@router.callback_query(F.data == 'my_subscriptions')
async def my_subscriptions(callback: CallbackQuery):
     await callback.message.delete()
     await callback.answer('')
     await callback.message.answer('👋Приветствуем!\nУ Вас активна подписка на:\n\n\n1. Подписка на обучение\nДо окончания подписки осталось-20 дней\n\n\n2. Подписка для масштабирования\nДо окончания подписки осталось-15 дней\n\n\nВыберите подписку, чтобы увидеть ее детали',
                                   reply_markup=kb.my_subscriptions)
     
@router.callback_query(F.data == 'no_subscription')
async def no_subscription(callback: CallbackQuery):
     await callback.message.delete()
     await callback.answer('')
     await callback.message.answer('😕У вас нет активных подписок на данный момент.\nЧтобы ознакомиться с доступными подписками, перейдите по кнопке "Подписки Школы".\nЕсли у вас есть вопросы или вам нужна помощь с оформлением подписки, свяжитесь с нашей тех.поддержкой',
                                   reply_markup=kb.no_subscription)
     
@router.callback_query(F.data == 'school_subscription_training')
async def school_subscription_training(callback: CallbackQuery):
     await callback.message.delete()
     await callback.answer('')
     await callback.message.answer('📚 Подписка на обучениe\n\n\nОписание: Данная подписка включает доступ к лучшим учебным материалам, курсам и вебинарам по теме.\n\n\nВключенные каналы и группы:\n- Канал 1: Обучение основам\n- Канал 2: Вебинары для продвинутых\nДля оформления подписки свяжитесь с техподдержкой',
                                   reply_markup=kb.school_subscription_training)
     

@router.callback_query(F.data == 'my_subscriptions_traning')
async def my_subscriptions_traning(callback: CallbackQuery):
     await callback.message.delete()
     await callback.answer('')
     await callback.message.answer('Подписка: Подписка на обучение\n\n\nВключенные каналы/группы/чаты;\n1. Канал 1\n2. Группа 1\n3. Канал 2\n\n\nЧтобы перейти в соответсвующий канал/группу/чат, нажмите на кнопки ниже',
                                   reply_markup=kb.my_subscriptions_traning)
     
# Admin

@router.message(Command('admin'))
async def start_admin(message: Message):
     try:
          await message.bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 1)
     except Exception as e:
          print(f"Не удалось удалить сообщение: {e}")
          
     if message.from_user.id in ADMIN_IDS:
          await message.answer('👋Добро пожаловать в админ-панель! Выберите действие:',
                               reply_markup=kb.admin)
     else:
          await message.answer(f'У тебя нет доступа к этой команде.{message.from_user.id}')


@router.callback_query(F.data == 'admin')
async def admin(callback: CallbackQuery):
     await callback.message.delete()
     await callback.answer('')
     await callback.message.answer('👋Добро пожаловать в админ-панель! Выберите действие:',
                                   reply_markup=kb.admin)

@router.callback_query(F.data == 'subscription_management')
async def subscription_management(callback: CallbackQuery):
     await callback.message.delete()
     await callback.answer('')
     await callback.message.answer('Управление подписками:',
                                   reply_markup=kb.subscription_management)

# Процес создание подписки
@router.callback_query(F.data == 'add_subscription')
async def add_subscription(callback: CallbackQuery, state: FSMContext):
     await callback.message.delete()
     await callback.answer('')
     await callback.message.answer('Пожалуйста, введите название подписки:')
     await state.set_state(SubscriptionForm.name)

@router.message(SubscriptionForm.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Отлично! Теперь введите описание подписки:")
    await state.set_state(SubscriptionForm.description)

@router.message(SubscriptionForm.description)
async def process_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Отлично! Теперь добавьте этого бота в администраторы указанных каналов и отправьте ID ваших каналов через запятую.")
    await state.set_state(SubscriptionForm.id_channels)
    
# создание подписки
@router.message(SubscriptionForm.id_channels)
async def process_channels(message: Message, state: FSMContext):
     input_text = message.text.strip()
     raw_ids = [channel.strip() for channel in input_text.split(',')]
     full_ids = []

     for cid in raw_ids:
          if not cid.startswith("-"):
           cid = f"-{cid}"

        # Проверка формата
          if not re.fullmatch(r"^-100\d{5,}$", cid):
               await message.answer(f"На Канал {cid} бот не добавлен в администраторы.")
               return

          try:
            chat_member = await message.bot.get_chat_member(cid, message.bot.id)
          except (TelegramForbiddenError, TelegramBadRequest):
            await message.answer(f"На Канал {cid} бот не добавлен в администраторы.")
            return

          if chat_member.status not in ['administrator', 'creator']:
            await message.answer(f"На Канал {cid} бот не добавлен в администраторы.")
            return

          full_ids.append(cid)

    # Сохран
     combined_ids = ",".join(full_ids)
     await state.update_data(id_channels=combined_ids)
     data = await state.get_data()

     async with async_session() as session:
          new_sub = Subscription(
               name=data['name'],
               description=data['description'],
               id_channels=combined_ids,
               user_id=message.from_user.id
          )
          session.add(new_sub)
          await session.commit()

     await message.answer(
        f"Подписка создана успешно!\nНазвание: {data['name']},\nОписание: {data['description']}\nКаналы: {combined_ids}",
        reply_markup=kb.add_subscription
     )

     await state.clear()

     
# ----------------------------------------------
# 
@router.callback_query(F.data == 'user_management')
async def user_management(callback: CallbackQuery):
     await callback.message.delete()
     await callback.answer('')
     await callback.message.answer('Выберите нужное действие:',
                                   reply_markup=kb.user_management)
     

@router.callback_query(F.data == 'user_list')
async def add_subscription(callback: CallbackQuery):
     async with async_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()

     await callback.message.delete()
     await callback.answer('')
     
     text = ''
     for user in users:
         text += (
             f"{user.id}. Пользователь: @{user.user_name}\n"
             f"- ID пользователя: {user.user_id}\n"
             f"- Телефон: +{user.user_phone}\n"
             f"- Gmail: {user.user_email}\n"
             '\n\n'
         )

     await callback.message.answer(text, reply_markup=kb.user_list)

# Редактирование подписки
@router.callback_query(F.data == 'edit_subscription')
async def edit_subscription(callback: CallbackQuery):
     await callback.message.delete()
     await callback.answer('')
     await callback.message.answer('Выберите подписку для редактирования:',
                                   reply_markup=await kb.edit_subscription())
     
# Работа с редактированием подписки
# ловит callback-запросы которые начинаются с sub_
@router.callback_query(lambda c: c.data.startswith("sub_"))
# Функция который ловит callback data.
async def show_subscription_details(callback: CallbackQuery):
     # извлекаем id из callback data.
     sub_id = int(callback.data.split("_")[1])
     # передаём id подписки в клавиатуру
     keyboard = kb.get_subscription_detail_keyboard(sub_id)
     #  выводим текст и клавиатуру
     await callback.message.edit_text("Что вы хотите изменить в подписке «Подписка на обучение»??", reply_markup=keyboard)

# FSM состояние, в котором бот ждёт ввода нового значения поля от пользователя.
class EditSubscription(StatesGroup):
    waiting_for_new_value = State()

# Этот хендлер срабатывает, если пользователь нажимает на одну из кнопок, где callback_data начинается с:
@router.callback_query(lambda c: c.data.startswith(("name_", "description_", "channels_")))
# Функция которая принимает callback и состояние
async def ask_new_value(callback: CallbackQuery, state: FSMContext):
     # Разделяем строку по "_", получаем
     # field = name, description, channels
     # sub_id = id
     field, sub_id = callback.data.split("_")
     
     async with async_session() as session:
          #  Подключаемся к базе данных.  Ищем подписку с нужным ID.
          result = await session.execute(select(Subscription).where(Subscription.id == sub_id))
          subscription = result.scalar_one_or_none()

     #  Сохраняем ID подписки и поле, которое нужно изменить, чтобы потом (на следующем шаге) использовать их.
     await state.update_data(sub_id=int(sub_id), field=field)

     # Просто для того, чтобы красиво отобразить в тексте (на русском языке), какое именно поле пользователь редактирует.
     field_names = {
         "name": "Пожалуйста, введите новое название для подписки:",
         "description": "Пожалуйста, введите новое описание для подписки:",
         "channels": f"""
Текущие каналы и группы для подписки «{subscription.name}»: 
{subscription.id_channels}
Пожалуйста, введите  ID новых каналов и групп через запятую, чтобы заменить текущие. И добавьте этого бота в администраторы указанных каналов"""
     }
     # удаление старого сообщения с кнопками
     await callback.message.delete()
     await callback.message.answer(f"{field_names[field]}")
     # Установка состояния 
     await state.set_state(EditSubscription.waiting_for_new_value)


# для редактирования подписки
# Этот хендлер срабатывает, когда бот в состоянии waiting_for_new_value
@router.message(EditSubscription.waiting_for_new_value)
async def process_new_value(message: Message, state: FSMContext):
     # возвращает ранее сохранённые данные (sub_id, field)
     data = await state.get_data()
     sub_id = data["sub_id"]
     field = data["field"]
     # новое значение, которое ввёл пользователь.
     new_value = message.text
 
     async with async_session() as session:
          #  Подключаемся к базе данных.  Ищем подписку с нужным ID.
          result = await session.execute(select(Subscription).where(Subscription.id == sub_id))
          subscription = result.scalar_one_or_none()
          # Если не нашли — отправляем сообщение об ошибке:
          if not subscription:
              await message.answer("❌ Подписка не найдена.")
              await state.clear()
              return

          # Меняем нужное поле
          if field == "name":
               subscription.name = new_value
               await message.answer(f"Название подписки успешно изменено на «{new_value}».",
               reply_markup=kb.back_sub)
          elif field == "description":
               subscription.description = new_value
               await message.answer(f"Описание подписки успешно изменено на «{new_value}».",
               reply_markup=kb.back_sub)
          elif field == "channels":
               raw_ids = [cid.strip() for cid in new_value.split(',')]
               full_ids = []

               for cid in raw_ids:
                    if not cid.startswith("-"):
                        cid = f"-{cid}"

                    if not re.fullmatch(r"^-100\d{5,}$", cid):
                        await message.answer(f"На Канал {cid} бот не добавлен в администраторы.")
                        return

                    try:
                        chat_member = await message.bot.get_chat_member(cid, message.bot.id)
                    except (TelegramForbiddenError, TelegramBadRequest):
                        await message.answer(f"На Канал {cid} бот не добавлен в администраторы.")
                        return

                    if chat_member.status not in ['administrator', 'creator']:
                        await message.answer(f"На Канал {cid} бот не добавлен в администраторы.")
                        return

                    full_ids.append(cid)

               valid_ids = ", ".join(full_ids)
               subscription.id_channels = valid_ids
               await message.answer(f"Каналы и группы для подписки успешно обновлены. Новые каналы: {valid_ids}.",
               reply_markup=kb.back_sub)

          await session.commit()

     # закрываем состояние
     await state.clear()

# для скрытия подписки.
@router.callback_query(F.data == 'hide_subscription')
async def hide_subscription(callback: CallbackQuery):
     await callback.message.delete()
     await callback.answer('')
     await callback.message.answer('Выберите подписку, которую вы хотите скрыть:',
                                   reply_markup=await kb.hide_subscription())
     
@router.callback_query(lambda c: c.data.startswith("hide_"))
async def hide_subscription(callback: CallbackQuery):
     hide_id = int(callback.data.split("_")[1])
     async with async_session() as session:
          result = await session.execute(select(Subscription).where(Subscription.id == hide_id))
          subscription = result.scalars().first()
          subscription.is_hidden = True

          sub_name = subscription.name
          await session.commit()


          await callback.message.edit_text(f'Подписка «{sub_name}» успешно скрыта. Она будет недоступна пользователям, но вся статистика сохранится.',
                                           reply_markup=kb.back_sub)

@router.callback_query(F.data == 'restore_subscription')
async def restore_subscription(callback: CallbackQuery):
     await callback.message.delete()
     await callback.answer('')
     await callback.message.answer('Выберите подписку, которую вы хотите восстановить:',
                                   reply_markup=await kb.restore_subscription())
     

@router.callback_query(lambda c: c.data.startswith("res_"))
async def res_subscription(callback: CallbackQuery):
     res_id = int(callback.data.split('_')[1])

     async with async_session() as session:
          result = await session.execute(select(Subscription).where(Subscription.id == res_id))
          subscription = result.scalars().first()
          subscription.is_hidden = False
          res_name = subscription.name
          await session.commit()

          await callback.message.edit_text(f'Подписка «{res_name}» успешно восстановлена и снова доступна пользователям.',
                                        reply_markup=kb.back_sub)
          
@router.callback_query(F.data == "delete_subscription")
async def delete_subscription(callback: CallbackQuery):
     await callback.message.delete()
     await callback.answer('')
     await callback.message.answer('Выберите подписку для удаления:', 
                                   reply_markup=await kb.delete_subscription())
     

@router.callback_query(lambda c: c.data.startswith('del_'))
async def del_subscription(callback: CallbackQuery):
     del_id = int(callback.data.split('_')[1])

     async with async_session() as session:
          result = await session.execute(select(Subscription).where(Subscription.id == del_id))
          subscription = result.scalars().first()
          sub_name = subscription.name

          await callback.message.edit_text(f'Вы уверены, что хотите удалить подписку «{sub_name}»? Это действие нельзя отменить.',
                                        reply_markup=await kb.delete__sub(del_id))
          
@router.callback_query(lambda c: c.data.startswith('delete_'))
async def delete_sub(callback: CallbackQuery):
     del_id = int(callback.data.split('_')[1])
     async with async_session() as session:
          result = await session.execute(select(Subscription).where(Subscription.id == del_id))
          subscription = result.scalars().first()

          if subscription:
               await session.execute(delete(Subscription).where(Subscription.id == del_id))
               await session.commit()
               await callback.message.edit_text(f'Подписка «{subscription.name}» успешно удалена.',
                                                reply_markup=kb.back_sub)



