#!/usr/bin/python
# vim: tabstop=8  softtabstop=4  shiftwidth=4  nocindent  smartindent
import os, sys
import sqlite3
import datetime
import subprocess
import shlex
import argparse
import string

def get_hash_from_file(filename):
    """Generate the git hash of a file"""
    global debug
    cmd = "git hash-object " + filename
    hashtxt, err = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    hashtxt = hashtxt.splitlines()
    err = err.splitlines()
    if debug:
        for line in hashtxt:
            print "  Txt: %s" % line
        for line in err:
            print "  Err: %s" % line
    obj_hash = hashtxt[0].strip()
    if Verbose:
        print "Hash:", obj_hash, filename
    return obj_hash

def do_one_way(the_hashes):
    global conn
    global curs
    conn = sqlite3.connect("gitxref.sqlite")
    curs = conn.cursor()
    blob_map = {}
    commit_map = {}

    select = "select blob_hash, blob_name, c.commit_hash, timestamp, message "+\
            "from blob_tab b, commit_tab c "+\
            "where b.blob_hash == :1 and b.commit_hash == c.commit_hash "+\
            "order by timestamp"
    for one_hash in the_hashes:
        curs.execute(select, (one_hash,))
        old_hash = None
        for blob_hash, blob_name, commit_hash, timestamp, message in  curs.fetchall():
            if blob_hash != old_hash:
                if Verbose:
                    print "File:", blob_hash, blob_name
                old_hash = blob_hash
            if blob_hash not in blob_map:
                blob_map[blob_hash] = (blob_name, set())
            blob_map[blob_hash][1].add(commit_hash)
            if commit_hash not in commit_map:
                commit_map[commit_hash] = (timestamp, message, set())
            commit_map[commit_hash][2].add(blob_hash)
            if len(message) > 60:
                message = message[:57] + "..."
            timestamp = datetime.datetime.fromtimestamp(timestamp)
            if Verbose:
                print "  Commit:", commit_hash, timestamp, message
    commit_union = set(commit_map.keys())
    junk = sorted(commit_map.keys(),\
        key=lambda x: (len(commit_map[x][2]), -commit_map[x][0]),\
        reverse=True)
    for blob_key in blob_map.keys():
        blob_name, commit_set = blob_map[blob_key]
        commit_union.intersection_update(commit_set)
    if len(commit_union) == 0:
        print "Recalculating commit_map"
        for commit_key in sorted(commit_map.keys(), key=lambda x: len(commit_map[x][2]), reverse=True):
            timestamp, message, blobs = commit_map[commit_key]
            if len(commit_union) == 0:
                blob_union = set(blobs)
            if len(blob_union.intersection(blobs)) < len(blob_union):
                break;
            commit_union.add(commit_key)
    if 1 in Summary:
        print "Summary1: Files with Commits"
        for blob_key in blob_map.keys():
            blob_name, commit_set = blob_map[blob_key]
            print blob_key +":", blob_name, len(commit_set)
    if 2 in Summary:
        print "Summary2: Commits with most files"
        for commit_key in sorted(commit_union, key=lambda x: commit_map[x][0]):
            timestamp, message, blobs = commit_map[commit_key]
            timestamp = datetime.datetime.fromtimestamp(timestamp)
            if len(message) > 50:
                message = message[:47] + "..."
            print "  Commit:", commit_key, timestamp, len(blobs), message
    if 3 in Summary:
        print "Summary3: Commits with files"
        for commit_key in sorted(commit_map.keys(), key=lambda x: commit_map[x][0]):
            timestamp, message, blobs = commit_map[commit_key]
            timestamp = datetime.datetime.fromtimestamp(timestamp)
            if len(message) > 60:
                message = message[:57] + "..."
            print "  Commit:", commit_key, timestamp, len(blobs), message
    if 4 in Summary:
        print "Summary4: Files not in Summary 2"
        for blob_key in blob_map.keys():
            blob_name, commit_set = blob_map[blob_key]
            if len(commit_union.intersection(commit_set)) == 0:
                print "\n"+blob_key +":", blob_name, len(commit_set), commit_set
    if 5 in Summary:
        print "Summary5: Files without Commits"
        for hash_key in [x for x in hash_map.keys() if x not in blob_map]:
            print hash_key, hash_map[hash_key]

def do_args():
    global hash_map, args
    the_hashes = []
    hash_map = {}
    for filename in args.filenames:
        if '.' in filename:
            one_hash = get_hash_from_file(filename)
            hash_map[one_hash] = filename
            the_hashes.append(one_hash)
        elif all(a in string.hexdigits for a in filename):
            the_hashes.append(filename)
    do_one_way(the_hashes)

def main_program():
    global debug, Verbose, Summary
    global hash_map, args
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", help="Add debugging output", action="store_true")
    parser.add_argument("-p", "--profile", help="Add profile output", action="store_true")
    parser.add_argument("-v", "--verbose", help="Add verbose output", action="store_true")
    parser.add_argument("-s", "--summary", \
        default = "2", \
        help="select summary")
    parser.add_argument("filenames", metavar="file", help="existing filename(s)", nargs="+")
    args = parser.parse_args()
    if args.debug:
        debug = True
    else:
        debug = False
    if args.verbose:
        Verbose = True
    else:
        Verbose = False
    if Verbose or debug:
        print args
    Summary = set()
    for rng in [x.strip() for x in args.summary.split(',')]:
        if '-' in rng:
            lo, hi = rng.split('-')
            if lo.isdigit() and hi.isdigit():
                for idx in range(int(lo), int(hi)+1):
                    Summary.add(idx)
        else:
            if rng.isdigit():
                Summary.add(int(rng))
    print "Summary:", Summary
    if args.profile:
        import cProfile
        cProfile.run('do_args()')
    else:
        do_args()

if __name__ == "__main__":
    main_program();
