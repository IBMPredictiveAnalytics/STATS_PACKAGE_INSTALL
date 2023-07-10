# STATS POP DESCRIPTIVES extension command
# This replaces the Population Descriptives custom dialog with a full extension command.


__author__ = "JKP"
__version__ = "1.0.0"

# history
# 26-jun-2023 original version

import spss, spssaux, SpssClient
from extension import Template, Syntax, processcmd

import math, copy, time


# debugging
try:
    import wingdbstub
    import threading
    wingdbstub.Ensure()
    wingdbstub.debugger.SetDebugThreads({threading.get_ident(): 1})
except:
    pass

def popdescrip(variables, missing="variable"):
    """do population descriptives"""
    
    vardict = spssaux.VariableDict(variables, variableType="numeric")
    varslower = [v.lower() for v in vardict.variables]
    var2 = copy.copy(variables)
    # remove any nonnumeric variables
    removecount = 0
    footnote = ""
    for i, v in enumerate(var2):
        if not v.lower() in varslower:
            variables.pop(i)
            removecount += 1
    if not variables:
        raise ValueError(_("""No numeric variables were specified."""))
    if removecount > 0:
        footnote = _(f"""{removecount} nonnumeric variables were excluded\n""")
    spss.Submit(f"""DESCRIPTIVES VARIABLES = {" ".join(variables)}
    /STATISTICS MIN MAX MEAN STDDEV VARIANCE
    /MISSING={missing}.""")
    SpssClient.StartClient()
    for i in range(5):
        pt = getPivotTable()
        if pt is not None:
            break
    else:
        raise ValueError(_("DESCRIPTIVES table not found"))
    pt.SetUpdateScreen(False)
    adjustStats(pt, variables, vardict, footnote)
    pt.SetUpdateScreen(True)
    SpssClient.StopClient()

def getPivotTable():
    """return the Descriptives pivot table"""
    
    # must give the Viewer a little time to recognize the pt.
    time.sleep(.5)
    items = SpssClient.GetDesignatedOutputDoc().GetOutputItems()
    itemcount = items.Size()
    if items.GetItemAt(itemcount-1).GetType() == SpssClient.OutputItemType.LOG:
        itemcount -= 1
    for itemnumber in range(itemcount-1, -1, -1):
        item = items.GetItemAt(itemnumber)
        if item.GetTreeLevel() <= 1:
            break
        if item.GetType() == SpssClient.OutputItemType.PIVOT and \
           item.GetSubType() == 'Descriptive Statistics':
            thetable = item.GetSpecificType()
            return thetable
    return None


def adjustStats(pt, variables, vardict, footnote):
    """pt is an activated DESCRIPTIVES pivot table"""

    caption = footnote + _("Standard Deviation and Variance use N, not N-1, in the denominator.")
    pt.SetCaptionText(caption)
    datacells = pt.DataCellArray()
    for row in range(datacells.GetNumRows() - 1):
        N = datacells.GetUnformattedValueAt(row, 0)
        try:
            N = float(N)
            if N == 0:
                continue
            dollar = vardict[variables[row]].VariableFormat.startswith("DOLLAR")
            val = float(datacells.GetUnformattedValueAt(row, 4))
            fmt = datacells.GetNumericFormatAt(row, 4)
            if dollar:
                fmt = "$#,###.##"
            datacells.SetValueAt(row, 4, str(math.sqrt((N-1)/N) * val))
            datacells.SetNumericFormatAt(row, 4,fmt)
            
            val = float(datacells.GetUnformattedValueAt(row, 5))
            fmt = datacells.GetNumericFormatAt(row, 5)
            datacells.SetValueAt(row, 5, str(((N-1)/N) * val))
            datacells.SetNumericFormatAt(row, 5, fmt)
        except:
            continue

def Run(args):
    """Run the STATS POP DESCRIPTIVES command"""
    
    args = args[list(args.keys())[0]]
    
    oobj = Syntax([
    Template("VARIABLES", subc="", var="variables", ktype="existingvarlist", islist=True), 
    Template("MISSING", subc="", var="missing", ktype="str", vallist=["variable", "listwise"])
    ])

    #enable localization
    global _
    try:
        _("---")
    except:
        def _(msg):
            return msg

    if "HELP" in args:
        #print helptext
        helper()
    else:
        processcmd(oobj, args, popdescrip, vardict=spssaux.VariableDict(caseless=True))

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