import json
import sys
import re
import csv
from math import acos, sin, cos, pi

iata_city_to_lat_lon = {}

with open('airports.dat') as fp:
    airports = csv.reader(fp)
    for info in airports:
        iata_city = info[4]
        lat = float(info[6])
        lon = float(info[7])
        iata_city_to_lat_lon[iata_city] = (lat, lon)
    # special case LHR because we really want LCY
    iata_city_to_lat_lon["LHR"] = iata_city_to_lat_lon["LCY"]

instances = []
with open('instances.txt') as fp:
    for line in fp:
        instances.append(line.strip())

def node_name_to_iata_city(node_name):
    # this is the CloudFlare format - so simple!
    if len(node_name) == 3:
        return node_name.upper()

    # this is the CIRA ANY.CA-SERVERS.CA mapping of HOSTNAME.BIND
    m = re.search(r'^ns\d\d.([a-z]{3}).ca-servers.ca$', node_name, re.I)
    if m:
        city = m.group(1).upper()
        # special case MTL because the Canadians really mean YUL
        if city == "MTL":
            city = "YUL"
        return city
    return None

def great_circle_dist(lat1, lon1, lat2, lon2):
    # convert to radians because math
    lon1 = lon1 * pi / 180
    lat1 = lat1 * pi / 180
    lon2 = lon2 * pi / 180
    lat2 = lat2 * pi / 180

    # maths!
    theta = lon2 - lon1
    dist = acos(sin(lat1) * sin(lat2) + cos(lat1) * cos(lat2) * cos(theta))
    if (dist < 0):
        dist = dist + pi
    dist = dist * 6371.2

    return dist

all_fixed_json = []
result_total = 0
result_good = 0
for measurement in json.load(sys.stdin):
    result_total += 1
    fixed_json = measurement.copy()

    try:
        node_name = fixed_json["result"]["answers"][0]["RDATA"]
    except KeyError:
        if not 'error' in fixed_json:
            print("No result", file=sys.stderr)
            print(fixed_json, file=sys.stderr)
        continue

    result_good += 1

    iata_city = node_name_to_iata_city(node_name)
    if iata_city not in iata_city_to_lat_lon:
        print(iata_city)
        print('Missing latitude/longitude for "{}"'.format(node_name),
              file=sys.stderr)
        sys.exit(1)
    fixed_json["dst_city"] = iata_city
    lat1, lon1 = iata_city_to_lat_lon[iata_city]

    lat2 = fixed_json["latitude"]
    lon2 = fixed_json["longitude"]
    del fixed_json["latitude"]
    del fixed_json["longitude"]

    fixed_json["dst_lat"] = lat1
    fixed_json["dst_lon"] = lon1
    fixed_json["src_lat"] = lat2
    fixed_json["src_lon"] = lon2

    # this is the distance used
    actual_dist = great_circle_dist(lat1, lon1, lat2, lon2)
    fixed_json["dist"] = actual_dist

    # also figure out all possible distances
    best_dist = actual_dist
    for instance in instances:
        lat1, lon1 = iata_city_to_lat_lon[instance]
        dist = great_circle_dist(lat1, lon1, lat2, lon2)
        fixed_json["dist_" + instance] = dist
        best_dist = min(best_dist, dist)

    # best distance
    fixed_json["dist_theoretical"] = best_dist
    fixed_json["dist_theoretical_improvement"] = actual_dist - best_dist

    all_fixed_json.append(json.dumps(fixed_json, indent=2, sort_keys=True))

print("[")
print(",\n".join(all_fixed_json))
print("]")

print("Total results: {}".format(result_total), file=sys.stderr)
print("Good results:  {}".format(result_good), file=sys.stderr)
