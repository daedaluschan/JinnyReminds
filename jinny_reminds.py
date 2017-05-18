import logging
from datetime import date
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
                          ConversationHandler)
from telegram import replykeyboardmarkup
from telegram import replykeyboardremove
from jinny_reminds_cfg import *
from jinny_reminds_static import *
from functools import wraps


# decorator to restrict the use of the functions from unauthorized users
def restricted(func):
    @wraps(func)
    def wrapped(bot, update, *args, **kwargs):
        # extract user_id from arbitrary update
        try:
            user_id = update.message.from_user.id
        except (NameError, AttributeError):
            try:
                user_id = update.inline_query.from_user.id
            except (NameError, AttributeError):
                try:
                    user_id = update.chosen_inline_result.from_user.id
                except (NameError, AttributeError):
                    try:
                        user_id = update.callback_query.from_user.id
                    except (NameError, AttributeError):
                        print("No user_id available in update.")
                        logging.info("No user_id available in update.")
                        return
        if user_id not in LIST_OF_ADMINS:
            logging.info(log_i_dont_know_u.format(user_id))
            bot.sendMessage(chat_id=update.message.chat_id, text=msg_i_dont_know_u)
            return
        return func(bot, update, *args, **kwargs)
    return wrapped

@restricted
def start(bot, update):
    markup = replykeyboardmarkup.ReplyKeyboardMarkup(keyboard=keyboard_start)
    bot.sendMessage(chat_id=update.message.chat_id, text=msg_greeting,
                    reply_markup=markup)

ITEM_NAME, END_DATE, REMIND_DATE = range(3)

@restricted
def add_new_memo(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text=msg_memo_name,
                    reply_markup=replykeyboardremove.ReplyKeyboardRemove())
    return ITEM_NAME

@restricted
def memo_name(bot, update):
    markup = replykeyboardmarkup.ReplyKeyboardMarkup(keyboard=keyboard_end_date)
    bot.sendMessage(chat_id=update.message.chat_id, text=msg_end_date,
                    reply_markup=markup)
    return END_DATE

@restricted
def end_date(bot, update):
    markup = replykeyboardmarkup.ReplyKeyboardMarkup(keyboard=keyboard_remind_date)
    bot.sendMessage(chat_id=update.message.chat_id, text=msg_remind_date,
                    reply_markup=markup)
    return REMIND_DATE

@restricted
def remind_date(bot, update):
    markup = replykeyboardmarkup.ReplyKeyboardMarkup(keyboard=keyboard_start)
    bot.sendMessage(chat_id=update.message.chat_id, text=msg_done_add,
                    reply_markup=markup)
    return -1

def fallback(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text=msg_dont_understand)
    return None

def main():
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG,
                        filename="logs/JinnyReminds." + str(date.today()) + ".log")

    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start))

    dispatcher.add_handler(ConversationHandler(entry_points=[RegexHandler(button_new_memo, add_new_memo)],
                                               states={ITEM_NAME: [MessageHandler(Filters.text, memo_name)],
                                                       END_DATE: [MessageHandler(Filters.text,end_date)],
                                                       REMIND_DATE: [MessageHandler(Filters.text, remind_date)]},
                                               fallbacks=[MessageHandler(Filters.text, fallback)],
                                               run_async_timeout=conv_time_out)
                           )

    updater.start_polling()



if __name__ == '__main__':
    main()
