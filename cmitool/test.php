<?php

	if ($argc < 3) {
		echo "Usage: " . $argv[0] . " <ip> <soapcall> [param]\n";
		exit();
	}

	$address = $argv[1];
	$call = $argv[2];

	if ($argc == 4) {
		$param = $argv[3];
	}
	else {
		$param = nil;
	}

	$client = new SoapClient("pcoip.wsdl", array('local_cert' => 'cms.pem', 'passphrase' => 'password', 'location' => 'https://$address:50000', 'trace' => 1, 'soap_version' => SOAP_1_2));
	$result = "(nothing)";

	try {
		$result = $client->__soapCall($call, array($param));
	}
	catch (Exception $e) {
		print "Error\n";
		print $e;
	}

	print_r($result);	
	print "\n";
?>