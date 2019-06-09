#!/usr/bin/env python
#
# A simple Python script to convert csv files to sqlite (with type guessing)
#
# @author: Rufus Pollock
# Placed in the Public Domain
# Bug fixes by Simon Heimlicher <sh@nine.ch> marked by `shz:'
# PySimpleGUI front end by Tom Imlay

# Import
# from __future__ import print_function
import sys
import os
import csv
import sqlite3
from sqlite3 import Error
import bz2
import gzip
import PySimpleGUI as sg
from six import string_types, text_type


# Variables
my_db_file = ''
lightblue = '#b9def4'
mediumblue = '#d2d2df'
mediumblue2 = '#534aea'
headersandtypes = []
dialect = ''
header_given = ''
types = []
compression = None
mycsvfilename = 'CSV filename'
mydbfilename = 'datbase'
mytablename = 'tablename'
thedbfile = ''
filecheckok = True

# Set read mode based on Python version
if sys.version_info[0] > 2:
    read_mode = 'rt'
else:
    read_mode = 'rU'
csvdata = []


# create a database connection to a SQLite database
def create_connection(my_db_file):
    if not os.path.isfile(my_db_file):
        my_db_file = sg.PopupGetFile('Please enter a database file name',
                default_path='C:/Users/imlay/OneDrive/Documents/')
    if not os.path.isfile(my_db_file):
        sg.Popup('No Database File Found', keep_on_top=True)
        sys.exit(1)
    try:
        conn = sqlite3.connect(my_db_file)
        print("sqlite3 version=", sqlite3.version)
        return conn
    except Error as e:
        print(e)
        sg.Popup('Could not connect to the database', keep_on_top=True)
        sys.exit(1)


def fill_csv_listbox(window, values):
    # #################################
    csvdata = []

    csvfilename = values['_CSVFILENAME_']
    with open(csvfilename, newline='') as f:
        # creating a csv reader object
        csvreader = csv.reader(f)
        # skip 1st line with headings
        next(csvreader, None)  # skip the first row
        # load all remaining rows into a local list
        csvdata = [row for row in csvreader]
        # print('csvdata=>', csvdata)

    window.FindElement('_CSVROWS_').Update(csvdata[:][0])


def fill_db_listbox(window, values, con):
    # #################################
    dbdata = []
    cur = con.cursor()
    tablename = values['_TABLENAME_']
    cur.execute('SELECT * FROM %s LIMIT 1;' % tablename)

    dbdata = cur.fetchall()
    window.FindElement('_DBTABLEROWS_').Update(dbdata)


def write_to_message_area(window, message):
    window.FindElement('_MESSAGEAREA_').Update(message)
    window.Refresh()


def open_csv_file(filepath_or_fileobj):
    # sg.Popup('open_csv_file')
    if isinstance(filepath_or_fileobj, string_types):
        if compression is None:
            fo = open(filepath_or_fileobj, mode=read_mode)
        elif compression == 'bz2':
            try:
                fo = bz2.open(filepath_or_fileobj, mode=read_mode)
            except AttributeError:
                fo = bz2.BZ2File(filepath_or_fileobj, mode='r')
        elif compression == 'gzip':
            fo = gzip.open(filepath_or_fileobj, mode=read_mode)
    return fo


def get_csv_headers(fo, dialect, events, window):
    # get the headers
    reader = csv.reader(fo, dialect)
    headers = [header.strip() for header in next(reader)]
    # print('headers=>', headers)
    fo.seek(0)

    # replace spaces in the column names with '_'
    theheaders = [x.replace(" ", "_") for x in headers]
    return theheaders


def get_csv_types(fo, window, headers, dialect):
    global header_given
    global types
    max_sample_size = 100
    number_of_columns = len(headers)

    # guess types
    type_reader = csv.reader(fo, dialect)
    if not header_given: next(type_reader)
    # types = _guess_types(type_reader, len(headers))

    # we default to text for each field
    types = ['text'] * number_of_columns
    # order matters
    # (order in form of type you want used in case of tie to be last)
    options = [
            ('text', text_type),
            ('real', float),
            ('integer', int)
    ]

    # for each column a set of bins for each type counting successful casts
    perresult = {
            'integer': 0,
            'real'   : 0,
            'text'   : 0
    }

    results = [dict(perresult) for x in range(number_of_columns)]
    sample_counts = [0 for x in range(number_of_columns)]

    for row_index, row in enumerate(type_reader):
        for column, cell in enumerate(row):
            cell = cell.strip()
            if len(cell) == 0:
                continue

            # replace ',' with '' to improve cast accuracy for ints and floats
            if cell.count('$') > 0:
                cell = cell.replace('$', '')
                if cell.count('E') == 0:
                    cell = cell + "E0"

            if cell[0].count('(') > 0:
                cell = cell.replace('(', '-')
                if cell.count('E') == 0:
                    cell = cell + "E0"

            if cell.count(')') > 0:
                cell = cell.replace(')', '')
                if cell.count('E') == 0:
                    cell = cell + "E0"

            # replace ',' with '' to improve cast accuracy for ints and floats
            if cell.count(',') > 0:
                cell = cell.replace(',', '')
                if cell.count('E') == 0:
                    cell = cell + "E0"

            for data_type, cast in options:
                try:
                    cast(cell)
                    results[column][data_type] += 1
                    sample_counts[column] += 1
                except ValueError:
                    pass

        have_max_samples = True
        for column, cell in enumerate(row):
            if sample_counts[column] < max_sample_size:
                have_max_samples = False

        if have_max_samples:
            break

    for column, colresult in enumerate(results):
        for _type, _ in options:
            if colresult[_type] > 0 and colresult[_type] >= colresult[types[column]]:
                types[column] = _type

    # return types


    fo.seek(0)
    return types


