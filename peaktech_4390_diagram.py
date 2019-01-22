#!/usr/bin/env python3

import argparse
import csv
import os.path
import sys

import matplotlib
matplotlib.use('TkAgg')

import matplotlib.pyplot as plt
matplotlib.use('TkAgg') # plt.show() does not work with this on my system (openSuse tumbleweed 20190110)


class DataLog(object):
    """!
        This class holds the content of a data log (datafile)
    """

    def __init__(self):
        self.Name = ""
        self.YUnit = ""
        self.XUnit = "s"
        self.XAxis = []
        self.YAxis = []



    def addData(self, x, y):
        """!
            Safely append a datapoint simultaneously to XAxis and YAxis
        """
        self.XAxis.append(float(x))
        self.YAxis.append(float(y))

    def alignXZero(self, value):
        """!
            Offset the x axsis zero to where the y axis crosses 'value' the first time
        """
        value = float(value)
        t_offset = 0
        previous_y = None

        # determine offset
        for i in range(len(self.XAxis)):
            if previous_y is not None:
                if (previous_y >= value and self.YAxis[i] < value) or (previous_y <= value and self.YAxis[i] > value):
                    t_offset = self.XAxis[i]
                    break
            previous_y = self.YAxis[i]

        # apply offset
        if t_offset == 0.0:
            print("WARNING: Cannot zero-align datafile '%s' because it does not cross the value %f!" % (self.Name, value), file=sys.stderr)
        else:
            for i in range(len(self.XAxis)):
                self.XAxis[i] = self.XAxis[i] - t_offset



class DataLogsContainer(object):
    """!
        This class stores and processes multiple DataLog objects
    """

    def __init__(self):
        self.DataLogs = []
        self.YUnits = []


    def addDataLog(self, dl):
        """!
            Safely append a DataLog object
        """
        if not isinstance(dl, DataLog):
            raise NotImplementedError("Parameter 'dl' must be of DataLog type!")
        self.DataLogs.append(dl)

        # remember all y axis units
        if dl.YUnit not in self.YUnits:
            self.YUnits.append(dl.YUnit)


    def scaleX(self):
        """!
            Automatically convert the x axis from seconds to minutes or hours
        """
        x_unit = "s"
        x_min = None
        x_max = None
        x_scale = 1.0

        # determine minium and maximum x axis values
        for dl in self.DataLogs:

            dl_x_min = min(dl.XAxis)
            if x_min is None or dl_x_min < x_min:
                x_min = dl_x_min

            dl_x_max = max(dl.XAxis)
            if x_max is None or dl_x_max > x_max:
                x_max = dl_x_max

        # calculate scaling
        if (x_max - x_min) > (99 * 60):
            x_unit = "h"
            x_scale = 60 * 60
        if (x_max - x_min) > 99:
            x_unit = "min"
            x_scale = 60

        # apply scaling
        for dl in self.DataLogs:
            for i in range(len(dl.XAxis)):
                dl.XAxis[i] = dl.XAxis[i] / x_scale
            dl.XUnit = x_unit


    def alignXZero(self, value):
        """!
            Align the x axis of all DataLog objects
        """
        for dl in self.DataLogs:
            dl.alignXZero(value)



def main():

    # -------------------------------------------------------------------------
    #                               argparse
    # -------------------------------------------------------------------------

    # program description
    description  = "Diagram generation from PeakTech 4390 multimeter data log.\n "
    description += "Each datafile which is passed as an argument is appended to the plot. "
    description += "When the datafiles use differnet physical units, multiple plots are generated.\n"
    description += "Whith the zero-shift parameter the x axis offset of all datafiles can be arranged."
    description += "To generate a diagram: 'find csv_export_dir/ -name \"*.csv\" | xargs " + __file__ + " -o diagram.svg'"

    # create parser
    parser = argparse.ArgumentParser(description=description)

    # output export
    parser.add_argument('-o', '--output', action="store", type=str,
                        help="If specified the diagram is stored to that file.")

    # rising trigger
    parser.add_argument('-z', '--zero-align', action="store", type=float,
                        help="the x axis zero of each plot is aligned to where this value is crossed for the first time (rising or falling)")

    # xkcd style
    parser.add_argument('--xkcd', action="store_true",
                        help="use xkcd matplotlib style")

    # datafiles
    parser.add_argument('datafiles', nargs='+',
                        help="One or more datafiles that have to be processed")

    # parse
    args = parser.parse_args()



    # -------------------------------------------------------------------------
    #                               Read Data Logs
    # -------------------------------------------------------------------------

    # data plotter
    mDataLogsContainer = DataLogsContainer()

    # read all logs
    for datafile in args.datafiles:
        with open(datafile) as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',')
            mDataLog = DataLog()
            mDataLog.Name = os.path.basename(datafile.strip())
            for row in spamreader:
                if len(row) >= 4:
                    mDataLog.addData(row[0], row[2])
                    mDataLog.YUnit = str(row[3]).strip()
                    mDataLog.XUnit = str(row[1]).strip()
            mDataLogsContainer.addDataLog(mDataLog)



    # -------------------------------------------------------------------------
    #                               Data Processing
    # -------------------------------------------------------------------------

    # automatic x axis scaling
    mDataLogsContainer.scaleX()

    # align x axis zero
    if args.zero_align:
        mDataLogsContainer.alignXZero(args.zero_align)



    # -------------------------------------------------------------------------
    #                                   Plot
    # -------------------------------------------------------------------------

    # apply xkcd style
    if args.xkcd:
        plt.xkcd()

    # create pyplot figure object
    mFigure = plt.figure(tight_layout=True)

    # create subplot for all existing y axis units
    previous_ax = None # remember the previous axis object to share it with the next
    for i in range(len(mDataLogsContainer.YUnits)):

        # create new Axis object for every new y axis unit
        ax = mFigure.add_subplot(len(mDataLogsContainer.YUnits), 1, i+1, sharex=previous_ax)
        previous_ax = ax

        # add all data logs with same unit
        for dl in mDataLogsContainer.DataLogs:
            if dl.YUnit == mDataLogsContainer.YUnits[i]:
                ax.plot(dl.XAxis, dl.YAxis, label=dl.Name)

        # apply style to axis
        ax.set_xlabel(dl.XUnit)
        ax.set_ylabel(mDataLogsContainer.YUnits[i])
        ax.legend()
        ax.grid(axis = 'both')



    # -------------------------------------------------------------------------
    #                                 Output
    # -------------------------------------------------------------------------

    if args.output:
        plt.savefig(args.output)
    else:
        plt.show()



if __name__ == "__main__":
    main()
