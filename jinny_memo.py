from datetime import date, datetime
from bson.objectid import ObjectId
import calendar
from pymongo import MongoClient, ASCENDING

db_host = 'localhost'
db_port = 27017

client = MongoClient(db_host, db_port)
db = client.JinRemind
jin_list = db.JinList

def get_all_memos():
    return jin_list.find().sort("remindDate", ASCENDING)

def del_item_by_id(obj_id):
    return jin_list.delete_one({"_id": ObjectId(obj_id)}).deleted_count

def update_sent_time_by_id(obj_id):
    return jin_list.find_one_and_update({"_id": ObjectId(obj_id)}, {"$set": {"sentTime": datetime.today()}})

def snooze_by_id(obj_id):
    return jin_list.find_one_and_update({"_id": ObjectId(obj_id)}, {"$unset": {"sentTime": ""}})

def update_remind_date_by_id(obj_id, remind_date):
    return jin_list.find_one_and_update({"_id": ObjectId(obj_id)}, {"$set": {"remindDate": datetime.combine(remind_date, datetime.min.time())}})

def update_end_and_remind_by_id(obj_id, end_date, remind_date):
    # jin_list.find_one_and_update({"_id": ObjectId(obj_id)}, {"$unset": {"sentTime": ""}})
    return jin_list.find_one_and_update({"_id": ObjectId(obj_id)}, {"$set": {"remindDate": datetime.combine(remind_date, datetime.min.time()),
                                                                             "endDate": datetime.combine(end_date, datetime.min.time())},
                                                                    "$unset": {"sentTime": ""}})
def get_memo_by_id(obj_id):
    return jin_list.find_one({"_id": ObjectId(obj_id)})

class memo():
    def __init__(self):
        self.memo_text = ""
        current_date = date.today()
        self.memo_end_date = current_date
        self.remind_date = current_date
        self.moving_year = current_date.year
        self.moving_mth = current_date.month

    def __str__(self):
        return "MEMO_STR -- memo text: {} | end date: {} | remind date: {} | calendar yr: {} | calendar mth: {}".format(self.memo_text,
                                                                                                            self.memo_end_date.ctime(),
                                                                                                            self.remind_date.ctime(),
                                                                                                            self.moving_year.__str__(),
                                                                                                            self.moving_mth.__str__())

    @property
    def memo_text(self):
        return self._memo_text

    @memo_text.setter
    def memo_text(self, value):
        self._memo_text = value

    @property
    def memo_end_date(self):
        return self._memo_end_date

    @memo_end_date.setter
    def memo_end_date(self, value):
        self._memo_end_date = value

    @property
    def remind_date(self):
        return self._remind_date

    @remind_date.setter
    def remind_date(self, value):
        self._remind_date = value

    @property
    def moving_year(self):
        return self._moving_year

    @moving_year.setter
    def moving_year(self, value):
        self._moving_year = value

    @property
    def moving_mth(self):
        return self._moving_mth

    @moving_mth.setter
    def moving_mth(self, value):
        self._moving_mth = value

    def save_data(self):
        jin_list.insert({"item": self.memo_text,
                         "createdDate": datetime.today(),
                         "endDate": datetime.combine(self.memo_end_date, datetime.min.time()),
                         "remindDate": datetime.combine(self.remind_date, datetime.min.time())})
