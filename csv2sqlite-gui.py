#!/usr/bin/env python
#
# A simple Python script to convert csv files to sqlite (with type guessing)
#
# @author: Rufus Pollock
# Placed in the Public Domain
# Bug fixes by Simon Heimlicher <sh@nine.ch> marked by `shz:'
# PySimpleGUI front end by Tom Imlay

# Import
from __future__ import print_function
import sys
import os
import argparse
import csv
import sqlite3
from sqlite3 import Error
import bz2
import gzip
import PySimpleGUI as sg
from six import string_types, text_type



# Variables
my_db_file = 'C:/Users/imlay/OneDrive/Documents/testcsv2sqlite'
# my_db_file = ''
lightblue = '#b9def4'
mediumblue = '#d2d2df'
mediumblue2 = '#534aea'
headersandtypes = []

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
        sg.Popup('No Database File Found')
        sys.exit(1)
    try:
        conn = sqlite3.connect(my_db_file)
        print("sqlite3 version=", sqlite3.version)
        return conn
    except Error as e:
        print(e)
        sg.Popup('Could not connect to the database')
        sys.exit(1)


def fill_csv_listbox(window, values):
# #################################
    csvdata = []
    csvfilename = values['_CSVFILENAME_']
    with open(csvfilename, newline='') as f:
        reader = csv.reader(f)
        indx = 1
        for row in reader:
            csvdata += {row[1], '|', row[3], '|', row[5], '\n'}
            indx += 1
            if indx > 19:
                break
    window.FindElement('_CSVROWS_').Update(csvdata)


def fill_db_listbox(window, values, con):
# #################################
    dbdata = []
    cur = con.cursor()
    tablename = values['_TABLENAME_']
    cur.execute('SELECT * FROM %s LIMIT 20;' % tablename)
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
    else:
        fo = filepath_or_fileobj
    return(fo)


def close_csv_file(filepointer):
    fo=filepointer
    fo.close

def get_csv_headers(fo, dialect, events, window, headerspath_or_fileobj=None):
    # sg.Popup('get_csv_headers')
    # get the headers
    header_given = headerspath_or_fileobj is not None
    if header_given:
        if isinstance(headerspath_or_fileobj, string_types):
            ho = open(headerspath_or_fileobj, mode=read_mode)
        else:
            ho = headerspath_or_fileobj
        header_reader = csv.reader(ho, dialect)
        headers = [header.strip() for header in next(header_reader)]
        ho.close()
    else:
        reader = csv.reader(fo, dialect)
        headers = [header.strip() for header in next(reader)]
        # window.FindElement('_HEADERS_').Update(headers)
        # window.Refresh()
        # sg.Popup('headers=>', headers)
        fo.seek(0)
    return headers

def get_csv_types(fo, events, window, headers, dialect, typespath_or_fileobj=None, headerspath_or_fileobj=None):
    # sg.Popup('get_csv_types')
    header_given = headerspath_or_fileobj is not None
    # get the types
    if typespath_or_fileobj is not None:
        if isinstance(typespath_or_fileobj, string_types):
            to = open(typespath_or_fileobj, mode=read_mode)
        else:
            to = typespath_or_fileobj
        type_reader = csv.reader(to, dialect)
        types = [_type.strip() for _type in next(type_reader)]
        to.close()
    else:
        # guess types
        type_reader = csv.reader(fo, dialect)
        if not header_given: next(type_reader)
        types = _guess_types(type_reader, len(headers))
        fo.seek(0)

    return types


def read_csv_write_db(filepointer, dbfilepath, events, window):
    sg.Popup('read_csv_write_db')


