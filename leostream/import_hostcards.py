#!/usr/bin/python

"""Match host cards up to desktops in Leostream

Reads a CSV file which should have the format:
service_tag,mac[,mac]

service_tag is a Dell service tag, which Leostream stores in the bios_serial_number field of the vm table (i.e. desktops)
mac is an uppercased hypenated MAC address of a host card chip which should be set as the host card in the desktop
Add a second mac address if the blade has two host cards

The script will not change a blade's configuration if it already has a hostcard set.

Note that the script does not use any pgsql modules as their availablity cannot be guaranteed. 
Instead, it calls out to the psql command-line tool a lot. This is not optimal, but since this script will only be used
for initial installs it shouldn't matter too much.

This script needs to run on Python 2.4, as the version installed in the broker VM is 2.4.3.
Reference link: http://docs.python.org/release/2.4.3/

JMS
20130207 (Happy birthday, me!)

"""

import os
import sys
import re

from subprocess import Popen, PIPE
from optparse import OptionParser


def load_desktops():
	D = {}

	try:
		desktop_info = Popen(["psql", "-d", "leo", "-A", "-t", "-c", "SELECT id,bios_serial_number,terahost_id,terahost_id2 FROM vm WHERE bios_serial_number != '' AND deleted = 0;"], stdout=PIPE).communicate()[0]
	except Exception, e:
		print "Error reading desktops from database"
		print e
		sys.exit(1)

	lines = desktop_info.split("\n")
	for line in lines:
		line = line.strip()
		if line == "":
			continue
		try:
			desktop = {}
			desktop['id'], desktop['service_tag'], desktop['terahost_id'], desktop['terahost_id2'] = line.split("|")
			D[desktop['service_tag']] = desktop
		except Exception, e:
			print "Error reading line %s: %s" % (line, e)

	print "Loaded %d desktops from Leostream database." % len(D)

	return D


def load_hostcards():
	H = {}

	try:
		hostcard_info = Popen(["psql", "-d", "leo", "-A", "-t", "-c", "SELECT id,mac FROM terahost WHERE mac != '' AND deleted = 0;"], stdout=PIPE).communicate()[0]
	except Exception, e:
		print "Error reading desktops from database"
		print e
		sys.exit(1)

	lines = hostcard_info.split("\n")
	for line in lines:
		line = line.strip()
		if line == "":
			continue
		try:
			hostcard = {}
			hostcard['id'], hostcard['mac'] = line.split("|")
			H[hostcard['mac']] = hostcard
		except Exception, e:
			print "Error reading line %s: %s" % (line, e)

	print "Loaded %d hostcards from Leostream database." % len(H)

	return H


def load_csv(filename):
	B = []

	r_no_hyphens = re.compile("^([0-9A-Fa-f]{2})([0-9A-Fa-f]{2})([0-9A-Fa-f]{2})([0-9A-Fa-f]{2})([0-9A-Fa-f]{2})([0-9A-Fa-f]{2})$")
	warned = False

	try:
		fh = open(filename, 'r')
	except:
		print "Unable to open %s" % filename
		sys.exit(1)

	for line in fh:
		line = line.strip()
		if line == "" or line.startswith("#"):
			continue
		bits = line.split(",")
		build_data = {}
		build_data["service_tag"] = bits[0].strip()
		build_data["mac1"] = bits[1].strip()
		if len(bits) == 3:
			build_data["mac2"] = bits[2].strip()
		else:
			build_data["mac2"] = ""

		matches = r_no_hyphens.search(build_data["mac1"])
		if matches:
			if not warned:
				print "Fixing MAC addresses to have hypens"
				warned = True
			build_data["mac1"] = "-".join([matches.group(x).upper() for x in range(1,6)])

		matches = r_no_hyphens.search(build_data["mac2"])
		if matches:
			if not warned:
				print "Fixing MAC addresses to have hypens"
				warned = True
			build_data["mac2"] = "-".join([matches.group(x).upper() for x in range(1,6)])

		B.append(build_data)

	print "Loaded %d lines from build data." % len(B)

	try:
		fh.close()
	except:
		pass

	return B


def do_matchup(DESKTOPS, HOSTCARDS, BUILD_DATA):
	S = []

	# for each desktop in build data
	for build_desktop in BUILD_DATA:
		service_tag = build_desktop['service_tag']
		if not service_tag in DESKTOPS:
			print "Blade %s is unknown to Leostream." % service_tag
			continue
		
		if not DESKTOPS[service_tag]["terahost_id"] in ["", "0"]:
			print "Blade %s already has a host card assigned in Leostream." % service_tag
			continue

		blade_id = DESKTOPS[service_tag]['id']

		host_mac_1 = build_desktop["mac1"]
		host_mac_2 = build_desktop["mac2"]
		try:
			host_id_1 = HOSTCARDS[host_mac_1]['id']
		except:
			print "Unable to find host card with MAC %s in Leostream (while processing blade %s)" % (host_mac_1, service_tag)
			continue
		
		try:
			if host_mac_2 != "":
				host_id_2 = HOSTCARDS[host_mac_2]['id']
			else:
				host_id_2 = "0"
		except:
			print "Unable to find host card with MAC %s in Leostream (while processing blade %s T2)." % (host_mac_2, service_tag)
			continue

		sql = "UPDATE vm SET terahost_id = '%s', terahost_id2 = '%s' WHERE id = '%s';" % (host_id_1, host_id_2, blade_id)
		
		S.append(sql)

	return S


def main():
	parser = OptionParser()
	parser.add_option("-f", "--file", dest="filename", help="Build data CSV filename")
	parser.add_option("-o", "--output", dest="output", help="Filename to save SQL script in")

	(options, args) = parser.parse_args()

	if not options.filename:
		print "Filename (-f) is required."
		sys.exit(3)

	DESKTOPS = load_desktops()
	if len(DESKTOPS) == 0:
		print "Can't continue without desktops."
		sys.exit(2)
	#print DESKTOPS

	HOSTCARDS = load_hostcards()
	if len(HOSTCARDS) == 0:
		print "Can't continue without hostcards."
		sys.exit(2)
	#print HOSTCARDS

	BUILD_DATA = load_csv(options.filename)
	if len(BUILD_DATA) == 0:
		print "Can't continue without any build data."
		sys.exit(2)
	#print BUILD_DATA

	SQL = do_matchup(DESKTOPS, HOSTCARDS, BUILD_DATA)
	
	if len(SQL) > 0:
		if options.output:
			print "Writing SQL commands to %s" % options.output
			try:
				fh = open(options.output, 'w')
				for line in SQL:
					fh.write("%s\n" % line)
				fh.close()
				print "Finished."
			except Exception, e:
				print "Failed while writing SQL commands out: %s", e
				sys.exit(4)
		else:
			print "SQL to execute follows:"
			for line in SQL:
				print line


if __name__ == "__main__":
	main()



