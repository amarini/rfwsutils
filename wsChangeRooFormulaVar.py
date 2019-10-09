#!/usr/bin/env python

# rfwsutils - utilities for manipulating RooFit workspaces from the command line
#
# Fri Oct  4 11:38:48 CEST 2019
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

parser = OptionParser(   """
   usage: %prog [options] input_workspace.root output_workspace.root old_pattern new_pattern [ old_pattern2 new_pattern2 ...]

   Tool for changing content of RooFormulaVars.

   WARNING: the program will overwrite the output workspace file without asking for confirmation.

   example:

   %prog --lib $CMSSW_BASE/lib/$SCRAM_ARCH/libHiggsAnalysisCombinedLimit.so input.root output.root \\
      '(.*)_v2$' '\\1'

   will rename e.g. XYZ_v2 to XYZ      

""")


wsutils.addCommonOptions(parser)

parser.add_option("-n",
                  dest="dryrun",
                  default = False,
                  action="store_true",
                  help="do NOT run any renaming but just check if renamings would not cause any conflict",
                  )

(options, ARGV) = parser.parse_args()

import ROOT; gcs = []

#----------------------------------------------------------------------

def findWorkspace(rootFile):
    """ searches for a toplevel RooWorkspace instance in the given TFile """

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

def findAllWorkspace(rootFile):
    """ searches for a toplevel RooWorkspace instance in the given TFile """


    retval = []

    for key in rootFile.GetListOfKeys():
        name = key.GetName()

        obj = rootFile.Get(name)

        if isinstance(obj,ROOT.RooWorkspace):
            retval.append(obj)

    if retval == []:
        print >> sys.stderr,"no RooWorkspace found in file",rootFile
        sys.exit(1)

    return retval    

def Import(w,o,arg=ROOT.RooFit.RecycleConflictNodes()):
    '''RecycleConflictNodes() default (needed in this flow), ROOT.RooArgCmd()'''
    getattr(w,'import')(o,arg)#,ROOT.RooFit.Silence())

def swap(l,pos1,pos2):
    tmp=l[pos1]
    l[pos1]=l[pos2]
    l[pos2]=tmp
    return l

#----------------------------------------------------------------------
# main
#----------------------------------------------------------------------

#----------------------------------------
wsutils.checkCommonOptions(options)


if len(ARGV) < 4:
    print >> sys.stderr,"must specify at least four positional arguments. Run with -h to get more information"
    sys.exit(1)

inputFname = ARGV.pop(0)
outputFname = ARGV.pop(0)

if len(ARGV) % 2 != 0:
    print >> sys.stderr,"must specify an even number of arguments after the input and output files"
    sys.exit(1)

renameArgs = zip(ARGV[::2],ARGV[1::2])


#----------------------------------------


wsutils.loadLibraries(options)

fin = ROOT.TFile.Open(inputFname)

if fin == None or not fin.IsOpen():
    print >> sys.stderr,"error opening input file " + inputFname
    sys.exit(1)


#ws = findWorkspace(fin)
allws = findAllWorkspace(fin)
allws2 = []
hassub=[]

import re
for ws in allws:
    allMembers = wsutils.getAllMembers(ws)
    ws2=ROOT.RooWorkspace(ws.GetName(),ws.GetTitle())
    S_nsubs=0
    allRFV=[]
    for x in allMembers:
        if isinstance(x,ROOT.RooFormulaVar):
            allRFV.append(x)

    count=0
    changed=True
    while changed:
        changed=False
        count+=1
        if count > 1002: 
            print "current allRFV are:"
            print "allRFV:",",".join([k.GetName() for k in allRFV])
            raise ValueError("Unable to sort by swapping?")
        for i,x in enumerate(allRFV):
            if changed: break
            follow=allRFV[i+1:]
            prec=allRFV[:i]
            precname=[k.GetName() for k in prec] 
            for y in wsutils.getClients(x):
                if changed: break
                if y.GetName() in precname:

                    allRFVname=[k.GetName() for k in allRFV]
                    j=allRFVname.index(y.GetName())

                    if count> 1000: 
                        print "->Swapping", x.GetName(),"<->",y.GetName() ## DEBUG
                        print "precname",precname
                        print "y:", y
                        print "x clients",",".join([k.GetName() for k in wsutils.getClients(x)])
                        print "allRFVname:",",".join(allRFVname), "len=",len(allRFV)
                        print "want to swap",i,j

                    swap(allRFV,i,j)
                    changed=True
    ##DEBUG
    for i,x in enumerate(allRFV):
        prec=allRFV[:i]
        precname=[k.GetName() for k in prec]
        for y in wsutils.getClients(x):
            if y.GetName() in precname:
                print "->ERROR Unimplemented (dependencies)", x.GetName(),y.GetName()

    for x in allRFV:
            name=x.GetName()

            s=ROOT.std.stringstream()
            x.printMetaArgs(s) ## stringstrema?
            formula=re.sub('"\ +$','',re.sub('formula="','',s.str()))
            formula2=formula[:]
            nsubs=0
            for src, dest in renameArgs:
                formula2, numSubs= re.subn(src,dest,formula2)
                nsubs+=numSubs
            S_nsubs+=nsubs
            if nsubs>0:
                dep=ROOT.RooArgList()
                idx=0
                while True:
                    p=x.getParameter(idx)
                    if p==None: break
                    idx+=1
                    dep.add(p)
                
                #x.SetName(name+"_old")
                x2=ROOT.RooFormulaVar(name,x.GetTitle(),formula2,dep)
                Import(ws2,x2)

                ### print info
                print "* changing formula from",formula,"to",formula2 ## DEBUG
                s2=ROOT.std.stringstream() ## DEBUG
                x2.printArgs(s2) ## DEBUG
                s1=ROOT.std.stringstream() ## DEBUG
                x.printArgs(s1) ## DEBUG
                print "  X ",s1.str() ## DEBUG
                print "  ->",s2.str() ## DEBUG


    if S_nsubs>0:
        ''' Copy all remaining stuff'''
        print "* copying remaining stuff" ## DEBUG
        for x in allMembers:
            print "** importing",x.GetName() ## DEBUG
            Import(ws2,x)

    hassub.append( (S_nsubs >0) )
    allws2.append( ws2 if S_nsubs>0 else None )

print >> sys.stderr,"writing output file",outputFname ## DEBUG
if not options.dryrun: fOut=ROOT.TFile.Open(outputFname,"RECREATE")
for ws,ws2,changed in zip(allws,allws2,hassub):
    if changed:
        print "* writing changed version of ws",ws2.GetName() ## DEBUG
        if not options.dryrun: fOut.WriteTObject(ws2)
    else:
        print "* writing original version of ws",ws.GetName() ## DEBUG
        if not options.dryrun: fOut.WriteTObject(ws)
if not options.dryrun: fOut.Close()
