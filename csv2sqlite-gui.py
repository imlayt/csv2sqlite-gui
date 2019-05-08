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

# Set read mode based on Python version
if sys.version_info[0] > 2:
    read_mode = 'rt'
else:
    read_mode = 'rU'


# convert the CSV file to a sqlite3 table
def convert(filepath_or_fileobj, dbpath, table, headerspath_or_fileobj=None, compression=None, typespath_or_fileobj=None):
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

    try:
        dialect = csv.Sniffer().sniff(fo.readline())
    except TypeError:
        dialect = csv.Sniffer().sniff(str(fo.readline()))
    fo.seek(0)

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
        fo.seek(0)

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

    # now load data
    _columns = ','.join(
        ['"%s" %s' % (header, _type) for (header,_type) in zip(headers, types)]
        )

    reader = csv.reader(fo, dialect)
    if not header_given: # Skip the header
        next(reader)

    conn = sqlite3.connect(dbpath)
    # shz: fix error with non-ASCII input
    conn.text_factory = str
    c = conn.cursor()

    try:
        create_query = 'CREATE TABLE %s (%s)' % (table, _columns)
        c.execute(create_query)
    except:
        pass

    _insert_tmpl = 'INSERT INTO %s VALUES (%s)' % (table,
        ','.join(['?']*len(headers)))

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
                else x for (x,y) in zip(row, types) ]
            c.execute(_insert_tmpl, row)
        except ValueError as e:
            # print("Unable to convert value '%s' to type '%s' on line %d" % (x, y, line), file=sys.stderr)
            sg.Popup("Unable to convert value '%s' to type '%s' on line %d" % (x, y, line), file=sys.stderr)
        except Exception as e:
            print("Error on line %d: %s" % (line, e), file=sys.stderr)


    conn.commit()
    c.close()


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
            [sg.Text('CSV File Name', justification='right', size=(20,1)), sg.InputText(key='_CSVFILENAME_', size=(80, 1))],
            [sg.Text('Database File Name', justification='right', size=(20, 1)), sg.InputText(key='_DBFILENAME_', size=(80, 1))],
            [sg.Button('Edit', key='_BUTTON-EDIT-CONTACT_', disabled=False), sg.Button('New', key='_BUTTON-NEW-CONTACT_', disabled=False)]]


mainscreenlayout = [[sg.Text('Company List', background_color=mediumblue, size=(30,1)), sg.Text('Contact List', background_color=mediumblue,  size=(30,1)), sg.Input(key='_CONTACTID_', visible=True)],
        [sg.Column(mainscreencolumn1, background_color=mediumblue)],
        [sg.Text('CSV File', background_color=mediumblue, justification='left', size=(60, 1)),
         sg.Text('Database File', background_color=mediumblue, justification='left', size=(60, 1))],
        [sg.Multiline(size=(70, 15), key='_CSVROWS_'), sg.Multiline(size=(70, 15), key='_DBTABLEROWS_')],
        [sg.Text('Message Area', size=(140,1),key='_MESSAGEAREA_')],
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


# ########################################
# initialize main screen window
window = sg.Window('CSV-2-Sqlite3', background_color='#534aea', default_element_size=(20, 1)).Layout(mainscreenlayout)
window.Finalize()


# ###############################
# get filenames
window.FindElement('_CSVFILENAME_').Update(thecsvfile)
window.FindElement('_DBFILENAME_').Update(thedbfile)
window.Refresh()


# event loop
while True:  # Event Loop
    event, values = window.Read()
    if event is None or event == "Exit":
        sg.Popup('event is EXIT')
        sys.exit(1)
    elif event == '_CONVERT_':
        window.FindElement('_MESSAGEAREA_').Update('Converting the file')
        convert(values['_CSVFILENAME_'], values['_DBFILENAME_'], 'MYTABLE')
        window.FindElement('_MESSAGEAREA_').Update('SUCCESS - Table converted')
        window.Refresh()


    # convert(args.csv_file, args.sqlite_db_file, args.table_name, args.headers, compression, args.types)