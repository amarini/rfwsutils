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

  usage: %prog [options] input_file member1 

  dumps a dataset
"""
)

wsutils.addCommonOptions(parser)

# parser.add_option("-v",
#                   dest="verbose",
#                   default = False,
#                   action="store_true",
#                   help="call Print with the verbose option",
#                   )

(options, ARGV) = parser.parse_args()

#----------------------------------------
# check the command line options
#----------------------------------------
wsutils.checkCommonOptions(options)

if len(ARGV) < 2:
    print >> sys.stderr,"expected at least two positional arguments"
    sys.exit(1)

#----------------------------------------


import ROOT

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

dsname = ARGV.pop(0)


ds = workspace.obj(dsname)

if ds == None:
    print >> sys.stderr,"could not find item %s in workspace %s in file %s" % (itemName, workspace.GetName(), fname)
    sys.exit(1)

#--------------------
# dump the dataset
#--------------------

numEvents = ds.numEntries()

for i in range(numEvents):

    # retrieve the values
    values = ds.get(i)

    if i == 0:
        # make sure we always have the same order
        # (or is this already guaranteed ?)
        varnames = []

        it = values.fwdIterator()
        while True:
            obj = it.next()
            if obj == None:
                break
            varnames.append(obj.GetName())

        print ",".join(varnames)

    # not very optimized version doing string comparisons all the time

    thisValues = [ values.getRealValue(varname) for varname in varnames ]

    print ",".join(str(x) for x in thisValues)
