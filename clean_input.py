#!/usr/bin/python

# A script to do some basic clean up of the Newton GWC Registation
# lottery. This operates on the exported CSV file representing the lottery
# entries. Several people made repeat entries, and this script discards all
# but the most recent. It assumes that no two entrants have the same child
# first-name/last-name combination, which looks to be true.
#
# The script outputs diagnostic information for what it cleans up so an
# administrator can audit the operation (and, for example, check for two
# different entrants with the same first/last name combination).
#
# Usage: cleanup_input.py --input <filename> --output <filename>

import csv
import sys
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--input', help='Name of the raw CSV file containing the lottery entries', required=True)
parser.add_argument('--output', help='Name of the cleaned CSV file containing the lottery entries', required=True)
args = parser.parse_args()
FLAGS = vars(args)

input_filename = FLAGS['input']
csv_file = open(input_filename, 'rb')
reader = csv.DictReader(csv_file)

# Simple accessor methods for lottery entries
def first_name(entry):
    return entry["Child's first name"].strip()

def last_name(entry):
    return entry["Child's last name"].strip()
                 
entries = []
duplicate_entries = []
entrant_by_names = {}
for entry in reader:
    key = ' '.join([first_name(entry), last_name(entry)])
    if key in entrant_by_names:
        old_entry = entrant_by_names[key]
        print "Warning! Duplicate entries for %s" % key
        print "\nKeeping new: %s" % entry
        print "\nDiscarding existing: %s" % old_entry
        duplicate_entries.append(old_entry)
        entries.remove(old_entry)
        entries.append(entry)
        # Overwrite the old entry with the new
        entrant_by_names[key] = entry
    elif key == "David Miller":
        print "Discarding David's test entry"
        duplicate_entries.append(entry)
    else:
        entrant_by_names[key] = entry
        entries.append(entry)
        print 'Parsed entry for %s' % key
        
print "Found %d distinct entries" % len(entries)
print "Found %d duplicates/dummy entries" % len(duplicate_entries)

cleaned_filename = FLAGS['output']
cleaned_file = open(cleaned_filename, 'wb')
writer = csv.DictWriter(cleaned_file, fieldnames=reader.fieldnames)
writer.writeheader()
for entry in entries:
    writer.writerow(entry)
