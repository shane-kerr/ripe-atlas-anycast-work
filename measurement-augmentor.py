import csv
import glob
import json
from math import acos, sin, cos, pi
import os
import re
import sys
import time

import dateutil.parser

# Requires: probe information ("meta-probes.json")
# Requires: dateutil library (python3-dateutil in Debian & derivatives)
# Requires: curl
# Requires: IATA ("airports.dat")
# Requires: UN/LOCODE csv data ("2014-2 UNLOCODE CodeListPart[123].csv")

##
## Command-line parsing (hand parsing because I'm scared of argument libraries)
##
def syntax(argv):
    print("Syntax: {} measurement_id [date_start [date_end]]".format(argv[0]),
          file=sys.stderr)
    print("    measurement_id  - RIPE Atlas measurement ID",
          file=sys.stderr)
    print("    date_start      - date/time to start output at",
          file=sys.stderr)
    print("    date_end        - date/time to stop output at",
          file=sys.stderr)
    sys.exit(1)

if not (1 < len(sys.argv) <5):
    syntax(sys.argv)
    
measurement_id = int(sys.argv[1])

date_start_sec = None
date_end_sec = None
if len(sys.argv) > 2:
    date_start = dateutil.parser.parse(sys.argv[2])
    date_start_sec = int(date_start.timestamp())
    date_start_iso = time.strftime("%Y%m%dT%H%M%S", time.gmtime(date_start_sec))
if len(sys.argv) > 3:
    date_end = dateutil.parser.parse(sys.argv[3])
    date_end_sec = int(date_end.timestamp())
    date_end_iso = time.strftime("%Y%m%dT%H%M%S", time.gmtime(date_end_sec))

##
## Read in our probe information
##
probe_id_to_json = {}
with open('meta-probes.json') as fp:
    for line in fp:
        line = line.strip()
        if line:
            probe_json = json.loads(line)
            probe_id_to_json[probe_json["id"]] = probe_json

##
## Read in IATA locations
##
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

## 
## Read in UN/LOCODE locations
##
un_locode_to_lat_lon = {}
for fname in glob.glob('*UNLOCODE*.csv'):
    with open(fname, encoding='latin_1') as fp:
        un_locodes = csv.reader(fp)
        for info in un_locodes:
            country = info[1]
            location = info[2]
            if info[10]:
                lat_str = info[10][0:5]
                lat = float(lat_str[:-1]) / 100.0
                if lat_str[-1] == 'S':
                    lat = -lat
                lon_str = info[10][6:]
                lon = float(lon_str[:-1]) / 100.0
                if lon_str[-1] == 'W':
                    lon = -lon
            else:
                lat = lon = None
            un_locode_to_lat_lon[country+location] = (lat, lon)
    # add a few sites since they're not properly listed
    un_locode_to_lat_lon["CATOR"] = iata_city_to_lat_lon["YYZ"]
    un_locode_to_lat_lon["GBLON"] = iata_city_to_lat_lon["LCY"]
    un_locode_to_lat_lon["HKHKG"] = iata_city_to_lat_lon["HKG"]
    un_locode_to_lat_lon["NLAMS"] = iata_city_to_lat_lon["AMS"]
    un_locode_to_lat_lon["USIAD"] = iata_city_to_lat_lon["IAD"]
    un_locode_to_lat_lon["USLAX"] = iata_city_to_lat_lon["LAX"]
    un_locode_to_lat_lon["USMIA"] = iata_city_to_lat_lon["MIA"]
    un_locode_to_lat_lon["USNBN"] = iata_city_to_lat_lon["LGA"]
    un_locode_to_lat_lon["USSNN"] = iata_city_to_lat_lon["SJC"]


##
## mapping from HOSTNAME.BIND string to identifier, latitude, and longitude
##
def node_name_to_city_lat_lon(node_name):
    city = None

    # this is the CloudFlare format - so simple! :)
    if len(node_name) == 3:
        city = node_name.upper()
        lat, lon = iata_city_to_lat_lon[city]

    # this is the CIRA ANY.CA-SERVERS.CA mapping of HOSTNAME.BIND
    m = re.search(r'^ns\d\d.([a-z]{3}).(ca-servers|d-zone).ca$',
                  node_name, re.I)
    if m:
        city = m.group(1).upper()
        # special case MTL because the Canadians really mean YUL
        if city == "MTL":
            city = "YUL"
        lat, lon = iata_city_to_lat_lon[city]

    # this is the Dyn Hivecast mapping of HOSTNAME.BIND
    m = re.search(r'^hivecast-\d+-([a-z]{2})([a-z]{3}).as15135.net \S+$',
                  node_name)
    if m:
        country = m.group(1).upper()
        loc = m.group(2).upper()
        city = country+loc
        lat, lon = un_locode_to_lat_lon[city]

    if city:
        assert lat, "Missing latitude for {}".format(city)
        assert lon, "Missing longitude for {}".format(city)
        return city, lat, lon
    else:
        return None, None, None

