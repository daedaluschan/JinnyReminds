conv_time_out = 20
poll_interval = 10

schedule_time_hh = 9
schedule_time_mm = 0

schedule_time_hh_2 = 12
schedule_time_mm_2 = 0

schedule_time_hh_3 = 15
schedule_time_mm_3 = 0

schedule_time_hh_4 = 18
schedule_time_mm_4 = 0

log_file_size_lmt = 10485760
log_file_count_lmt = 5

msg_i_dont_know_u = "唔識你，唔同你講嘢。"
log_i_dont_know_u = "唔識你（{}），唔同你講嘢。"

msg_greeting = "你好，這是可愛小 Jinny Telegram 機械人。"

button_new_memo = "加入新提示"
button_show_all = "所有提示"

keyboard_start=[[button_new_memo],[button_show_all]]

msg_memo_name = "提示名稱係乜？"
msg_end_date = "邊日到期？"

button_1W = "一星期後"
button_2W = "兩星期後"
button_3W = "三星期後"
button_1M = "一個月後"
button_2M = "兩個月後"
button_3M = "三個月後"
button_6M = "半年後"
button_1Y = "一年後"
button_specific_date = "用小日曆揀日期。"

keyboard_end_date=[[button_specific_date],
                   [button_1W, button_2W, button_3W],
                   [button_1M, button_2M, button_3M],
                   [button_6M, button_1Y]]

msg_remind_date = "到期前幾耐提你？"

button_remind_1D = "一日前"
button_remind_3D = "三日前"
button_remind_1W = "一星期前"
button_remind_10D = "十日前"
button_remind_2W = "兩星期前"
button_remind_3W = "三星期前"
button_remind_1M = "一個月前"
button_remind_specific = "用小日曆揀日期。"

keyboard_remind_date=[[button_remind_specific],
                      [button_remind_1D, button_remind_3D, button_remind_1W],
                      [button_remind_10D, button_remind_2W, button_remind_3W],
                      [button_remind_1M]]

msg_done_add = "Done 啦。"

msg_dont_understand = "唔明，請再試過啦。"

button_prev_mth = "前一個月"
button_next_mth = "後一個月"
msg_pls_choose_date = "請選擇日子。"
msg_invalid_date_pick = "雖然個 UI 寫得唔係咁好，但呢個唔係一個日期，請 click 數字或轉月份。"

msg_input_date = "輸入日期係：{}"

msg_confirm_curr_mth = "{} 年 {} 月。"
msg_cannot_process_date_input = "認唔到呢個日子，請重新試過。"

button_confirm = "確定"
msg_all_memos_as_show = "所有提示如下。"

button_each_item_prefix = "[{}]: {}"
button_each_item_del = "刪除[{}]"


regex_each_item_prefix = "^\[(\d+)\]:.*"
regex_del_item_prefix = "^刪除\[(\d+)\]"
msg_memo_detail = "提示詳情：\n\n{}\n到期日：{}\n提示日：{}"

msg_confirm_to_del = "確定要刪除？"
button_confirm_Y = "是"
button_confirm_N = "否"

keyboard_confirm_del =[[button_confirm_Y, button_confirm_N]]

key_remind_module = "special"
msg_remind_now = "[提示到期]\n\n{}"

button_il_ok = "OK"
button_il_snooze = "Snooze"
snooze_cb_data = "{}_{}"
snooze_cb_regex = "{}_([\d\w]+)".format(button_il_snooze)

button_next_schedule = "下一個時段"
button_snooze_1D = "一日"
button_snooze_2D = "兩日"
button_snooze_3D = "三日"
button_snooze_1W= "一星期"

regex_snooze_options = "[{}|{}|{}|{}|{}]".format(button_next_schedule,
                                                 button_snooze_1D, button_snooze_2D,
                                                 button_snooze_3D, button_snooze_1W)

keyboard_snooze = [[button_next_schedule, button_snooze_1D],
                   [button_snooze_2D, button_snooze_3D, button_snooze_1W]]

msg_snooze_till_when = "Snooze 幾耐？"

msg_cacelled = "取消咗。"
