# PeakTech4390

Simple command line tool to log data from PeakTech 4390 multimeter.
The output is in CSV format containing a timestamp, the measured value and the physical units.

## Examples

simple use (stdout only):

```bash
>./peaktech_4390.py
0.1056, s, 24.1, degC
0.6216, s, 24.1, degC
1.1374, s, 24.1, degC
1.6533, s, 24.1, degC
...
```

using a different device and log to file:

```bash
>./peaktech_4390.py --device=/dev/ttyUSB2 | tee log.csv
0.1056, s, 24.1, degC
0.6216, s, 24.1, degC
1.1374, s, 24.1, degC
1.6533, s, 24.1, degC
...
```
