import logging
from logging.handlers import RotatingFileHandler
#import calendar
#from datetime import date
from datetime import time
from datetime import timedelta
from jinny_memo import *
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
                          ConversationHandler, StringRegexHandler, jobqueue, CallbackQueryHandler)
from telegram import replykeyboardmarkup, inlinekeyboardbutton, inlinekeyboardmarkup
from telegram import replykeyboardremove
from jinny_reminds_cfg import *
from jinny_reminds_static import *
from functools import wraps
from itertools import islice
import re

memos = {}
jin_list_cache = {}
captioned_memo = {}
snoozing_memo = {}

ITEM_NAME, END_DATE, REMIND_DATE, END_DATE_CALENDAR, REMIND_DATE_CALENDAR, SHOW_ALL, \
DEL_ITEM, SNOOZE = range(8)

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

    for admin_id in LIST_OF_ADMINS:
        bot.sendMessage(chat_id=admin_id, text=msg_add_memo_detail.format(memos[update.message.chat_id].memo_text,
                                                                          memos[update.message.chat_id].memo_end_date,
                                                                          memos[update.message.chat_id].remind_date))

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

@restricted
def show_all(bot, update):
    keyboard_list = [[button_confirm]]

    if update.message.chat_id in jin_list_cache:
        del jin_list_cache[update.message.chat_id]

    jin_list_cache[update.message.chat_id] = []

    for idx, each_memo in enumerate(get_all_memos()):
        jin_list_cache[update.message.chat_id].append(each_memo)
        keyboard_list.append([button_each_item_prefix.format(idx.__str__(), each_memo["item"]),
                              button_each_item_del.format(idx.__str__())])

    markup = replykeyboardmarkup.ReplyKeyboardMarkup(keyboard=keyboard_list)

    bot.sendMessage(chat_id=update.message.chat_id, text=msg_all_memos_as_show, reply_markup=markup)

    return SHOW_ALL

@restricted
def send_memo_detail(bot, update, idx):
    show_memo = jin_list_cache[update.message.chat_id][int(idx)]
    bot.sendMessage(chat_id=update.message.chat_id,
                    text=msg_memo_detail.format(show_memo["item"], show_memo["endDate"], show_memo["remindDate"]))

@restricted
def memo_detail(bot, update):
    matched_obj = re.match(re.compile(regex_each_item_prefix), update.message.text)
    send_memo_detail(bot, update, matched_obj.group(1))
    # send_memo_detail(bot, update, groups(1))
    return None

@restricted
def show_all_confirmed(bot, update):
    markup = replykeyboardmarkup.ReplyKeyboardMarkup(keyboard=keyboard_start)
    bot.sendMessage(chat_id=update.message.chat_id, text=msg_greeting,
                    reply_markup=markup)
    return -1

@restricted
def del_memo(bot, update):
    matched_obj = re.match(re.compile(regex_del_item_prefix), update.message.text)
    del_idx = matched_obj.group(1)
    send_memo_detail(bot, update, del_idx)

    captioned_memo[update.message.chat_id] = int(del_idx)

    markup = replykeyboardmarkup.ReplyKeyboardMarkup(keyboard=keyboard_confirm_del)
    bot.sendMessage(chat_id=update.message.chat_id, text=msg_confirm_to_del, reply_markup=markup)

    return DEL_ITEM

@restricted
def del_memo_Y(bot, update):
    session = update.message.chat_id

    for admin_id in LIST_OF_ADMINS:
        bot.sendMessage(chat_id=admin_id, text=msg_del_memo_detail.format(jin_list_cache[session][captioned_memo[session]]["item"]))

    bot.sendMessage(chat_id=session, text=del_item_by_id(jin_list_cache[session][captioned_memo[session]]["_id"]).__str__())

    del captioned_memo[session]
    return show_all(bot, update)

@restricted
def del_memo_N(bot, update):
    return show_all(bot, update)

def reminds(bot, job):
    for chat_id in LIST_OF_SUPER_ADMINS:
        bot.sendMessage(chat_id=chat_id, text="scheduled sending")

    if key_remind_module in jin_list_cache:
        del jin_list_cache[key_remind_module]
    jin_list_cache[key_remind_module] = []

    reference_date = datetime.today()

    for each_memo in get_all_memos():
        if each_memo["remindDate"] < reference_date and "sentTime" not in each_memo:
            inline_button = inlinekeyboardbutton.InlineKeyboardButton(button_il_snooze,
                                                                      callback_data=snooze_cb_data.format(button_il_snooze,
                                                                                                          each_memo["_id"]))
            inline_button_recur_1M = inlinekeyboardbutton.InlineKeyboardButton(button_il_recur_pos_1M,
                                                                               callback_data=recur_cb_data.format(each_memo["_id"]))

            for chat_id in LIST_OF_ADMINS:
                bot.sendMessage(chat_id=chat_id,
                                text=msg_remind_now.format(msg_memo_detail.format(each_memo["item"],
                                                                                  each_memo["endDate"],
                                                                                  each_memo["remindDate"])),
                                reply_markup=inlinekeyboardmarkup.InlineKeyboardMarkup([[inline_button, inline_button_recur_1M]]))
            update_sent_time_by_id(each_memo["_id"])