## 
## Download the measurement JSON
##
if date_end_sec is not None:
    url = ("https://atlas.ripe.net/api/v1/measurement/{}/result/?"
           "start={}&stop={}&format=json".format(measurement_id,
                                                 date_start_sec, date_end_sec))
    meas_fname = "atlas-meas-{}-{}-{}".format(measurement_id,
                                              date_start_iso, date_end_iso)
elif date_start_sec is not None:
    url = ("https://atlas.ripe.net/api/v1/measurement/{}/result/?"
           "start={}&format=json".format(measurement_id, date_start_sec))
    meas_fname = "atlas-meas-{}-{}".format(measurement_id, date_start_iso)
else:
    url = ("https://atlas.ripe.net/api/v1/measurement/{}/result/?"
           "format=json".format(measurement_id))
    meas_fname = "atlas-meas-{}".format(measurement_id)

try:
    fp = open(meas_fname + ".json")
except FileNotFoundError:
    os.system("curl --output '{}' --url '{}'".format(meas_fname + ".json", url))
    try:
        fp = open(meas_fname + ".json")
    except FileNotFoundError:
        print("Unable to get '{}'".format(url), file=sys.stderr)
        sys.exit(1)



##
## Add probe info into the measurements, also get instance sites
##
cnt_total = 0
cnt_good = 0
measurements = []          # our updated set of measurements
missing_probes = set()     # probes that are missing from our probe dataset
instance_to_lat_lon = {}   # sites with anycast instances
for measurement in json.load(fp):
    cnt_total += 1
    fixed_json = measurement.copy()
    prb_id = measurement["prb_id"]
    if prb_id not in probe_id_to_json:
        missing_probes.add(prb_id)
        continue
    probe_json = probe_id_to_json[prb_id]
    for field in [ "asn_v4", "asn_v6", "country_code", ]:
        fixed_json[field] = probe_json[field]
    fixed_json["src_lat"] = probe_json["latitude"]
    fixed_json["src_lon"] = probe_json["longitude"]
    try:
        instance_name = measurement["result"]["answers"][0]["RDATA"]
        city, lat, lon = node_name_to_city_lat_lon(instance_name)
        if not city:
            print("Unable to convert instance '{}' to city (first)".
                  format(instance_name), file=sys.stderr)
            sys.exit(1)
        instance_to_lat_lon[city] = (lat, lon)
    except KeyError:
        pass
    measurements.append(fixed_json)
    cnt_good += 1

print("Total measurements: {}".format(cnt_total), file=sys.stderr)
print("Good measurements:  {} ({:5.2f}%)".format(cnt_good, 
                                                 100*cnt_good / cnt_total), 
      file=sys.stderr)

if missing_probes:
    print("Missing probes:", file=sys.stderr)
    for missing_probe in sorted(list(missing_probes)):
       print(missing_probe, file=sys.stderr)


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


##
## Add distance information
##
all_fixed_json = []
for measurement in measurements:
    try:
        instance_name = measurement["result"]["answers"][0]["RDATA"]
        city, dst_lat, dst_lon = node_name_to_city_lat_lon(instance_name)
        if not city:
            print("Unable to convert instance '{}' to city (second)".
                  format(instance_name), file=sys.stderr)
            sys.exit(1)
        measurement["dst_lat"] = dst_lat
        measurement["dst_lon"] = dst_lon
        src_lat = measurement["src_lat"]
        src_lon = measurement["src_lon"]
        actual_dist = great_circle_dist(dst_lat, dst_lon, src_lat, src_lon)
        measurement["dist"] = actual_dist

        # also figure out possible distances
        best_dist = actual_dist
        for city, pos in instance_to_lat_lon.items():
            dist = great_circle_dist(pos[0], pos[1], src_lat, src_lon)
            measurement["dist_" + city] = dist
            best_dist = min(best_dist, dist)

        # best distance
        measurement["dist_theoretical"] = best_dist
        measurement["dist_theoretical_improvement"] = actual_dist - best_dist
    
    except KeyError:
        pass
    all_fixed_json.append(json.dumps(measurement, indent=2, sort_keys=True))

with open(meas_fname + "-with-dist.json", "w") as fp:
    print("[", file=fp)
    print(",\n".join(all_fixed_json), file=fp)
    print("]", file=fp)

