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
def folder_walk(folder, fo, includefiles=None):
    for folderName, subfolders, filenames in os.walk(folder):
        # print to stdout which is redirected to the Output element in the UI
        if includefiles:
            for filename in filenames:
                print('"%s","%s"' % (folderName, filename))
                if fo is not None:
                    print('"%s","%s"' % (folderName, filename), file=fo)
        else:
            print(folderName + '/')
            window.Refresh()
            # print to a text file
            if fo is not None:
                print(folderName + '/', file=fo)


# define layouts
mainscreencolumn1 = [[sg.Radio('Directories only', "RADIO1", default=True, key='_DONLY_', size=(20, 1)),
         sg.Radio('Include files', "RADIO1", key='_INCLFILES_', size=(20, 1))],
        [sg.Radio('Display only', "RADIO2", default=True, key='_DISPONLY_', size=(20, 1)),
         sg.Radio('Save to output file', "RADIO2", key='_SAVE2FILE_', size=(20, 1))],
        [sg.Text('Root Folder', justification='right', size=(20, 1)),
        sg.InputText(key='_ROOTDIRECTORY_', size=(77, 1), enable_events=True), sg.FolderBrowse()],
        [sg.Text('Output File', justification='right', size=(20, 1)),
         sg.InputText(key='_OUTPUTFILE_', size=(77, 1), enable_events=True), sg.FileBrowse()]
        ]

# layout mainscreen window
mainscreenlayout = [[sg.Column(mainscreencolumn1, background_color=mediumblue)],
        [sg.Output(size=(112, 20), key='_OUTPUT_', font='courier 8')],
        [sg.Text('Message Area', size=(100, 1), key='_MESSAGEAREA_')],
        [sg.Button('Walk the Directory', key='_WALKDIR_'), sg.Exit()]]

# if __name__ == '__main__':
# ########################################
# initialize main screen window
window = sg.Window('CSV2Sqlite-GUI', background_color=mediumblue2,
        default_element_size=(20, 1)).Layout(mainscreenlayout)
window.Finalize()

# print('whatever', file=fo)

# event loop
while True:  # Event Loop
    event, values = window.Read()
    if event is None or event=="Exit":
        sys.exit(1)
    elif event=='_WALKDIR_':
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

        if values['_DONLY_']:
            if values['_SAVE2FILE_']:
                # sg.Popup('Directories only', keep_on_top=True)
                try:
                    fo = open(values['_OUTPUTFILE_'], 'w')
                    print('"%s"' % ('Directoryname'), file=fo)
                    sg.Popup('directory only and write to file')
                    folder_walk(therootdir, fo, False)
                    fo.close()
                except:
                    sg.Popup('Enter a filename for the output')
            else:   #don't save to a file
                sg.Popup('directory only and display only')
                folder_walk(therootdir, None, False)
        else:   # include files
            if values['_SAVE2FILE_']:
                try:
                    fo = open(values['_OUTPUTFILE_'], 'w')
                    print('"%s","%s"' % ('Directoryname', 'Filename'), file=fo)
                    sg.Popup('directory and files and write to file')
                    folder_walk(therootdir, fo, True)
                    fo.close()
                except:
                    sg.Popup('Enter a filename for the output')
                    continue
            else:   # don't save to a file
                sg.Popup('directory and files and display only')
                folder_walk(therootdir, None, True)

        write_to_message_area(window, 'Directory walk complete')
# folder_walk('/name/of/folder')


