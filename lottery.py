#!/usr/bin/python

# A script that executes the Newton GWC Registration lottery. The input is
# a (cleaned -- see clean_input.py) CSV file representing the lottery
# entries.  It runs the lottery on first time and/or returning students,
# assigning to two sections of size N each.
#
# It runs the following algorithm until 2*N entrants are assigned:
#   * draw the next entrant
#
#   * if entrant can go to only one section, assign them to that section if it is still open.
#
#   * else, if entrant can go to either section, defer making an assignment until
#     one section fills, then assign that entrant to the other section.
#
# If neither section fills up but the limit of 2*N entrants is reached
# (including both assignments and deferred decisions), output the 3 lists:
# assigned-A, assigned-B, flexible. The let's the staff make the final
# assignments of flexible entrants to optimize age distribution and special
# cases (e.g. siblings assigned to different/same section)
#
# If either section fills up, all the deferrals are assigned to the
# remaining open section before the next entrant is drawn. When the global
# limit is reached, output 2 lists: assigned-A and assigned-B.
#
# The entrants are drawn randomly by shuffling the (timestamp-ordered)
# input using Python's random.shuffle() routine, and a random seed. The
# random seed can be provided at the command line (for reproducibility /
# testing) or can be taken from the system.
#
# Usage: lottery.py --section_limit N [--returning | --firsttime] --seed R --response_filename <filename>
#
# Author: David Miller, 2016

import csv
import random
import sys
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--section_limit', type=int)
parser.add_argument('--seed', help='Seed to random generator. If not set, users system seed', type=int)
parser.add_argument('--returning', help='Specify this to include returning participants', action='store_true')
parser.add_argument('--firsttime', help='Specify this to include first-time participants', action='store_true')
parser.add_argument('--response_filename', help='Name of the CSV file containing the lottery entries')
args = parser.parse_args()
FLAGS = vars(args)
# print "limit: %d" % FLAGS['section_limit']
# print "returning: %r" % FLAGS['returning']
# print "first-time: %r" % FLAGS['firsttime']

section_limit = FLAGS['section_limit']

# response_filename = '/Users/drm/Downloads/Lottery sample input - Sheet1.csv'
#response_filename = '/Users/drm/Downloads/Newton Girls Who Code Club 2016-2017 Registration (Responses) - Form Responses 1.csv'
response_filename = FLAGS['response_filename']
csv_file = open(response_filename, 'rb')
reader = csv.DictReader(csv_file)

# Simple accessor methods for lottery entries
def first_name(entry):
    return entry["Child's first name"]

def last_name(entry):
    return entry["Child's last name"]

def available_tuesday(entry):
    response = entry["Which sections are you entering the lottery for (you'll be assigned to at most one)?"]
    return 'T' in response

def available_friday(entry):
    response = entry["Which sections are you entering the lottery for (you'll be assigned to at most one)?"]
    return 'F' in response

def returning_student(entry):
    response = entry["Are you a returning Newton GWC Club member?"]
    return response == 'Yes' 

def available_both_days(entry):
    return available_tuesday(entry) and available_friday(entry)

entries = []
for entry in reader:
    if ((returning_student(entry) and FLAGS['returning']) or
        (not returning_student(entry) and FLAGS['firsttime'])):
        entries.append(entry)

if FLAGS['seed']:
    random.seed(FLAGS['seed'])
random.shuffle(entries)

accepted_tuesday = []
accepted_friday = []
accepted_flexible = []
drawn_after_full = []

def section_open(accepted_list):
    return len(accepted_list) < section_limit


def total_accepted():
    return len(accepted_tuesday) + len(accepted_friday) + len(accepted_flexible)


def to_string(entry):
    return ' '.join([first_name(entry), last_name(entry)])


def print_entry_list(entry_list):
    for entry in entry_list:
        print to_string(entry)


def print_lottery_result():
    print "\nAll done! Here are the results."
    print "\nAccepted Tuesday (%d): " % len(accepted_tuesday)
    print_entry_list(accepted_tuesday)

    print "\nAccepted Friday (%d): " % len(accepted_friday)
    print_entry_list(accepted_friday) 

    print "\nAccepted flexible (%d): " % len(accepted_flexible)
    print_entry_list(accepted_flexible)

    print "\nDrawn after full (%d): " % len(drawn_after_full)
    print_entry_list(drawn_after_full)

    print "\nNever drawn (%d): "% len(entries)
    print_entry_list(entries)

# Phase 1 -- put entrants in their sole-available section, or accept them but be flexible if they are.
print "\nStarting Phase 1"
while(section_open(accepted_tuesday) and section_open(accepted_friday) and total_accepted() < 2*section_limit and entries):
    entry = entries.pop()
    print "\nDrew entry: %s" % to_string(entry)
    if available_both_days(entry):
        accepted_flexible.append(entry)
        print "Keeping, flexible."
    elif available_friday(entry):
        accepted_friday.append(entry)
        print "Assigned to Friday"
    elif available_tuesday(entry):
        accepted_tuesday.append(entry)
        print "Assigned to Tuesday"
    else:
        print "Error! Entry %s had no valid availability" % to_string(entry)

# If we have enough flexibility that neither section was
# individually over-subscribed, print the three lists to allow Newton
# GWC Staff to distribute the flexible students to make a good balance
# of ages in each section. We're done.
if total_accepted() == 2*section_limit or not entries:
    print_lottery_result()
    sys.exit()

print "\nStarting Phase 2"
# Phase 2 -- one section filled up with entrants who have no
# flexibility. Move all the flexible ones to the other section.
underfull_section = None
if section_open(accepted_tuesday) and not section_open(accepted_friday):
    print "Friday section filled up! Assigning flexibles to Tuesday."
    accepted_tuesday.extend(accepted_flexible)
    accepted_flexible = []
    underfull_section = "tuesday"
elif section_open(accepted_friday) and not section_open(accepted_tuesday):
    print "Tuesday section filled up! Assigning flexibles to Friday."
    accepted_friday.extend(accepted_flexible)
    accepted_flexible = []
    underfull_section = "friday"
else:
    print "Error! Exited initial phase of the lottery without filling all slots and without filling either section."
    print_lottery_result()
    sys.exit()

# Phase 3 fill it out remaining section with additional draws from the pool.
print "\nStarting Phase 3"
while(total_accepted() < 2*section_limit and entries):
    entry = entries.pop()
    print "\nDrew entry: %s" % to_string(entry)
    if available_both_days(entry):
        if underfull_section == "tuesday":
            accepted_tuesday.append(entry)
            print "Assigned to Tuesday"
        elif underfull_section == "friday":
            accepted_friday.append(entry)
            print "Assigned to Friday"
        else:
            print "Error! Invalid value for underfull section"
    elif available_friday(entry) and underfull_section == "friday":
        accepted_friday.append(entry)
        print "Assigned to Friday"
    elif available_tuesday(entry) and underfull_section == "tuesday":
        accepted_tuesday.append(entry)
        print "Assigned to Tuesday"
    else:
        drawn_after_full.append(entry)
        print "Can't assign! Only available for full section"


print_lottery_result()