@restricted
def snooze(bot, update):
    #logging.info("callback_query : {}".format(update.callback_query))
    #logging.info("from id : {}".format(update.callback_query.from_user.id))
    #logging.info("callback data : {}".format(update.callback_query["data"]))
    # bot.sendMessage(chat_id=update.message.chat_id, text="reveived snooze")
    #logging.info("snoozing obj id : {}".format(matched_obj.group(1)))

    session = update.callback_query.from_user.id
    matched_obj = re.match(re.compile(snooze_cb_regex), update.callback_query["data"])

    if matched_obj != None:
        snoozing_memo[session] = matched_obj.group(1)

        markup = replykeyboardmarkup.ReplyKeyboardMarkup(keyboard=keyboard_snooze)
        bot.sendMessage(chat_id=session, text=msg_snooze_till_when, reply_markup=markup)

        return SNOOZE

    else:
        matched_obj = re.match(re.compile(recur_cb_regex), update.callback_query["data"])
        start(bot, update)
        return -1

@restricted
def snooze_options(bot, update):
    session = update.message.chat_id
    snooze_by_id(snoozing_memo[session])

    reference_date = date.today()
    if update.message.text == button_snooze_1D:
        obj_date = reference_date + timedelta(days=1)
    elif update.message.text == button_snooze_2D:
        obj_date = reference_date + timedelta(days=2)
    elif update.message.text == button_snooze_3D:
        obj_date = reference_date + timedelta(days=3)
    elif update.message.text == button_snooze_1W:
        obj_date = reference_date + timedelta(days=7)
    else:
        if update.message.text != button_next_schedule:
            bot.sendMessage(chat_id=session, text=msg_cannot_process_date_input)
            return None

    if update.message.text != button_next_schedule:
        update_remind_date_by_id(snoozing_memo[session], obj_date)

    bot.sendMessage(chat_id=session, text=msg_done_add)

    markup = replykeyboardmarkup.ReplyKeyboardMarkup(keyboard=keyboard_start)
    bot.sendMessage(chat_id=session, text=msg_greeting,
                    reply_markup=markup)

    del snoozing_memo[session]
    return -1

def cancel(bot, update):
    session = update.message.chat_id
    if session in memos:
        del memos[session]
    if session in jin_list_cache:
        del jin_list_cache[session]
    if session in captioned_memo:
        del captioned_memo[session]
    if session in snoozing_memo:
        del snoozing_memo[session]

    bot.sendMessage(chat_id=update.message.chat_id, text=msg_cacelled)
    start(bot, update)
    return -1

def main():
    #logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG,
    #                    filename="logs/JinnyReminds." + str(date.today()) + ".log")

    # logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

    handler =  RotatingFileHandler(filename="logs/JinnyReminds.log", maxBytes=log_file_size_lmt, backupCount=log_file_count_lmt)
    handler.setFormatter(logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s'))

    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.DEBUG)

    updater = Updater(TOKEN)
    jq = updater.job_queue

    jq.run_daily(callback=reminds, time=time(hour=schedule_time_hh, minute=schedule_time_mm))
    jq.run_daily(callback=reminds, time=time(hour=schedule_time_hh_2, minute=schedule_time_mm_2))
    jq.run_daily(callback=reminds, time=time(hour=schedule_time_hh_3, minute=schedule_time_mm_3))
    jq.run_daily(callback=reminds, time=time(hour=schedule_time_hh_4, minute=schedule_time_mm_4))

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start))

    dispatcher.add_handler(ConversationHandler(entry_points=[CallbackQueryHandler(snooze)],
                                               states={SNOOZE:[RegexHandler(regex_snooze_options, snooze_options)]},
                                               fallbacks=[CommandHandler("cancel", cancel),
                                                          MessageHandler(Filters.text, fallback)],
                                               run_async_timeout=conv_time_out))

    dispatcher.add_handler(ConversationHandler(entry_points=[RegexHandler(button_show_all, show_all)],
                                               states={SHOW_ALL: [RegexHandler(button_confirm, show_all_confirmed),
                                                                  RegexHandler(regex_each_item_prefix, memo_detail),
                                                                  RegexHandler(regex_del_item_prefix, del_memo)],
                                                       DEL_ITEM: [RegexHandler(button_confirm_Y, del_memo_Y),
                                                                  RegexHandler(button_confirm_N, del_memo_N)]},
                                               fallbacks=[CommandHandler("cancel", cancel),
                                                          MessageHandler(Filters.text, fallback)],
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
                                               fallbacks=[CommandHandler("cancel", cancel),
                                                          MessageHandler(Filters.text, fallback)],
                                               run_async_timeout=conv_time_out)
                           )

    updater.start_polling()



if __name__ == '__main__':
    main()
