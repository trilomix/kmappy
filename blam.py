#!/usr/bin/env python 
import wx
from wx import Config

import blam
from blamframe import *
from  multiprocessing import freeze_support
class blamapp(wx.App):
    def OnInit(self):
##	wxConfig *config = new wxConfig(wxT("Karnaugh Map Minimizer"));
##	
##	wxString lang;
##	if ( config->Read(wxT("Language"), &lang) ) 
##	{
##		if(lang==wxT("hr")) m_locale.Init(wxLANGUAGE_CROATIAN);
##	}
##	else 
##	{
##		if(wxLocale::GetSystemLanguage()==wxLANGUAGE_CROATIAN)
##		{
##			m_locale.Init(wxLANGUAGE_CROATIAN);
##			config->Write(wxT("Language"), wxT("hr"));
##		}
##	}
##	
##	delete config;
##	
##	m_locale.AddCatalog(wxT("blam"));
	
        self.main = blamFrame( ( "Karnaugh Map Minimizer" ), wx.DefaultPosition, wx.Size(450,700) );

        self.main.Show()
        self.SetTopWindow(self.main)
        return True

def main():
    application = blamapp(0)
    if __debug__:
        from wx.lib.inspection import InspectionTool
        if not InspectionTool().initialized:
            InspectionTool().Init()
        wnd = wx.FindWindowAtPointer()
        if not wnd:
            wnd = application
        InspectionTool().Show(wnd, True)
        application.MainLoop()
##    if __debug__:
##        blamapp.OnOpenWidgetInspector(application)
    application.MainLoop()

if __name__ == '__main__':
##    import wx.lib.inspection
##    wx.lib.inspection.InspectionTool().Show()
	freeze_support()
	main()