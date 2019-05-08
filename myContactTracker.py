import sqlite3
from sqlite3 import Error
import PySimpleGUI as sg
import os
import sys
from datetime import datetime


# Variables
my_db_file = 'C:/Users/imlay/OneDrive/Documents/my-CRM-AppData.db'
# my_db_file = ''
contact_detail_id = 1
lightblue = '#b9def4'
mediumblue = '#d2d2df'

def new_actionitemlog():
    sg.Popup('new_actionitemlog')


def new_contact():
    sg.Popup('new_contact')


def new_company():
    sg.Popup('new_company')


def new_contactlog():
    sg.Popup('new_contactlog')


def process_edit(event, values, con):
    # sg.Popup('edit_contact')
    windowedit = sg.Window('Edit Contact Details', background_color='#b9def4').Layout(editcontactlayout)
    # window.FindElement('_EDCONTACTID_')
    # contact_detail_id=values['_CONTACTID_']
    # sg.Popup('contact_detail_id ==>', contact_detail_id)
    windowedit.Finalize()
    # fill_contactdetailwindow(con, windowedit, contact_detail_id)

    while True:  # Loop
        event, values = windowedit.Read()
        if event == 'Exit' or event is None:
            windowedit.Close()
        elif event == 'Save':
            # sg.Popup('values -=-=> ', values)
            # updatecontactinfo(con, values, windowedit, contact_detail_id)
            windowedit.Close()
        else:
            sg.Popup('else something else')
            windowedit.Close()
        break


def edit_company():
    sg.Popup('edit_company')


def edit_actionitemlog():
    sg.Popup('edit_actionitemlog')


def initmainscreen():
    sg.Popup('mainscreen')


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


# define layouts
# layout mainscreen window
mainscreencolumn1 = [[sg.Text('Contact Details', background_color=lightblue, justification='center', size=(25, 1))],
            [sg.Text('Contact Name', justification='right', size=(20,1)), sg.InputText(key='_CONTACTNAME_')],
            [sg.Text('Work Email', justification='right', size=(20, 1)), sg.InputText(key='_WORKEMAIL_')],
            [sg.Text('Work Phone', justification='right', size=(20, 1)), sg.InputText(key='_WORKPHONE_')],
            [sg.Text('Company Name', justification='right', size=(20, 1)), sg.InputText(key='_COMPANYNAME_')],
            [sg.Button('Edit', key='_BUTTON-EDIT-CONTACT_', disabled=False), sg.Button('New', key='_BUTTON-NEW-CONTACT_', disabled=False)]]


mainscreenlayout = [[sg.Text('Company List', background_color=mediumblue, size=(30,1)), sg.Text('Contact List', background_color='#d2d2df',  size=(30,1)), sg.Input(key='_CONTACTID_', visible=True)],
        [sg.Listbox(values='', size=(30, 7),key='_COMPANYLIST_', bind_return_key=True),
        sg.Listbox(values='', size=(30, 7), key='_CONTACTLIST_', bind_return_key=True),
        sg.Column(mainscreencolumn1, background_color='#d2d2df')],
        [sg.Text('Contact History', background_color='#d2d2df', justification='left', size=(25, 1))],
        [sg.Multiline(size=(70, 15), key='_CONTACTHISTORY_'), sg.Multiline(size=(70, 15), key='_ACTIONITEMLIST_')],
        [sg.Button('Save Changes', key='_SAVE_'), sg.Exit()]]


# layout contact window

editcontactColumn1 = [[sg.Text('Edit Contact Details', background_color='#d2d2df', justification='center', size=(15, 1))],
                [sg.Text('Email', justification='right', size=(15, 1)), sg.InputText(key='_EDWORKEMAIL_')],
                [sg.Text('Phone Number', justification='right', size=(15, 1)), sg.InputText(key='_EDWORKPHONE_')]]

editcontactColumn2 = [[sg.Text('Edit Contact Details', background_color='#d2d2df', justification='center', size=(15, 1))],
                [sg.Text('Company', justification='right', size=(15, 1)), sg.InputText(key='_EDCOMPANYNAME_')],
                [sg.Text('Job Title', justification='right', size=(15, 1)), sg.InputText(key='_EDJOBTITLE_')],
                [sg.Text('Cell Phone', justification='right', size=(15, 1)), sg.InputText(key='_EDCELLPHONE_')],
                [sg.Text('Personal Email', justification='right', size=(15, 1)), sg.InputText(key='_EDPERSONALEMAIL_')]]

editcontactColumn3 = [[sg.Text('Last Name', size=(20,1)), sg.Text('First Name', size=(20,1)), sg.Text('Full Name', size=(20,1)), sg.InputText(key='_EDCONTACTID_', size=(4,1), visible=True), sg.InputText(key='_EDCOMPANYID_', size=(4,1), visible=True)],
                [sg.InputText(key='_EDLASTNAME_', size=(20,1)), sg.InputText(key='_EDFIRSTNAME_', size=(20,1)), sg.InputText(key='_EDCONTACTNAME_', size=(20,1))]]

editcontactlayout = [[sg.Column(editcontactColumn3)],
                [sg.Column(editcontactColumn1), sg.Column(editcontactColumn2)],
                [sg.Text('Notes', justification='right', size=(20, 1)), sg.Multiline(key='_EDNOTES_', size=(100, 5), autoscroll=True)],
                [sg.Button('Save Changes',key='_EDSAVE_'), sg.Exit()]]


# layout company window
# layout actionitemlog window
# layout contactlog window




# Connect to db
con = create_connection(my_db_file)


# initialize mainscreen window
window = sg.Window('Contact Tracker', background_color='#534aea', default_element_size=(20, 1)).Layout(mainscreenlayout)
window.Finalize()

# fill_companylistbox(con, window)
window.Refresh()

#event loop
while True:                 # Event Loop
    event, values = window.Read()
    if event is None or event == "Exit":
        con.close()
        sys.exit(1)
    elif event == '_BUTTON-EDIT-CONTACT_':
        process_edit(event, values, con)
        # window.FindElement('_BUTTON-EDIT-CONTACT_').Update(disabled=True)
        # window.FindElement('_BUTTON-NEW-CONTACT_').Update(disabled=False)
        window.Refresh()