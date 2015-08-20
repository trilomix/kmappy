import wx
from wx import Notebook
from wx import grid
from wx import TreeCtrl
from wx import SpinCtrl
from wx import Config

import os
from time import sleep, time
import sys
import math

import truthtable
from kmap import *
from karnaughmap import *
from perfTableparser import perfTableParser
from ReduceBoolExpression import ReduceSol
#from DataThread import SolveTask

import traceback
import multiprocessing as mp
from multiprocessing import Process, Lock, Queue, Manager, Pool, cpu_count
import logging
from thread import start_new_thread
from threading import Thread

import blamframe

[Resize, wxID_STATUSBAR,
    Menu_File_Load, Menu_File_Save, Menu_File_SaveTo,Menu_File_SaveSolution ,
    Menu_File_Quit, Menu_File_About, Menu_Language_Croatian,
    Menu_Language_Default, Menu_Cell_Adresses, Menu_Show_Zeros,

    Vars_Count, Outputs_Count, Truth_Table,
    Function_Button, Paste_Button,
    Solve_Button, Sol_Txt, Sol_Tree, Equ_Txt, Equ_Tree, Solution_Type] = [wx.NewId() for __init__ in range(23)]

class MyStatusBar(wx.StatusBar):
    """ Displays information about the current view. Also global stats/
        progress bar etc. """
    def __init__(self, *_args, **_kwargs):
        wx.StatusBar.__init__(self, _kwargs['parent'], _kwargs['id'], style=wx.ST_SIZEGRIP)
        self.progress_bar = wx.Gauge(self, -1, style=wx.GA_HORIZONTAL|wx.GA_SMOOTH)
        self.SetFieldsCount(3)
        self.ProgressBarSize()

    def ProgressBarSize(self):
        rect = self.GetFieldRect(1)
        #self.progress_bar.SetPosition((rect.x+2, rect.y+2))
    	#self.progress_bar.SetSize((rect.width-4, rect.height-4))
        self.progress_bar.SetDimensions(rect.x+1, rect.y+1, rect.width -2, rect.height -2)

class TaskKarnaughMap(KarnaughMap):
    def __init__(self, numberOfOutputs, out, NbWorkers):
        KarnaughMap.__init__(self, numberOfOutputs, int(NbWorkers))
        self.out = out
    def __call__(self):
        return self.Solve()
    def __str__(self):
        return '%s * %s' % (self.out, self.out)

class Worker(Process):

    def __init__(self, work_queue, result_queue):

        # base class initialization
        Process.__init__(self)

        # job management stuff
        self.work_queue = work_queue
        self.result_queue = result_queue
        self.kill_received = False
        print('Worker init...')

    def run(self):
        print('Worker run...')
        while not self.kill_received:

            # get a task
            #job = self.work_queue.get_nowait()
            try:
                if not self.work_queue.empty():
                    Kmap = self.work_queue.get(True,0.1)
                else  :
                     break
##            except Empty:
##                break
            except:
                print("Error")
                traceback.print_exc()
                pass
            # the actual processing
            print("Starting " + str(Kmap.out) + " ...")

            Kmap()

            # store the result
            self.result_queue.put(Kmap)


class SolveTask(Thread):
    def __init__ (self,parent):
        Thread.__init__(self)
        self.daemon = True
        self.parent = parent

    def Solve(self):
        # Mutlti Processing
        NbWorkers = cpu_count()-1
        mp.log_to_stderr()
        logger = mp.get_logger()
        logger.setLevel(logging.INFO)

        outs = self.parent.numberOfOutputs.GetValue()
        KmapList = []
        numberOfVariables = self.parent.numberOfVariables.GetValue()
        for out in range(0, outs):
            #if ('' == self.parent.solution[out].GetItemText(self.parent.solution[out].GetRootItem())):
            if (not self.parent.solution[out].GetRootItem().IsOk()) or ('' == self.parent.solution[out].GetItemText(self.parent.solution[out].GetRootItem())):
                self.parent.solution[out].DeleteAllItems()
                self.parent.kmap[out].ClearSolutions()
                K = TaskKarnaughMap(numberOfVariables, out, NbWorkers)
                for i in range(0, self.parent.kmap[out].GetNumberRows()) :
            		for j in range(0, self.parent.kmap[out].GetNumberCols()) :
            			if(self.parent.solveSOP):
            				if(self.parent.kmap[out].GetCellValue(i, j)==("1")):
            					K.Set(j,i, 1)
            				if(self.parent.kmap[out].GetCellValue(i, j)==("0")):
            					K.Set(j,i, 0)
            				if(self.parent.kmap[out].GetCellValue(i, j)==("?")):
            					K.Set(j,i, 2)
            			else :
            				if(self.parent.kmap[out].GetCellValue(i, j)==("1")):
            					K.Set(j,i, 0)
            				if( (self.parent.kmap[out].GetCellValue(i, j)==("0")) | (self.parent.kmap[out].GetCellValue(i, j)==(""))):
            					K.Set(j,i, 1)
            				if(self.parent.kmap[out].GetCellValue(i, j)==("?")):
            					K.Set(j,i, 2)
                self.parent.work_queue.put(K)
                KmapList.append(K)

        if self.parent.work_queue.qsize() < NbWorkers:
            NbWorkers = self.parent.work_queue.qsize()
        print('Start Workers')
        self.parent.WorkerList = []
        for i in range(NbWorkers):
            worker = Worker(self.parent.work_queue, self.parent.result_queue)
            worker.start()
            #worker.run()
            self.parent.WorkerList.append(worker)
        print('Workers Run')
##        while not self.work_queue.empty():
##            NbWorkLeft = work_queue.qsize()
##            self.UpdateLock.acquire()
##            #wx.CallAfter(self.progress_bar.SetValue, (outs-NbWorkLeft)*100/outs)
##            self.UpdateLock.release()
##            sleep(0.1)

##        for i in range(len(KmapList)):
##            Kmap = result_queue.get()
##            self.Updateparent(Kmap, Kmap.out)

        for worker in self.parent.WorkerList:
                worker.join()
                self.parent.WorkerList.remove(worker)
        print('Workers Join')

    def run(self):
        self.Solve()

def walk_branches(tree,root):
    """ a generator that recursively yields child nodes of a wx.TreeCtrl """
    if root.IsOk():
        item, cookie = tree.GetFirstChild(root)
        while item.IsOk():
            yield item
            if tree.ItemHasChildren(item):
                walk_branches(tree,item)
            item,cookie = tree.GetNextChild(root,cookie)

