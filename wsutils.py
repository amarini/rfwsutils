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


import os, re, sys
import ConfigParser


#----------------------------------------------------------------------

def rootListTolist(rootList):
    """ converts a ROOT.list object to a list

        see also http://root.cern.ch/phpBB3/viewtopic.php?f=14&t=11376
    """

    if not rootListTolist.initialized:
        # make sure we load the corresponding class dictionary
        # TODO: this is not thread safe...

        import ROOT
        import tempfile

        linkDefFile = tempfile.NamedTemporaryFile(suffix = ".h")

        print >> linkDefFile, '#include "RooAbsData.h"'
        print >> linkDefFile, '#include <list>'
        print >> linkDefFile, '#ifdef __CINT__'
        print >> linkDefFile, '#pragma link C++ class std::list<RooAbsData*>::iterator;'
        print >> linkDefFile, '#endif'

        linkDefFile.flush()

        # workaround for CMSSW
        if os.environ.has_key("ROOFITSYS"):
            ROOT.gInterpreter.AddIncludePath(os.path.join(os.environ["ROOFITSYS"], "include"))        

        # load this generated macro
        ROOT.gROOT.LoadMacro(linkDefFile.name + "+")
        
        rootListTolist.initialized = True
    
    #----------
    
    retval = []

    it = rootList.begin()
    end = rootList.end()
    
    while it != end:
        retval.append(it.__deref__())
        it.__postinc__(1)

    return retval

# static variable
rootListTolist.initialized = False

#----------------------------------------------------------------------
def addCommonOptions(parser,
                     addSetVars = False,
                     ):
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

    parser.add_option("--nolib",
                      # note the inverted logic here
                      dest="loadProfileLibs",
                      default = True,
                      action="store_false",
                      help="do NOT load the libraries specified in the startup profile",
                      )

    parser.add_option("-w",
                      dest="workspaceName",
                      default = None,
                      type = str,
                      help="specify the workspace name explicitly (in case more than one is in top level directory in the file)",
                      metavar = "WSNAME",
                      )
    if addSetVars:
        parser.add_option("--set",
                          dest="setVars",
                          default = "",
                          type = str,
                          help="comma separated list of expressions var1=value1,var2=value2,... will set variables to the given values after loading the workspace continuing",
                          metavar = "EXPRS",
                          )


#----------------------------------------------------------------------

def checkCommonOptions(options):
    """ perform some common checks on command line options """

    # TODO: is there a way to see whether the libraries were specified
    #       in --lib or read from the profile ?
    
    # replace environment variables in the variable expressions
    options.lib = [ os.path.expandvars(x) for x in options.lib ]

    if options.loadProfileLibs:
        for lib in options.lib:
            if not os.path.exists(lib):
                print >> sys.stderr,"library " + lib + " does not exist, exiting"
                sys.exit(1)

    if hasattr(options, "setVars"):
        # parse this

        tmp = {}

        if options.setVars != "":
            for spec in options.setVars.split(","):
                varname, value = spec.split("=",1)
                tmp[varname] = float(value)

        options.setVars = tmp
            

#----------------------------------------------------------------------

def findWorkspaces(topdir, options):
    import ROOT

    # topdir can be a TFile or more generally a TDirectory
    retval = []

    if options.workspaceName != None:
        # a workspace was specified explicitly
        ws = topdir.Get(options.workspaceName)
        if ws == None:
            print >> sys.stderr,"no workspace named",options.workspaceName,"found"
            sys.exit(1)

        retval = [ ws ]
        
    else:
        # find all workspaces in the top level directory in the file
        
        for key in topdir.GetListOfKeys():

            # TODO: support subdirectories
            obj = topdir.Get(key.GetName())
            if isinstance(obj,ROOT.RooWorkspace):
                retval.append(obj)

    return retval

#----------------------------------------------------------------------    

def findSingleWorkspace(topdir, options):
    """like findWorkspaces(..) but insists that exactly one workspace was selected/found"""
    import ROOT

    workspaces = findWorkspaces(topdir, options)

    if len(workspaces) > 1:
        print >> sys.stderr,"more than one workspace found"
        sys.exit(1)

    if len(workspaces) < 1:
        print >> sys.stderr,"no workspace found"
        sys.exit(1)

    return workspaces[0]

#----------------------------------------------------------------------    


def getObj(ws, name):
    """ tries to find the given object in the workspace or prints
    an error message an exits if there is no such object """

    obj = ws.obj(name)

    if obj == None:
        print >> sys.stderr,"object '" + name + "' not found in workspace " + ws.GetName()
        sys.exit(1)

    return obj

#----------------------------------------------------------------------

def loadLibraries(options):
    """ loads the libraries specified in the options """

    if not options.loadProfileLibs:
        return

    import ROOT
    
    for lib in options.lib:
        ROOT.gSystem.Load(lib)



#----------------------------------------------------------------------

def getAllMembers(ws):
    """ @return a list of all components of the given workspace """

    components = ws.components()
    it = components.iterator()

    allMembers = []

    while True:

        obj = it.Next()
        if obj == None:
            break

        allMembers.append(obj)

    # add datasets (which seem NOT to be included in the above ?)
    allMembers += rootListTolist(ws.allData())

    return allMembers


#----------------------------------------------------------------------

def applySetVars(workspace, setVarsDict):
    for name, value in setVarsDict.items():
        var = getObj(workspace, name)

        import ROOT

        if not isinstance(var, ROOT.RooRealVar):
            raise Exception("object %s in workspace %s is not of type RooRealVar" % (name, workspace.GetName()))

        # TODO: should we print a warning if the value is outside the range ?

        # adapt maximum or minimum if necessary
        if value < var.getMin():
            var.setMin(value)
        elif value > var.getMax():
            var.setMax(value)
            
        var.setVal(value)

#----------------------------------------------------------------------

def rooArgSetToList(argset):
    """creates a python list with the contents of argset (which should be a RooArgSet)"""
    it = argset.createIterator()

    retval = []
    while True:
        obj = it.Next()

        if obj == None:
            break

        retval.append(obj)

    return retval

#----------------------------------------------------------------------
def printVars(vars):

    it = vars.iterator()

    while True:
        var = it.Next()
        if var == None:
            break

        var.Print()

#----------------------------------------------------------------------

def printVarsCSV(vars):
    # vars is a RooArgSet

    it = vars.iterator()

    print ",".join([
        "name",
        "value",
        "min",
        "max",
        "constant"])

    while True:
        var = it.Next()
        if var == None:
            break

        parts = [
            var.GetName(),
            var.getVal(),
            var.getMin(),
            var.getMax(),
            var.isConstant(),
            ]
        
        print ",".join([ str(p) for p in parts ])

#----------------------------------------------------------------------


