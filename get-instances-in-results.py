import json
import sys
import re

def node_name_to_iata_city(node_name):
    # this is the CIRA ANY.CA-SERVERS.CA mapping of HOSTNAME.BIND
    m = re.search(r'^ns\d\d.([a-z]{3}).ca-servers.ca$', node_name, re.I)
    if m:
        city = m.group(1).upper()
        # special case MTL because the Canadians really mean YUL
        if city == "MTL":
            city = "YUL"
        return city
    return None

instances = set()
for measurement in json.load(sys.stdin):
    try:
        node_name = measurement["result"]["answers"][0]["RDATA"]
    except KeyError:
        if not 'error' in measurement:
            print("No result", file=sys.stderr)
            print(measurement, file=sys.stderr)
        continue

    iata_city = node_name_to_iata_city(node_name)
    instances.add(iata_city)

for instance in sorted(list(instances)):
    print(instance)
