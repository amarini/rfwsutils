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

  usage: %prog [options] file member rangespec

  sets the range of the given parameter in the workspace found in file

  Works for floating point values only

  To set the upper and lower bound, use a rangespec of the form:

    min,max

  To set the lower bound only, use a rangespec like:

    min,

  To set the upper bound only, use a rangespec like:

    ,max

  Note that when specifying a negative value, this might
  be interpreted as a command line option. In this case,
  add a -- argument before the range specification:

  %proc file.root var -- -10,
  
"""
)

wsutils.addCommonOptions(parser)

(options, ARGV) = parser.parse_args()

#----------------------------------------
# check the command line options
#----------------------------------------
wsutils.checkCommonOptions(options)

if len(ARGV) != 3:
    print >> sys.stderr,"expected exactly three positional arguments"
    sys.exit(1)

#----------------------------------------


import ROOT

# avoid unnecessary X11 connections
ROOT.gROOT.SetBatch(True)

wsutils.loadLibraries(options)

fname = ARGV.pop(0)
itemName = ARGV.pop(0)
rangeSpec = ARGV.pop(0)

minSpec, maxSpec = rangeSpec.split(',',1)

if minSpec != "":
    minSpec = float(minSpec)
else:
    minSpec = None

if maxSpec != "":
    maxSpec = float(maxSpec)
else:
    maxSpec = None


if minSpec == None and maxSpec == None:
    print >> sys.stderr,"neither upper nor lower bound specified, exiting"
    sys.exit(1)
#--------------------

fin = ROOT.TFile.Open(fname,"UPDATE")
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



obj = workspace.obj(itemName)

if obj == None:
    print >> sys.stderr,"could not find item %s in workspace %s in file %s" % (itemName, workspace.GetName(), fname)
    sys.exit(1)


if minSpec != None and maxSpec != None:
    # set the range in one go
    obj.setRange(minSpec, maxSpec)
elif minSpec == None:
    obj.setMax(maxSpec)
elif maxSpec == None:
    obj.setMin(minSpec)
else:
    raise Exception("internal error")

#----------------------------------------
# write the workspace back
fin.cd()
# workspace.Write()
fin.WriteTObject(workspace,workspace.GetName(), 'WriteDelete')
fin.Close()

    
