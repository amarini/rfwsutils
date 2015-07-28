#!/usr/bin/env python

# rfwsutils - utilities for manipulating RooFit workspaces from the command line
#
# Copyright 2013-2015 University of California, San Diego
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

def printSnapshotStandard(snapshot):

    # snapshot is a RooArgSet
    # convert this to a python list
    params = wsutils.rooArgSetToList(snapshot)

    # sort them in alphabetical order (case-insensitive)
    params.sort(key = lambda arg: arg.GetName().lower())
    
    # print them
    for param in params:
        param.Print()

#----------------------------------------------------------------------

def printVarsCSV(ws):
    # vars is a RooArgSet
    vars = ws.allVars()

    it = vars.iterator()

    print ",".join([
        "name",
        "value",
        "min",
        "max",
        "constant"])

    while True:
        var = it.Next()
        if var == None:
            break

        parts = [
            var.GetName(),
            var.getVal(),
            var.getMin(),
            var.getMax(),
            var.isConstant(),
            ]
        
        print ",".join([ str(p) for p in parts ])




#----------------------------------------------------------------------
# main
#----------------------------------------------------------------------

from optparse import OptionParser
parser = OptionParser("""

  usage: %prog [options] input_file snapshot_name

  prints the values of the parameters in a RooFit workspace snapshot
"""
)

parser.add_option("--csv",
                  default = False,
                  action="store_true",
                  help="print information about variables in .csv format",
                  )

parser.add_option("--only-non-const",
                  dest = "onlyNonConst",
                  default = False,
                  action="store_true",
                  help="only consider variables which are not set to constant",
                  )

parser.add_option("--pattern",
                  default = None,
                  help="only consider variables which match the given pattern (using fnmatch)",
                  )


wsutils.addCommonOptions(parser)

(options, ARGV) = parser.parse_args()

#----------------------------------------
# check the command line options
#----------------------------------------
wsutils.checkCommonOptions(options)

if len(ARGV) != 2:
    parser.print_help()
    sys.exit(1)


fname, snapshotName = ARGV

filters = []

if options.onlyNonConst:
    filters.append(lambda var: not var.isConstant())

if options.pattern != None:
    import fnmatch
    filters.append(lambda var: fnmatch.fnmatch(var.GetName(), options.pattern))

#----------------------------------------


import ROOT

# avoid unnecessary X11 connections
ROOT.gROOT.SetBatch(True)

wsutils.loadLibraries(options)

fin = ROOT.TFile.Open(fname)
if not fin.IsOpen():
    print >> sys.stderr,"problems opening file " + fname
    sys.exit(1)

# insist that there is a single workspace in this file
workspace = wsutils.findSingleWorkspace(fin, options)


snapshot = workspace.getSnapshot(snapshotName)
if snapshot == None:
    print >> sys.stderr,"could not find snapshot %s in file %s" % (snapshotName, fname)
    sys.exit(1)


sortKeyFunc = lambda var: var.GetName().lower()

#----------
# combine the filters
#----------
if filters:
    # only accept variables which pass all filters
    filterFunc = lambda var: all([ filterFunc(var) for filterFunc in filters ])
else:
    filterFunc = None

#----------

if options.csv:
    wsutils.printVarsCSV(snapshot, sortKeyFunc = sortKeyFunc, filterFunc = filterFunc)
else:
    wsutils.printVars(snapshot, sortKeyFunc = sortKeyFunc, filterFunc = filterFunc)

    
