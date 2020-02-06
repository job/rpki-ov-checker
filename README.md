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

Use
---

`$ rpki-ov-checker <file>`

or, with a local VRP JSON file

`$ cat <file> | rpki-ov-checker -c export.json`

Example output
--------------

`invalid_unreachable` the RIB entry is invalid, and no alternative _valid_ or
_not-found_ route exists to that set of destination IP addresses.

`invalid_covered_by_valid` the RIB entry is invalid, but covered by a _valid_ route

`invalid_covered_by_not-found` the RIB entry is invalid, but covered by a less specific route which is _not-found_

```
$ cd testdata
$ rpki-ov-checker -c rpki-export.json router_output_bgp_rib | sort -R | head
invalid_covered_by_valid 202.158.104.0/22 4787 covering route: 202.158.0.0/17 4787
invalid_unreachable 92.118.115.0/24 43260
not-found 135.0.192.0/20 54614
not-found 184.7.224.0/20 2379
not-found 185.140.193.0/24 203257
not-found 199.27.86.0/24 22071
not-found 2402:3a80:1406::/47 38266
not-found 37.98.234.0/24 16839
not-found 74.44.252.0/24 3593
valid 201.200.155.0/24 11830
```

Copyright
---------

Copyright (c) 2020 Job Snijders <job@ntt.net>