def tableexists(con, tablename):
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
def convert(filepath_or_fileobj, dbpath, table, events, window, headerspath_or_fileobj=None, compression=None, typespath_or_fileobj=None):
    global headersandtypes
    header_given = headerspath_or_fileobj is not None
    fo = open_csv_file(filepath_or_fileobj)
    try:
        dialect = csv.Sniffer().sniff(fo.readline())
    except TypeError:
        dialect = csv.Sniffer().sniff(str(fo.readline()))
    fo.seek(0)

    headers = get_csv_headers(fo, dialect, values, window, headerspath_or_fileobj=None)

    types = get_csv_types(fo, events, window, headers, dialect, typespath_or_fileobj=None)

    # replace spaces in the column names with '_'
    theheaders = [x.replace(" ", "_") for x in headers]

    # sg.Popup('theheaders=>', theheaders)
    headersandtypes = list(zip(theheaders, types))
    dheadersandtypes = dict(headersandtypes)
    # print("dheadersandtypes", dheadersandtypes)
    # sg.Popup('headersandtypes=>', headersandtypes)

    window.FindElement('_HEADERS_').Update(headersandtypes)
    window.Refresh()
    # sg.Popup('headers=>', headersandtypes)
    # sg.Popup('types=',types)

    # now load data
    _columns = ','.join(
        ['"%s" %s' % (header, _type) for (header,_type) in zip(headers, types)]
        )
    # sg.Popup('_columns=', _columns)
    reader = csv.reader(fo, dialect)
    if not header_given: # Skip the header
        next(reader)

    conn = sqlite3.connect(dbpath)
    # shz: fix error with non-ASCII input
    conn.text_factory = str
    c = conn.cursor()

    if tableexists(conn, table):
        # sg.Popup('Table already exists, please enter a different one: ', table)
        return False

    try:
        create_query = 'CREATE TABLE %s (%s)' % (table, _columns)
        c.execute(create_query)

    except:
        sg.Popup('Creating table FAILED(', table, ')')
        return False
    else:
        _insert_tmpl = 'INSERT INTO %s VALUES (%s)' % (table, ','.join(['?'] * len(headers)))
        # sg.Popup('_insert_tmp1 =>', _insert_tmpl)

        line = 0
        for row in reader:
            line += 1
            if len(row) == 0:
                continue
            # we need to take out commas from int and floats for sqlite to
            # recognize them properly ...
            try:
                row = [
                    None if x == ''
                    else float(x.replace(',', '')) if y == 'real'
                    else int(x) if y == 'integer'
                    else x for (x, y) in zip(row, types)]
                c.execute(_insert_tmpl, row)
            except ValueError as e:
                # print("Unable to convert value '%s' to type '%s' on line %d" % (x, y, line), file=sys.stderr)
                sg.Popup("ValueError Unable to convert value '%s' to type '%s' on line %d" % (x, y, line))
            except Exception as e:
                sg.Popup("Error on line %d: %s" % (line, e))

        conn.commit()
        c.close()
        return True



def getcsvfilename(defaultfilename):
    if not os.path.isfile(defaultfilename):
        csvfilename = sg.PopupGetFile('Please enter a CSV file name',
                                      default_path=defaultfilename)
    if not os.path.isfile(csvfilename):
        sg.Popup('No CSV File Found - exiting program', csvfilename)
        sys.exit(1)
    return csvfilename


def getdbfilename(defaultfilename):
    if not os.path.isfile(defaultfilename):
        dbfilename = sg.PopupGetFile('Please enter a database file name',
        default_path=defaultfilename)
    if not os.path.isfile(dbfilename):
        sg.Popup('No database File Found - a new file will be created', dbfilename)
        # sys.exit(1)
    return dbfilename

def gettablename(defaulttablename):
    tablename = sg.PopupGetText('Please enter a table name',default_text=defaulttablename)
    return tablename
	

def updatecolumnheader(events, window):
    # sg.Popup('_UPDATECOLUMNHEADING_')
    global headersandtypes
    window.FindElement('_TYPES_').Update(headersandtypes)


# Guess the column types based on the first 100 rows
def _guess_types(reader, number_of_columns, max_sample_size=100):
    '''Guess column types (as for SQLite) of CSV.

    :param fileobj: read-only file object for a CSV file.
    '''
    # we default to text for each field
    types = ['text'] * number_of_columns
    # order matters
    # (order in form of type you want used in case of tie to be last)
    options = [
        ('text', text_type),
        ('real', float),
        ('integer', int)
        # 'date',
        ]
    # for each column a set of bins for each type counting successful casts
    perresult = {
        'integer': 0,
        'real': 0,
        'text': 0
        }

    results = [ dict(perresult) for x in range(number_of_columns) ]
    sample_counts = [ 0 for x in range(number_of_columns) ]

    for row_index,row in enumerate(reader):
        for column,cell in enumerate(row):
            cell = cell.strip()
            if len(cell) == 0:
                continue

            # replace ',' with '' to improve cast accuracy for ints and floats
            if(cell.count(',') > 0):
               cell = cell.replace(',', '')
               if(cell.count('E') == 0):
                  cell = cell + "E0"

            for data_type,cast in options:
                try:
                    cast(cell)
                    results[column][data_type] += 1
                    sample_counts[column] += 1
                except ValueError:
                    pass

        have_max_samples = True
        for column,cell in enumerate(row):
            if sample_counts[column] < max_sample_size:
                have_max_samples = False

        if have_max_samples:
            break

    for column,colresult in enumerate(results):
        for _type, _ in options:
            if colresult[_type] > 0 and colresult[_type] >= colresult[types[column]]:
                types[column] = _type

    return types


# define layouts
# layout mainscreen window
mainscreencolumn1 = [[sg.Text('Filenames', background_color=lightblue, justification='center', size=(25, 1))],
            [sg.Text('CSV File Name', justification='right', size=(20,1)), sg.InputText(key='_CSVFILENAME_', size=(80, 1), enable_events=True)],
            [sg.Text('Database File Name', justification='right', size=(20, 1)), sg.InputText(key='_DBFILENAME_', size=(80, 1))],
            [sg.Text('Table Name', justification='right', size=(20,1)), sg.InputText(key='_TABLENAME_', size=(80, 1))],
            [sg.Button('Check Filenames', key='_BUTTON-CHECK-FILENAMES_', disabled=False)]]
			

