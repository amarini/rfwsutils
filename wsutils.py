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


import os, re
import ConfigParser

#----------------------------------------------------------------------
def addCommonOptions(parser):
    """ adds common options to the command line arguments parser """

    conf = ConfigParser.SafeConfigParser()
    conf.read(os.path.expanduser("~/.rfwsutilsrc"))

    try:
        defaultLibs = conf.get('options','lib')
        defaultLibs = re.split(',\s*',defaultLibs)
        
    except ConfigParser.Error:
        defaultLibs = []

    parser.add_option("--lib",
                  dest="lib",
                  default = defaultLibs,
                  type="str",
                  action="append", # append to list
                  help="library to load before opening the files. Can be specified multiple times.",
                  metavar="LIB")


#----------------------------------------------------------------------

def checkCommonOptions(options):
    """ perform some common checks on command line options """

    for lib in options.lib:
        if not os.path.exists(lib):
            print >> sys.stderr,"library " + lib + " does not exist, exiting"
            sys.exit(1)


#----------------------------------------------------------------------

def findWorkspaces(topdir):
    import ROOT

    # topdir can be a TFile or more generally a TDirectory
    retval = []

    for key in topdir.GetListOfKeys():

        # TODO: support subdirectories
        obj = topdir.Get(key.GetName())
        if isinstance(obj,ROOT.RooWorkspace):
            retval.append(obj)

    return retval



#----------------------------------------------------------------------