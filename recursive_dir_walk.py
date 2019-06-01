#! /usr/local/bin/python3
# findLargeFiles.py - given a folder name, walk through its entire hierarchy
#                   - print folders and files within each folder

import os

def recursive_walk(folder):
    for folderName, subfolders, filenames in os.walk(folder):
        if subfolders:
            for subfolder in subfolders:
                recursive_walk(subfolder)
        print(folderName + '/')
        for filename in filenames:
            print(' ' * len(folderName) + '/' + filename)


# recursive_walk('/name/of/folder')
recursive_walk('/Users/imlay/PycharmProjects/')