import mysql.connector
import pandas as pd
import database_config as dc  # change to 'database_config_example'
import utilities as ut

cnx = mysql.connector.connect(user=dc.USERNAME,
                              password=dc.PASSWORD,
                              host=dc.HOST,
                              database=dc.DB_NAME)

mycursor = cnx.cursor(buffered=True)


def setup():
    """
    Run this function to create the necessary tables and database
    """
    mycursor.execute("CREATE DATABASE work_hours")

    mycursor.execute("CREATE TABLE shifts ("
                     "mon TIME, "
                     "tue TIME, "
                     "wed TIME, "
                     "thu TIME, "
                     "fri TIME, "
                     "sat TIME, "
                     "sun TIME)")

    mycursor.execute("CREATE TABLE work_times ("
                     "date DATE, "
                     "start_time TIME, "
                     "end_time TIME, "
                     "hours_worked DECIMAL, "
                     "pay DECIMAL)")

    ut.insert_days_off()

    mycursor.close()


def print_table(table):
    """
    Given the database and table name, prints table to console

    :param table: table name (str)
    """
    try:
        print(pd.read_sql(f'SELECT * FROM {table}', cnx))
    except pd.errors.DatabaseError as e:
        print(str(e))


def export_to_excel(table, filename):
    """
    Export table to xlsx file

    :param table: table name (str)
    :param filename: name of the file exported (str)
    """
    df = pd.read_sql(f'SELECT * FROM {table}', cnx)
    df.to_excel(f"{filename}.xlsx")


def insert_row(table, **kwargs):
    """
    Inserts row into given table

    :param table: table name (str)
    :param kwargs: **dict {column_name: value}
    """
    d = kwargs
    keys = ''
    placeholders = ''
    for i, key in enumerate(d.keys()):
        keys += key
        placeholders += '%s'
        if not i == len(d) - 1:
            keys += ', '
            placeholders += ', '
    query = f"INSERT INTO {table} ({keys}) VALUES ({placeholders})"
    val = tuple(val for val in d.values())
    mycursor.execute(query, val)
    cnx.commit()
    print(f"Row added with values: {val}")


def update_row(table, column, value, where, val_id):
    """
    Updates row using the given arguments

    :param table: table name (str)
    :param column: column to change (str)
    :param value: value to change to (str)
    :param where: column to identify row (str)
    :param val_id: value to identify row (str)
    """
    sql = f"UPDATE {table} SET {column} = %s WHERE {where} = %s"
    val = (value, val_id)
    mycursor.execute(sql, val)
    cnx.commit()
    print(mycursor.rowcount, "record(s) affected")


def delete_row(table, column, value):
    """
    Deletes row from table

    :param table: table name (str)
    :param column: column name (str)
    :param value: tuple ('value', )
    """
    sql = f"DELETE FROM {table} WHERE {column} = %s"
    mycursor.execute(sql, value)
    cnx.commit()
    print(f"{mycursor.rowcount} record(s) deleted from {table}")


def delete_table(table):
    try:
        mycursor.execute(f"DROP TABLE {table}")
        cnx.commit()
        print(f"Deleted '{table}'")
    except mysql.connector.Error as err:
        print(err)


def delete_all_records(table):
    """
    Deletes all records from given table

    :param table: table name (str)
    """
    sql = f"DELETE FROM {table}"
    mycursor.execute(sql)
    cnx.commit()
    print("All records deleted")


def delete_records_where(table, column, value):
    """
    Deletes all records where 'column' = 'value'

    :param table: table name (str)
    :param column: column name (str)
    :param value: str
    """
    sql = f"DELETE FROM {table} WHERE {column} = %s"
    val = [value]
    mycursor.execute(sql, val)
    cnx.commit()
    print(f"Deleted all rows where {column} = {value}")


def change_col_name(table, old_col, new_col):
    try:
        mycursor.execute(f"ALTER TABLE {table} RENAME COLUMN {old_col} TO {new_col}")
        cnx.commit()
        print(f"Colum '{old_col}' has been updated to '{new_col}'")
    except mysql.connector.Error as err:
        print(err)


def get_col_values(col, table):
    try:
        mycursor.execute(f"SELECT {col} FROM {table}")
        row = mycursor.fetchall()
        return row[0][0]
    except IndexError:
        pass


def alter_data_type(table, col, data_type):
    """
    Use to alter a columns datatype in a table

    :param table: table name (str)
    :param col: column name (str)
    :param data_type: data type to alter (str)
    """
    try:
        mycursor.execute(f"ALTER TABLE {table} MODIFY COLUMN {col} {data_type}")
        cnx.commit()
        print(f"Column '{col}' datatype changed to '{data_type}'")
    except mysql.connector.Error as err:
        print(err)
