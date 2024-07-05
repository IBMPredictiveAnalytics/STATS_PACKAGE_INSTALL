__author__  =  'Jon K Peck'
__version__ =  '1.0.1'
version = __version__

# history
# 07-31-2021 initial version
# 09-27-2022 protect against unset repos option

# The STATS PACKAGE INSTALL extension command

import spss, spssaux, os, random, platform
from extension import Template, Syntax, processcmd


# debugging
        # makes debug apply only to the current thread
#try:
    #import wingdbstub
    #import threading
    #wingdbstub.Ensure()
    #wingdbstub.debugger.SetDebugThreads({threading.get_ident(): 1})
#except:
    #pass

# main routine
def doinstalls(python=None, R=None):
    """Install list of packages from PyPI or CRAN"""
    
    if not (python or R):
        raise ValueError(_("No packages to install were specified."))
    if python and not python[:] == ['[',']']:
        pyinstall(python)
    if R and not R[:] == ['[',']']:
        rinstall(R)
    
def pyinstall(packages):
    "Install list of Python packages"
    
    loc, part2 = getSpssLocation() # part2 holds extra stuff for Mac
    tloc = getTargetLocation()
    
    # Install or upgrade packages using the first location specified by SHOW EXTPATH
    for p in packages:
        print(_(f"*** Installing Python package {p} into {tloc[0]} for {spss.GetDefaultPlugInVersion()} ***"))
        cmd = ["HOST COMMAND=["]
        if part2 is not None:
            cmd.append(part2)
        cmd.append(spssaux._smartquote(fr"""{loc}statisticspython3 -m pip --disable-pip-version-check install -U -t "{tloc[0]}" {p} """) +"]")
        try:
            spss.Submit(cmd)
        except:
            pass    # keep going.  errors are reported in the Submit output.
    return

def getSpssLocation():
    """Return a duple of where Statistics is installed and, on Mac, an export command, or None

    The Statistics location does not have to be on the system path"""
    
    plat = platform.system().lower()

    if plat.startswith("win"):
        try:
            spsshome = os.environ["SPSS_HOME"]
        except:
            raise ValueError(_("Could not find SPSS_HOME environment variable"))        
        return ('"' + spsshome + os.path.sep + '"', None)
    
    elif plat.startswith("darw"):
        try:
            # SPSSHOME is not currently set on the Mac, so make  code to set it if that is still true
            # Without this set, the statisticspython3 script file will fail
            part2 = os.environ["SPSSHOME"]
            part2 = None
        except:
            exportcode = f"/Applications/IBM SPSS Statistics/SPSS Statistics.app/Contents"
            part2 = spssaux._smartquote(fr"""export SPSSHOME="{exportcode}" """)
        return ('"' + "/Applications/IBM SPSS Statistics/SPSS Statistics.app/Contents/bin/" + '"',
            part2)
    
    elif plat.startswith("lin"):
        try:
            spsshome = os.environ["SPSS_SERVER_HOME"]
        except:
            raise ValueError(_("Could not find SPSS_SERVER_HOME environment variable"))
        return ('"' + spsshome + os.path.sep + "bin" + os.path.sep +'"', None)
    
    raise SystemError(_("Could not find SPSS Statistics location"))

    
def getTargetLocation():
    """Use the SHOW EXT output to find where installed Python modules should go"""
    
    workspace = "X." + str(random.uniform(.05, 1))  # no scientific notation will be used
    spss.Submit(f"""PRESERVE.
    OMS SELECT TABLES/IF SUBTYPES='System Settings'
    /DESTINATION  FORMAT=OXML XMLWORKSPACE="{workspace}" VIEWER=NO
    /TAG = "{workspace}".
    SHOW EXT.
    OMSEND.
    RESTORE.""")
    
    locs = spss.EvaluateXPath(workspace, "/outputTree", 
        """//pivotTable//group[@text="EXTPATHS EXTENSIONS"]//category[@text="Setting"]/cell/@*""")
    spss.DeleteXPathHandle(workspace)
    return locs

def rinstall(packages):
    "install list of R packages"
    
    # The command is formatted so as not to prematurely terminate the program
    for p in packages:
        cmd = f"""begin program r.
r = getOption("repos")
if (r == "@CRAN@") {{
  r["CRAN"] <- "https://cloud.r-project.org"
  options(repos = r)
}}
install.packages("{p}", quiet=TRUE)""" + "\nend program."
        print(_(f"**** Installing R package {p} for {spss.GetDefaultPlugInVersion()} ****")) 
        try:
            spss.Submit(cmd)
        except:
            pass
    
def  Run(args):
    """Execute the STATS PACKAGE INSTALL command"""

    args = args[list(args.keys())[0]]


    oobj = Syntax([
        Template("PYTHON", subc="",  ktype="literal", var="python", islist=True),
        Template("R", subc="",  ktype="literal", var="R", islist=True)
    ])
        
    #debugging
# debugging
        # makes debug apply only to the current thread
    #try:
        #import wingdbstub
        #import threading
        #wingdbstub.Ensure()
        #wingdbstub.debugger.SetDebugThreads({threading.get_ident(): 1})
    #except:
        #pass

    #enable localization
    global _
    try:
        _("---")
    except:
        def _(msg):
            return msg

    # A HELP subcommand overrides all else
    if "HELP" in args:
        #print helptext
        helper()
    else:
        processcmd(oobj, args, doinstalls)

def helper():
    """open html help in default browser window
    
    The location is computed from the current module name"""
    
    import webbrowser, os.path
    
    path = os.path.splitext(__file__)[0]
    helpspec = "file://" + path + os.path.sep + \
         "markdown.html"
    
    # webbrowser.open seems not to work well
    browser = webbrowser.get()
    if not browser.open_new(helpspec):
        print(("Help file not found:" + helpspec))
try:    #override
    from extension import helper
except:
    pass        
