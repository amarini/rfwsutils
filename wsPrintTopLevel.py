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


from optparse import OptionParser
parser = OptionParser("""

  usage: %prog [options] input_file 

  prints the top level objects in the workspace, i.e. those which have no clients
"""
)

wsutils.addCommonOptions(parser,
                         addSetVars = True
                         )

parser.add_option("-v",
                  dest="verbose",
                  default = False,
                  action="store_true",
                  help="call Print with the verbose option",
                  )

parser.add_option("--brief",
                  dest="brief",
                  default = False,
                  action="store_true",
                  help="only print the name of the items rather than the name and the description",
                  )

(options, ARGV) = parser.parse_args()

#----------------------------------------
# check the command line options
#----------------------------------------
wsutils.checkCommonOptions(options)

if len(ARGV) != 1:
    print >> sys.stderr,"expected exactly one positional argument"
    sys.exit(1)

if options.verbose and options.brief:
    print >> sys.stderr,"-v and --brief can't be specified together"
    sys.exit(1)

#----------------------------------------


# avoid ROOT trying to use the command line arguments
# (which causes a segmentation fault if one e.g. a regex contains a $ etc.)
sys.argv[1:] = []

import ROOT

# avoid unnecessary X11 connections
ROOT.gROOT.SetBatch(True)

wsutils.loadLibraries(options)

fname = ARGV.pop(0)
fin = ROOT.TFile.Open(fname)
if not fin.IsOpen():
    print >> sys.stderr,"problems opening file " + fname
    sys.exit(1)

# insist that there is a single workspace in this file
workspace = wsutils.findSingleWorkspace(fin, options)

wsutils.applySetVars(workspace, options.setVars)

allItemNames = None

allObjs = wsutils.getAllMembers(workspace)

for obj in allObjs:
    if not hasattr(obj, 'hasClients'):
        # RooDataSets for example don't have this function
        continue

    if obj.hasClients():
        # this is not a top level object
        continue

    if options.brief:
        print obj.GetName()
    elif options.verbose:
        obj.Print("V")
    else:
        obj.Print()

    # sys.stdout.flush()
    #     obj.Print()
            

    
