A few tools to help us graph anycast results.

We need some stuff to work:

* Requires a file named `meta-probes.json` which has a list of all
  probe information in JSON format.
* Requires the dateutil library (`apt-get install python3-dateutil` in
  Debian & derivatives).
* Requires the curl utility (`apt-get install curl` in Debian &
  derivatives).
* Requires IATA information (`airports.dat`),  which you can get from:

  https://sourceforge.net/p/openflights/code/HEAD/tree/openflights/data/airports.dat?format=raw
* Requires the UN/LOCODE csv data (`2014-2 UNLOCODE CodeListPart[123].csv`),
  which you can get from:

  http://www.unece.org/cefact/codesfortrade/codes_index.html

To run:

    $ python3 measurement-augmentor.py 
    Syntax: measurement-augmentor.py measurement_id [date_start [date_end]]
    measurement_id  - RIPE Atlas measurement ID
    date_start      - date/time to start output at
    date_end        - date/time to stop output at

    $ python3 measurement-augmentor.py 1911128

