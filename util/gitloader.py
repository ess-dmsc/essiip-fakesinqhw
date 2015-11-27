#!/usr/bin/python
# vim: tabstop=8  softtabstop=4  shiftwidth=4  nocindent  smartindent
import os, sys
import sqlite3
import subprocess
import shlex
import traceback

def setup_database():
    """Create a database to hold the data"""
    global conn, curs
    if os.path.exists("gitxref.sqlite"):
        os.remove("gitxref.sqlite")
    conn = sqlite3.connect("gitxref.sqlite")
    curs = conn.cursor()
    curs.execute("CREATE TABLE commit_tab (commit_hash TEXT, timestamp INTEGER, message TEXT)")
    curs.execute("CREATE TABLE blob_tab (commit_hash TEXT, blob_hash TEXT, blob_name TEXT)")

def populate_data():
    global conn, curs
    cmd = 'git log --pretty=format:"%T %H %at %s" ' + args.branch
    log_txt, err = subprocess.Popen(shlex.split(cmd),\
            stdout=subprocess.PIPE,\
            stderr=subprocess.PIPE).communicate()
    log_txt = log_txt.splitlines()
    err = err.splitlines()
    for log_line in log_txt:
        tree_hash, commit_hash, timestamp, message = log_line.split(" ", 3)
        curs.execute("insert into commit_tab values (:1, :2, :3)",\
            (commit_hash, timestamp, repr(message)))

        cmd = "git ls-tree -r " + tree_hash
        if args.full:
            cmd += " --full-tree"
        ls_txt, err = subprocess.Popen(shlex.split(cmd),\
                stdout=subprocess.PIPE,\
                stderr=subprocess.PIPE).communicate()
        ls_txt = ls_txt.splitlines()
        err = err.splitlines()
        for line in ls_txt:
            a, b, blob_hash, fname = line.split(None, 3)
            curs.execute("insert into blob_tab values (:1, :2, :3)",\
                (commit_hash, blob_hash, fname))

def create_indexes():
    global conn, curs
    curs.execute("CREATE INDEX commit_commit on commit_tab (commit_hash)")
    curs.execute("CREATE INDEX commit_blob on blob_tab (commit_hash)")
    curs.execute("CREATE INDEX blob_blob on blob_tab (blob_hash)")

def main_program():
    setup_database()
    populate_data()
    create_indexes()

if __name__ == "__main__":
    global args
    import argparse
    import cProfile
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--branch", default="HEAD", help="git branch [HEAD]")
    parser.add_argument("-d", "--debug", action="store_true", help="debugging output")
    parser.add_argument("-f", "--full", action="store_true", help="git --full-tree")
    parser.add_argument("-p", "--profile", action="store_true", help="profile output")
    args = parser.parse_args()
    if args.profile:
        cProfile.run('main_program()')
    else:
        main_program()
