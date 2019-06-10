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
dheadersandtypes = []
dialect = ''
header_given = ''
types = []
compression = None
mycsvfilename = 'CSV filename'
mydbfilename = 'datbase'
mytablename = 'tablename'
thedbfile = ''
filecheckok = True
csvfilecheck = False
dbfilecheck = False
tablenamecheck = False
csvdata = []
read_mode = 'rt'


def table_example(csvfilename):
    # filename = sg.PopupGetFile('filename to open', no_window=True, file_types=(("CSV Files","*.csv"),))
    # --- populate table with file contents --- #
    if csvfilename=='':
        sys.exit(69)
    data = []
    header_list = []
    if csvfilename is not None:
        with open(csvfilename, "r") as infile:
            reader = csv.reader(infile)
            header_list = next(reader)
            try:
                data = list(reader)  # read everything else into a list of rows
                # if button == 'No':
                #     header_list = ['column' + str(x) for x in range(len(data[0]))]
            except:
                sg.PopupError('Error reading file')
                sys.exit(69)
    sg.SetOptions(element_padding=(0, 0))

    layout = [[sg.Table(values=data,
            headings=header_list,
            max_col_width=min(round(250 / len(header_list)),10),
            auto_size_columns=True,
            justification='left',
            display_row_numbers='true',
            alternating_row_color='lightblue',
            num_rows=min(len(data), 10))]]

    tablewindow = sg.Window('Table', grab_anywhere=False, keep_on_top=True).Layout(layout)
    event, values = tablewindow.Read()


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
        # csvdata = [list(row) for row in csvreader]
        csvdata = [row for row in csvreader]

        # print('csvdata=>', csvdata)

    window.FindElement('_CSVROWS_').Update(csvdata[:][0])


def fill_db_listbox(window, values, con):
    # #################################
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

    fo.seek(0)
    return types


def tableexists(con, tablename):
    # returns True if the table already exists and False if noe
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
    global dheadersandtypes
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
    dheadersandtypes = dict(headersandtypes)
    # print('dheadersandtypes =>', dheadersandtypes)
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
    global dheadersandtypes
    global headersandtypes
    # sg.Popup('headers and types =>', headersandtypes)
    window.FindElement('_HEADERSANDTYPES_').Update(headersandtypes)
    window.Refresh()


def validatecsvfile(values, window):
    # global thecsvfile
    if len(values['_CSVFILENAME_'])==0:
        sg.Popup('Enter a csv filename')
        return False
    elif os.path.isfile(values['_CSVFILENAME_']):
        write_to_message_area(window, 'CSV file exists')
        return True
    else:
        sg.Popup(values['_CSVFILENAME_'], 'not found')
        return False


def validatedbfile(adbfile, values, window):
    if len(values['_DBFILENAME_'])==0:
        sg.Popup('Enter a db filename')
        return False
    elif os.path.isfile(values['_DBFILENAME_']):
        write_to_message_area(window, 'Database file exists')
        thedbfile = values['_DBFILENAME_']
        return True
    else:
        sg.Popup(values['_DBFILENAME_'], 'not found - it will be created.')
        return False


def validatedbtable(atablename, adbfile, window):
    if len(values['_TABLENAME_'])==0:
        sg.Popup('Enter a tablename')
        return False
    else:
        con = create_connection(adbfile)
        
    if not tableexists(con, values['_TABLENAME_']):
        write_to_message_area(window, 'Table does not exist - it will be created.')
        # thetablename = values['_TABLENAME_']
        return True


# define layouts
mainscreencolumn1 = [[sg.Text('Filenames', background_color=lightblue, justification='center', size=(25, 1))],
        [sg.Text('CSV File Name', justification='right', size=(15, 1)),
         sg.InputText(key='_CSVFILENAME_', size=(80, 1), enable_events=True),
         sg.FileBrowse(file_types=(('CSV Files', '*.csv'),))],
        [sg.Text('Database File Name', justification='right', size=(15, 1)),
         sg.InputText(key='_DBFILENAME_', size=(80, 1)), sg.FileBrowse(file_types=(("Sqlite files", "*.db"),))],
        [sg.Text('Table Name', justification='right', size=(15, 1)),
         sg.InputText(key='_TABLENAME_', size=(80, 1))],
        [sg.Button('Check Filenames', key='_BUTTON-CHECK-FILENAMES_', disabled=False)]]

mainscreencolumn3 = [[sg.Text('CSV File', background_color=mediumblue, justification='left', size=(60, 1))],
        [sg.Multiline(size=(104, 2), key='_CSVROWS_', autoscroll=False)],
        [sg.Text('Database File', background_color=mediumblue, justification='left', size=(60, 1))],
        [sg.Multiline(size=(104, 2), key='_DBTABLEROWS_', autoscroll=False)]]

mainscreencolumn4 = [[sg.Text('Headers / Types', background_color=mediumblue, justification='left', size=(30, 1))],
                     [sg.Listbox(values=headersandtypes, size=(37, 10), key='_HEADERSANDTYPES_')]]
                     
mainscreencolumn5 = [[sg.Text('Column Header', justification='left', size=(30, 1))],
                    [sg.InputText(key='_COLHEADER_', size=(39, 1))],
                    [sg.Text('Column Type', justification='left', size=(30, 1))],
                    [sg.InputText(key='_COLTYPE_', size=(39, 1))]]                     

# Define the mainscreen layout using the above layouts
mainscreenlayout = [[sg.Column(mainscreencolumn1, background_color=mediumblue),sg.Column(mainscreencolumn5, background_color=mediumblue)],
                    [sg.Column(mainscreencolumn3, background_color=lightblue), sg.Column(mainscreencolumn4)],
                    [sg.Text('Message Area', size=(131, 1), key='_MESSAGEAREA_')],
                    [sg.Button('Convert', key='_CONVERT_'), sg.Button('Preview CSV Data', key='_CSVPREVIEW_'),
                     sg.Exit()]]


# ########################################
# initialize main screen window
sg.SetOptions(element_padding=(2, 2))
window = sg.Window('CSV2Sqlite-GUI', background_color=mediumblue2,
        default_element_size=(20, 1)).Layout(mainscreenlayout)
window.Finalize()
window.Refresh()

# event loop
while True:  # Event Loop
    event, values = window.Read()
    if event is None or event == "Exit":
        sys.exit(1)
    elif event == '_CONVERT_':
        write_to_message_area(window, 'Converting the file')
        fill_csv_listbox(window, values)
        # updatecolumnheader(event, window)
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
        csvfilecheck = False  # reset the flag to False
        dbfilecheck = False  # reset the flag to False
        tablenamecheck = False  # reset the flag to False
        if validatecsvfile(values, window):
            thecsvfile = values['_CSVFILENAME_']
            csvfilecheck = True

        if validatedbfile(values['_DBFILENAME_'], values, window):
            thedbfile = values['_DBFILENAME_']
            dbfilecheck = True

        if validatedbtable(values['_TABLENAME_'], values['_DBFILENAME_'], window):
            tablenamecheck = True
            
        if csvfilecheck:
            fo = fillheadersandtypes(thecsvfile, window)
            updatecolumnheader(event, window)
            window.Refresh()
            
        if csvfilecheck and dbfilecheck and tablenamecheck:
            sg.Popup('Filenames and Tablename check complete.')

    elif event=='_CSVPREVIEW_':
        if os.path.isfile(values['_CSVFILENAME_']):
            table_example(values['_CSVFILENAME_'])
        else:
            sg.Popup('CSV file not found.')
