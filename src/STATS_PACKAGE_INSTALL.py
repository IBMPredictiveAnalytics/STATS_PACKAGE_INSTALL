__author__  =  'Jon K Peck'
__version__ =  '1.1.0'
version = __version__

# history
# 07-31-2021 initial version
# 09-27-2022 protect against unset repos option
# 03-jul-2024 add version specification and uninstall capability
# 04-jul-2024

# The STATS PACKAGE INSTALL extension command
# R version numbers are not implemented

import spss, spssaux, os, random, platform, re, subprocess
from extension import Template, Syntax, processcmd

# debugging (optional)
try:
    import wingdbstub
    import threading
    wingdbstub.Ensure()
    wingdbstub.debugger.SetDebugThreads({threading.get_ident(): 1})
except:
    pass

def doinstalls(python=None, R=None, pyuninstalls=None):
    """Install or uninstall Python and R packages"""

    # Uninstall Python packages first if specified
    if pyuninstalls and pyuninstalls != ['[', ']']:
        pyuninstall(pyuninstalls)

    # Validate and install Python packages if specified
    if python and python != ['[', ']']:
        python, pypackagever = validatever(python)
        if python:  # Ensure there are valid packages to install
            pyinstall(python, pypackagever)

    # Validate and install R packages if specified
    if R and R != ['[', ']']:
        R, rpackagever = validatever(R)
        if not all(item in ["*", None] for item in rpackagever):
            raise ValueError("Version specifications for R packages are not currently supported")
        if R:  # Ensure there are valid packages to install
            rinstall(R)


def validatever(pspec):
    """Validate package names and versions for Python and R"""

    regex = "[\d.*<>]+"  # Regular expression to match version specifications

    if pspec is None:
        return None, None
    
    plist = []
    vlist = []

    for item in pspec:
        match = re.match(regex, item)
        if match is None:
            plist.append(item)   # Package name
        else:
            vlist.append(match.group())  # Version specification
    
    lplen = len(plist)
    lvlen = len(vlist)

    if lvlen > lplen:
        raise ValueError("Too many version numbers specified")

    vlist.extend((lplen - lvlen) * ['*'])  # Pad with "*" as needed

    return plist, vlist


def pyinstall(packages, versions):
    """Install Python packages"""

    if not packages:
        return
    
    loc, part2 = getSpssLocation()
    tloc = getTargetLocation()
    
    for pnumber, p in enumerate(packages):
        if not p:
            continue

        print(f"*** Installing Python package {p} into {tloc[0]} for {spss.GetDefaultPlugInVersion()} ***")

        # Determine the version specification
        if versions[pnumber] == "*":
            vspec = ""
        else:
            vspec = f"=={versions[pnumber]}"

        # Build the pip command
        command = f'"{loc}statisticspython3" -m pip --disable-pip-version-check install -U -t "{tloc[0]}" {p}{vspec} --no-cache-dir'

        try:
            # Run the pip command
            result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(result.stdout.decode())
        except subprocess.CalledProcessError as e:
            print(f"Error installing {p}: {e.stderr.decode()}")


def pyuninstall(packages):
    """Uninstall Python packages"""

    if not packages:
        return

    loc, part2 = getSpssLocation()
    for p in packages:
        print(f"*** Uninstalling Python package {p} ***")
        command = f'"{loc}statisticspython3" -m pip uninstall -y {p}'
        
        try:
            result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(result.stdout.decode())
        except subprocess.CalledProcessError as e:
            print(f"Error uninstalling {p}: {e.stderr.decode()}")


def getSpssLocation():
    """Return SPSS installation location"""

    plat = platform.system().lower()

    if plat.startswith("win"):
        try:
            spsshome = os.environ["SPSS_HOME"]
            #print(f"SPSS_HOME is set to: {spsshome}")
        except KeyError:
            raise ValueError("Could not find SPSS_HOME environment variable")        
        if not os.path.isdir(spsshome):
            raise ValueError(f"SPSS_HOME does not point to a valid directory: {spsshome}")
        return os.path.join(spsshome, ""), None
    
    elif plat.startswith("darwin"):
        # macOS specific
        spsshome = "/Applications/IBM SPSS Statistics/SPSS Statistics.app/Contents/bin/"
        #print(f"SPSS_HOME is set to: {spsshome}")
        return spsshome, None
    
    elif plat.startswith("linux"):
        try:
            spsshome = os.environ["SPSS_SERVER_HOME"]
            #print(f"SPSS_SERVER_HOME is set to: {spsshome}")
        except KeyError:
            raise ValueError("Could not find SPSS_SERVER_HOME environment variable")
        if not os.path.isdir(spsshome):
            raise ValueError(f"SPSS_SERVER_HOME does not point to a valid directory: {spsshome}")
        return os.path.join(spsshome, "bin/"), None
    
    raise SystemError("Could not find SPSS Statistics location")


def getTargetLocation():
    """Retrieve target location for Python modules"""

    workspace = "X." + str(random.uniform(.05, 1))
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
    #print(f"Target locations: {locs}")
    return locs


def rinstall(packages):
    """Install R packages"""

    for p in packages:
        print(f"**** Installing R package {p} for {spss.GetDefaultPlugInVersion()} ****")
        cmd = f"""BEGIN PROGRAM R.
r = getOption("repos")
if (r == "@CRAN@") {{
  r["CRAN"] <- "https://cloud.r-project.org"
  options(repos = r)
}}
install.packages("{p}", quiet=TRUE)
END PROGRAM."""
        
        try:
            spss.Submit(cmd)
        except Exception as e:
            print(f"Error installing {p}: {str(e)}")


def Run(args):
    """Execute the STATS PACKAGE INSTALL command"""

    args = args[list(args.keys())[0]]

    oobj = Syntax([
        Template("PYTHON", subc="",  ktype="literal", var="python", islist=True),
        Template("R", subc="",  ktype="literal", var="R", islist=True),
        Template("PYTHON", subc="UNINSTALL", ktype="literal", var="pyuninstalls", islist=True)
    ])

    # Enable localization
    global _
    try:
        _("---")
    except:
        def _(msg):
            return msg

    # Handle HELP subcommand
    if "HELP" in args:
        helper()
    else:
        processcmd(oobj, args, doinstalls)


def helper():
    """Open HTML help in default browser window"""

    import webbrowser, os.path
    
    path = os.path.splitext(__file__)[0]
    helpspec = "file://" + path + os.path.sep + "markdown.html"
    
    browser = webbrowser.get()
    if not browser.open_new(helpspec):
        print(f"Help file not found: {helpspec}")

try:
    from extension import helper
except:
    pass















     