def tableexists(con, tablename):
    # returns True if the table already exists and False if noe
    # sg.Popup('table=>', tablename)
    sql2 = "SELECT name FROM sqlite_master WHERE type = 'table' AND name LIKE '%s' ;" % tablename

    cur = con.cursor()
    cur.execute(sql2)

    thetablename = cur.fetchall()
    # sg.Popup('thetablename=>', thetablename)

    if len(thetablename) == 0:
        return False
    else:
        return True


# convert the CSV file to a sqlite3 table
def convert(filepath_or_fileobj, dbpath, table, events, window):
    global headersandtypes
    global dialect

    # fill the headers and types list boxes - get file object back
    fo = fillheadersandtypes(filepath_or_fileobj, window)

    # now load data
    _columns = ','.join(['"%s" %s' % (header, _type) for (header, _type) in headersandtypes])

    # sg.Popup('_columns=', _columns,keep_on_top=True)
    reader = csv.reader(fo, dialect)
    if not header_given:  # Skip the header
        next(reader)

    conn = sqlite3.connect(dbpath)
    # shz: fix error with non-ASCII input
    conn.text_factory = str
    c = conn.cursor()

    if tableexists(conn, table):
        sg.Popup('Table already exists, please enter a different one: ', table)
        return False

    try:
        create_query = 'CREATE TABLE %s (%s)' % (table, _columns)
        c.execute(create_query)
    except:
        sg.Popup('Creating table FAILED(', table, ')', keep_on_top=True)
        return False
    else:
        _insert_tmpl = 'INSERT INTO %s VALUES (%s)' % (table, ','.join(['?'] * len(headersandtypes)))

# sdfgvb
        line = 0
        for row in reader:
            line += 1
            if len(row) == 0:
                continue
            else:
                for column in range(0, len(row)):
                    columntype = types[column]
                    tmpvalue = str(row[column])

                    if len(tmpvalue) == 0:
                        continue
                    elif columntype == 'real':
                        row[column] = tmpvalue.replace('$', '')
                        tmpvalue = str(row[column])
                        row[column] = tmpvalue.replace(',', '')
                        tmpvalue = str(row[column])
                        row[column] = tmpvalue.replace('(', '-')
                        tmpvalue = str(row[column])
                        row[column] = tmpvalue.replace(')', '')
                    elif columntype == 'integer':
                        tmpvalue = str(row[column])
                        row[column] = tmpvalue.replace('$', '')
                        tmpvalue = str(row[column])
                        row[column] = tmpvalue.replace(',', '')
                c.execute(_insert_tmpl, row)
    # commit the changes
    conn.commit()
    c.close()

    # the data was converted successfully
    return True


def fillheadersandtypes(filepath_or_fileobj, window):
    global headersandtypes
    global dialect

    fo = open_csv_file(filepath_or_fileobj)
    try:
        dialect = csv.Sniffer().sniff(fo.readline())
    except TypeError:
        dialect = csv.Sniffer().sniff(str(fo.readline()))
    fo.seek(0)

    # get the list of headers
    headers = get_csv_headers(fo, dialect, values, window)

    # get the list of types
    types = get_csv_types(fo, window, headers, dialect)

    # combine headers and types into space separated values
    headersandtypes = list(zip(headers, types))

    # fill the headers listbox
    # window.FindElement('_HEADERS_').Update(headersandtypes)
    # window.Refresh()
    return fo


def getcsvfilename(defaultfilename, window):
    csvfilename = sg.PopupGetFile('Please enter a CSV file name',
                default_path=defaultfilename, keep_on_top=True, file_types=(("CSV Files", "*.csv"),))
    if not os.path.isfile(csvfilename):
        sg.Popup('No CSV File Found - exiting program', csvfilename, keep_on_top=True)
        sys.exit(1)
    window.FindElement('_CSVFILENAME_').Update(csvfilename)
    return csvfilename


def getdbfilename(defaultfilename, window, thecsvfile=None):
    dbfilename = 'UNKNOWN'
    dbfilename = sg.PopupGetFile('Please enter a database file name',
                default_path=defaultfilename, keep_on_top=True, file_types=(("Sqlite Files", "*.db"),))
    if not os.path.isfile(dbfilename) and thecsvfile is not None:
        dbfilename = thecsvfile.replace('.csv', '.db')
        sg.Popup('No database File Found - a new file will be created', dbfilename, keep_on_top=True)

    return dbfilename


