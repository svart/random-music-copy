#!/usr/bin/env python2
# -*- coding: utf8 -*-

import os
import optparse
import subprocess
import random
import shutil
import sys
import multiprocessing
import time

sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

EXCLUDE_DIRS = ['OST', 'Classical']
EXTENSIONS = ('mp3', 'flac', 'm4a')


def get_free_disk_space(path):
    return int(subprocess.check_output('df ' + path, shell=True).split('\n')[1].split()[3])

def get_size(start_path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size


def must_be_excluded(dirpath, exclude_list):
    for item in exclude_list:
        if item in dirpath:
            return True
    return False


def print_error(message):
    print 'ERROR: ' + message
    exit(1)


def process_options():
    usage = '''%prog -f SOURCE_DIR [-f SOURCE_DIR2 ...] -t DEST_DIR -s MBYTES [-n NFILES].'''

    parser = optparse.OptionParser(usage=usage)
    parser.add_option('-f', '--from', dest='from_dir',
            action='append', type='string', default=[],
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
    for from_dir in opts.from_dir:
        if not os.path.isdir(from_dir):
            print_error('No such directory: ' + from_dir)

    FROM_DIRS = opts.from_dir
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

print 'Scanning source directories...'

for from_dir in FROM_DIRS:
    for dirname, dirnames, filenames in os.walk(from_dir):
        if not must_be_excluded(dirname, EXCLUDE_DIRS):
            for filename in filenames:
                if filename.lower().endswith(EXTENSIONS):
                    found_files.append(os.path.join(dirname, filename))

print 'Copying files...'

if not found_files:
    print 'Nothing to copy'
    exit(0)

def do_copy(from_path, to_path):
    shutil.copy(from_path, to_path)
    #print 'Copy', from_path, to_path


def do_transcode(from_path, to_path):
    base_name = os.path.basename(from_path)
    path_to_temp_file = '/tmp/' + base_name[:base_name.rfind('.')] + '.mp3'

    ffmpeg_command = 'ffmpeg -loglevel quiet -threads 1 -i "' + from_path + '" -b:a 320k "' + path_to_temp_file + '"'
    os.system(ffmpeg_command)

    shutil.move(path_to_temp_file, to_path)
    #os.remove(path_to_temp_file)
    #print 'Transcode', from_path, to_path


copied_indexes = []
copied_size = 0
number_of_cores = multiprocessing.cpu_count()
jobs = []
while True:
    index = random.randint(0, len(found_files) - 1)
    if index not in copied_indexes:
        fileSize = os.stat(found_files[index]).st_size
        copied_size = get_size(TO_DIR)
        if fileSize + copied_size < FILES_SIZE * 1024 * 1024:
            if FILES_NUMBER and FILES_NUMBER <= len(copied_indexes):
                break

            if len(jobs) < number_of_cores:
                if found_files[index].lower().endswith('mp3'):
                    #do_copy(found_files[index], TO_DIR)
                    p = multiprocessing.Process(target=do_copy, args=(found_files[index], TO_DIR,))
                    jobs.append(p)
                    p.start()
                else:
                    #do_transcode(found_files[index], TO_DIR)
                    p = multiprocessing.Process(target=do_transcode, args=(found_files[index], TO_DIR,))
                    jobs.append(p)
                    p.start()

                copied_indexes.append(index)

            for i, job in enumerate(jobs):
                if not job.is_alive():
                    jobs.pop(i)
            time.sleep(0.25)
        else:
            break

    if len(copied_indexes) == len(found_files):
        break

    print '\rCopied %d files with size %d MB of %d'%(len(copied_indexes), copied_size / (1024*1024), FILES_SIZE),


print ''
print 'Copied files: ', len(copied_indexes)
print 'With total size: ', copied_size/(1024*1024), "MB"
