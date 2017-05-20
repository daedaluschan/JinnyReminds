from datetime import date
import calendar

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