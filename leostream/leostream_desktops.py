#!/usr/bin/python

import xmlrpclib
import sys
from optparse import OptionParser

def main(server_address, desktops_filename):
    print "Connecting..."
    try:
        leo = xmlrpclib.ServerProxy("http://%s/RPC2" % server_address)
    except Exception, e:
        print "Failed to connect"
        print e
        sys.exit(2)

    print "Authenticating..."

    login_info = {"USERNAME": "admin", "PASSWORD": "leo"}
    result = leo.Broker.Login(login_info)

    if result["ERROR"] != 0:
        print result
        sys.exit(2)

    login_token = result["SESSION_ID"]
    print "Session ID received."

    try:
        fh = open(desktops_filename, "r")
    except:
        print "Unable to open %s for reading" % desktops_filename
        sys.exit(3)

    success = 0
    failure = 0

    print "\n==> Adding desktops from %s" % desktops_filename

    for line in fh:
        line = line.strip()
        if line == "":
            continue
        if line.startswith("#"):
            continue

        desktop_info = {}
        desktop_info["SESSION_ID"] = login_token
        desktop_info["NAME"] = line
        desktop_info["ADDRESS"] = line
        desktop_info["OS"] = "WIN7"
        desktop_info["NOTES"] = "Added via API"

        result = leo.VM.Add(desktop_info)

        if not "ERROR" in result:
            print "Added desktop %s with ID %s" % (line, result["DESKTOP_ID"])
            success += 1
        elif result["ERROR"] == 24:
            print "Desktop %s already exists." % line
        else:
            print "Error while adding desktop %s: %s", (line, result)
            failure += 1

    print "Logging out from broker..."
    leo.Broker.Logout({"SESSION_ID": login_token})

    print "\n==> %d desktops added, %d failed." % (success, failure)

parser = OptionParser()
parser.add_option("-f", "--file", dest="filename", help="Build data CSV filename")
parser.add_option("-l", "--leostream", dest="leostream", help="IP or hostname of Leostream server")

(options, args) = parser.parse_args()

if not options.filename:
    print "Filename (-f) is required."
    sys.exit(3)

if not options.leostream:
    print "Leostream server (-l) is required."
    sys.exit(3)

main(options.leostream, options.filename)
