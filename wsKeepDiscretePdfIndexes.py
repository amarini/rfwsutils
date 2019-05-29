#!/usr/bin/env python

# rfwsutils - utilities for manipulating RooFit workspaces from the command line
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
import re


from optparse import OptionParser
parser = OptionParser("""

  usage: %prog [options] file output pdf keepindex [keepindex ...]

  keep in a RooMultiPdf only a set of nuisances

  keepindex can be a number or a regexp on the pdf name
"""
)

parser.add_option("--rename_index",
                  default = "",
                  #action = "store_true",
                  help="instead of keeping the discrete index name instead use this one",
                  )

wsutils.addCommonOptions(parser)

(options, ARGV) = parser.parse_args()

#----------------------------------------
# check the command line options
#----------------------------------------
wsutils.checkCommonOptions(options)

if len(ARGV) < 4:
    print >> sys.stderr,"expected at least three positional arguments"
    sys.exit(1)

#----------------------------------------


import ROOT

def getClients(node):
    clients = []
    iter = node.clientIterator()
    while True:
        client = iter.Next()
        if client == None:
            break
        clients.append(client)
    return clients

def getServers(node):
    servers = []
    iter = node.serverIterator()
    while True:
        server = iter.Next()
        if server == None:
            break
        servers.append(server)
    return servers


# avoid unnecessary X11 connections
ROOT.gROOT.SetBatch(True)

wsutils.loadLibraries(options)

fname = ARGV.pop(0)
outname = ARGV.pop(0)
pdfname = ARGV.pop(0)

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

pdf = workspace.pdf(pdfname)
if pdf == None:
    print >> sys.stderr,"could not find item %s in workspace %s in file %s" % (pdfname, workspace.GetName(), fname)
    sys.exit(1)
if not pdf.InheritsFrom("RooMultiPdf"):
    print >> sys.stderr,"pdf %s is not a RooMultiPdf" % (pdfname)
    sys.exit(1)

catname=""
#print "CLIENTS:",getClients(pdf)
#print "SERVERS:",getServers(pdf)
for o in getServers(pdf):
    #print "Considering Client",o.GetName()
    if o.InheritsFrom("RooCategory"): catname=o.GetName()

if catname=="": 
    print >>sys.stderr,"unable to find RooCategoryName. (?)"

storedPdfs = ROOT.RooArgList();

npdf=pdf.getNumPdfs()
for ipdf in range(0,npdf):
    myfunc=pdf.getPdf(ipdf)
    toadd=False
    for item in ARGV:
        try:
            idx=int(item)
            if ipdf==idx: 
                print "* mapping with index",item
                toadd=True
        except ValueError:
            if re.match(item,myfunc.GetName()): 
                print "* mapping with regexp",item
                toadd=True
    
    if toadd: 
        print "-> Adding function", myfunc.GetName()
        storedPdfs.add(myfunc)

if options.rename_index != "":
    catname=options.rename_index
print "catname is",catname
pdf_cat = ROOT.RooCategory(catname,"remapped")
newpdf=ROOT.RooMultiPdf(pdf.GetName(),pdf.GetTitle(),pdf_cat,storedPdfs)

ws2=ROOT.RooWorkspace(workspace.GetName(),workspace.GetTitle())
getattr(ws2,'import')(newpdf,ROOT.RooFit.RecycleConflictNodes(),ROOT.RooFit.Silence())
allMembers = wsutils.getAllMembers(workspace)
for x in allMembers:
    if x.GetName() != pdfname:
        getattr(ws2,'import')(x,ROOT.RooFit.RecycleConflictNodes(),ROOT.RooFit.Silence())

ws2.writeToFile(outname)
print "-- DONE --"
ws2.pdf(pdfname).Print()
print "----------"
del ws2

    
