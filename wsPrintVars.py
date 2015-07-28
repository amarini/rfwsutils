#!/usr/bin/env python

# rfwsutils - utilities for manipulating RooFit workspaces from the command line
#
# Copyright 2013,2014 University of California, San Diego
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

#----------------------------------------------------------------------
# main
#----------------------------------------------------------------------

from optparse import OptionParser
parser = OptionParser("""

  usage: %prog [options] input_file [ input_file ... ]

  finds RooFit workspaces in ROOT files and print the variables found in them
"""
)

parser.add_option("--csv",
                  default = False,
                  action="store_true",
                  help="print information about variables in .csv format",
                  )

wsutils.addCommonOptions(parser)

(options, ARGV) = parser.parse_args()

#----------------------------------------
# check the command line options
#----------------------------------------
wsutils.checkCommonOptions(options)

if len(ARGV) < 1:
    print >> sys.stderr,"no input file specified"
    sys.exit(1)

#----------------------------------------


import ROOT

# avoid unnecessary X11 connections
ROOT.gROOT.SetBatch(True)

wsutils.loadLibraries(options)

for fname in ARGV:

    fin = ROOT.TFile.Open(fname)

    if not fin.IsOpen():
        print >> sys.stderr,"problems opening file " + fname
        sys.exit(1)

    # traverse all directories in this file
    for ws in wsutils.findWorkspaces(fin, options):
        if options.csv:
            wsutils.printVarsCSV(ws.allVars())
        else:
            print "variables in " + fname + ":" + ws.GetName() + ":"
            print "----------------------------------------"
            sys.stdout.flush()

            wsutils.printVars(ws.allVars())

    ROOT.gROOT.cd()
    fin.Close()

    
