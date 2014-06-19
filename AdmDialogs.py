# The Admin4 Project
# (c) 2013-2014 Andreas Pflug
#
# Licensed under the Apache License, 
# see LICENSE.TXT for conditions of usage

import adm
import os
import wx.html
from wh import xlt, modPath, localizePath
import version as admVersion

class PasswordDlg(adm.Dialog):
  def __init__(self, parentWin, msg, caption):
    adm.Dialog.__init__(self, parentWin)
    self.SetTitle(caption)
    self.staticPassword=msg

  def Save(self):
    return True

class AboutDlg(adm.Dialog):
  def __init__(self, parent):
    super(AboutDlg, self).__init__(parent)
    stdFont=self.GetFont()
    pt=stdFont.GetPointSize()
    family=stdFont.GetFamily()
    bigFont=wx.Font(pt*2 , family, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
    mediumFont=wx.Font(pt*1.4, family, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
    self['Admin'].SetFont(bigFont)
    self['Version'].SetFont(mediumFont)

    self.Admin="Admin4"
    self.Version=xlt("Version %s") % admVersion.version

    if not adm.IsPackaged():
        self.Revision = xlt("(%s)\nunknown changes") % admVersion.revDate 
        rev=xlt("unknown")
    elif admVersion.revLocalChange:
      if admVersion.revDirty:
        self.Revision = xlt("(+ %s)\nLocally changed/uncommitted") % admVersion.modDate 
        rev=xlt("locally changed %s") % admVersion.modDate
      else:
        self.Revision = xlt("(+ %s)\nLocally committed") % admVersion.revDate 
        rev="+ %s" % admVersion.revDate
    elif admVersion.revOriginChange:
      self.Revision = "(+ %s)" % admVersion.revDate
      rev="+ %s" % admVersion.revDate 
    else:
      if admVersion.tagDate:
        self.Revision = "(%s)" % admVersion.tagDate
      rev=admVersion.tagDate 
    self.Description = admVersion.description
    copyrights=[admVersion.copyright]
    licenses=[xlt("%s\nFor details see LICENSE.TXT") % admVersion.license]

    lv=self['Modules']
    lv.AddColumn(xlt("Module"), "PostgreSQL")
    lv.AddColumn(xlt("Ver."), "2.4.5")
    lv.AddColumn(xlt("Rev."), "2014-01-01++")
    lv.AddColumn(xlt("Description"), 30)
    
    vals=["Core", admVersion.version, rev, xlt("Admin4 core framework")]
    lv.AppendItem(adm.images.GetId("Admin4Small"), vals)

    wxver=wx.version().split(' ')
    v=wxver[0].split('.')
    vals=["wxWidgets", '.'.join(v[:3]), '.'.join(v[3:]), "wxWidgets %s" % ' '.join(wxver[1:])]
    lv.AppendItem(adm.images.GetId("wxWidgets"), vals)

    for modid, mod in adm.modules.items():
      vals=[]
      mi=mod.moduleinfo
      modulename=mi.get('modulename', modid)
      vals.append(modulename)
      vals.append(mi.get('version'))
      rev=mi.get('revision')
      if rev:
        vals.append(rev)
      else:
        vals.append("")
      vals.append(mi.get('description'))
      serverclass=mi['serverclass'].__name__.split('.')[-1]
      icon=adm.images.GetId(os.path.join(modid, serverclass))
      lv.AppendItem(icon, vals)
      credits=mi.get('credits')
      if credits:
        copyrights.append(credits)
      license=mi.get("license")
      if license:
        licenses.append("%s: %s" % (modulename, license))
    self.Copyright = "\n\n".join(copyrights).replace("(c)", unichr(169))
    
    licenses.append("Additional licenses from libraries used may apply.")
    self.License="\n\n".join(licenses)
  

class PreferencesDlg(adm.CheckedDialog):
  def __init__(self, parentWin):
    adm.Dialog.__init__(self, parentWin)
    self.panels=[]

    notebook=self['Notebook']
    for panelclass in adm.getAllPreferencePanelClasses():
        panel=panelclass(self, notebook)
        self.panels.append(panel)
        notebook.AddPage(panel, panel.name)

  def Go(self):
    for panel in self.panels:
      panel.Go()
      panel.SetUnchanged()

  def GetChanged(self):
    for panel in self.panels:
      if panel.GetChanged():
        return True
    return False

  def Check(self):
    for panel in self.panels:
      if hasattr(panel, "Check"):
        if not panel.Check():
          return False
    return True

  def Save(self):
    for panel in self.panels:
      if not panel.Save():
        return False
    return True


class HintDlg(adm.Dialog):

  @staticmethod
  def WantHint(hint, module):
    return adm.config.GetWantHint(hint, module)
  
  def __init__(self, parentWin, hint, hintModule, title, args):
    adm.Dialog.__init__(self, parentWin)
    self.hint=hint
    self.hintModule=hintModule
    self.title=title
    if args:
      self.args=args
    else:
      self.args={}
    args['appName'] = adm.appTitle
    
  def AddExtraControls(self, res):
    self.browser=wx.html.HtmlWindow(self)
    res.AttachUnknownControl("HtmlWindow", self.browser)
    

  def Go(self):
    f=open(localizePath(modPath(os.path.join("hints", "%s.html" % self.hint), self.hintModule)))
    html=f.read()
    f.close()
    for tag, value in self.args.items():
      html=html.replace("$%s" % tag.upper(), value.encode('utf-8'))
      
    self.browser.SetPage(html.decode('utf-8'))
    if not self.title:
      self.title=self.browser.GetOpenedPageTitle()
    if self.title:
      self.SetTitle(self.title)
    else:
      self.SetTitle(xlt("%s hint") % adm.appTitle)
    
  def Execute(self):
    adm.config.SetWantHint(self.hint, self.hintModule, not self.NeverShowAgain)
    return True
  

class Preferences(adm.NotebookPanel):
  name="General"
  
  def Go(self):
    self.ConfirmDeletes=adm.confirmDeletes
    self.MonthlyChecks=adm.monthlyChecks
    self.Proxy=adm.proxy

  def Save(self):
    adm.confirmDeletes=self.ConfirmDeletes
    adm.monthyChecks=self.MonthlyChecks
    adm.proxy=self.Proxy
    adm.config.Write("ConfirmDeletes", adm.confirmDeletes)
    adm.config.Write("MonthlyChecks", adm.monthlyChecks)
    adm.config.Write("Proxy", adm.proxy)
    return True

  @staticmethod
  def Init():
    adm.confirmDeletes=adm.config.Read("ConfirmDeletes", True)
    adm.monthlyChecks=adm.config.Read("MonthlyChecks", True)
    adm.proxy=adm.config.Read("Proxy")


  