class blamFrame(wx.Frame):
    def __init__(self, title,  pos, size, locale=None ):
        parent=None
        wx.Frame.__init__(self, parent, -1, title, pos, size)

        # ##### Variable initialization ****/
    	self.solveSOP=1
    	self.Reduce = None

    	self.WorkerList = []
    	self.work_queue = Queue()
    	self.result_queue = Queue()
    	self.solvethread = None
    	self.UpdateLock = Lock()
    	self.LastTime = None
    	self.SolveLeft = 0

    	# ##### Icon *****/

    	appdir =  os.path.dirname(sys.argv[0])
    	if appdir == '':
    	    appdir = '.'
    	icon = wx.Icon( appdir + os.sep +'wxwin.ico', wx.BITMAP_TYPE_ICO)
    	self.SetIcon(icon)

    	# ##### Menu *****/

    	menuFile = wx.Menu()

    	menuFile.Append(Menu_File_Load, ("&Load"), ("Load from file"))
        self.Bind(wx.EVT_MENU, self.OnLoad, id=Menu_File_Load)

    	menuFile.Append(Menu_File_Save, ("&Save"), ("Save to file"))
        self.Bind(wx.EVT_MENU, self.OnSave, id=Menu_File_Save)

    	menuFile.Append(Menu_File_SaveTo, ("Save to ..."), ("Save to new file"))
        self.Bind(wx.EVT_MENU, self.OnSaveTo, id=Menu_File_SaveTo)

    	menuFile.Append(Menu_File_SaveSolution, ("Save Solution to ..."), ("Save solution to file"))
        self.Bind(wx.EVT_MENU, self.OnSaveSol, id=Menu_File_SaveSolution)

    	# wxBitmap aboutBitmap(wxT("about.xpm"), wxBITMAP_TYPE_XPM )
    	menuFile.Append(Menu_File_About, ("&About"), ("About the program"))
        self.Bind(wx.EVT_MENU, self.OnAbout, id=Menu_File_About)
    	# about.SetBitmap(aboutBitmap)

        menuFile.AppendSeparator()

    	# wxBitmap exitBitmap(wxT("exit.xpm"), wxBITMAP_TYPE_XPM )
        menuFile.Append(Menu_File_Quit, ("E&xit"), ("Exit the program"))
        self.Bind(wx.EVT_MENU, self.OnQuit, id=Menu_File_Quit)
    	# exit.SetBitmap(exitBitmap)

    	# Settings menu

        menuSettings = wx.Menu()
        menuLanguage = wx.Menu()

    	menuLanguage.Append(Menu_Language_Default, ("English (default)"), ("Set language to english"), wx.ITEM_RADIO)
        self.Bind(wx.EVT_MENU, self.OnLangDefault, id=Menu_Language_Default)

        menuSettings.AppendMenu(-1, u'Language', menuLanguage, u'Set language (requires restart)')

    	menuSettings.AppendSeparator()

    	#showZeros= wx.MenuItem(0, Menu_Show_Zeros, ("Show zeros"), ("Show / hide zero values"), wx.ITEM_CHECK)
    	showZeros= wx.MenuItem(menuSettings, Menu_Show_Zeros, ("Show zeros"), ("Show / hide zero values"), wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self.OnShowZeros, id=Menu_Show_Zeros)
    	showAdress=wx.MenuItem(menuSettings, Menu_Cell_Adresses, ("Show cell adresses"), ("Show / hide cell adresses in the K-map"), wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self.OnCellAdresses, id=Menu_Cell_Adresses)

    	menuSettings.AppendItem( showZeros )
    	menuSettings.AppendItem( showAdress )

    	menuBar =  wx.MenuBar()
    	menuBar.Append( menuFile, ( "&Program" ) )
    	menuBar.Append( menuSettings, ( "&Settings" ) )


    	self.SetMenuBar( menuBar )

    	# ##### Status Bar *****/

        self.statusbar = MyStatusBar(id=wxID_STATUSBAR,
              name='statusBar', parent=self, style=0)
        self.SetStatusBar(self.statusbar)
    	#self.statusbar = self.CreateStatusBar()
    	self.statusbar.SetFieldsCount(3)
    	self.statusbar.SetStatusWidths([-3, -1, -2])
    	self.SetStatusText( ( "Welcome to Karnaugh Map Minimizer!" ),0 )
    	# Progress Bar
    	self.progress_bar = self.statusbar.progress_bar
    	#self.ProgressBarSize()

    	self.progress_bar.Hide()

    	# ##### Main panel initialization *****/

    	mainPanel= wx.Panel(self, -1, wx.DefaultPosition, wx.DefaultSize)

    	# ##### Spliter #####/

    	mainSpliter    = wx.SplitterWindow(mainPanel, -1, style=wx.SP_LIVE_UPDATE)
    	mainLeftPanel  = wx.Panel(mainSpliter)
    	mainLeftPanel.SetMinSize(wx.Size(300, 400))
    	mainRightPanel = wx.Panel(mainSpliter)
    	mainRightPanel.SetMinSize(wx.Size(100, 400))
    	mainSpliter.SplitVertically(mainLeftPanel, mainRightPanel, sashPosition=0)
    	#mainSpliter.Fit()

    	# ##### Notebook control initialization *****/

    	self.methodBook =  wx.Notebook(mainRightPanel, -1)

    	# ##### Sizers initialization *****/

        panelSizer = wx.BoxSizer(wx.HORIZONTAL)
        mainSizer = wx.BoxSizer(wx.VERTICAL)
    	leftSizer = wx.StaticBoxSizer( wx.StaticBox(mainLeftPanel, -1, ("Truth table")), wx.VERTICAL)
    	rightSizer = wx.BoxSizer(wx.VERTICAL)
    	rightSizerTop = wx.BoxSizer(wx.HORIZONTAL)
    	rightSizerBottom = wx.BoxSizer(wx.HORIZONTAL)

    	# Layout

    	mainSizer.Add(rightSizerTop, 0, wx.EXPAND | wx.BOTTOM, 10)
    	panelSizer.Add(mainPanel, 1, wx.EXPAND)
    	rightSizer.Add(rightSizerBottom, 2, wx.EXPAND)
    	mainSizer.Add(mainSpliter, 1, wx.EXPAND | wx.ALL, 0)

    	# ##### Controls *****/

    	# ##### Trouth table *****/

    	self.truthTable =  truthtable.TruthTable(mainLeftPanel, Truth_Table, 4, 1, wx.DefaultPosition, wx.Size(170,200), wx.SIMPLE_BORDER, wx.PanelNameStr)
    	leftSizer.Add(self.truthTable, 1, wx.EXPAND | wx.ALL, 5)
    	leftSizer.Add( wx.Button(mainLeftPanel, Function_Button, ("Fill from function")), 0, wx.EXPAND | wx.ALL, 5)
    	leftSizer.Add( wx.Button(mainLeftPanel, Paste_Button, ("Paste from clipboard")), 0, wx.EXPAND | wx.LEFT | wx.BOTTOM | wx.RIGHT, 5)

    	# ##### Karnaugh Map Notebook page *****/

    	self.kmap = []
    	self.solution = []
    	self.solutionTxt = []

    	self.AddPage(0)

    	# ##### Equations tree control *****/

    	self.EquationsTxt = wx.StaticText(mainRightPanel, Equ_Txt, ("Equations:"))
    	rightSizer.Add( self.EquationsTxt, 0, wx.EXPAND | wx.TOP, 0)
    	self.EquationsTxt.Hide()

    	self.Equations = wx.TreeCtrl(mainRightPanel, Equ_Tree, wx.DefaultPosition, wx.DefaultSize, wx.SIMPLE_BORDER | wx.TR_HAS_BUTTONS | wx.TR_HIDE_ROOT | wx.TR_MULTIPLE )
    	self.Equations.Hide()

    	#rightSizer.Add(self.solution, 1, wx.EXPAND | wx.TOP, 5)
    	rightSizer.Add(self.Equations, 1, wx.EXPAND | wx.TOP, 5)

    	# ##### Solve Button ****/
    	Solve_Button_wx = wx.Button(mainRightPanel, Solve_Button, ("Solve"))
    	rightSizer.Add( Solve_Button_wx, 0, wx.ALIGN_RIGHT | wx.TOP, 10)

    	rightSizerBottom.Add(self.methodBook, 1, wx.EXPAND  | wx.BOTTOM, 10)

    	# ##### Settings controls ****/

    	rightSizerTop.Add( wx.StaticText(mainPanel, -1, ("Number of variables: ")), 0, wx.CENTER | wx.RIGHT, 10)
    	self.numberOfVariables = wx.SpinCtrl(mainPanel, Vars_Count, ("4"), wx.DefaultPosition, wx.Size(50,-1))
    	self.numberOfVariables.SetRange(1, 11)
    	rightSizerTop.Add(self.numberOfVariables, 0, wx.CENTER)
    	rightSizerTop.Add( wx.StaticText(mainPanel, -1, ("Number of outputs: ")), 0, wx.CENTER | wx.RIGHT, 10)
    	self.numberOfOutputs = wx.SpinCtrl(mainPanel, Outputs_Count, ("1"), wx.DefaultPosition, wx.Size(50,-1))
    	self.numberOfOutputs.SetRange(1, 11)
    	rightSizerTop.Add(self.numberOfOutputs, 0, wx.CENTER)
    	rightSizerTop.Add( wx.StaticText(mainPanel, -1, ("Type of solution: ")), 0, wx.CENTER | wx.LEFT | wx.RIGHT, 10)
    	solutionType =  wx.Choice(mainPanel, Solution_Type)
    	solutionType.Append(("Sum of products"))
    	solutionType.Append(("Product of sums"))
    	solutionType.SetSelection(0)
    	rightSizerTop.Add(solutionType, 1,  wx.CENTER)

    	# ##### Set sizers *****/

    	mainPanel.SetSizer(mainSizer)
    	mainSizer.SetSizeHints(mainPanel)

    	mainLeftPanel.SetSizer(leftSizer)

    	mainRightPanel.SetSizer(rightSizer)

    	self.SetSizerAndFit(panelSizer)
    	panelSizer.SetSizeHints(self)
    	self.SetAutoLayout(1)

    	mainLeftPanel.Layout()
    	mainRightPanel.Layout()

    	# Event

    	self.Bind(wx.EVT_SIZE,      self.OnSize, self,            id=Resize)

    	self.Bind(wx.EVT_SPINCTRL,    self.OnVarsChange,          id=Vars_Count)
    	self.Bind(wx.EVT_SPINCTRL,    self.OnOutsChange,          id=Outputs_Count)
    	self.Bind(grid.EVT_GRID_CMD_CELL_CHANGE, self.OnTruthTChange, id=Truth_Table)
    	self.Bind(grid.EVT_GRID_CMD_LABEL_LEFT_CLICK, self.OnTruthTLabelChange, id=Truth_Table)
    	self.Bind(grid.EVT_GRID_CMD_LABEL_RIGHT_CLICK, self.OnTruthTLabelChange, id=Truth_Table)
    	self.Bind(wx.EVT_BUTTON, self.OnSolve,                    id=Solve_Button)
    	self.Bind(wx.EVT_BUTTON, self.OnFunction,                 id=Function_Button)
    	self.Bind(wx.EVT_BUTTON, self.OnPaste,                     id=Paste_Button)
    	self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSolSelect,      id=Sol_Tree)
    	self.Bind(wx.EVT_CHOICE, self.OnSolutionTypeChange,       id=Solution_Type)

    	self.Bind(wx.EVT_IDLE, self.OnIdle)

    	# ##### Load configuration ****/

    	config =  wx.Config(("Karnaugh Map Minimizer"))
