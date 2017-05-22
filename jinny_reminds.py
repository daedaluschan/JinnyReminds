import logging
#import calendar
#from datetime import date
from datetime import timedelta
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
ITEM_NAME, END_DATE, REMIND_DATE, END_DATE_CALENDAR, REMIND_DATE_CALENDAR, SHOW_ALL = range(6)

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

#@restricted
#def end_date(bot, update):
#    markup = replykeyboardmarkup.ReplyKeyboardMarkup(keyboard=keyboard_remind_date)
#    bot.sendMessage(chat_id=update.message.chat_id, text=msg_remind_date,
#                    reply_markup=markup)
#    return REMIND_DATE

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

    markup = replykeyboardmarkup.ReplyKeyboardMarkup(keyboard=keyboard_remind_date)
    bot.sendMessage(chat_id=update.message.chat_id, text=msg_remind_date,
                    reply_markup=markup)

@restricted
def end_date_click_num(bot, update):
    set_end_date(bot, update,
                 memos[update.message.chat_id].moving_year,
                 memos[update.message.chat_id].moving_mth,
                 int(update.message.text))

    return REMIND_DATE

@restricted
def end_date_fix_tenor(bot, update):
    reference_date = date.today()
    if update.message.text == button_1W:
        obj_date = reference_date + timedelta(days=7)
    elif update.message.text == button_2W:
        obj_date = reference_date + timedelta(days=14)
    elif update.message.text == button_3W:
        obj_date = reference_date + timedelta(days=21)
    elif update.message.text == button_1M:
        obj_date = reference_date + timedelta(days=30)
    elif update.message.text == button_2M:
        obj_date = reference_date + timedelta(days=60)
    elif update.message.text == button_3M:
        obj_date = reference_date + timedelta(days=91)
    elif update.message.text == button_6M:
        obj_date = reference_date + timedelta(days=182)
    elif update.message.text == button_1Y:
        obj_date = reference_date + timedelta(days=365)
    else:
        bot.sendMessage(chat_id=update.message.chat_id, text=msg_cannot_process_date_input)
        return None

    set_end_date(bot, update, obj_date.year, obj_date.month, obj_date.day)
    return  REMIND_DATE

@restricted
def prev_mth(bot, update):
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
                    text=msg_confirm_curr_mth.format(curr_year.__str__(), curr_mth.__str__()),
                    reply_markup=markup)
    return None

@restricted
def next_mth(bot, update):
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
                    text=msg_confirm_curr_mth.format(curr_year.__str__(), curr_mth.__str__()),
                    reply_markup=markup)
    return None

@restricted
def remind_date_calendar(bot, update):
    markup = replykeyboardmarkup.ReplyKeyboardMarkup(keyboard=gen_calendar_keyboard(memos[update.message.chat_id].moving_year,
                                                                                    memos[update.message.chat_id].moving_mth))

    bot.sendMessage(chat_id=update.message.chat_id,
                    text=msg_pls_choose_date,
                    reply_markup=markup)

    return REMIND_DATE_CALENDAR

@restricted
def set_remind_date(bot, update, yyyy, mm, dd):
    obj_date = date(yyyy, mm, dd)
    memos[update.message.chat_id].remind_date = obj_date
    bot.sendMessage(chat_id=update.message.chat_id,
                    text=msg_input_date.format(memos[update.message.chat_id].remind_date.__str__()))

    markup = replykeyboardmarkup.ReplyKeyboardMarkup(keyboard=keyboard_start)
    bot.sendMessage(chat_id=update.message.chat_id, text=msg_done_add,
                    reply_markup=markup)

    memos[update.message.chat_id].save_data()

    del memos[update.message.chat_id]

@restricted
def remind_date_click_num(bot, update):
    set_remind_date(bot, update,
                    memos[update.message.chat_id].moving_year,
                    memos[update.message.chat_id].moving_mth,
                    int(update.message.text))
    return -1

