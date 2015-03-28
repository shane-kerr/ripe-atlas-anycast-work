A few tools to help us graph anycast results.

* add-probe-info.py
  This tool takes the JSON results of a RIPE Measurement and puts
  certain information about the probe that took the measurement into
  the measurement.

  We add `asn_v4`, `asn_v6`, `latitude`, `longitude`, and
  `country_code`.

  Usage:
  
      $ python3 add-probe-info < measurement.json > meas-with-probe.json

  Requires a file named `meta-probes.txt` which has a list of all
  probe information in JSON format.

* add-dist.py
  This tool takes the results of the above tool, and figures out the
  physical distance from the source probe to the destination DNS
  server, and adds that information to the JSON output.

  Usage:

      $ python3 add-dist.py < meas-with-probe.json > meas-with-dist.json

  Requires the file named `airports.dat` which you can get from:

  https://sourceforge.net/p/openflights/code/HEAD/tree/openflights/data/airports.dat?format=raw