mainscreencolumn2 = [[sg.Listbox(values='', size=(25, 20), key='_HEADERS_', enable_events=True), sg.Listbox(values='', size=(25, 20), key='_TYPES_')]]


mainscreencolumn3 = [[sg.Multiline(size=(100, 10), key='_CSVROWS_')],
			[sg.Text('Database File', background_color=mediumblue, justification='left', size=(60, 1))],
            [sg.Multiline(size=(100, 10), key='_DBTABLEROWS_')]]

mainscreencolumn4 = [[sg.Text('Column Heading', size=(15, 1), justification='right'), sg.InputText(key='_HEADERCHANGE_', size=(30, 1))],
                     [sg.Text('Column Type', size=(15, 1) ,justification='right'), sg.InputText(key='_COLUMNTYPECHANGE_', size=(30, 1))],
					 [sg.Button('Update', key='_UPDATECOLUMNHEADING_')]]

mainscreenlayout = [[sg.Column(mainscreencolumn1, background_color=mediumblue), sg.Column(mainscreencolumn4)],
        [sg.Text('CSV File', background_color=mediumblue, justification='left', size=(60, 1))],
        [sg.Column(mainscreencolumn3, background_color=lightblue),
         sg.Column(mainscreencolumn2, background_color=lightblue)],
        [sg.Text('Message Area', size=(120,1),key='_MESSAGEAREA_')],
        [sg.Button('Convert', key='_CONVERT_'), sg.Exit()]]

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='''
Convert a CSV file to a table in a SQLite database.
The database is created if it does not yet exist.
''')
    # parser commented out. will use a window to get input from the user
    #
    # parser.add_argument('csv_file', type=str, help='Input CSV file path')
    # parser.add_argument('sqlite_db_file', type=str, help='Output SQLite file')
    # parser.add_argument('table_name', type=str, nargs='?', help='Name of table to write to in SQLite file', default='data')
    # parser.add_argument('--headers', type=str, nargs='?', help='Headers are read from this file, if provided.', default=None)
    # parser.add_argument('--types', type=list, nargs='?', help='Types are read from this file, if provided.', default=None)

    # group = parser.add_mutually_exclusive_group()
    # group.add_argument('--bz2', help='Input csv file is compressed using bzip2.', action='store_true')
    # group.add_argument('--gzip', help='Input csv file is compressed using gzip.', action='store_true')

    # args = parser.parse_args()

    compression = None
    # if args.bz2:
    #     compression = 'bz2'
    # elif args.gzip:
    #     compression = 'gzip'

# ########################################
# get the file names
thecsvfile = getcsvfilename('mycsvfilename')
thedbfile = getdbfilename('mydbfilename')
thetablename = gettablename('mytablename')


# ########################################
# initialize main screen window
window = sg.Window('CSV-2-Sqlite3', background_color=mediumblue2, default_element_size=(20, 1)).Layout(mainscreenlayout)
window.Finalize()


# ###############################
# get filenames
window.FindElement('_CSVFILENAME_').Update(thecsvfile)
window.FindElement('_DBFILENAME_').Update(thedbfile)
window.FindElement('_TABLENAME_').Update(thetablename)
window.Refresh()



# event loop
while True:  # Event Loop
    event, values = window.Read()
    if event is None or event == "Exit":
        # sg.Popup('event is EXIT')
        sys.exit(1)
    elif event == '_CONVERT_':
        fill_csv_listbox(window, values)
        write_to_message_area(window, 'Converting the file')
        converttf = convert(values['_CSVFILENAME_'], values['_DBFILENAME_'], values['_TABLENAME_'], values, window)
        if converttf:
            write_to_message_area(window, 'SUCCESS - File converted')
            con = create_connection(thedbfile)
            fill_db_listbox(window, values, con)
        else:
            write_to_message_area(window, 'FAIL - File NOT converted')
    elif event == '_HEADERS_':
        # sg.Popup('_HEADERS_ changed. current value=>', values['_HEADERS_'])
        aheader, atype = values['_HEADERS_'][0]
        window.FindElement('_HEADERCHANGE_').Update(aheader)
        window.FindElement('_COLUMNTYPECHANGE_').Update(atype)
    elif event == '_UPDATECOLUMNHEADING_':
        # sg.Popup('_UPDATECOLUMNHEADING_')
        updatecolumnheader(values, window)
    elif event == '_BUTTON-CHECK-FILENAMES_':
        sg.Popup('_BUTTON-CHECK-FILENAMES_')


    # convert(args.csv_file, args.sqlite_db_file, args.table_name, args.headers, compression, args.types)
