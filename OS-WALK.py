import os


def CheckSubFolder( folder ):
    for root, directories, files in os.walk(folder):
        for f in files:
            print('"%s","%s"' % (root, f))

# Code Entry
# path = sys.argv[1]

CheckSubFolder('C:/Users/imlay/OneDrive/Documents/GitHub/csv2sqlite-gui')