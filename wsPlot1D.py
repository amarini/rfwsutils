#!/usr/bin/env python

# rfwsutils - utilities for manipulating RooFit workspaces from the command line
#
# Copyright 2013 University of California, San Diego
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import sys, os, wsutils


from optparse import OptionParser
parser = OptionParser("""

  usage: %prog [options] input_file variable itemToPlot1 [ itemToPlot2 ... ]

  does a 1D plot of the items to plot on the variable
"""
)

wsutils.addCommonOptions(parser)

parser.add_option("--range",
                  dest="rangeSpec",
                  default = None,
                  type="str",
                  help="specify the plotting range",
                  metavar="min,max")

parser.add_option("-o",
                  dest="outputFile",
                  default = None,
                  type="str",
                  help="output file to save the plot to",
                  metavar="FNAME")


(options, ARGV) = parser.parse_args()

#----------------------------------------
# check the command line options
#----------------------------------------
wsutils.checkCommonOptions(options)

if len(ARGV) < 3:
    print >> sys.stderr,"expected at least three positional arguments"
    sys.exit(1)

#----------------------------------------

import ROOT
gcs = []

wsutils.loadLibraries(options)

fname = ARGV.pop(0)
fin = ROOT.TFile.Open(fname)
if not fin.IsOpen():
    print >> sys.stderr,"problems opening file " + fname
    sys.exit(1)

# insist that there is a single workspace in this file
workspaces = wsutils.findWorkspaces(fin, options)

if len(workspaces) > 1:
    print >> sys.stderr,"more than one workspace found"
    sys.exit(1)

if len(workspaces) < 1:
    print >> sys.stderr,"no workspace found"
    sys.exit(1)

workspace = workspaces[0]

varname = ARGV.pop(0)
var = wsutils.getObj(workspace, varname)

if options.rangeSpec != None:
    rangeMin, rangeMax = [ float(x) for x in options.rangeSpec.split(',') ]

    assert rangeMin <= rangeMax

    var.setRange(rangeMin, rangeMax)

frame = var.frame()

for itemName in ARGV:
    item = wsutils.getObj(workspace, itemName)
    gcs.append(item)

    item.plotOn(frame)

# it looks like we have to create a TCanvas by hand ?
gcs.append(ROOT.TCanvas())
frame.Draw()


if options.outputFile:
    ROOT.gPad.SaveAs(options.outputFile)

# if not running interactively and not asked to save to an output
# file, should we enter a waiting loop ? (how do we do this ?)


