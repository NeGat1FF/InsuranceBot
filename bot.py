import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    filters,
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
)
from services.mindee_api import process_passport, process_vehicle
from services.openai_api import generate_response, generate_policy, confirm_details
from config import config


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

PASSPORT_STATE = "Awaiting Passport Photo"
PASSPORT_CONFIRMATION_STATE = "Awaiting Passport Confirmation"
VEHICLE_STATE = "Awaiting Vehicle Registration Photo"
VEHICLE_CONFIRMATION_STATE = "Awaiting Vehicle Registration Confirmation"
PRICE_CONFIRMATION_STATE = "Awaiting Price Confirmation"
FINISHED_STATE = "Finished"

YES_BTN = InlineKeyboardButton("Yes", callback_data="yes_btn")
NO_BTN = InlineKeyboardButton("No", callback_data="no_btn")

welcome_message = """👋 Hello! I'm your assistant for purchasing car insurance.

To get started, please send me:
📄 A clear photo of your passport  

I'll extract the necessary details, confirm them with you, and issue a policy once everything checks out.

Let’s begin when you’re ready!"""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["state"] = PASSPORT_STATE
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=welcome_message
    )


async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if (
        context.user_data.get("state") != PASSPORT_STATE
        and context.user_data.get("state") != VEHICLE_STATE
    ):
        response = await generate_response(
            f"User sent a photo, but the bot is not in a state to process it. Current state: {context.user_data.get('state')}"
        )
        await context.bot.send_message(chat_id=update.effective_chat.id, text=response)
        return
    doc_info = update.message.document
    if not doc_info:
        doc_info = update.message.photo[-1]  # Get the highest resolution photo
    doc = await doc_info.get_file()
    filename = doc.file_path.split("/")[-1]  # Extract filename from file path
    doc_bytes = await doc.download_as_bytearray()
    result = None
    try:
        if context.user_data.get("state") == PASSPORT_STATE:
            result = process_passport(doc_bytes, filename)
            context.user_data["passport_data"] = result
        elif context.user_data.get("state") == VEHICLE_STATE:
            result = process_vehicle(doc_bytes, filename)
            context.user_data["vehicle_data"] = result
    except Exception as e:
        try:
            response = await generate_response(
                f"Error processing document: {e}. Tell the user what is wrong and what to do."
            )
        except Exception as e2:
            response = f"An error occurred while processing your document: {e2}. Please try again"
        await context.bot.send_message(chat_id=update.effective_chat.id, text=response)
        return
    try:
        response = await generate_response(
            f"Extracted details: {result}. Ask user to confirm if they are correct."
        )
    except Exception as e:
        response = (
            f"An error occurred while generating the response: {e}. Please try again."
        )
    if context.user_data.get("state") == PASSPORT_STATE:
        context.user_data["state"] = PASSPORT_CONFIRMATION_STATE
    elif context.user_data.get("state") == VEHICLE_STATE:
        context.user_data["state"] = VEHICLE_CONFIRMATION_STATE
    context.user_data["confirmation_prompt"] = response
    await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=response,
            reply_markup=InlineKeyboardMarkup([[YES_BTN, NO_BTN]]),
        )