def gettablename(defaulttablename):
    tablename = sg.PopupGetText('Please enter a table name', default_text=defaulttablename, keep_on_top=True)
    thetablename = (tablename.replace(' ', '_'))
    tablename = (thetablename.replace('-', '_')) # '-' throws an exception when creating a table
    return tablename


def updatecolumnheader(events, window):
    global headersandtypes
    window.FindElement('_TYPES_').Update(headersandtypes)


# define layouts
# layout mainscreen window
mainscreencolumn1 = [[sg.Text('Filenames', background_color=lightblue, justification='center', size=(25, 1))],
        [sg.Text('CSV File Name', justification='right', size=(20, 1)),
        sg.InputText(key='_CSVFILENAME_', size=(78, 1), enable_events=True), sg.FileBrowse(file_types=(('CSV Files', '*.csv'),))],
        [sg.Text('Database File Name', justification='right', size=(20, 1)),
        sg.InputText(key='_DBFILENAME_', size=(78, 1)), sg.FileBrowse(file_types=(("Sqlite files", "*.db"),))],
        [sg.Text('Table Name', justification='right', size=(20, 1)),
        sg.InputText(key='_TABLENAME_', size=(78, 1))],
        [sg.Button('Check Filenames', key='_BUTTON-CHECK-FILENAMES_', disabled=False)]]

mainscreencolumn3 = [[sg.Text('CSV File', background_color=mediumblue, justification='left', size=(60, 1))],
        [sg.Multiline(size=(100, 2), key='_CSVROWS_', autoscroll=False)],
        [sg.Text('Database File', background_color=mediumblue, justification='left', size=(60, 1))],
        [sg.Multiline(size=(100, 2), key='_DBTABLEROWS_', autoscroll=False)]]

mainscreenlayout = [[sg.Column(mainscreencolumn1, background_color=mediumblue)],
        [sg.Column(mainscreencolumn3, background_color=lightblue)],
        [sg.Text('Message Area', size=(100, 1), key='_MESSAGEAREA_')],
        [sg.Button('Convert', key='_CONVERT_'), sg.Exit()]]

# if __name__ == '__main__':
# ########################################
# initialize main screen window
window = sg.Window('CSV2Sqlite-GUI', background_color=mediumblue2, default_element_size=(20, 1)).Layout(mainscreenlayout)
window.Finalize()

# ########################################
# get the file names
# thecsvfile = getcsvfilename(mycsvfilename, window)
# print('thecsvfile=>', thecsvfile)
# thedbfile = getdbfilename(mydbfilename, window, thecsvfile)
# thetablename = gettablename(mytablename)



# ###############################
# get filenames

# window.FindElement('_DBFILENAME_').Update(thedbfile)
# window.FindElement('_TABLENAME_').Update(thetablename)
window.Refresh()

# event loop
while True:  # Event Loop
    event, values = window.Read()
    if event is None or event == "Exit":
        sys.exit(1)
    elif event == '_CONVERT_':
        write_to_message_area(window, 'Converting the file')
        fill_csv_listbox(window, values)
        thedbfile = values['_DBFILENAME_']
        converttf = convert(values['_CSVFILENAME_'], values['_DBFILENAME_'], values['_TABLENAME_'], values, window)
        if converttf:
            write_to_message_area(window, 'SUCCESS - File converted')
            con = create_connection(thedbfile)
            fill_db_listbox(window, values, con)
        else:
            write_to_message_area(window, 'FAIL - File NOT converted')
    elif event == '_BUTTON-CHECK-FILENAMES_':
        filecheckok = True  # reset the flag to True
        # check the file names
        if len(values['_CSVFILENAME_']) == 0:
            sg.Popup('Enter a csv filename')
            filecheckok = False
        elif os.path.isfile(values['_CSVFILENAME_']):
            write_to_message_area(window, 'CSV file exists')
            thecsvfile = values['_CSVFILENAME_']
        else:
            filecheckok = False
            sg.Popup(values['_CSVFILENAME_'], 'not found')

        if len(values['_DBFILENAME_']) == 0:
            sg.Popup('Enter a db filename')
            filecheckok = False
        elif os.path.isfile(values['_DBFILENAME_']):
            write_to_message_area(window, 'Database file exists')
            thedbfile = values['_DBFILENAME_']
        else:
            filecheckok = False
            sg.Popup(values['_DBFILENAME_'], 'not found')

        if not len(values['_DBFILENAME_'])==0:
            con = create_connection(thedbfile)
            if len(values['_TABLENAME_'])==0:
                sg.Popup('Enter a tablename')
                filecheckok = False
            elif not tableexists(con, values['_TABLENAME_']):
                write_to_message_area(window, 'Table does not exist')
                thetablename = values['_TABLENAME_']

        window.Refresh()
        if filecheckok:
            sg.Popup('Filenames and Tablename check complete.')
