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
# main
#----------------------------------------------------------------------

from optparse import OptionParser
parser = OptionParser("""

  usage: %prog [options] input_file itemname [ itemname ]

  prints the objects which use the given items (i.e. are 'clients'
  of the specified objects)
"""
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

if len(ARGV) < 2:
    print >> sys.stderr,"no items specified"
    sys.exit(1)

fname = ARGV.pop(0)
#----------------------------------------


import ROOT

# avoid unnecessary X11 connections
ROOT.gROOT.SetBatch(True)

wsutils.loadLibraries(options)



fin = ROOT.TFile.Open(fname)

if not fin.IsOpen():
    print >> sys.stderr,"problems opening file " + fname
    sys.exit(1)

workspaces = wsutils.findWorkspaces(fin, options)

if len(workspaces) > 1:
    print >> sys.stderr,"more than one workspace found"
    sys.exit(1)

if len(workspaces) < 1:
    print >> sys.stderr,"no workspace found"
    sys.exit(1)

workspace = workspaces[0]

for itemName in ARGV:

    # find the given items

    obj = workspace.obj(itemName)
    if obj == None:
        print >> sys.stderr,"could not find item %s in workspace %s in file %s" % (itemName, workspace.GetName(), fname)
        sys.exit(1)


    # loop over clients
    iter = obj.clientIterator()
    while True:
        client = iter.Next()
        if client == None:
            break

        client.Print()

ROOT.gROOT.cd()
fin.Close()

    