@restricted
def remind_date_fix_tenor(bot, update):
    reference_date = memos[update.message.chat_id].memo_end_date

    if update.message.text == button_remind_1D:
        obj_date = reference_date + timedelta(days=-1)
    elif update.message.text == button_remind_3D:
        obj_date = reference_date + timedelta(days=-3)
    elif update.message.text == button_remind_1W:
        obj_date = reference_date + timedelta(days=-7)
    elif update.message.text == button_remind_10D:
        obj_date = reference_date + timedelta(days=-10)
    elif update.message.text == button_remind_2W:
        obj_date = reference_date + timedelta(days=-14)
    elif update.message.text == button_remind_3W:
        obj_date = reference_date + timedelta(days=-21)
    elif update.message.text == button_remind_1M:
        obj_date = reference_date + timedelta(days=-30)
    else:
        bot.sendMessage(chat_id=update.message.chat_id, text=msg_cannot_process_date_input)
        return None

    set_remind_date(bot, update, obj_date.year, obj_date.month, obj_date.day)
    return  -1

@restricted
def end_date_invalid(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id,
                    text=msg_invalid_date_pick)
    return END_DATE_CALENDAR

@restricted
def remind_date_invalid(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id,
                    text=msg_invalid_date_pick)
    return REMIND_DATE_CALENDAR

def fallback(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text=msg_dont_understand)
    return None

def show_all(bot, update):
    keyboard_list = [[button_confirm]]
    print("keyboard before loop: {}".format(keyboard_list))
    for each_memo in get_all_memos():
        keyboard_list.append([each_memo["item"]])
        print("each memo: {}".format(each_memo))
        print("keyboard in each loop: {}".format(keyboard_list))

    markup = replykeyboardmarkup.ReplyKeyboardMarkup(keyboard=keyboard_list)

    bot.sendMessage(chat_id=update.message.chat_id, text=msg_all_memos_as_show, markup=markup)


def show_all_confirmed(bot, update):
    markup = replykeyboardmarkup.ReplyKeyboardMarkup(keyboard=keyboard_start)
    bot.sendMessage(chat_id=update.message.chat_id, text=msg_greeting,
                    reply_markup=markup)
    return -1

def main():
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG,
                        filename="logs/JinnyReminds." + str(date.today()) + ".log")

    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start))

    dispatcher.add_handler(ConversationHandler(entry_points=[RegexHandler(button_show_all, show_all)],
                                               states={SHOW_ALL: [RegexHandler(button_confirm, show_all_confirmed)]},
                                               fallbacks=[MessageHandler(Filters.text, fallback)],
                                               run_async_timeout=conv_time_out))

    dispatcher.add_handler(ConversationHandler(entry_points=[RegexHandler(button_new_memo, add_new_memo)],
                                               states={ITEM_NAME: [MessageHandler(Filters.text, memo_name)],
                                                       END_DATE: [RegexHandler(button_specific_date, end_date_calendar),
                                                                  MessageHandler(Filters.text, end_date_fix_tenor)],
                                                       END_DATE_CALENDAR: [RegexHandler('\d+', end_date_click_num),
                                                                           RegexHandler(button_prev_mth, prev_mth),
                                                                           RegexHandler(button_next_mth, next_mth),
                                                                           MessageHandler(Filters.text, end_date_invalid)],
                                                       REMIND_DATE: [RegexHandler(button_remind_specific, remind_date_calendar),
                                                                     MessageHandler(Filters.text, remind_date_fix_tenor)],
                                                       REMIND_DATE_CALENDAR: [RegexHandler('\d+', remind_date_click_num),
                                                                              RegexHandler(button_prev_mth, prev_mth),
                                                                              RegexHandler(button_next_mth, next_mth),
                                                                              MessageHandler(Filters.text, remind_date_invalid)]},
                                               fallbacks=[MessageHandler(Filters.text, fallback)],
                                               run_async_timeout=conv_time_out)
                           )

    updater.start_polling()



if __name__ == '__main__':
    main()
