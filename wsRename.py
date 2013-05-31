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


import sys, os

#----------------------------------------------------------------------

def findWorkspace(rootFile):
    """ searches for a toplevel RooWorkspace instance in the given TFile """

    import ROOT

    retval = None

    for key in rootFile.GetListOfKeys():
        name = key.GetName()

        obj = rootFile.Get(name)

        if isinstance(obj,ROOT.RooWorkspace):
            if retval == None:
                retval = obj
            else:
                print >> sys.stderr,"more than one instance of RooWorkspace found in file",rootFile
                sys.exit(1)

    if retval == None:
        print >> sys.stderr,"no RooWorkspace found in file",rootFile
        sys.exit(1)

    return retval    


#----------------------------------------------------------------------
# main
#----------------------------------------------------------------------

from optparse import OptionParser

parser = OptionParser(   """
   usage: %prog [options] input_workspace.root output_workspace.root old_pattern new_pattern [ old_pattern2 new_pattern2 ...]

   Tool for mass renaming objects in a RooWorkspace.

   WARNING: the program will overwrite the output workspace file without asking for confirmation.

   example:

   %prog --lib $CMSSW_BASE/lib/$SCRAM_ARCH/libHiggsAnalysisCombinedLimit.so input.root output.root \\
      '(.*)_v2$' '\\1'

   will rename e.g. XYZ_v2 to XYZ      

""")


parser.add_option("--lib",
                  dest="libs",
                  default = [],
                  type="str",
                  action="append", # append to list
                  help="library to load before opening the files. Can be specified multiple times.",
                  metavar="LIB")

(options, ARGV) = parser.parse_args()


if len(ARGV) < 4:
    print >> sys.stderr,"must specify at least four positional arguments. Run with -h to get more information"
    sys.exit(1)

inputFname = ARGV.pop(0)
outputFname = ARGV.pop(0)

if len(ARGV) % 2 != 0:
    print >> sys.stderr,"must specify an even number of arguments after the input and output files"
    sys.exit(1)

renameArgs = zip(ARGV[::2],ARGV[1::2])

for lib in options.libs:
    if not os.path.exists(lib):
        print >> sys.stderr,"library " + lib + " does not exist"
        sys.exit(1)


#----------------------------------------

import ROOT; gcs = []
for lib in options.libs:
    ROOT.gSystem.Load(lib)

fin = ROOT.TFile.Open(inputFname)

if fin == None or not fin.IsOpen():
    print >> sys.stderr,"error opening input file " + inputFname
    sys.exit(1)


ws = findWorkspace(fin)

components = ws.components()
it = components.iterator()

allMembers = []

while True:

    obj = it.Next()
    if obj == None:
        break

    allMembers.append(obj)

#----------
# check that we do not produce any collisions
# with the names: no new name must have been
# an old name and no two new names must
# be the same

import re

oldNames = [ x.GetName() for x in allMembers ]
newNames = [ ]

numRenames = 0

for name in oldNames:

    # only apply the rules until the first
    # pattern matches

    newName = None

    for src, dest in renameArgs:

        newName, numSubs = re.subn(src, dest, name)

        if numSubs > 0:
            # the pattern matched, don't continue to apply rules
            break
        else:
            # no match
            newName = None

    if newName != None:

        numRenames += 1

        # we must rename this object
        # check whether the new name does not appear in the
        # list of original names
        if newName in oldNames:
            print >> sys.stderr,"conflict: %s -> %s where %s exists already in the list of original names" % (
                name, newName, newName)
            sys.exit(1)

        if newName in newNames:
            print >> sys.stderr,"conflict: %s -> %s where %s exists already in the list of new names" % (
                name, newName, newName)
            sys.exit(1)
        
    newNames.append(newName)

# now we can do the renaming
assert len(oldNames) == len(newNames)
assert len(oldNames) == len(allMembers)

for oldName, newName, member in zip(oldNames, newNames, allMembers):
    if newName == None:
        continue

    print >> sys.stderr,"renaming %s -> %s" % (oldName, newName)
    member.SetName(newName)

    

if numRenames == 0:
    print >> sys.stderr,"WARNING: no object renamed"
else:
    print >> sys.stderr,"%d objects renamed" % numRenames

print >> sys.stderr,"writing output file",outputFname
ws.writeToFile(outputFname)