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

  usage: %prog [options] file member (True|False)

  calls setConstant on the given item in the workspace found in file

  If no third argument is specified, 'True' is assumed
"""
)

wsutils.addCommonOptions(parser)

(options, ARGV) = parser.parse_args()

#----------------------------------------
# check the command line options
#----------------------------------------
wsutils.checkCommonOptions(options)

if len(ARGV) < 2 or len(ARGV) > 3:
    print >> sys.stderr,"expected 2-3 positional arguments"
    sys.exit(1)

#----------------------------------------


import ROOT

wsutils.loadLibraries(options)


fname = ARGV.pop(0)
itemName = ARGV.pop(0)

if len(ARGV) > 0:
    value = bool(ARGV.pop(0))
else:
    value = True

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

obj.setConstant(value)

# write the workspace back
fin.cd()
# workspace.Write()
fin.WriteTObject(workspace,workspace.GetName(), 'WriteDelete')
fin.Close()

    
