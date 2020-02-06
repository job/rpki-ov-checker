#!/usr/bin/env python3
# This file is part of the RPKI OV Checker tool
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

from ipaddress import ip_network


def validation_state(tree, prefix, origin):
    """
    tree is a radix.Radix() object
    prefix is the to-be-tested prefix
    origin is the origin asn to be used in the test
    """

    if not tree.search_best(prefix):
        return {"state": "notfound"}

    p = ip_network(prefix)
    s = tree.search_worst(prefix).prefix
    vrps = tree.search_covered(s)
    passback_roas = []
    for vrp in vrps:
        r = ip_network(vrp.prefix)
        if not (p.network_address >= r.network_address and p.broadcast_address <= r.broadcast_address):
            continue

        for roa in vrp.data["roas"]:
            passback_roas.append({"roa": vrp.prefix, "maxlen": roa['maxlen'],
                                  "origin": roa['origin'],
                                  "ta": roa['ta']})

            if vrp.prefixlen <= p.prefixlen <= roa['maxlen']:
                if origin == roa['origin']:
                    return {"state": "valid", "roa": {"roa": vrp.prefix,
                                                      "maxlen": roa['maxlen'],
                                                      "origin": roa['origin'],
                                                      "ta": roa['ta']}}
    return {"state": "invalid", "roas": passback_roas}
