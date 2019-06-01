#! /usr/local/bin/python3
# findLargeFiles.py - given a folder name, walk through its entire hierarchy
#                   - print folders and files within each folder

import os
import PySimpleGUI as sg
import sys

lightblue = '#b9def4'
mediumblue = '#d2d2df'
mediumblue2 = '#534aea'


def write_to_message_area(window, message):
    window.FindElement('_MESSAGEAREA_').Update(message)
    window.Refresh()
    
def getrootdirectory(defaultfilename, window):
    rootdirectory = sg.PopupGetFolder('Please enter a root directory name',
                default_path=defaultfilename, keep_on_top=True)
    if not os.path.isdir(rootdirectory):
        sg.Popup('Not a directory', rootdirectory, keep_on_top=True)
        # sys.exit(1)
    window.FindElement('_ROOTDIRECTORY_').Update(rootdirectory)
    return rootdirectory

# pass in the root folder and a file object for saving the output. The file is overwritten with each run.
def recursive_walk(folder, fo):
    for folderName, subfolders, filenames in os.walk(folder):
        if subfolders:
            for subfolder in subfolders:
                recursive_walk(subfolder, fo)
        # print to stdout which is redirected to the Output element in the UI
        print(folderName + '/')
        window.Refresh()
        # print to a text file
        print(folderName + '/', file=fo)
        for filename in filenames:
            print('.' * len(folderName) + '/' + filename)
            print('.' * len(folderName) + '/' + filename, file=fo)

# define layouts
mainscreencolumn1 = [[sg.Text('Root Directory', background_color=lightblue, justification='center', size=(25, 1))],
        [sg.Text('Root Folder', justification='right', size=(20, 1)),
        sg.InputText(key='_ROOTDIRECTORY_', size=(78, 1), enable_events=True), sg.FolderBrowse()],
        [sg.Text('Output File', justification='right', size=(20, 1)),
         sg.InputText(key='_OUTPUTFILE_', size=(78, 1), enable_events=True), sg.FileBrowse()]
        ]

# layout mainscreen window
mainscreenlayout = [[sg.Column(mainscreencolumn1, background_color=mediumblue)],
        [sg.Output(size=(110, 20), key='_OUTPUT_', font='courier 8')],
        [sg.Text('Message Area', size=(100, 1), key='_MESSAGEAREA_')],
        [sg.Button('Recurse', key='_RECURSE_'), sg.Exit()]]

# if __name__ == '__main__':
# ########################################
# initialize main screen window
window = sg.Window('CSV2Sqlite-GUI', background_color=mediumblue2, default_element_size=(20, 1)).Layout(mainscreenlayout)
window.Finalize()

# print('whatever', file=fo)

# event loop
while True:  # Event Loop
    event, values = window.Read()
    if event is None or event=="Exit":
        sys.exit(1)
    elif event=='_RECURSE_':
        # ########################################
        # get the root folder
        if len(values['_ROOTDIRECTORY_']) == 0:
            therootdir = getrootdirectory(values['_ROOTDIRECTORY_'], window)
        elif os.path.isdir(values['_ROOTDIRECTORY_']):
            write_to_message_area(window, 'Root directory exists')
            therootdir = values['_ROOTDIRECTORY_']
        else:
            therootdir = getrootdirectory(values['_ROOTDIRECTORY_'], window)
        window.FindElement('_ROOTDIRECTORY_').Update(therootdir)
        window.FindElement('_OUTPUT_').Update('')
        write_to_message_area(window, 'Show the directories')
        fo = open(values['_OUTPUTFILE_'], 'w')
        # fo = open('/Users/imlay/Downloads/directorylist.txt', 'w')
        recursive_walk(therootdir, fo)
        fo.close()
        write_to_message_area(window, 'Directory recursion complete')
# recursive_walk('/name/of/folder')


