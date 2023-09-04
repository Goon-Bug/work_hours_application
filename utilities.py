import calendar
import re
import pandas as pd
from datetime import datetime as dt, timedelta as td
import database as db

DEFAULT_PAY_RATE = "11.11"
START_OF_THE_WEEK = 5  # Saturday
BREAKS_DICT = {
    'break1': [td(hours=8, minutes=10), td(minutes=45)],
    'break2': [td(hours=6, minutes=10), td(minutes=30)],
    'break3': [td(hours=4, minutes=10), td(minutes=15)]
}

time_re = re.compile("^([01]\d|2[0-3]):([0-5]\d)$")


def is_time_format(string):
    return True if re.match(time_re, string) else False


def insert_shifts(values):
    def merge_times(d):
        new_d = {}
        key_list = [key for key in d]
        for i, day in enumerate(key_list):
            abbr = day[:3]
            new_d[abbr] = f"{d[f'{abbr}_start']} - {d[f'{abbr}_end']}"
        return new_d

    db.delete_all_records("shifts")
    dict_to_insert = merge_times(values)
    db.insert_row("shifts", **dict_to_insert)


def row_empty(table, col):
    row_exists = db.get_col_values(col, table)
    if row_exists:
        return False
    else:
        return True


def get_shift_times(day):
    if row_empty("shifts", "mon"):
        return "00:00 - 00:00"
    else:
        return db.get_col_values(day, "shifts")


def insert_days_off():
    if row_empty("shifts", "mon"):
        d = {day: "00:00 - 00:00" for day in calendar.day_abbr}
        db.insert_row("shifts", **d)


def start_end_times(day):
    """
    Returns start and end times for given column as a string

    :param day: day of the week abbreviation (mon,tue etc.)
    :return: start, end (str)
    """
    start, end = db.get_col_values(day.lower(), "shifts").split(' - ')
    return start, end


def work_out_pay(rate, hours):
    """
    Takes pay rate and number of hours and returns total pay

    :param: rate(float): rate of pay
    :param: hours(float or int): number of hours worked
    """
    pay = hours * float(rate)
    return round(pay, 2)


def convert_to_time_obj(string):
    """
    Takes time(str) in format '00:00' and converts to time delta object

    :param string
    :return: datetime object
    """
    return dt.strptime(string, "%H:%M")


def get_total_hours(start, end):
    """
    Return total hours in decimal format between two times(str)

    :param: times(str): start and end times in format '00:00 - 00:00'
    :return: total hours(float)
    """
    times = locals()
    times = {key: convert_to_time_obj(times[key]) for key, val in times.items()}
    dt_hours = times["end"] - times["start"]
    total_hours = minus_break_times(dt_hours)
    dt_string = str(total_hours).split(':')
    total_hours_dec = float(f"{dt_string[0]}.{dt_string[1]}")
    return total_hours_dec


def save_pay_rate(rate):
    with open("pay_rate.txt", "w") as file:
        file.write(rate)


def get_pay_rate():
    with open("pay_rate.txt", "r") as file:
        rate = file.readline()
    return rate if not (len(rate) <= 0) else DEFAULT_PAY_RATE


def ready_values_dictionary(d, window):
    """
    Takes values dictionary and returns a dictionary ready to be inserted into database

    :param d: values dictionary (dict)
    :param window: pysimplegui window
    :return: dict
    """
    new_d = d
    new_d.pop("Choose Date")
    date = window["-DATE-"].get()
    new_d["date"] = date
    start, end = d["start_time"], d["end_time"]
    new_d["hours_worked"] = get_total_hours(start, end)
    new_d["pay"] = work_out_pay(get_pay_rate(), new_d["hours_worked"])
    return new_d


def get_day_from_date(date):
    """
    Returns the abbreviated day as a string from a string date

    :param date: date in form '2000-12-31'(str)
    :return: abbreviated day of the week (mon, tue, etc.)
    """
    date = dt.strptime(date, "%Y-%m-%d")
    day = dt.strftime(date, "%a").lower()
    return day


def holiday_btn(window):
    """
    Replaces the inputs 'start_time' and 'end_time' to the dates shift times

    :param window: pysimplegui window object
    """
    start_in, end_in = window["start_time"], window["end_time"]
    day = get_day_from_date(window["-DATE-"].get())
    times = get_shift_times(day)
    split_times = times.split(' - ')
    start_in.update(split_times[0])
    end_in.update(split_times[1])


def refresh_window(window, func):
    window.close()
    func()


def work_week_date_range():
    """
    Returns the date range of the working week

    :return: date(datetime)
    """
    date = dt.now().date()
    for day in range(1, 8):
        if date.weekday() == START_OF_THE_WEEK:
            break
        else:
            date -= td(days=1)
    return pd.date_range(date, (dt.now().date()))


def get_working_week(cnx):
    """
    Returns all rows of the working week

    :param mycursor: mysql cursor object
    :return: list
    """
    dates = work_week_date_range()
    dates_list = []
    for date in dates:
        mycursor = cnx.cursor(dictionary=True, buffered=True)
        mycursor.execute(f"SELECT * FROM work_times WHERE date = '{date.date()}'")
        row = mycursor.fetchall()
        if row is not None:
            pass
        if len(row) > 0:
            dates_list.append(row[0])
    return dates_list


def shifts_for_display(cnx):
    converter = {
        'date': ['Day', lambda x: dt.strftime(x, "%a")],
        'start_time': ['Start', lambda x: str(x)[:-3]],
        'end_time': ['End', lambda x: str(x)[:-3]],
    }

    l = get_working_week(cnx)
    new_d = {}
    new_list = []
    pay_hrs_wrkd = {"pay": 0,
                    "hours_worked": 0}

    for d in l:
        for key, val in d.items():
            if key == "pay" or key == "hours_worked":
                pay_hrs_wrkd[key] += d[key]
            if key in converter:
                new_d[converter[key][0]] = converter[key][1](val)

        new_list.append(dict(new_d))
    return new_list, pay_hrs_wrkd


def minus_break_times(hours):
    for br in BREAKS_DICT:
        if hours >= BREAKS_DICT[br][0]:
            hours = hours - BREAKS_DICT[br][1]
            return hours
        elif hours < BREAKS_DICT['break3'][0]:
            return hours


def get_row_where_date(mycursor, value):
    mycursor.execute(f"SELECT * FROM work_times WHERE date = '{value}'")
    rows = mycursor.fetchall()
    rows_list = []
    for row in rows:
        if len(row) <= 0:
            print("No date found")
        else:
            rows_list.append(row)

    return rows_list


def is_duplicate(mycursor, date):
    mycursor.execute(f"SELECT * FROM work_times WHERE date = '{date}'")
    rows = mycursor.fetchall()
    if rows:
        return True
    else:
        return False


# make minus breaks function
