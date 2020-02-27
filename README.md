# csv2sqlite-gui
csv2sqlite with a PySimpleGUI front end

This script is based on csv2sqlite.py. That script (as the name implies) converted a CSV file to a table in a Sqlite database. While it worked well, it was a command line script. I'd been looking for something with which to practice building a gui. I'd also been interested in Python scripts to manipulate data so this new version was born.

In addition to putting a front end on the conversion script, I added some functionality to update filenames and change the table name if it already exists in the database. Future improvements will include the ability to update table column names and column types before the file is converted into a table.
