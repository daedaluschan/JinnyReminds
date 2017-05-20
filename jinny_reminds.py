import logging
#import calendar
#from datetime import date
from jinny_memo import *
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
                          ConversationHandler)
from telegram import replykeyboardmarkup
from telegram import replykeyboardremove
from jinny_reminds_cfg import *
from jinny_reminds_static import *
from functools import wraps
from itertools import islice

memos = {}

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

ITEM_NAME, END_DATE, REMIND_DATE, END_DATE_CALENDAR = range(4)

@restricted
def add_new_memo(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text=msg_memo_name,
                    reply_markup=replykeyboardremove.ReplyKeyboardRemove())

    if update.message.chat_id in memos:
        del memos[update.message.chat_id]

    memos[update.message.chat_id] = memo()
    logging.info(memos[update.message.chat_id].__str__())

    return ITEM_NAME

@restricted
def memo_name(bot, update):
    memos[update.message.chat_id].memo_text = update.message.text

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

    del memos[update.message.chat_id]
    return -1

def gen_calendar_keyboard(yr, mth):
    c = calendar.TextCalendar()
    text_outputs = c.formatmonth(yr, mth).splitlines()
    mth_text = text_outputs[0]

    keyboard = []
    keyboard.append([mth_text])
    keyboard.append(text_outputs[1].split())

    for row in islice(text_outputs, 2, len(text_outputs)):
        days_of_month = row.split()
        if (len(days_of_month)<7):
            num_white_space = 7 - len(days_of_month)
            if days_of_month[0] == "1":
                for i in range(num_white_space):
                    days_of_month = [" "] + days_of_month
            else:
                for i in range(num_white_space):
                    days_of_month = days_of_month + [" "]
        keyboard.append(days_of_month)

    keyboard = [[button_prev_mth, button_next_mth]] + keyboard
    return keyboard

@restricted
def end_date_calendar(bot, update):
    calendar_date = date.today()
    markup = replykeyboardmarkup.ReplyKeyboardMarkup(keyboard=gen_calendar_keyboard(calendar_date.year, calendar_date.month))

    logging.info("before send calendar")
    # logging.info(markup_pkg)
    bot.sendMessage(chat_id=update.message.chat_id,
                    text=msg_pls_choose_date,
                    reply_markup=markup)
    logging.info("after send calendar")
    return END_DATE_CALENDAR

@restricted
def set_end_date(bot, update, yyyy, mm, dd):
    obj_date = date(yyyy, mm, dd)
    memos[update.message.chat_id].memo_end_date = obj_date
    bot.sendMessage(chat_id=update.message.chat_id,
                    text=msg_input_date.format(memos[update.message.chat_id].memo_end_date.__str__()))

@restricted
def end_date_click_num(bot, update):
    set_end_date(bot, update,
                 memos[update.message.chat_id].moving_year,
                 memos[update.message.chat_id].moving_mth,
                 int(update.message.text))

    markup = replykeyboardmarkup.ReplyKeyboardMarkup(keyboard=keyboard_remind_date)
    bot.sendMessage(chat_id=update.message.chat_id, text=msg_remind_date,
                    reply_markup=markup)
    return REMIND_DATE

@restricted
def end_date_prev_mth(bot, update):
    curr_year = memos[update.message.chat_id].moving_year
    curr_mth = memos[update.message.chat_id].moving_mth

    if curr_mth == 1:
        curr_mth = 12
        curr_year = curr_year - 1
    else:
        curr_mth = curr_mth - 1

    memos[update.message.chat_id].moving_year = curr_year
    memos[update.message.chat_id].moving_mth = curr_mth

    markup = replykeyboardmarkup.ReplyKeyboardMarkup(keyboard=gen_calendar_keyboard(curr_year, curr_mth))
    bot.sendMessage(chat_id=update.message.chat_id,
                    text=msg_confirm_curr_mth.format(curr_mth.__str__()), reply_markup=markup)
    return None

@restricted
def end_date_next_mth(bot, update):
    curr_year = memos[update.message.chat_id].moving_year
    curr_mth = memos[update.message.chat_id].moving_mth

    if curr_mth == 12:
        curr_mth = 1
        curr_year = curr_year + 1
    else:
        curr_mth = curr_mth + 1

    memos[update.message.chat_id].moving_year = curr_year
    memos[update.message.chat_id].moving_mth = curr_mth

    markup = replykeyboardmarkup.ReplyKeyboardMarkup(keyboard=gen_calendar_keyboard(curr_year, curr_mth))
    bot.sendMessage(chat_id=update.message.chat_id,
                    text=msg_confirm_curr_mth.format(curr_mth.__str__()), reply_markup=markup)
    return None

@restricted
def end_date_invalid(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id,
                    text=msg_invalid_date_pick)
    return END_DATE_CALENDAR

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
                                                       END_DATE: [RegexHandler(button_specific_date, end_date_calendar),
                                                                  MessageHandler(Filters.text,end_date)],
                                                       END_DATE_CALENDAR: [RegexHandler('\d+', end_date_click_num),
                                                                           RegexHandler(button_prev_mth, end_date_prev_mth),
                                                                           RegexHandler(button_next_mth, end_date_next_mth),
                                                                           MessageHandler(Filters.text, end_date_invalid)],
                                                       REMIND_DATE: [MessageHandler(Filters.text, remind_date)]},
                                               fallbacks=[MessageHandler(Filters.text, fallback)],
                                               run_async_timeout=conv_time_out)
                           )

    updater.start_polling()



if __name__ == '__main__':
    main()