##    	if ( config.Read(("Language"), lang) ) :
##    		if(lang==("")): menuLanguage.Check(Menu_Language_Default, 1)
##    		if(lang==("hr")): menuLanguage.Check(Menu_Language_Croatian, 1)


    	if config.HasEntry('Cell_Adresses') :
    		adresses = config.Read(("Cell_Adresses"), 'yes')
    		if(adresses==("no")) :
    			menuSettings.Check(Menu_Cell_Adresses, 0)
    			self.kmap[0].SetCellAdresses(0)
    		else :
    			menuSettings.Check(Menu_Cell_Adresses, 1)
    			self.kmap[0].SetCellAdresses(1)
    	else :
    		menuSettings.Check(Menu_Cell_Adresses, 1)
    		self.kmap[0].SetCellAdresses(1)

    	if config.HasEntry('Show_Zeros') :
    	    zeros = config.Read('Show_Zeros', 'yes' )
    	    if(zeros=="no") :
    	        menuSettings.Check(Menu_Show_Zeros, 0)
    	        self.kmap[0].SetShowZeros(0)
    	        self.truthTable.SetShowZeros(0)
    	    else :
    			menuSettings.Check(Menu_Show_Zeros, 1)
    			self.kmap[0].SetShowZeros(1)
    			self.truthTable.SetShowZeros(1)
    	else :
    		menuSettings.Check(Menu_Show_Zeros, 0)
    		self.kmap[0].SetShowZeros(0)
    		self.truthTable.SetShowZeros(0)

        argv = sys.argv[1:]
        if len(argv) == 1 and type(argv[0]) == str and argv[0][0] in ['"', "'"]:
            argv[0] = eval(argv[0])
        if len(argv) == 1 and (os.path.isfile(argv[0]) or os.path.islink(argv[0] )):
            self.LoadFile(argv[0])
            self.currentFileName = argv[0]
            config.Write('CurrentFileName', self.currentFileName)
    	elif config.HasEntry('CurrentFileName') :
    	    self.currentFileName = config.Read('CurrentFileName', '' )
    	    if self.currentFileName != '' and (os.path.isfile(self.currentFileName) or os.path.islink(self.currentFileName) ) :
    	        print "Loading %s ..." % self.currentFileName
    	        self.LoadFile(self.currentFileName)
    	    else:
    	        self.currentFileName = None
    	else :
    	    self.currentFileName = None

        del config



    def OnSize(self, event):
        self.ProgressBarSize()
        self.Layout()


    def ProgressBarSize(self):
        rect = self.statusbar.GetFieldRect(1)
        #self.progress_bar.SetPosition((rect.x+2, rect.y+2))
    	#self.progress_bar.SetSize((rect.width-4, rect.height-4))
        self.progress_bar.SetDimensions(rect.x+1, rect.y+1, rect.width -2, rect.height -2)

    def OnLoad( self, event):
        filters = 'kmap files (*.kmap)|*.kmap|All files (*.*)|*.*'
        if self.currentFileName:
            StartDirectory = os.path.dirname(self.currentFileName)
        else:
            StartDirectory = '.'
        dialog = wx.FileDialog ( None, message = 'Save Table to File',
                  defaultDir=StartDirectory ,
                  wildcard = filters, style = wx.OPEN )

        if dialog.ShowModal() == wx.ID_OK:
            filePath = dialog.GetPath()
        else:
            filePath = []
        dialog.Destroy()

        if filePath:
            config =  wx.Config('Karnaugh Map Minimizer')
            config.Write('CurrentFileName', filePath)

            self.currentFileName = filePath

            self.LoadFile(filePath)

    def LoadFile( self, filePath):
        parser = perfTableParser()
        if parser.parseFile(self, filePath):
            self.UpdateData(parser)
            self.SetStatusText( os.path.basename(filePath),2 )


    def OnSave( self, event):
        if (self.currentFileName != None):
            self.truthTable.Write(self.currentFileName)
        else:
            self.OnSaveTo(event)

    def OnSaveTo( self, event=None):
        filters = 'kmap files (*.kmap)|*.kmap|All files (*.*)|*.*'
        if self.currentFileName:
            StartDirectory = os.path.dirname(self.currentFileName)
        else:
            StartDirectory = '.'
        dialog = wx.FileDialog ( None, message = 'Save Table to File',
                  defaultDir=StartDirectory ,
                  wildcard = filters, style = wx.SAVE )

        if dialog.ShowModal() == wx.ID_OK:
            selected = dialog.GetPath()
            FileNameExt = dialog.GetFilename().split('.').pop()
        else:
            selected = []
        dialog.Destroy()

        if selected:
            if FileNameExt != 'kmap':
                file = selected + '.kmap'
            else:
                file = selected

            self.truthTable.Write(file)
            self.currentFileName = file
            self.SetStatusText( os.path.basename(file),2 )

    def OnVarsChange( self, event ):
        for solution in self.solution:
            solution.DeleteAllItems()
        for solutionTxt in self.solutionTxt:
            solutionTxt.SetLabel('Solution:')
        for kmap in self.kmap:
            kmap.ClearSolutions()

        self.truthTable.SetVars(self.numberOfVariables.GetValue())
        for kmap in self.kmap:
            kmap.SetVars(self.numberOfVariables.GetValue())

    def OnOutsChange( self, event ):
        outs = self.numberOfOutputs.GetValue()
        self.truthTable.SetOuts(outs)

        nbpages = self.methodBook.GetPageCount()

        if(nbpages<outs):
            while nbpages<outs:
                self.AddPage(outs-1)
                nbpages = self.methodBook.GetPageCount()
        if(nbpages>outs):
            while nbpages>outs:
                self.methodBook.DeletePage(nbpages-1)
                del self.kmap[nbpages-1]
                del self.solution[nbpages-1]
                del self.solutionTxt[nbpages-1]
                nbpages = self.methodBook.GetPageCount()

    def OnFunction( self, event ):
        None

    def OnPaste( self, event ):
        if not wx.TheClipboard.IsOpened():  # may crash, otherwise
            do = wx.TextDataObject()
            wx.TheClipboard.Open()
            success = wx.TheClipboard.GetData(do)
            wx.TheClipboard.Close()
            if success:
                parser = perfTableParser()
                if parser.parseClipboard(self, do.GetText()):
                    parser.sweepVarNames = parser.variablesList[:-1]
                    MAX = max([value[-1] for value in parser.myArray if type(value[-1]) == float])
                    NbOutputs = int(ceil(log(MAX+1)/log(2)))
                    if NbOutputs >= 2:
                        savevar = parser.variablesList[-1]
                        parser.variablesList = parser.variablesList[:-1]
                        for index in range(NbOutputs-1,-1,-1):
                            newVar = (savevar[0]+'<'+str(index)+'>', float, 1)
                            parser.variablesList.append(newVar)
                    self.UpdateData(parser)
            else:
                return

    def ClearInterface(self):
        for solution in self.solution:
            solution.DeleteAllItems()
        for solutionTxt in self.solutionTxt:
            solutionTxt.SetLabel('Solution:')
        if self.Reduce:
            self.Equations.DeleteAllItems()
            self.EquationsTxt.Hide()
            self.Equations.Hide()
            self.Layout()
            self.Reduce = []
    def UpdateData (self, parser):
        for kmap in self.kmap:
            kmap.ClearSolutions()
        self.ClearInterface()
        # Update True Table and Karnaugh
        vars = len(parser.sweepVarNames)
        outs = len(parser.variablesList) - vars
        self.numberOfVariables.SetValue(vars)
        self.numberOfOutputs.SetValue(outs)

        # Update the number of Karnaugh table
        nbpages = self.methodBook.GetPageCount()
        if(nbpages<outs):
            while(nbpages<outs):
                self.AddPage(nbpages)
                nbpages = self.methodBook.GetPageCount()
        if(nbpages>outs):
            while(nbpages>outs):
                self.methodBook.DeletePage(nbpages-1)
                del self.kmap[nbpages-1]
                del self.solution[nbpages-1]
                del self.solutionTxt[nbpages-1]
                nbpages = self.methodBook.GetPageCount()
        # Update Karnaugh Table Label
        for pagenb in range(0, self.methodBook.GetPageCount()):
            self.methodBook.SetPageText(outs-1-pagenb,("Karnaugh map %s") % parser.variablesList[vars+pagenb][0])
        # Update True Table Size
        self.truthTable.SetVars(vars)
        self.truthTable.SetOuts(outs)
        for kmap in self.kmap:
            kmap.SetVars(vars)
        # Update True Table Columns Label
        col = 0
        for Varname, Type, Size in parser.variablesList:
            self.truthTable.SetColLabelValue(col,Varname)
            self.truthTable.SetColLabelSizefromLabel(col)
            col += 1
        # Update True Table data
        MAX = max([value[-1] for value in parser.myArray if type(value[-1]) == float])
        for row in range(0,int(pow(2,vars))):
            rowbit=[]
            conv = row
            for index in range(0,vars):
                rowbit.append(conv%2)
                conv = conv /2
            rowbit.reverse()
            line = [line for line in parser.myArray  if self.SameBitCode(rowbit, line)]
            try:
                line = line[0]
            except IndexError:
                raise Exception( 'Probably undefine value for row : %s' % rowbit )
            #for col in range(0,vars):
            #    self.truthTable.SetCellValueEvent(row, col,  str(int(colbit[col])))

            col = vars
            if MAX > 2:
                # MAX = 2 can not be perform as it is the don't care state
                value = line[-1]
                if type(value) == str or type(value) == unicode :
                    self.truthTable.SetCellValueEvent(row, vars+outs,  value)
                else:
                    self.truthTable.SetCellValueEvent(row, vars+outs,  str(int(value)))
            else:
                for value in line[vars:]:
                    self.truthTable.SetCellValueEvent(row, col,  str(int(value)))
                    col += 1

    def SameBitCode(self, a, b):
        for abit,bbit in zip(a,b):
            if abit != bbit:
                if abit != 'X' and bbit != 'X':
                    return False
        return True

    def OutputName(self, out):
        vars=self.numberOfVariables.GetValue()
        outs=self.numberOfOutputs.GetValue()
        Name = self.truthTable.GetColLabelValue(vars+outs-1-out)
        return Name

    def ColName(self, inputNb):
        Name = self.truthTable.GetColLabelValue(inputNb)
        return Name

    def AddPage(self, PageNumber):
        Karnaugh_Map = wx.NewId()
        # ##### Karnaugh Map Notebook page *****/

    	kmapPanel =  wx.Panel(self.methodBook, -1)
    	kmapSizer =  wx.BoxSizer(wx.VERTICAL)

    	# ##### Karnaugh map grid control *****/

    	self.kmap.append( KMap(kmapPanel, Karnaugh_Map, 4, wx.DefaultPosition, wx.Size(100,130), wx.SIMPLE_BORDER) )
    	kmapSizer.Add(self.kmap[PageNumber], 1, wx.EXPAND | wx.ALL, 5)

    	# ##### Solutions tree control *****/

    	#rightSizer.Add( wx.StaticText(mainPanel, -1, ("Solution:")), 0, wx.EXPAND | wx.TOP, 0)
    	self.solutionTxt.append(wx.StaticText(kmapPanel, Sol_Txt, ("Solution:")) )
    	kmapSizer.Add( self.solutionTxt[PageNumber], 0, wx.EXPAND | wx.TOP, 0)

    	#self.solution = wx.TreeCtrl(mainPanel, Sol_Tree, wx.DefaultPosition, wx.DefaultSize, wx.SIMPLE_BORDER | wx.TR_HAS_BUTTONS )
    	self.solution.append( wx.TreeCtrl(kmapPanel, Sol_Tree, wx.DefaultPosition, wx.DefaultSize, wx.SIMPLE_BORDER | wx.TR_HAS_BUTTONS ) )

    	#rightSizer.Add(self.solution, 1, wx.EXPAND | wx.TOP, 5)
    	kmapSizer.Add(self.solution[PageNumber], 1, wx.EXPAND | wx.TOP, 5)
    	kmapPanel.SetSizer(kmapSizer)
    	self.methodBook.AddPage(kmapPanel, ("Karnaugh map f%d") % PageNumber)

    	# Event

    	self.Bind(grid.EVT_GRID_CMD_CELL_CHANGE, self.OnKMapChange, id=Karnaugh_Map)

    	# config
    	config =  wx.Config(("Karnaugh Map Minimizer"))
    	if config.HasEntry('Cell_Adresses') :
    		adresses = config.Read(("Cell_Adresses"), 'yes')
    		if(adresses==("no")) :
    			self.kmap[-1].SetCellAdresses(0)
    		else :
    			self.kmap[-1].SetCellAdresses(1)
    	else :
    		self.kmap[-1].SetCellAdresses(1)

    	if config.HasEntry('Show_Zeros') :
    	    zeros = config.Read('Show_Zeros', 'yes' )
    	    if(zeros=="no") :
    	        self.kmap[-1].SetShowZeros(0)
    	    else :
    			self.kmap[-1].SetShowZeros(1)
    	else :
    		self.kmap[-1].SetShowZeros(0)

        del config


    def OnTruthTChange( self, event ):
        vars = self.numberOfVariables.GetValue()
        outs = self.numberOfOutputs.GetValue()
        OutCol = outs-1 - (event.GetCol() - vars)
        if OutCol >= 0 and OutCol < self.numberOfOutputs.GetValue():
            # Only column for outputs
            self.solution[OutCol].DeleteAllItems()
            self.solutionTxt[OutCol].SetLabel('Solution:')
            if self.Reduce:
                self.Equations.DeleteAllItems()
                self.Reduce = []
            self.kmap[OutCol].ClearSolutions()

            self.kmap[OutCol].Set(event.GetRow(), self.truthTable.GetCellValue(event.GetRow(), event.GetCol()))
    def OnTruthTLabelChange( self, event):
        vars = self.numberOfVariables.GetValue()
        outs = self.numberOfOutputs.GetValue()
        Row = event.GetRow()
        Col = event.GetCol()
        OutCol = outs-1 - (Col - vars)
        if Col >= 0 :
            ColLabel = self.truthTable.GetColLabelValue(Col)
            if OutCol >= 0 and OutCol < self.numberOfOutputs.GetValue():
                # Only column for outputs
                self.methodBook.SetPageText(OutCol,("Karnaugh map %s") % ColLabel)

    def OnKMapChange( self, event ):
        vars = self.numberOfVariables.GetValue()
        outs = self.numberOfOutputs.GetValue()
        PageNb = self.kmap.index(event.GetEventObject())
        self.solution[PageNb].DeleteAllItems()
        self.solutionTxt[PageNb].SetLabel('Solution:')
        if self.Reduce:
            self.Equations.DeleteAllItems()
            self.Reduce = []
        self.kmap[PageNb].ClearSolutions()

        self.truthTable.SetCellValueEvent(self.kmap[PageNb].GetMapValue(event.GetCol(), event.GetRow()), vars+(outs-1-PageNb), self.kmap[PageNb].GetCellValue(event.GetRow(), event.GetCol()))
    def OnSolve( self, event ):

        # Disable Interface entries
        #self.Disable()
