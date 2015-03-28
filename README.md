A few tools to help us graph anycast results.

* add-probe-info.py
  This tool takes the JSON results of a RIPE Measurement and puts
  certain information about the probe that took the measurement into
  the measurement.

  We add `asn_v4`, `asn_v6`, `latitude`, `longitude`, and
  `country_code`.

  Usage:
  
      $ python3 add-probe-info < measurement.json

  Requires a file named `meta-probes.txt` which has a list of all
  probe information in JSON format.
