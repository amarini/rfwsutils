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
def findObjectsOnPaths(ws, srcObj, destObj):
    """ looks for all objects which can be 'reached' from srcObj
        and from which one can 'reach' destObj,
        i.e. all objects which are (indirect) clients of
        srcObj and (indirect) servers of destObj

        @param srcObj is assumed to be 'lower' than destObj in the tree,
        i.e. a (possibly indirect) server of destObj.
    """

    # names of nodes from which one can definitively NOT reach destObj
    badNodeNames = set()

    # names of nodes from which we can definitively reach destObj
    # (and which we have reached starting from srcObj, so we
    # can return goodNodes)
    goodNodeNames = set()
    goodNodes = []

    # probably not the most efficient implementation
    # but should at least be easy to understand
    def isGoodNode(node):
        nodeName = node.GetName()

        # query the cache
        if nodeName in goodNodeNames:
            return True
        
        if nodeName in badNodeNames:
            return False

        # check if we have reached the destination
        if nodeName == destObj.GetName():
            # we've reached the destination
            # add to the cache
            if not nodeName in goodNodeNames:
                goodNodes.append(node)
                goodNodeNames.add(nodeName)

            return True

        # we don't know if the node is good (can reach destObj)
        # or bad (can't read destObj for sure)
        # 
        # so we look at the node's clients

        #----------
        # get all clients
        #----------
        clients = wsutils.getClients(node)

        #----------
        # if this node has no clients at this point,
        # we will not be able to reach destObj
        
        if not clients:
            badNodeNames.add(nodeName)
            return False

        isGood = False

        for client in clients:

            # do a depth first search: go higher up before
            # visiting the other clients

            if isGoodNode(client):
                # client can reach the destination so we can as well
                if not nodeName in goodNodeNames:
                    goodNodes.append(node)
                    goodNodeNames.add(nodeName)

                isGood = True

            # note that we also want to find paths to the same destination
            # via other clients so we don't immediately return here
            
                
        if not isGood:
            # none of the clients could reach destObj so neither can we
            badNodeNames.add(nodeName)
            
        return isGood

    # walk on the graph
    isGoodNode(srcObj)

    return goodNodes
        
#----------------------------------------------------------------------
# main
#----------------------------------------------------------------------

from optparse import OptionParser
parser = OptionParser("""

  usage: %prog [options] input_file member1 member2 

  searches for all possible paths between member1 and member2 in the graph,
  assuming there are no loops. Both directions are tried (i.e.
  the graph is considered as undirected)
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

wsutils.loadLibraries(options)

fname = ARGV.pop(0)
fin = ROOT.TFile.Open(fname)
if fin == None or not fin.IsOpen():
    print >> sys.stderr,"problems opening file " + fname
    sys.exit(1)

# insist that there is a single workspace in this file
workspace = wsutils.findSingleWorkspace(fin, options)

srcObj  = wsutils.getObj(workspace, ARGV.pop(0))
destObj = wsutils.getObj(workspace, ARGV.pop(0))

# assume that there are no cycles in the object graph,
# so if one direction finds a path, the other will not

nodes = findObjectsOnPaths(workspace, srcObj, destObj)

if not nodes:
    # try the reverse direction
    nodes = findObjectsOnPaths(workspace, destObj, srcObj)

    if not(nodes):
        print >> sys.stderr,"no path found beween %s and %s" % (srcObj.GetName(), destObj.GetName())
        sys.exit(1)

# print [ node.GetName() for node in nodes ]

# get names of good nodes so that we can later on check
# which edges to draw
nodeNames = set([ node.GetName() for node in nodes ])

#----------
# produce graphviz code
#----------

fout = sys.stdout


print >> fout, "digraph G {"

# make sure the root node is at the top
# despite the fact that it has only incoming
# vertices
print >> fout, "  rankdir = BT;"

for node in nodes:

    # print attributes of node first
    print >> fout,'%s [label="%s\\n%s"]' % (node.GetName(),
                                           node.ClassName(),
                                           node.GetName())

print >> fout

# draw edges
for node in nodes:

    clients = wsutils.getClients(node)
    
    for client in clients:
        # note that not all clients are 'good' nodes
        # (i.e. they may not have a path to the upper level
        # object

        if not client.GetName() in nodeNames:
            continue

        # make arrows point 'upwards' in the sense
        # 'A -> B' means 'A influences B'
        print >> fout,"%s->%s" % (node.GetName(), client.GetName())


print >> fout,"}" # digraph


