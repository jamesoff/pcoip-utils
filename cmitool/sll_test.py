# Teradici CMI interface devlopment script
#
# dave.glenton@amulethotley.com, 1-11-11
#
# Notes: 	
#	http://docs.python.org/library/ssl.html
# 	http://www3.rad.com/networks/applications/secure/tls.htm
# How to convert pfx to pem (as needed by Python)
#	http://help.globalscape.com/help/eft5/admin/exporting_a_certificate_from_pfx_to_pem.htm
#   pfx password is password
#
# TERA uses SSL/TLS and requires a X.509 certificate in PEM format(Pg 134)

import socket, ssl, pprint
url = "192.168.16.137"

# Create a new socket 's' 
# socket.AF_INET 		: Socket address family host IP address and port no
# socket.SOCK_STREAM 	: Default socket type (vs DGRAM, RAW, RDM, SEQPACKET
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Wrap the socket s into a SSL 
# certfile 				: Certificate file to identify local side of the connection
# cert_reqs				: Is a certificate required to authenticate Teradici (No)
ssl_sock = ssl.wrap_socket(s,certfile="cms.pem",cert_reqs=ssl.CERT_NONE)

# open a connection
ssl_sock.connect((url, 50000))

# Display SSL properties
print repr(ssl_sock.getpeername())
print ssl_sock.cipher()

# Hack up a SOAP message
message = """<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://www.w3.org/2003/05/soap-envelope" xmlns:SOAP-ENC="http://www.w3.org/2003/05/soap-encoding" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:pcoip="http://www.pcoip.org/2006/XMLSchema" xmlns:SOAP-RPC="http://www.w3.org/2003/05/soap-rpc"><SOAP-ENV:Body><pcoip:getNetwork SOAP-ENV:encodingStyle="http://www.w3.org/2003/05/soap-encoding"></pcoip:getNetwork></SOAP-ENV:Body></SOAP-ENV:Envelope>"""
print "-------------------------- [Rx]"
print message

# Send SOAP message to socket
ssl_sock.write(message)

# Read upto 1024 bytes of data.  Will not necessarily
# read all the data returned by the server.
print "------------------------- [Rx]"
data = ssl_sock.read()
print data
data = ssl_sock.read()
print data

# Be polite and close down the link
ssl_sock.close()
