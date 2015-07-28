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

  usage: %prog [options] input_file member1 [ member2 ... ]

  prints the given members of the workspace in the input file
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
                  help="only print the name of the item (if it exists) rather than the name and the description. Useful together with wildcards to see which members are in a workspace",
                  )

parser.add_option("--regex",
                  dest="regex",
                  default = False,
                  action="store_true",
                  help="interpret the patterns as regular experssions (rather than using fnmatch)",
                  )



(options, ARGV) = parser.parse_args()

#----------------------------------------
# check the command line options
#----------------------------------------
wsutils.checkCommonOptions(options)

if len(ARGV) < 2:
    print >> sys.stderr,"expected at least two positional arguments"
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

allObjs = []

for itemName in ARGV:


    if options.regex:
        # always interpret this as a regex
        if allItemNames == None:
            # get the names of all items
            allItemNames = [ x.GetName() for x in wsutils.getAllMembers(workspace) ]

        import re

        # use search(..) (not necessarily starting from the beginning) rather
        # than match(..)

        for name in allItemNames:
            mo = re.search(itemName, name)
            if mo:
                # don't care about duplicates for the moment
                obj = workspace.obj(name)
                assert obj != None
                allObjs.append(obj)
                               
        # end of loop over all items in the workspace

    else:

        obj = workspace.obj(itemName)

        if obj != None:
            # found in workspace, add to the list of items to be printed
            allObjs.append(obj)
            continue

        # not found, try a wildcard
        if allItemNames == None:
            # get the names of all items
            allItemNames = [ x.GetName() for x in wsutils.getAllMembers(workspace) ]
            import fnmatch

            matchingNames = fnmatch.filter(allItemNames, itemName)

            if not matchingNames:
                print >> sys.stderr,"could not find item %s (nor does it match as a wildcard) in workspace %s in file %s" % (itemName, workspace.GetName(), fname)
                sys.exit(1)

            allObjs.extend(workspace.obj(name) for name in matchingNames)

    # end of loop over item specifications

# print the objects found

for obj in allObjs:
    if options.brief:
        print obj.GetName()
    elif options.verbose:
        obj.Print("V")
    else:
        obj.Print()

    # sys.stdout.flush()
    #     obj.Print()
            

    