async def handle_states(update, context, query=None):
    try:
        if update.message:
            user_input = update.message.text
        elif update.callback_query:
            user_input = update.callback_query.data
        else:
            user_input = ""

        if query:
            chat_id = query.message.chat.id
        else:
            chat_id = update.effective_chat.id

        state = context.user_data.get("state")
        if state in [
            PASSPORT_CONFIRMATION_STATE,
            VEHICLE_CONFIRMATION_STATE,
            PRICE_CONFIRMATION_STATE,
        ]:
            if query:
                if query.data == "yes_btn":
                    confirmation = "confirmed"
                else:
                    confirmation = "rejected"
            else:
                try:
                    confirmation = await confirm_details(
                        f"Confirmation prompt: {context.user_data.get('confirmation_prompt')}\nUser response: {user_input}"
                    )
                except Exception as e:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text="Couldn't interpret your reply. Please respond clearly.",
                    )
                    return

            print(f"Confirmation received: {confirmation}")
            if confirmation == "confirmed":
                if state == PASSPORT_CONFIRMATION_STATE:
                    context.user_data["state"] = VEHICLE_STATE
                    try:
                        response = await generate_response(
                            f"Passport details confirmed. Now ask the user to send a clear photo of their vehicle registration document. CURRENT STATE: {context.user_data.get('state')}"
                        )
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text=response,
                        )
                    except Exception:
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text="Something went wrong while generating the next instruction.",
                        )

                elif state == VEHICLE_CONFIRMATION_STATE:
                    context.user_data["state"] = PRICE_CONFIRMATION_STATE
                    try:
                        response = await generate_response(
                            f"Vehicle details confirmed. Now inform the user that the insurance price is fixed at 100 USD and ask them to confirm if they want to proceed with the purchase. CURRENT STATE: {context.user_data.get('state')}"
                        )
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text=response,
                            reply_markup=InlineKeyboardMarkup([[YES_BTN, NO_BTN]]),
                        )
                    except Exception:
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text="Failed to generate the next step. Please try again.",
                        )

                elif state == PRICE_CONFIRMATION_STATE:
                    context.user_data["state"] = FINISHED_STATE
                    try:
                        response = await generate_response(
                            f"User confirmed the price. Confirm proceeding with insurance policy. It will be ready in few seconds. CURRENT STATE: {context.user_data.get('state')}"
                        )
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text=response,
                        )
                    except Exception:
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text="Couldn't continue after price confirmation. Try again later.",
                        )
                        return

                    try:
                        policy = await generate_policy(
                            context.user_data.get("passport_data"),
                            context.user_data.get("vehicle_data"),
                        )
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text=f"Your insurance policy has been generated:\n{policy}",
                        )
                    except Exception:
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text="Failed to generate your policy. Please try again later.",
                        )
            else:
                # Rejection flow
                try:
                    if state == PASSPORT_CONFIRMATION_STATE:
                        context.user_data["state"] = PASSPORT_STATE
                        response = await generate_response(
                            f"User rejected the passport details. Ask to provide it again. Current state: {context.user_data.get('state')}."
                        )
                    elif state == VEHICLE_CONFIRMATION_STATE:
                        context.user_data["state"] = VEHICLE_STATE
                        response = await generate_response(
                            f"User rejected the vehicle details. Ask to provide it again. Current state: {context.user_data.get('state')}."
                        )
                    elif state == PRICE_CONFIRMATION_STATE:
                        response = await generate_response(
                            f"User rejected the price. Inform them that the price is fixed at 100 USD and cannot be changed. CURRENT STATE: {context.user_data.get('state')}"
                        )
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=response,
                    )
                except Exception:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text="Something went wrong processing your answer. Please try again.",
                    )
        else:
            response = await generate_response(f"{user_input}. Current state: {state}.")
            await context.bot.send_message(chat_id=chat_id, text=response)
    except Exception as e:
        await context.bot.send_message(
            chat_id=chat_id,
            text="An unexpected error occurred. Please try again later.",
        )
        print(f"Exception in text handler: {e}")


async def text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Received text: {update.message.text}")
    await handle_states(update, context)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Received button callback: {update.callback_query.data}")
    query = update.callback_query
    await query.answer()  # Acknowledge the callback query
    await handle_states(update, context, query)


if __name__ == "__main__":
    application = ApplicationBuilder().token(config.BOT_TOKEN).build()
    start_handler = CommandHandler("start", start)
    photo_handler = MessageHandler(filters=filters.ATTACHMENT, callback=photo)
    text_handler = MessageHandler(filters=filters.TEXT, callback=text)
    button_handler = CallbackQueryHandler(button)

    application.add_handlers(
        [start_handler, photo_handler, text_handler, button_handler]
    )

    application.run_polling()
