import argparse
from library.files import FileObject
from library.plots import ScatterPlot
import numpy
import time
import os
import sqlite3
from collections import defaultdict


def main():
    # Argument parsing
    parser = argparse.ArgumentParser(
        description='Calculates the entropy of a file.')
    parser.add_argument('MalwareDirectory',
                        help='The directory containing malware to analyze.')
    parser.add_argument('SQLFile',
                        help='The SQLite file to be created for '
                             'the file metadata.')
    parser.add_argument("-w", "--window",
                        help="Window size, in bytes, for running entropy."
                             "Multiple windows can be identified as comma "
                             "separated values without spaces."
                             "", type=str, required=False)
    parser.add_argument("-n", "--nonormalize", action='store_true',
                        help="Disables entropy normalization."
                             "", required=False)

    args = parser.parse_args()

    # Normalize setup...
    if args.nonormalize:
        normalize = False
    else:
        normalize = True

    # Find window sizes
    windows = None
    if args.window:
        windows = args.window.split(',')
        windows = [x.strip() for x in windows]
        windows = [int(x) for x in windows]

    print("Storing data in SQLite file {0}".format(args.SQLFile))
    try:
        os.remove(args.SQLFile)
    except:
        pass

    main_conn = sqlite3.connect(args.SQLFile)
    main_cursor = main_conn.cursor()

    main_cursor.execute('CREATE TABLE metadata(' +
                        'ID INTEGER PRIMARY KEY AUTOINCREMENT,'
                        'filepath TEXT NOT NULL,'
                        'filesize INT NOT NULL,'
                        'filetype TEXT,'
                        'fileentropy REAL,'
                        'MD5 TEXT,'
                        'SHA256 TEXT,'
                        'DBFile TEXT'
                        ');')
    main_conn.commit()

    # Crawl the directories for malware
    for root, dirs, files in os.walk(args.MalwareDirectory):
        for f in files:
            # Create the malware file name...
            malwarepath = os.path.join(root, f)
            m = FileObject(malwarepath)
            print("\tCalculating {0}".format(m.filename))

            # Calculate the entropy of the file...
            fileentropy = m.entropy(normalize)

            # Create the DB file name by first creating the directory...
            dbfile = os.path.join(root + "_db", f)
            dbfile = dbfile + ".db"

            # Create the directory if needed...
            try:
                os.stat(root + "_db")
            except:
                os.mkdir(root + "_db")

            # Prepare and execute SQL for main DB...
            sql = "INSERT INTO metadata (filepath, filesize, filetype, " + \
                  "fileentropy, MD5, SHA256, DBFile) VALUES " + \
                  "(:filepath, :filesize, :filetype, :fileentropy, " + \
                  ":md5, :sha256, :dbfile);"
            params = {'filepath': m.filename, 'filesize': m.file_size,
                      'filetype': m.filetype, 'fileentropy': fileentropy,
                      'md5': m.md5, 'sha256': m.sha256, 'dbfile': dbfile}
            main_cursor.execute(sql, params)
            main_conn.commit()

            # Calculate the window entropy for malware samples...
            if windows is not None:
                # Prepare and execute SQL for sample DB...
                try:
                    os.remove(dbfile)
                except:
                    pass
                malware_conn = sqlite3.connect(dbfile)
                malware_cursor = malware_conn.cursor()
                malware_cursor.execute('CREATE TABLE windowentropy(' +
                                       'ID INTEGER PRIMARY KEY AUTOINCREMENT,'
                                       'windowsize INT NOT NULL,'
                                       'offset INT NOT NULL,'
                                       'entropy REAL NOT NULL'
                                       ');')
                malware_conn.commit()
                malware_cursor.execute('CREATE TABLE windows(' +
                                       'ID INTEGER PRIMARY KEY AUTOINCREMENT,'
                                       'windowsize INT NOT NULL'
                                       ');')
                malware_conn.commit()

                for w in windows:
                    print("\t\tCalculating window size {0}".format(w))
                    # Add the window size to the database...
                    sql = "INSERT INTO windows (windowsize) VALUES (:windowsize)"
                    params = {'windowsize': w}
                    malware_cursor.execute(sql, params)
                    malware_conn.commit()

                    # Calculate running entropy...
                    running_entropy = m.running_entropy(w, normalize)

                    # Add running entropy to the database...
                    malware_offset = 0
                    for r in running_entropy:
                        sql = "INSERT INTO windowentropy " + \
                              "(windowsize, offset, entropy) " + \
                              "VALUES (:windowsize, :offset, :entropy);"
                        params = {'windowsize': w, 'offset': malware_offset,
                                  'entropy': r}
                        malware_cursor.execute(sql, params)
                        malware_conn.commit()
                        malware_offset += 1

                malware_conn.commit()
                malware_conn.close()

    main_conn.commit()
    main_conn.close()


if __name__ == "__main__":
    main()