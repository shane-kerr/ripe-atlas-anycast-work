import json
import sys

probe_id_to_json = {}
#with open('meta-20150223.txt') as fp:
with open('meta-probes.txt') as fp:
    for line in fp:
        line = line.strip()
        if line:
            probe_json = json.loads(line)
            probe_id_to_json[probe_json["id"]] = probe_json

cnt_total = 0
cnt_good = 0
all_fixed_json = []
missing_probes = set()
for measurement in json.load(sys.stdin):
    cnt_total += 1
    fixed_json = measurement.copy()
    prb_id = measurement["prb_id"]
    if prb_id not in probe_id_to_json:
        missing_probes.add(prb_id)
        continue
    probe_json = probe_id_to_json[prb_id]
    for field in [ "asn_v4", "asn_v6", "latitude", "longitude",
                   "country_code", ]:
        fixed_json[field] = probe_json[field]
    all_fixed_json.append(json.dumps(fixed_json, indent=2, sort_keys=True))
    cnt_good += 1

print("[")
print(",\n".join(all_fixed_json))
print("]")

print("Total measurements: {}".format(cnt_total), file=sys.stderr)
print("Good measurements:  {} ({:5.2f}%)".format(cnt_good, 
                                                 100*cnt_good / cnt_total), 
      file=sys.stderr)

print("Missing probes:", file=sys.stderr)
for missing_probe in sorted(list(missing_probes)):
   print(missing_probe, file=sys.stderr)
