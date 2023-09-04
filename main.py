import calendar
import PySimpleGUI as sg
from datetime import datetime as dt

import mysql.connector

import utilities as ut
import database as db

sg.theme("darkamber")
sg.set_options(font="helvetica")
days = calendar.day_abbr


def delete_shift_window():
    layout = [[sg.T("Enter Date to delete")],
              [sg.I(key="-DATE-", size=(18, 5))],
              [sg.Submit(), sg.Cancel()]]

    window = sg.Window("Main Window", layout, element_padding=(5, 5))
    while True:
        event, values = window.read()
        if event == "Exit" or event == sg.WIN_CLOSED:
            break
        if event == "Submit":
            try:
                db.delete_records_where("work_times", "date", values["-DATE-"])
                sg.popup_ok(f"\n{values['-DATE-']} deleted from database\n")
            except mysql.connector.errors.DataError:
                sg.popup_ok("\nPlease enter valid date in format '2000-12-31'\n")
        if event == "Cancel":
            break

    window.close()


def input_times_window():
    col_date = [[sg.T(f"{dt.now().date()}", key="-DATE-", border_width=30)]]

    layout = [[sg.Column(col_date, element_justification="left", expand_x=True),
               sg.CalendarButton("Choose Date", pad=(15, 15), target="-DATE-", format='%Y-%m-%d')],

              [sg.T("Enter Times or Select Holiday", pad=(20, 0), font=("", "15"))],
              [sg.T("Format 00:00", font="default 10")],

              [sg.T("Start Time: "),
               sg.In(default_text="00:00", size=(10, 10), pad=(10, 20), key="start_time"),
               sg.T("End Time: "),
               sg.In(default_text="00:00", size=(10, 10), pad=(10, 20), key="end_time")],

              [sg.Button(f"Pay Rate: {ut.get_pay_rate()}", key="-RATE-", pad=(20, 20)),
               sg.Submit(pad=(15, 15)),
               sg.B("Holiday", pad=(15, 15))]]

    window = sg.Window("Input Window", layout, modal=True, element_justification="center")
    while True:
        event, values = window.read()
        if event == "Exit" or event == sg.WIN_CLOSED:
            break
        if event == "Submit":
            if ut.is_time_format(values["start_time"]) and ut.is_time_format(values["end_time"]):
                dict_to_insert = ut.ready_values_dictionary(values, window)
                if ut.is_duplicate(db.mycursor, dict_to_insert["date"]):
                    pop_answer = sg.popup_ok_cancel("\n\nShift for this date is already present.\n"
                                                    "\nOverwrite with new shift?\n\n")
                    if pop_answer == "OK":
                        db.delete_records_where("work_times", "date", dict_to_insert["date"])

                db.insert_row("work_times", **dict_to_insert)
                sg.popup_ok("\nShift Added\n")
            else:
                sg.popup_ok("Please enter times in correct format '00:00'")

        if event == "-RATE-":
            change_pay_rate()
            ut.refresh_window(window, input_times_window)
        if event == "Holiday":
            ut.holiday_btn(window)

    window.close()


def change_pay_rate():
    layout = [[sg.T("Enter Pay Rate"), sg.In(ut.get_pay_rate(), size=(15, 15), key="-RATE-")],
              [sg.Submit()]]

    window = sg.Window("Input Window", layout, modal=True, element_justification="center")
    while True:
        event, values = window.read()
        if event == "Exit" or event == sg.WIN_CLOSED:
            break
        if event == "Submit":
            ut.save_pay_rate(values["-RATE-"])
            print("Pay rate saved")
            window.close()

    window.close()


def change_shifts_window():
    ut.insert_days_off()
    title_col = [[sg.T("Start     "), sg.T("     End")]]
    main_col = [[sg.T(f"{day}"),
                 sg.In(ut.start_end_times(day)[0], key=f"{day.lower()}_start", size=(10, 10), enable_events=True),
                 sg.In(ut.start_end_times(day)[1], key=f"{day.lower()}_end", size=(10, 10), enable_events=True)]
                for day in days]

    layout = [[sg.Column(title_col, element_justification="center", expand_x=True, pad=(5, 5))],
              [sg.Column(main_col)],
              [sg.Submit(pad=(5, 5))]]

    window = sg.Window("Main Window", layout)

    while True:
        valid = True
        event, values = window.read()
        if event == "Exit" or event == sg.WIN_CLOSED:
            break
        if event == "Submit":
            for val in values.values():
                if not ut.is_time_format(val):
                    valid = False
            if valid:
                ut.insert_shifts(values)
                break
            else:
                sg.popup_ok("Please enter times in correct format '00:00'")

    window.close()

    window.close()


def main():
    worked_shifts, pay_hrs = ut.shifts_for_display(db.cnx)
    shifts_col = [[sg.T(day, key=f"-{day.lower()}-"),
                   sg.T(ut.get_shift_times(day.lower()))]
                  for day in days]
    working_week = [[sg.T(d["Day"]), sg.T(f"{d['Start']} - {d['End']}")] for d in worked_shifts]

    layout = [[sg.T("Your Shifts", font=("", "15", "bold", "underline"), expand_x=True, justification="l"),
               sg.T("Worked Week", font=("", "15", "bold", "underline"), pad=(0, 20), expand_x=True,
                    justification="r")],
              [sg.Column(shifts_col), sg.VSeperator(pad=(10, 10)), sg.Column(working_week)],
              [sg.T(f"Total Pay: £{pay_hrs['pay']}", expand_x=True, justification="r")],
              [sg.T(f"Total Hours Worked: {pay_hrs['hours_worked']}", expand_x=True, justification="r")],
              [sg.B("Input Times", key="-TIMES-", expand_x=True)],
              [sg.B("Delete shift", key="-DELETE-", expand_x=True)],
              [sg.B("Change Shifts", key="-SHIFTS-", expand_x=True)]]

    window = sg.Window("Main Window", layout)
    while True:
        event, values = window.read()
        if event == "Exit" or event == sg.WIN_CLOSED:
            break
        if event == "-TIMES-":
            input_times_window()
            ut.refresh_window(window, main)
        if event == "-SHIFTS-":
            change_shifts_window()
            ut.refresh_window(window, main)
        if event == "-DELETE-":
            delete_shift_window()
            ut.refresh_window(window, main)

    window.close()


if __name__ == "__main__":
    main()
