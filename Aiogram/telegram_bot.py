import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ContentType
from aiogram.dispatcher.storage import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

TOKEN = ""

bot = Bot(TOKEN)

bot_info = None

async def fetch_bot_info():
    global bot_info
    bot_info = await bot.get_me()

asyncio.run(fetch_bot_info())

storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage) 

class CreateTicketState(StatesGroup):
    subject = State()
    description = State()

predefined_subjects = ["Technical Issue", "Billing Inquiry", "Feature Request", "Other"]

async def main():
    global bot_info
    bot_info = await fetch_bot_info(bot)
    if bot_info:
        print(f"Bot Info: {bot_info}")

@dp.message_handler(commands=['start'])
async def command_start_handler(message: Message) -> None:
    """
    This handler sends a welcome message with a button.
    """
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("Create a ticket"))

    await message.answer("Hello, welcome to the bot! Please use one of the buttons below", reply_markup=markup)

@dp.message_handler(lambda message: bot_info.username in message.text)
async def mention_handler(message: Message, state: FSMContext) -> None:
    """
    Respond to mentions with a welcome message.
    """
    print("Mention detected")

    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("Create a ticket"))
    await message.answer("Hello, welcome to the bot! Please use one of the buttons below", reply_markup=markup)

    return

@dp.message_handler(lambda message: message.text == "Create a ticket")
async def create_ticket_handler(message: Message, state: FSMContext) -> None:
    """
    This handler allows the user to select the subject of the ticket using buttons.
    """
    subject_markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True, row_width=1)
    for subject in predefined_subjects:
        subject_markup.add(KeyboardButton(subject))

    await message.answer("Please select the subject of the ticket:", reply_markup=subject_markup)
    await CreateTicketState.subject.set()

@dp.message_handler(state=CreateTicketState.subject)
async def process_subject(message: Message, state: FSMContext) -> None:
    """
    Process the selected subject and prompt the user for the description.
    """
    selected_subject = message.text

    if selected_subject not in predefined_subjects:
        await message.answer("Please select a valid subject from the provided options.")
        return

    await state.update_data(subject=selected_subject)
    await message.answer(f"Subject: {selected_subject}\n\nPlease enter the description of the ticket:", reply_markup=ReplyKeyboardMarkup(resize_keyboard=True, selective=True, row_width=1).add(KeyboardButton("Cancel")))
    await CreateTicketState.description.set()

@dp.message_handler(state=CreateTicketState.description, content_types=[types.ContentType.PHOTO, types.ContentType.TEXT])
async def process_description(message: Message, state: FSMContext) -> None:
    """
    Process the description.
    """
    subject_data = await state.get_data()
    subject = subject_data.get('subject', 'No Subject')

    user_full_name = f"{message.from_user.first_name} {message.from_user.last_name}"
    user_mention = message.from_user.get_mention(as_html=True)

    if 'photo_id_subject' in subject_data:
        photo_id_subject = subject_data['photo_id_subject']

    if message.content_type == types.ContentType.TEXT:
        description = message.text

        ticket_info = f"Ticket created!\n\n{subject}\nDescription: {description}\n\nCreated by: {user_full_name} ({user_mention})"

        await message.answer(ticket_info, parse_mode=types.ParseMode.HTML)

    if message.content_type == types.ContentType.PHOTO:
        photo_id_description = message.photo[-1].file_id
        caption = f"Photo Caption: {message.caption}" if message.caption else "No caption"

        ticket_info = f"Ticket created!\n\n{subject}\nDescription: {caption}\n\nCreated by: {user_full_name} ({user_mention})"
        await message.answer(ticket_info, parse_mode=types.ParseMode.HTML)

        if 'photo_id_subject' in subject_data:
            await bot.send_photo(message.chat.id, photo_id_subject)

        await bot.send_photo(message.chat.id, photo_id_description)

    await state.finish()

@dp.message_handler(state=CreateTicketState.description, content_types=[types.ContentType.VOICE])
async def process_voice_message_description(message: Message, state: FSMContext) -> None:
    """
    Handle voice messages for the description.
    """
    description = f"Voice message for description: {message.caption if message.caption else 'No caption'}"
    subject_data = await state.get_data()
    subject = subject_data.get('subject', 'No Subject')

    user_full_name = f"{message.from_user.first_name} {message.from_user.last_name}"
    user_mention = message.from_user.get_mention(as_html=True)

    await state.finish()
    final_message = f"Ticket created!\n\nSubject: {subject}\nDescription: {description}\n\nCreated by: {user_full_name} ({user_mention})"

    await message.answer(final_message, parse_mode=types.ParseMode.HTML)

@dp.message_handler(lambda message: message.content_type == ContentType.TEXT and 'http' in message.text)
async def process_link(message: Message, state: FSMContext) -> None:
    """
    Handle messages containing links.
    """
    link = message.text
    subject_data = await state.get_data()
    subject = subject_data.get('subject', 'No Subject')

    user_full_name = f"{message.from_user.first_name} {message.from_user.last_name}"
    user_mention = message.from_user.get_mention(as_html=True)

    await state.finish()
    final_message = f"Ticket created!\n\nSubject: {subject}\nDescription: Link - {link}\n\nCreated by: {user_full_name} ({user_mention})"

    await message.answer(final_message, parse_mode=types.ParseMode.HTML)    

async def main() -> None:
    await dp.start_polling()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
    asyncio.run(dp.start_polling())
