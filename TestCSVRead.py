#!/usr/bin/env python
#
# A simple Python script to test reading 25 rows from a CSV file and adding them to a list box
#
# @author: Tom Imlay
# Placed in the Public Domain

# Import
# from __future__ import print_function
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
# Variables
my_db_file = 'C:/Users/imlay/OneDrive/Documents/testcsv2sqlite'
# my_db_file = ''
lightblue = '#b9def4'
mediumblue = '#d2d2df'

# layout mainscreen window
mainscreencolumn1 = [[sg.Text('Filenames', background_color=lightblue, justification='center', size=(25, 1))],
            [sg.Text('CSV File Name', justification='right', size=(20,1)), sg.InputText(key='_CSVFILENAME_', size=(80, 1))],
            [sg.Text('Database File Name', justification='right', size=(20, 1)), sg.InputText(key='_DBFILENAME_', size=(80, 1))],
            [sg.Text('Table Name', justification='right', size=(20,1)), sg.InputText(key='_TABLENAME_', size=(80, 1))],
            [sg.Button('Edit', key='_BUTTON-EDIT-CONTACT_', disabled=False), sg.Button('New', key='_BUTTON-NEW-CONTACT_', disabled=False)]]


mainscreenlayout = [[sg.Text('Company List', background_color=mediumblue, size=(30,1)), sg.Text('Contact List', background_color=mediumblue,  size=(30,1)), sg.Input(key='_CONTACTID_', visible=True)],
        [sg.Column(mainscreencolumn1, background_color=mediumblue)],
        [sg.Text('CSV File', background_color=mediumblue, justification='left', size=(60, 1)),
         sg.Text('Database File', background_color=mediumblue, justification='left', size=(60, 1))],
        [sg.Multiline(size=(140, 10), key='_CSVROWS_')],
        [sg.Multiline(size=(140, 10), key='_DBTABLEROWS_')],
        [sg.Text('Message Area', size=(140,1),key='_MESSAGEAREA_')],
        [sg.Button('Convert', key='_CONVERT_'), sg.Exit()]]

# initialize mainscreen window
window = sg.Window('Contact Tracker', background_color='#534aea', default_element_size=(20, 1)).Layout(mainscreenlayout)
window.Finalize()

# fill_companylistbox(con, window)
window.Refresh()

csvdata = []

# #################################
with open('C:/Users/imlay/Downloads/1952648870_MilestoneDashboard.csv', newline='') as f:
    reader = csv.reader(f)

    for row in reader:
        # sg.Popup('row=', len(row))
        # csvdata += field
        csvdata += {row[1][0:10], '|', row[3][0:10],'|', row[5][0:10], '\n'}
        print(row[1], '|',row[3])

window.FindElement('_CSVROWS_').Update(csvdata)

while True:                 # Event Loop
    event, values = window.Read()
    if event is None or event == "Exit":
        con.close()
        sys.exit(1)
    elif event == '_BUTTON-EDIT-CONTACT_':
        sg.Popup('event == edit')
        # process_edit(event, values, con)
        # window.FindElement('_BUTTON-EDIT-CONTACT_').Update(disabled=True)
        # window.FindElement('_BUTTON-NEW-CONTACT_').Update(disabled=False)
        window.Refresh()