##        self.methodBook.Disable()
##        self.truthTable.Disable()
        self.SetStatusText( ( "Solving, please wait..." ) )
        self.progress_bar.Show()
        self.SolveLeft = self.numberOfOutputs.GetValue()
        self.solvethread = SolveTask(self)
        self.solvethread.start()
        #self.solvethread.run()

    def OnIdle(self, event):
        try:
            time()-self.LastTime
        except:
            self.LastTime = time()
        TimeInterval = 5
        try:
            if time()-self.LastTime > TimeInterval:
                self.LastTime = time()
                if self.solvethread:
                    outs = self.numberOfOutputs.GetValue()
                    if self.solvethread.is_alive():
                        NbWorkLeft = self.SolveLeft
                        wx.CallAfter(self.progress_bar.SetValue, (outs-NbWorkLeft)*100/outs)
##                    else:
##                    	if self.SolveLeft == 0:
##                    	    self.SetStatusText( ( "Karnaugh map solved!" ) )
##                    	    self.progress_bar.Hide()

                    while not self.result_queue.empty():
                        try:
                            Kmap = self.result_queue.get()
                            self.Updateparent(Kmap.GetSolutions(), Kmap.out)
                            self.SolveLeft -= 1
                            if self.SolveLeft == 0:
                                vars = self.numberOfVariables.GetValue()
                                self.Reduce = ReduceSol(self, self.GetSolutions(), vars, outs)
                                self.Reduce.reduce()
                                for out in range(outs):
                                    self.solution[out].DeleteAllItems()
                                    self.Updateparent(self.Reduce.AllSolutions[out],out)
                                self.UpdateEquations()
                                self.SetStatusText( ( "Karnaugh map solved!" ) )
                                self.progress_bar.Hide()
