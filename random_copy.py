#!/usr/bin/env python2
# -*- coding: utf8 -*-

import os
import optparse
import subprocess
import random
import shutil


EXCLUDE_DIRS = ['OST']

def get_free_disk_space(path):
    return int(subprocess.check_output('df ' + path, shell=True).split('\n')[1].split()[3])

def must_be_excluded(dirpath, exclude_list):
    for item in exclude_list:
        if item in dirpath:
            return True
    return False

def print_error(message):
    print 'ERROR: ' + message
    exit(1)

def process_options():
    usage = '''%prog -f SOURCE_DIR -t DEST_DIR -s MBYTES [-n NFILES].'''

    parser = optparse.OptionParser(usage=usage)
    parser.add_option('-f', '--from', dest='from_dir',
            action='store', type='str', default='',
            help=('Source directory.'))
    parser.add_option('-t', '--to', dest='to_dir',
            action='store', type='str', default='',
            help=('Destination directory'))
    parser.add_option('-s', '--size', dest='size',
            action='store', type='int', default=0,
            help=('Entire size of copied files in MB'))
    parser.add_option('-n', '--number', dest='number',
            action='store', type='int', default=0,
            help=('Number of copied files'))

    opts, args = parser.parse_args()
    if not args:
        args = ['.']
    return opts, args

# Parsing options
opts, args = process_options()

# Checking options
if opts.from_dir:
    if os.path.isdir(opts.from_dir):
        FROM_DIR = opts.from_dir
    else:
        print_error('No such directory: ' + opts.from_dir)
else:
    print_error('Source directory must be set')

if opts.to_dir:
    if os.path.isdir(opts.to_dir):
        TO_DIR = opts.to_dir
    else:
        print_error('No such directory: ' + opts.to_dir)
else:
    print_error('Destination directory must be set')

if opts.size:
    FILES_SIZE = opts.size
else:
    print_error('Copy size mus be set')

if opts.number:
    FILES_NUMBER = opts.number
else:
    FILES_NUMBER = 0

# Checking free space on destination
if get_free_disk_space(TO_DIR) < FILES_SIZE * 1024:
    print_error('Not enough free space in destination directory')

found_files = []

print 'Scanning directory...'

for dirname, dirnames, filenames in os.walk(FROM_DIR):
    if not must_be_excluded(dirname, EXCLUDE_DIRS):
        for filename in filenames:
            if filename.endswith('mp3'):
                found_files.append(os.path.join(dirname, filename))

print 'Copying files...'

if not found_files:
    print 'Nothing to copy'
    exit(0)

copied_indexes = []
copied_size = 0
while True:
    index = random.randint(0, len(found_files) - 1)
    if index not in copied_indexes:
        fileSize = os.stat(found_files[index]).st_size
        if fileSize + copied_size < FILES_SIZE * 1024 * 1024:
            if FILES_NUMBER and FILES_NUMBER <= len(copied_indexes):
                break

            shutil.copy(found_files[index], TO_DIR)
            copied_indexes.append(index)
            copied_size += fileSize

        else:
            break

    if len(copied_indexes) == len(found_files):
        break
        

print 'Copied files: ', len(copied_indexes)
print 'With total size: ', copied_size/(1024*1024), "MB"
