[![Build Status](https://travis-ci.org/job/rpki-ov-checker.svg?branch=master)](https://travis-ci.org/job/rpki-ov-checker)
[![Requirements Status](https://requires.io/github/job/rpki-ov-checker/requirements.svg?branch=master)](https://requires.io/github/job/rpki-ov-checker/requirements/?branch=master)

RPKI Origin Validation Checker
==============================

*Rpki-ov-checker* is a small tool to show what prefixes with what AS Origins
are impacted by the [RFC 6811](https://tools.ietf.org/html/rfc6811) Origin
Validation procedure.

The purpose is to quickly identify the operational impact of the various RPKI
validation states.

Installation
------------

`pip3 install git+https://github.com/job/rpki-ov-checker`

Example use case
----------------

Here we extract routes from an IOS XR device and process them to figure out
which customers we should contact to help them repair their RPKI ROAs or BGP
announcements.

```
# obtain a list of all customer prefixes
$ ssh r02.amstnl02.nl.bb.gin.ntt.net 'show bgp ipv4 uni community 2914:370 | include /' \
    | grep -v /32 | grep -v \( > customers-v4
$ dos2unix customers-v4

# obtain whole BGP RIB
$ ssh r02.amstnl02.nl.bb 'show bgp ipv4 uni | include /' \
    | grep -v /32 | grep -v \( > rib-v4
$ dos2unix rib-v4

# cook the output a bit, screen scraping sucks... I weep gently
$ sed 's/^...//' customers-v4 \
    | awk '{ print $1 }' \
    | egrep "^[0-9]" > customer_prefixes
$ sed 's/^...//;s/ .$//;s/{.*//' rib-v4 \
    | awk '{ print $1 " " $NF }' \
    | egrep "^[0-9]" > full_rib 

# run the checker and filter out customers
$ rpki-ov-checker full_rib | fgrep -f customer_prefixes | grep invalid | sort -R | head
invalid_covered_by_notfound 123.101.0.0/21 4809 covering route: 123.101.0.0/16 4134
invalid_covered_by_valid 46.3.74.0/24 134121 covering route: 46.3.0.0/16 207636
invalid_unreachable 83.231.209.0/24 3949
invalid_unreachable 124.30.247.0/24 9583
invalid_covered_by_valid 125.21.232.0/24 9730 covering route: 125.21.0.0/16 9498
invalid_unreachable 120.29.92.0/24 17639
invalid_unreachable 31.40.164.0/24 200872
invalid_covered_by_notfound 45.12.139.0/24 40676 covering route: 45.12.136.0/22 35913
invalid_covered_by_valid 122.160.178.0/24 24560 covering route: 122.160.0.0/16 24560
invalid_covered_by_valid 61.90.251.0/24 21734 covering route: 61.90.192.0/18 7470

```

`invalid_unreachable` the RIB entry is invalid, and no alternative _valid_ or
_notfound_ route exists to that set of destination IP addresses. These entries
are the problematic ones.

`invalid_covered_by_valid` the RIB entry is invalid, but covered by a _valid_
route. The IP addresses covered by the route will remain reachable.

`invalid_covered_by_notfound` the RIB entry is invalid, but covered by a
less specific route which is _notfound_.

Copyright
---------

Copyright (c) 2020 Job Snijders <job@ntt.net>