##                        except Empty:
##                            pass
                        except:
                            traceback.print_exc()
                            pass
        except:
            traceback.print_exc()
            pass

        event.Skip()

    def solutionStr(self, values, OP ='.', inv=False):
        outs = [len(out) for out in self.GetSolutions()]
        vars=self.numberOfVariables.GetValue()
        if OP == '.':
            b = ''  # A, B, C, D
        else:
            b = '('

        a = ''  # All the rest
        for i in range(0, len(values)):
            if values[i] != 2:
                if i < vars:
                    # Intputs
                    InvStr = ''
                    if ((values[i]==0) and (self.solveSOP)) or ((values[i]==1) and (not self.solveSOP)):
                        InvStr = '|'
                    if inv :
                        if InvStr == '':
                            InvStr = '|'
                        else:
                            InvStr = ''

                    a += InvStr+self.ColName(i)+OP
                elif i >=vars and i < sum(outs)+vars:
                    # Output Equations
                    for outindex in range(len(outs)):
                        if i >= vars+sum(outs[:outindex]) and i < vars+sum(outs[:outindex+1]):
                            InvStr = ''
                            if(values[i]==0):
                                InvStr = '|'
                            if inv :
                                if InvStr == '':
                                    InvStr = '|'
                                else:
                                    InvStr = ''
                            a += InvStr
                            SolName=self.OutputName(outindex)
                            if SolName.endswith('>'):
                               SolName  = SolName.replace('<','').replace('>','')
                            a += '%s_Equ%s' % (SolName,str(i- (vars+sum(outs[:outindex])) ))+OP

                elif i >= sum(outs)+vars:
                    # Equations
                    InvStr = ''
                    if(values[i]==0):
                        InvStr = '|'
                    if inv :
                        if InvStr == '':
                            InvStr = '|'
                        else:
                            InvStr = ''
                    a += InvStr
                    a += 'Equ%s' % str(i- (sum(outs)+vars) ) + OP

        b=b+a[0:-1]


        if OP == '.' and b == '':
            b='1'
        elif OP == '+':
            if b == '(':
                b='0'
            else:
                b = b + ')'
        return b

    def Dependency(self):
        AllSolutions = self.Reduce.AllSolutions
        outsList = [len(out) for out in self.GetSolutions()]
        vars=self.numberOfVariables.GetValue()
        outs = self.numberOfOutputs.GetValue()
        b = []
        a= ''
        for out in range(0,len(AllSolutions)):
            solutionsList0 = AllSolutions[out]
            NbInputs0 = len(solutionsList0)
            if out >= outs:
                #Equations
                NbInputs0 = 1
                print 'Equation...'
            for index, iter in enumerate(solutionsList0):
                if type(iter) != list:
                    values = iter.values
                    self.kmap[out].AddSolution(values)
                else:
                    values = iter

                for i in range(vars, sum(outsList)+vars):
                    # Outputs Equations
                    if values[i] != 2:
                        # Used
                        a= ''
                        # Do we use the Value or the complement
                        InvStr = ''
                        if values[i]==0:
                            InvStr = '|'
                        if NbInputs0 == 1:
                            InvStr = InvStr
                        elif (int(math.log(NbInputs0-1,4)) % 2) == 0:
                            if self.Reduce.Length(values) == 1:
                                if InvStr == '':
                                    InvStr = '|'
                                else:
                                    InvStr = ''
                            else:
                                InvStr = InvStr
                        elif (int(math.log(NbInputs0-1,4)) % 2) != 0:
                            if self.Reduce.Length(values) > 1:
                                if InvStr == '':
                                    InvStr = '|'
                                else:
                                    InvStr = ''

                        for outindex in range(len(outsList)):
                            if i >= vars+sum(outsList[:outindex]) and i < vars+sum(outsList[:outindex+1]):
                                # Locate which Output
                                solutionsList1 = AllSolutions[outindex]
                                NbInputs1 = len(solutionsList1)
                                SolName=self.OutputName(outindex)
                                if SolName.endswith('>'):
                                   SolName  = SolName.replace('<','').replace('>','')

                                if NbInputs1 == 1 and (InvStr==''):
                                    a = ''
                                elif NbInputs1 == 1 and (InvStr=='|'):
                                    a = '%s_Equ%s' % (SolName, str(i- (vars+sum(outsList[:outindex])) ))
                                    a = 'INV |' + a + '=' + a
                                elif (int(math.log(NbInputs1-1,4)) % 2) == 0 and (InvStr==''):
                                    # We generate the complement and we need to normal
                                    a = '%s_Equ%s' % (SolName, str(i- (vars+sum(outsList[:outindex])) ))
                                    a = 'INV ' + a + '=|' + a
                                elif (int(math.log(NbInputs1-1,4)) % 2) != 0 and (InvStr=='|'):
                                    # We generate the normal and we need the complement
                                    a = '%s_Equ%s' % (SolName, str(i- (vars+sum(outsList[:outindex])) ))
                                    a = 'INV |' + a + '=' + a

                    if a != '' and not a in b:
                        b.append(a)


        return b

    def CountEqu(self, solutionsList):
        def GetValue(solutionsList):
            if solutionsList:
                if type(solutionsList[0]) != list:
                    NbList = [self.Reduce.Length(sol.values) for sol in solutionsList]
                else:
                    NbList = [self.Reduce.Length(sol) for sol in solutionsList]
                return NbList
            else:
                return []
        if self.Reduce:
            NbList = GetValue(solutionsList)
        else:
            self.Reduce = ReduceSol(self, self.GetSolutions(),1,1)
            NbList = GetValue(solutionsList)
            self.Reduce = []
        return NbList

    def UpdateEquations(self):
        self.Equations.DeleteAllItems()
        self.Equations.AddRoot('')

        TreeRoot = self.Equations.GetRootItem()

        #print len(self.Reduce.AllSolutions[-1])
        #print [self.solutionStr(values) for values in self.Reduce.AllSolutions[-1]]
        if len(self.Reduce.AllSolutions) > self.numberOfOutputs.GetValue():
            Txt = 'Equations: '
            NbList = self.CountEqu(self.Reduce.AllSolutions[-1])
            for index in range(max(NbList),1,-1):
                Nb = NbList.count(index)
                if Nb > 0:
                    if(self.solveSOP):
                        Txt = Txt + ' %s*And%s' % (Nb,index)
                    else:
                        Txt = Txt + ' %s*Or%s' % (Nb,index)
            self.EquationsTxt.SetLabel(Txt)

            for index, values in enumerate(self.Reduce.AllSolutions[-1]):
                if(self.solveSOP):
                    b = 'Equ%s =' % str(index) + self.solutionStr(values, '.')
                else:
                    b = 'Equ%s =' % str(index) + self.solutionStr(values, '+')
                #bData = SolveTreeItemData()
                bData = wx.TreeItemData()
                bData.SetData(values)
                self.Equations.AppendItem(TreeRoot, b, -1, -1, bData)

            #print [self.solutionStr(self.Equations.GetItemData(item).GetData()) for item in walk_branches(self.Equations,TreeRoot)]
            self.Equations.Show()
            #self.Equations.Expand(TreeRoot)
            self.EquationsTxt.Show()
            self.Layout()

    def Updateparent(self, solutionsList, out):
        SolName = self.OutputName(out)
        s="%s = " % SolName

        self.solution[out].DeleteAllItems()
        self.solution[out].AddRoot(s)

        TreeRoot = self.solution[out].GetRootItem()
        if len(solutionsList) >1 :
            if(self.solveSOP):
                Txt = 'Solution: Or' + str(len(solutionsList))
            else:
                Txt = 'Solution: And' + str(len(solutionsList))
        else:
            Txt = 'Solution:'

        if solutionsList:
            NbList = self.CountEqu(solutionsList)
            for index in range(max(NbList),1,-1):
                Nb = NbList.count(index)
                if Nb > 0:
                    if(self.solveSOP):
                        Txt = Txt + ' %s*And%s' % (Nb,index)
                    else:
                        Txt = Txt + ' %s*Or%s' % (Nb,index)

        self.solutionTxt[out].SetLabel(Txt)

        for index, iter in enumerate(solutionsList):
            if type(iter) != list:
                values = iter.values
                self.kmap[out].AddSolution(values)
            else:
                values = iter

            if(self.solveSOP):
                b=self.solutionStr(values, '.')
            else:
                b = self.solutionStr(values, '+')

            s+=b

            #bData = SolveTreeItemData()
            bData = wx.TreeItemData()
            bData.SetData(values)
            self.solution[out].AppendItem(TreeRoot, '%s_Equ%s =' % (SolName,str(index)) + b, -1, -1, bData)

            if(iter!=solutionsList[-1]):
                if(self.solveSOP):
                    s += ' + '
                else:
                    s += ' . '
        if(s==("%s = "  % SolName)):
			    if(self.solveSOP):
			        s=("%s = 0"  % SolName)
			    else:
			        s=("%s = 1"  % SolName)

        self.solution[out].Expand(TreeRoot)
        self.solution[out].SetItemText(TreeRoot, s[:256])



    def GetSolutions(self):
        """ Get the solution from the tree
            For each Outputs [Solution0, ..., SolutionN]
            For each Solution [Var0, ..., VarN]
        """
        outs = self.numberOfOutputs.GetValue()
        AllSolutions = []
        if self.Reduce:
            for out in range(0,outs):
                AllSolutions.append(list(self.Reduce.AllSolutions[out]))
            return list(AllSolutions)
        else:
            for out in range(0,outs):
                tree = self.solution[out]
                root = tree.GetRootItem()
                SolutionList = []
                for item in walk_branches(tree,root):
                    sol=list((self.solution[out].GetItemData(item)).GetData());
                    SolutionList.append(sol)
                AllSolutions.append(list(SolutionList))
        return list(AllSolutions)

    def OnSolSelect( self, event ):
        solutions = self.GetSolutions()
        outs = [len(out) for out in solutions]
        vars=self.numberOfVariables.GetValue()
        PageNb = self.solution.index(event.GetEventObject())
        if(self.solution[PageNb].GetRootItem()!=event.GetItem()):
            sol=(self.solution[PageNb].GetItemData(event.GetItem())).GetData();
            if len(sol) == vars:
                self.kmap[PageNb].SelectSolution(sol)
            else:
                if self.Reduce:

                    self.kmap[PageNb].SelectSolution(self.Reduce.GetSimpleValue(sol))
                    ValueList = self.Reduce.GetSubValues(sol)
                    tree = self.Equations
                    root = tree.GetRootItem()
                    tree.UnselectAll()
                    for item in walk_branches(tree,root):
                        if tree.GetItemData(item).GetData() in ValueList:
                            tree.SelectItem(item)
        else :
            self.kmap[PageNb].ClearSelection()

    def OnSolutionTypeChange( self, event ):
        if(event.GetSelection()==0):
            self.solveSOP=1
            self.ClearInterface()
        if(event.GetSelection()==1):
            self.solveSOP=0
            self.ClearInterface()

    def OnSaveSol(self, event):
        filters = 'kmapSolultion files (*.ksol)|*.ksol|All files (*.*)|*.*'
        if self.currentFileName:
            StartDirectory = os.path.dirname(self.currentFileName)
        else:
            StartDirectory = '.'
        dialog = wx.FileDialog ( None, message = 'Save Solution to File',
                  defaultDir=StartDirectory ,
                  wildcard = filters, style = wx.SAVE )

        if dialog.ShowModal() == wx.ID_OK:
            selected = dialog.GetPath()
            FileNameExt = dialog.GetFilename().split('.').pop()
        else:
            selected = []
        dialog.Destroy()

        if selected:
            if FileNameExt != 'ksol':
                file = selected + '.ksol'
            else:
                file = selected

            self.WriteSol(file)

    def WriteSol( self, filePath):
        """
        Genere un fichier a partir du resultat
        """

        fh = open(filePath, "w")

        fh.write("%Generated by Kmapreducer\n\n")
        # @TODO Rajouter la date et l'heure
        fh.write("\n")

        AllSolutions = self.GetSolutions()
        outs = self.numberOfOutputs.GetValue()
        OUTNAMES = []
        INNAMES = []
        InvEquXList = []
        for outindex in range(0,outs):
            Name = self.OutputName(outindex)
            if Name in [Output[0] for Output in OUTNAMES]:
                print 'Duplicate Names %s' % (Name)
            else:
                if Name.endswith('>'):
                    BaseName = Name[:Name.find('<')]
                    BusIndex = eval(Name[Name.find('<')+1:-1])
                else:
                    BaseName = Name
                    BusIndex = -1
                if BaseName in [Output[0] for Output in OUTNAMES]:
                    for Output in OUTNAMES:
                        if Output[0] == BaseName:
                            if Output[1] < BusIndex:
                                Output[1] = BusIndex
                            elif Output[2] > BusIndex:
                                Output[2] = BusIndex
                            break
                else:
                    OUTNAMES.append([BaseName,BusIndex,BusIndex])

        vars = self.numberOfVariables.GetValue()
        for inputindex in range(0,vars):
            Name = self.ColName(inputindex)
            if Name in [Input[0] for Input in INNAMES]:
                print 'Duplicate Names %s' % (Name)
            else:
                if Name.endswith('>'):
                    BaseName = Name[:Name.find('<')]
                    BusIndex = eval(Name[Name.find('<')+1:-1])
                else:
                    BaseName = Name
                    BusIndex = -1
                if BaseName in [Input[0] for Input in INNAMES]:
                    for Input in INNAMES:
                        if Input[0] == BaseName:
                            if Input[1] < BusIndex:
                                Input[1] = BusIndex
                            elif Input[2] > BusIndex:
                                Input[2] = BusIndex
                            break
                    print Name
                    print INNAMES
                else:
                    INNAMES.append([BaseName,BusIndex,BusIndex])


        for input in INNAMES:
            if input[1] != input[2]:
                Str = input[0]+'<'+str(input[1])+':'+str(input[2])+'>'
            elif input[1] >-1:
                Str = input[0]+'<'+str(input[1])+'>'
            else:
                Str = input[0]
            fh.write('IN %s\n' % Str)

        fh.write('\n')

        for Equ in self.Dependency():
            fh.write(Equ+'\n')
        fh.write('\n')

        for out in range(0,outs):
            solutionsList = AllSolutions[out]
            SolName = self.OutputName(out)
            s="%s=" % SolName
            if len(solutionsList) >1 :
                if(self.solveSOP):
                    Txt = 'Or' + str(len(solutionsList))
                else:
                    Txt = 'And' + str(len(solutionsList))
            else:
                Txt = ''
            EquNbEntriesList = self.CountEqu(solutionsList)
            for index, iter in enumerate(solutionsList):
                NbInputs = len(solutionsList)
                if type(iter) != list:
                    values = iter.values
                    self.kmap[out].AddSolution(values)
                else:
                    values = iter

                if SolName.endswith('>'):
                    Name = SolName.replace('<','').replace('>','')
                    EquName = '%s_Equ%s' % (Name,str(index))
                else:
                    EquName = '%s_Equ%s' % (SolName,str(index))
                b = EquName

                if(self.solveSOP):
                    if (EquNbEntriesList[index]>1):
                        if NbInputs ==1:
                            EquStr = 'NOR%i %s=%s' % (EquNbEntriesList[index],EquName,self.solutionStr(values, '+', True))
                        elif (int(math.log(NbInputs-1,4)) % 2) == 0:
                            EquStr = 'NAND%i |%s=%s' % (EquNbEntriesList[index],EquName,self.solutionStr(values, '.'))
                        else:
                            EquStr = 'NOR%i %s=%s' % (EquNbEntriesList[index],EquName,self.solutionStr(values, '+', True))
                    else:
                        if NbInputs ==1:
                            EquStr = 'None %s=%s' % (EquName,self.solutionStr(values, '.'))
                        elif (int(math.log(NbInputs-1,4)) % 2) == 0:
                            EquStr = 'None |%s=%s' % (EquName,self.solutionStr(values, '+', True))
                        else:
                            EquStr = 'None %s=%s' % (EquName,self.solutionStr(values, '.'))
                else:
                    if EquNbEntriesList[index]>1:
                        if NbInputs ==1:
                            EquStr = 'NAND%i %s=%s' % (EquNbEntriesList[index],EquName,self.solutionStr(values, '.', True))
                        elif (int(math.log(NbInputs-1,4)) % 2) == 0:
                            EquStr = 'NOR%i |%s=%s' % (EquNbEntriesList[index],EquName,self.solutionStr(values, '+'))
                        else:
                            EquStr = 'NAND%i %s=%s' % (EquNbEntriesList[index],EquName,self.solutionStr(values, '.', True))
                    else:
                        if NbInputs ==1:
                            EquStr = 'None %s=%s' % (EquName,self.solutionStr(values, '+'))
                        elif (int(math.log(NbInputs-1,4)) % 2) == 0:
                            EquStr = 'None |%s=%s' % (EquName,self.solutionStr(values, '.', True))
                        else:
                            EquStr = 'None %s=%s' % (EquName,self.solutionStr(values, '+'))

                #Search for EquX
                Formula = EquStr.split()[1].split('=')[1]
                if Formula.find('+') > -1:
                    FormulaList = Formula.split('+')
                else:
                    FormulaList = Formula.split('.')
                for Entrie in FormulaList:
                    if Entrie.startswith('Equ') and not(Entrie in InvEquXList):
                        InvEquXList.append(Entrie)

                fh.write('%s\n' % EquStr)

                s+=b


                if(iter!=solutionsList[-1]):
                    if(self.solveSOP):
                        s += '+'
                    else:
                        s += '.'
            if(s==("%s="  % SolName)):
			    if(self.solveSOP):
			        s=("%s=0"  % SolName)
			    else:
			        s=("%s=1"  % SolName)

            if (len(solutionsList)>1):
                if(self.solveSOP):
                    s = 'OR%i %s' % (len(solutionsList),s)
                else:
                    s = 'AND%i %s' % (len(solutionsList),s)
            else:
                s = 'None %s' % (s)
            fh.write(s+'\n\n')


        if len(self.Reduce.AllSolutions) > self.numberOfOutputs.GetValue():
            Txt = ''
            NbList = self.CountEqu(self.Reduce.AllSolutions[-1])

            for index, values in enumerate(self.Reduce.AllSolutions[-1]):
                if(self.solveSOP):
                    b = 'NAND%i |Equ%s=' % (NbList[index], str(index)) + self.solutionStr(values, '.')
                else:
                    b = 'NOR%i |Equ%s=' % (NbList[index], str(index)) + self.solutionStr(values, '+')
                fh.write(b+'\n')

                #Search for EquX
                Formula = b.split()[1].split('=')[1]
                if Formula.find('+') > -1:
                    FormulaList = Formula.split('+')
                else:
                    FormulaList = Formula.split('.')
                for Entrie in FormulaList:
                    if Entrie.startswith('Equ') and not(Entrie in InvEquXList):
                        InvEquXList.append(Entrie)

            fh.write('\n')

        for EquX in InvEquXList:
            fh.write('INV %s=|%s\n' % (EquX,EquX))

        if InvEquXList:
            fh.write('\n')
        for out in OUTNAMES:
            if out[1] != out[2]:
                Str = out[0]+'<'+str(out[1])+':'+str(out[2])+'>'
            elif out[1] >-1:
                Str = out[0]+'<'+str(out[1])+'>'
            else:
                Str = out[0]
            fh.write('OUT %s\n' % Str)

        fh.close()

    def OnQuit( self, event ):
        for worker in self.WorkerList:
            worker.terminate()

        self.Close(True)


    def OnLangCroatian( self, event ):
        config =  wx.Config(("Karnaugh Map Minimizer"))
        config.Write(("Language"), ("hr"))
        #delete config
        wx.MessageBox( _( "You have to restart the program for self change to take effect." ),
			_( "Restart required" ), wx.OK | wx.ICON_INFORMATION, self )

    def OnLangDefault( self, event ):
        config =  wx.Config(("Karnaugh Map Minimizer"))
        config.Write(wx.T("Language"), (""))
        #delete config
        wx.MessageBox( _( "You have to restart the program for self change to take effect." ),
			_( "Restart required" ), wx.OK | wx.ICON_INFORMATION, self )

    def OnCellAdresses( self, event ):
        config =  wx.Config(("Karnaugh Map Minimizer"))
        outs = self.numberOfOutputs.GetValue()
        for out in range(0, outs):
            if(self.kmap[out].GetCellAdresses()):
                config.Write(("Cell_Adresses"), ("no"))
                self.kmap[out].SetCellAdresses(0)
            else:
                config.Write(("Cell_Adresses"), ("yes"))
                self.kmap[out].SetCellAdresses(1)
        del config

    def OnShowZeros( self, event ):
        config =  wx.Config(("Karnaugh Map Minimizer"))
        outs = self.numberOfOutputs.GetValue()
        if(self.truthTable.GetShowZeros()):
            config.Write(("Show_Zeros"), ("no"))
            self.truthTable.SetShowZeros(0)
        else:
            config.Write(("Show_Zeros"), ("yes"))
            self.truthTable.SetShowZeros(1)
        for out in range(0, outs):
            if(self.kmap[out].GetShowZeros()):
                self.kmap[out].SetShowZeros(0)
            else:
                self.kmap[out].SetShowZeros(1)
        del config

    def OnAbout( self, event ):
        wx.MessageBox( ( "self is a program for minimizing boolean functions using Karnaugh maps method."
	"\n\nCopyright (C) 2013. Bertrand PIGEARD""\n\nBase on code from Copyright (C) 2005. Robert Kovacevic"),
( "About Karnaugh Map Minimizer" ), wx.OK | wx.ICON_INFORMATION, self )

class SolveTreeItemData(wx.TreeItemData):
    def __init__(self):
        wx.TreeItemData(self)
