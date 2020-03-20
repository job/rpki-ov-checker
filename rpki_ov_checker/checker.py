#!/usr/bin/env python3
# RPKI Origin Validation checker
#
# Copyright (C) 2020 Job Snijders <job@ntt.net>
#
# Permission to use, copy, modify, and distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

from collections import OrderedDict
from ipaddress import ip_network
from pprint import pformat
from operator import itemgetter
from .ov import validation_state

import argparse
import json
import os
import radix
import requests
import rpki_ov_checker
import sys


def sort_prefixes(p_list):
    l = []
    for p in p_list:
        l.append(tuple(p.split('/')))
    l.sort(key=itemgetter(1))
    return ['/'.join(t) for t in l]


def subnet_in_subnet(p1, p2):
    p1 = ip_network(p1)
    p2 = ip_network(p2)
    return p1.network_address >= p2.network_address and \
        p1.broadcast_address <= p2.broadcast_address

def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('-c', dest='cache',
                        default="https://rpki.gin.ntt.net/api/export.json",
                        type=str,
                        help="""Location of the RPKI Cache in JSON format
(default: https://rpki.gin.ntt.net/api/export.json)""")

    parser.add_argument('-j', '--json', action='store_true', default=False,
                        dest='json', help="Display output in JSON format")

    parser.add_argument('-v', '--version', action='version',
                        version='%(prog)s ' + rpki_ov_checker.__version__)

    parser.add_argument('rib_dump', metavar='file', nargs='?', type=str,
                        default=False,
                        help='Path to a file containing prefixes and orgins')

    args = parser.parse_args()

    if 'http' in args.cache:
        print("Downloading %s" % args.cache, file=sys.stderr)
        r = requests.get(args.cache, headers={'Accept': 'text/json'})
        validator_export = r.json()
    else:
        validator_export = json.load(open(args.cache, "r"))

    if not args.rib_dump:
        bgp_rib = [x.strip() for x in sys.stdin.readlines()]
    else:
        with open(args.rib_dump) as f:
            bgp_rib = [x.strip() for x in f.readlines()]

    if args.json:
        json_blob = {}

    vrps = create_vrp_index(validator_export)

    rib = radix.Radix()

    for line in bgp_rib:
        try:
            prefix, origin = line.split()
        except ValueError:
            print("Error parsing this input line:")
            print(line)
            print("The expected format is a prefix and an origin ASN per line, whitespace separated.")
            sys.exit(1)

        origin = int(origin)
        rnode = rib.search_exact(prefix)
        if not rnode:
            rnode = rib.add(prefix)
            rnode.data[origin] = validation_state(vrps, prefix, origin)
        elif origin in rnode.data.keys(): # dont duplicate work
            continue
        else:
            rnode.data[origin] = validation_state(vrps, prefix, origin)

    for rnode in rib.nodes():
        for origin in rnode.data:
            if rnode.data[origin]['state'] in ['notfound', 'valid']:
                pass

            # figure out what kind of invalid this is
            elif rnode == rib.search_worst(rnode.prefix):
                rnode.data[origin]['state'] = 'invalid_unreachable'
            else:
                supernet = rib.search_worst(rnode.prefix)
                related = rib.search_covered(supernet.prefix)
                for r in sort_prefixes([x.prefix for x in related]):
                    if not subnet_in_subnet(rnode.prefix, r):
                        continue
                    covering_prefix = rib.search_exact(r)
                    for c_origin in covering_prefix.data:
                        if covering_prefix.data[c_origin]['state'] == 'valid':
                            rnode.data[origin]['state'] = 'invalid_covered_by_valid'
                            rnode.data[origin]['covered'] = (covering_prefix.prefix, c_origin)
                        elif covering_prefix.data[c_origin]['state'] == 'notfound':
                            rnode.data[origin]['state'] = 'invalid_covered_by_notfound'
                            rnode.data[origin]['covered'] = (covering_prefix.prefix, c_origin)
                        elif covering_prefix.data[c_origin]['state'] == 'invalid':
                            rnode.data[origin]['state'] = 'invalid_unreachable'

            if args.json:
                if not rnode.prefix in json_blob.keys():
                    json_blob[rnode.prefix] = {origin: rnode.data[origin]}
                else:
                    json_blob[rnode.prefix][origin] = rnode.data[origin]
            else:
                print("{} {} {}".format(rnode.data[origin]['state'],
                                        rnode.prefix, origin), end='')

                if rnode.data[origin]['state'].startswith('invalid_covered_by_'):
                    print(" covering route: %s %s"
                          % rnode.data[origin]['covered'])
                else:
                    print("")
    if args.json:
        print(json.dumps(json_blob))

def create_vrp_index(export):
    #
    # :param export:  the JSON blob with all ROAs

    roa_list = []
    tree = radix.Radix()

    # each roa tuple has these fields:
    # asn, prefix, maxLength, ta

    for roa in export['roas']:
        prefix_obj = ip_network(roa['prefix'])

        try:
            asn = int(roa['asn'].replace("AS", ""))
            if not 0 <= asn < 4294967296:
                raise ValueError
        except ValueError:
            print("ERROR: ASN malformed", file=sys.stderr)
            print(pformat(roa, indent=4), file=sys.stderr)
            continue

        prefix = str(prefix_obj)
        prefixlen = prefix_obj.prefixlen
        maxlength = int(roa['maxLength'])
        ta = roa['ta']

        roa_list.append((prefix, prefixlen, maxlength, asn, ta))

    for roa in set(roa_list):
        rnode = tree.search_exact(roa[0])
        if not rnode:
            rnode = tree.add(roa[0])
            rnode.data["roas"] = [{'maxlen': roa[2], 'origin': roa[3],
                                    'ta': roa[4]}]
        else:
            rnode.data["roas"].append({'maxlen': roa[2], 'origin': roa[3],
                                        'ta': roa[4]})

    return tree


if __name__ == "__main__":
    main()
