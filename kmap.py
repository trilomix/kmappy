import wx
from wx import grid as gridlib
#from wx import font
from math import ceil, floor, log
from threading import Lock
import random

##BEGIN_EVENT_TABLE( KMap, wx.Grid )
##	EVT_GRID_CELL_RIGHT_CLICK( KMap::DisplayPopup )
##	EVT_GRID_CELL_CHANGE(KMap::OnCellChange)
##	EVT_MENU(KMAP_MENU_SET1, KMap::OnMenuSet1)
##	EVT_MENU(KMAP_MENU_SET0, KMap::OnMenuSet0)
##	EVT_MENU(KMAP_MENU_SETDC, KMap::OnMenuSetDC)
##	EVT_MENU(KMAP_MENU_SETRAND, KMap::OnMenuSetRand)
##END_EVENT_TABLE()
[
KMAP_MENU_SET1,
KMAP_MENU_SET0, 
KMAP_MENU_SETDC, 
KMAP_MENU_SETRAND
] = [wx.NewId() for i in range(4)]



class KMap( gridlib.Grid):
    def __init__(self, parent, id=-1, vars=4, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0, name=''):
        gridlib.Grid.__init__(self, parent, id, pos, size, style, name)
        
        self.Lock = Lock()
        self.width=pow(2, ceil(vars/2))
    	self.height=pow(2, floor(vars/2))
    	
    	self.kmapValues = {}
    	self.menuRow = 0
    	self.menuCol = 0
    	self.showZeros=0
    	
    	self.CreateGrid( self.height,self.width)
    	
    	self.SetVars(vars)
    	
    	self.EnableDragGridSize(0)
    	
    	self.Bind(gridlib.EVT_GRID_CELL_CHANGE, self.OnCellChange)
    	
    	self.Bind(gridlib.EVT_GRID_CELL_RIGHT_CLICK, self.DisplayPopup )
    	
    	self.stateMenu =  wx.Menu()
    	    	
    	self.stateMenu.Append(KMAP_MENU_SET1, ("Set to 1"))
    	self.stateMenu.Append(KMAP_MENU_SET0, ("Set to 0"))
    	self.stateMenu.Append(KMAP_MENU_SETDC, ("Set to \"don't care\""))
    	self.stateMenu.AppendSeparator()
    	self.stateMenu.Append(KMAP_MENU_SETRAND, ("Set randomly"))
    
    	self.Bind(wx.EVT_MENU, self.OnMenuSet1,    id=KMAP_MENU_SET1)
    	self.Bind(wx.EVT_MENU, self.OnMenuSet0,    id=KMAP_MENU_SET0)
    	self.Bind(wx.EVT_MENU, self.OnMenuSetDC,   id=KMAP_MENU_SETDC)
    	self.Bind(wx.EVT_MENU, self.OnMenuSetRand, id=KMAP_MENU_SETRAND)
    	
    	self.SetDefaultCellAlignment(wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)
    	
    	self.useCellAdresses=1;
    	self.SetDefaultRenderer( KMapGridCellRenderer())
    	
    	self.ForceRefresh()

    def SetCellValue(self, i, j, value):
        self.Lock.acquire()
        val = gridlib.Grid.SetCellValue(self, i, j, value)
        self.Lock.release()
        return val
    def AddSolution(self, sol):
	    for i in range(0, self.height):
	        for j in range(0,self.width):
	            m=self.GetMapBoolValue(j, i)
	            is_var = 1
	            for k in range(0, len(sol)):
	                if( (sol[k]!=m[k]) & (sol[k]!=2) ): 
	                    is_var=0
	            if(is_var==1):
    			 
    				c=self.GetCellBackgroundColour(i, j)
    				if (c.Red()-20)>0 and (c.Green()-15)>0:
    				    self.SetCellBackgroundColour(i, j, wx.Colour(c.Red()-20, c.Green()-15, c.Blue()))
    				elif (c.Green()-15)>0:
    				    self.SetCellBackgroundColour(i, j, wx.Colour(0, c.Green()-15, c.Blue()))
    				else:
    				    self.SetCellBackgroundColour(i, j, wx.Colour(0, 0, c.Blue()))
	    self.ForceRefresh()
    
    def SelectSolution(self, sol):
     
    	self.ClearSelection()
    	for i in range(0, self.height):
    	 
    		for j in range(0, self.width):
    		 
    			m=self.GetMapBoolValue(j, i)
    			is_var=1
    			for k in range(0, len(sol)):
    			 
    				if( (sol[k]!=m[k]) & (sol[k]!=2) ): is_var=0
    			 
    			
    			if(is_var==1):
    			 
    				self.SelectBlock(i, j, i, j, 1)
    			 
    		 
    	 
    	self.ForceRefresh()
     
    
    def ClearSolutions(self):
     
    	for i in range(0, self.GetNumberRows()):
    	 
    		for j in range(0, self.GetNumberCols()):
    		 
    			if( ((j/4+i/4)%2)==1): 
    			    self.SetCellBackgroundColour(i, j, wx.Colour(245,245,245))
    			else: 
    			    self.SetCellBackgroundColour(i, j, self.GetDefaultCellBackgroundColour())
    		 
    	 
    	self.ForceRefresh()
     
    
    def DisplayPopup(self, event):
     
    	self.menuRow=event.GetRow()
    	self.menuCol=event.GetCol()
    	self.SetGridCursor(self.menuRow, self.menuCol)
    	self.popup=event.GetPosition()
    	self.PopupMenu(self.stateMenu, event.GetPosition())
     
    
    def OnCellChange(self, event=None, Row=0, Col=0):
        if event:
            Row = event.GetRow()
            Col = event.GetCol()
        if( (self.GetCellValue(Row, Col)!=("1")) &
    		(self.GetCellValue(Row, Col)!=("")) &
    		(self.GetCellValue(Row, Col)!=("0")) ):
    		    self.SetCellValue(Row, Col, ("?"))
    	
    	if(self.GetCellValue(Row, Col)==("")):
    		if(self.showZeros): self.SetCellValue(Row, Col, ("0"))
    	
    	if(self.GetCellValue(Row, Col)==("0")):
    		if(not self.showZeros): 
    		    self.SetCellValue(Row, Col, (""))
    	
    	if event:
    	    event.Skip(1)
     
    
    def OnMenuSet1(self, event):
     
    	if(self.IsSelection()):
    	 
    		for i in range(0, self.height):
    		 
    			for j in range(0, self.width):
    			 
    				if(self.IsInSelection(i, j)): 
    				 
    					self.SetCellValue(i, j, ("1"))
    					evt = wx.grid.GridEvent(self.GetId(), wx.grid.wxEVT_GRID_CELL_CHANGE, self, i, j)
    					self.GetEventHandler().ProcessEvent(evt)
    					#self.OnCellChange(None, i, j )
    	else:
    	 
    		self.SetCellValue(self.menuRow, self.menuCol, ("1"))
    		evt = wx.grid.GridEvent(self.GetId(), wx.grid.wxEVT_GRID_CELL_CHANGE, self, self.menuRow, self.menuCol)
    		self.GetEventHandler().ProcessEvent(evt) 
    		#self.OnCellChange(None, self.menuRow, self.menuCol )
    
    def OnMenuSet0(self, event):
     
    	if(self.IsSelection()):
    	 
    		for i in range(0, self.height):
    		 
    			for j in range(0, self.width):
    			 
    				if(self.IsInSelection(i, j)):
    				 
    					if(self.showZeros):
    						self.SetCellValue(i, j, ("0"))
    					else:
    						self.SetCellValue(i, j, (""))
    					evt = wx.grid.GridEvent(self.GetId(), wx.grid.wxEVT_GRID_CELL_CHANGE, self, i, j)
    					self.GetEventHandler().ProcessEvent(evt)
    					#self.OnCellChange(None, i, j )
    	else:
    	    if(self.showZeros): 
    		    self.SetCellValue(self.menuRow, self.menuCol, ("0"))
    	    else: 
    		    self.SetCellValue(self.menuRow, self.menuCol, (""))
    	    evt = wx.grid.GridEvent(self.GetId(), wx.grid.wxEVT_GRID_CELL_CHANGE, self, self.menuRow, self.menuCol)
    	    self.GetEventHandler().ProcessEvent(evt) 
    	    #self.OnCellChange(None, self.menuRow, self.menuCol )
    
    def OnMenuSetDC(self, event):
     
    	if(self.IsSelection()):
    	 
    		for i in range(0, self.height):
    		 
    			for j in range(0, self.width-1):
    			 
    				if(self.IsInSelection(i, j)):
    				 
    					self.SetCellValue(i, j, ("?"))
    					evt = wx.grid.GridEvent(self.GetId(), wx.grid.wxEVT_GRID_CELL_CHANGE, self, i, j)
    					self.GetEventHandler().ProcessEvent(evt) 
    					#self.OnCellChange(None, i, j )
    	else:
    	 
    		self.SetCellValue(self.menuRow, self.menuCol, ("?"))
    		evt = wx.grid.GridEvent(self.GetId(), wx.grid.wxEVT_GRID_CELL_CHANGE, self, self.menuRow, self.menuCol)
    		self.GetEventHandler().ProcessEvent(evt) 
    		#self.OnCellChange(None, self.menuRow, self.menuCol )

    def OnMenuSetRand(self, event):
     
    	if(self.IsSelection()):
    	    for i in range(0, self.height):
    	        for j in range(0, self.width):
    	            if(self.IsInSelection(i, j)):
    	                if(random.random()>=0.5):
    						self.SetCellValue(i, j, ("1"))
    	                else:
    	                    if(self.showZeros): 
    						    self.SetCellValue(i, j, ("0"))
    	                    else: 
    						    self.SetCellValue(i, j, (""))
    					
    	                evt = wx.grid.GridEvent(self.GetId(), wx.grid.wxEVT_GRID_CELL_CHANGE, self, i, j)
    	                self.GetEventHandler().ProcessEvent(evt) 
    	                #self.OnCellChange(None, i, j )
    	else:
    	 
    		if(random.random()>=0.5):
    			self.SetCellValue(self.menuRow, self.menuCol, ("1"))
    		else:
    		 
    			if(self.showZeros): 
    			    self.SetCellValue(self.menuRow, self.menuCol, ("0"))
    			else: 
    			    self.SetCellValue(self.menuRow, self.menuCol, (""))
    		 
    		evt = wx.grid.GridEvent(self.GetId(), wx.grid.wxEVT_GRID_CELL_CHANGE, self, self.menuRow, self.menuCol)
    		self.GetEventHandler().ProcessEvent(evt) 
    		#self.OnCellChange(None, self.menuRow, self.menuCol )
    	 
     
    
    def SetShowZeros(self, s):
        self.showZeros=s
    	for i in range(0, self.GetNumberCols() ):
    	 
    		for j in range(0, self.GetNumberRows() ):
    		 
    			if(self.showZeros & (self.GetCellValue(j, i)==(""))): 
    				self.SetCellValue(j, i, ("0"))
    			else: 
    			    if((not self.showZeros) & (self.GetCellValue(j, i)==("0"))): 
    			        self.SetCellValue(j, i, (""))	
    		 
    	 
    	self.ForceRefresh()
     
    
    def GetShowZeros(self):
     
    	return self.showZeros
     
    
    def SetVars(self, vars):
     
    	self.ClearGrid()
    	
    	self.numberOfVariables=vars
    	
    	self.width=int(pow(2, ceil(vars/2.0)))
    	self.height=int(pow(2, floor(vars/2.0)))
    	
    	# Fill map self.kmapValues with values that each cell in the map
    	# has. Look here for rules:
    	# http:#www.allaboutcircuits.com/vol_4/chpt_8/3.html
    	self.kmapValues={}
    	if(self.numberOfVariables>2):
    	 
    		for i in range(0, self.height):
    		 
    			for j in range(0, self.width):
    			 
    				# Set every 4x4 block's first 4 vars to gray code
    				self.SetMapValue( j,  i)
    				
    	else:
    	 
    		if(self.numberOfVariables==2):
    		 
    			self.kmapValues[(0, 0)]=0
    			self.kmapValues[(1, 0)]=1
    			self.kmapValues[(0, 1)]=2
    			self.kmapValues[(1, 1)]=3
    		 
    		if(self.numberOfVariables==1):
    		 
    			self.kmapValues[(0, 0)]=0
    			self.kmapValues[(1, 0)]=1
    		 
    	 
    
    	if(self.GetNumberCols()<((self.width))): 
    	    self.AppendCols(self.width-self.GetNumberCols())
    	if(self.GetNumberCols()>((self.width))): 
    	    self.DeleteCols(0, self.GetNumberCols()-self.width)
    	
    	if(self.GetNumberRows()<(((self.height)))): 
    	    self.AppendRows(self.height-self.GetNumberRows())
    	if(self.GetNumberRows()>((self.height))): 
    	    self.DeleteRows(0, self.GetNumberRows()-self.height)
    	
    	
    	for i in range(0, self.GetNumberRows() ):
    	 
    		a=self.GetMapBoolValue(0,i)
    		for j in range(0, self.GetNumberCols() ):
    		 
    			b=self.GetMapBoolValue(j,i)
    			for k in range(0, len(a) ):
    			    if( a[k]!=b[k] ): 
    			        a[k]=2
    		r = ''
    		for k in range(0, len(a)):
    		 
    			if( a[k]!=2 ): 
    			    r += str(a[k])
    		 
    		self.SetRowLabelValue(i, r)
    	 
    	
    	for i in range(0, self.GetNumberCols() ):
    	 
    		a=self.GetMapBoolValue(i,0)
    		for j in range(0, self.GetNumberRows() ):
    		 
    			b=self.GetMapBoolValue(i,j)
    			for k in range(0, len(a) ):
    			    if( a[k]!=b[k] ):
    			        a[k]=2
    		r =''
    		for k in range(0, len(a) ):
    		    if( a[k]!=2 ): 
    			    r += str(a[k])
    		 
    		self.SetColLabelValue(i, r)
    	for i in range(0, self.GetNumberRows() ):
    	 
    		for j in range(0, self.GetNumberCols() ):
    		 
    			if( ((j/4+i/4)%2)==1): 
    			    self.SetCellBackgroundColour(i, j, wx.Colour(245,245,245))
    			else: 
    			    self.SetCellBackgroundColour(i, j, self.GetDefaultCellBackgroundColour())
    			if(self.showZeros): 
    			    self.SetCellValue(i, j, ("0"))
    	#dc = wx.PaintDC(self)
    	dc = wx.ClientDC(self)
    	dc.SetFont(self.GetLabelFont())
    	[w, h] = dc.GetTextExtent( self.GetRowLabelValue(0))
    	
    	self.SetRowLabelSize(w+15)
    	
    	#self.AutoSizeColumns(1)
    	
    	[w, h] = dc.GetTextExtent( self.GetColLabelValue(0))
    	
    	for i in range(0, self.GetNumberCols() ):
    	 
    		if(w<20): 
    		    w=20;
    		self.SetColSize(i, w+15)
    	self.ForceRefresh()
    	self.AdjustScrollbars()
     
    
    def GrayEncode(self, g):
     
    	return int(g) ^ (int(g) >> 1)
    
     
    
    def GetMapValue(self, x,  y):
        if not self.kmapValues.has_key((x,y)):
            self.SetMapValue( x,  y)
        return self.kmapValues[(x,y)]
     
    
    def GetMapBoolValue(self, x, y):
     
    	b = []
    	i=self.GetMapValue(x, y)
    	while(i>0):
    	 
    		b.insert(0, i%2)
    		i=i/2
    	 
    	for j in range(len(b), self.numberOfVariables):
    		b.insert(0,0)
    	return b
     
    def SetMapValue(self, x,  y):
        if(y%2 ==0 ):
            self.kmapValues[(x, y)]=self.GrayEncode(x+((y)*self.width))
        else:
            self.kmapValues[(x, y)]=self.GrayEncode((self.width-1-x)+((y)*self.width))
    
    def Set(self, adr, value):
        MaskRowadr = (( 1<< int(log(self.GetNumberRows())/log(2)) ) -1) << int(log(self.GetNumberCols())/log(2))
        Rowadr = adr & MaskRowadr
        
        for i in range(0, self.height):
            if self.kmapValues[(0, i)]==Rowadr:
                break
        for j in range(0, self.width):
            if(self.kmapValues[(j, i)]==adr):
                self.SetCellValue(i, j, value)
                return
    			 
    		 
    	 
     
    
    def SetCellAdresses(self, on):
     
    	if(on==0):
    	 
    		self.useCellAdresses=0;
    		self.SetDefaultRenderer( gridlib.GridCellStringRenderer())
    		self.ForceRefresh()
    	 
    	if(on==1):
    	 
    		self.useCellAdresses=1;
    		self.SetDefaultRenderer( KMapGridCellRenderer())
    		self.ForceRefresh()
    	 
     
    
    def GetCellAdresses(self):
     
    	return self.useCellAdresses
     

# Grid cell renderer
##class KMapGridCellRenderer(grid.GridCellRenderer):
##    def __init__( grid, attr, dc, rect, row, col, isSelected):
##        grid.GridCellRenderer.__init__(grid, attr, dc, rect, row, col, isSelected)

class KMapGridCellRenderer(gridlib.PyGridCellRenderer):
    #def __init__( self):
    #    grid.PyGridCellRenderer.__init__(self)
    def Draw(self, grid, attr, dc, rect, row, col, isSelected):
        
        gridlib.GridCellStringRenderer().Draw(grid, attr, dc, rect, row, col, isSelected)
    	
    	if wx.Platform == '__WXMSW__':
    	    font =  wx.Font(7, wx.DEFAULT, wx.NORMAL, wx.NORMAL)
    	    font.SetFaceName(('MS Reference Sans Serif'))
    	else:
    	    font =  wx.Font(7, wx.DEFAULT, wx.NORMAL, wx.NORMAL)
    	    font.SetFaceName(('sans'))
    	     
    	dc.SetFont(font)
    	dc.SetTextForeground(wx.Colour(150, 150, 150))
    	
    	dc.SetPen(wx.GREY_PEN)
    	dc.SetBrush(wx.TRANSPARENT_BRUSH)
    	
    	adr=self.GetMapValue(col, row, grid.GetNumberCols(), grid.GetNumberRows())
    	
    	[w, h] = dc.GetTextExtent(str(adr))
    	
    	dc.DrawText(str(adr), rect.GetX()+rect.GetWidth()-w-2, rect.GetY()+rect.GetHeight()-h-1)
     
    
    def GrayEncode(self, g):
     
    	return int(g) ^ (int(g) >> 1)
     
    
    def GetMapValue(self, x, y, width, height):
     
    	if(width>2):
    	 
    		if(y%2==0):
    		    r=self.GrayEncode(x+((y)*width))
    		 
    		else:
    		    r=self.GrayEncode((width-1-x)+((y)*width))
    		 
    		return r
    	 
    	else:
    	    if(height==2):
    		 
    			if( (x==0) & (y==0) ): return 0;
    			if( (x==1) & (y==0) ): return 1;
    			if( (x==0) & (y==1) ): return 2;
    			if( (x==1) & (y==1) ): return 3;
    		 
    	    if(height==1):
    		 
    			if( (x==0) & (y==0) ): return 0;
    			if( (x==1) & (y==0) ): return 1;
    		 
    	 
class TestFrame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, -1, "Simple Grid Demo", size=(640,480))
        self.grid = KMap(self)

class BoaApp(wx.App):
    def OnInit(self):
        frame = TestFrame(None)
        self.main = frame
        self.SetTopWindow(self.main)
        self.main.Show(True)
        return True
        

    def OnOpenWidgetInspector(self):
        # Activate the widget inspection tool
        if __debug__:
            #from wx.lib.inspection import InspectionTool
            #if not InspectionTool().initialized:
            #    InspectionTool().Init()
                
            # Find a widget to be selected in the tree.  Use either the
            # one under the cursor, if any, or this frame.
            #wnd = wx.FindWindowAtPointer()
            #if not wnd:
            #    wnd = self
            #InspectionTool().Show(wnd, True)
            None

def main():
    application = BoaApp(0)
    if __debug__:
        BoaApp.OnOpenWidgetInspector(application)
    #from wx.lib.mixins.inspection import InspectableApp
    #app = InspectableApp(False)    
    #frame = TestFrame(None)
    #frame.Show(True)
    #import wx.lib.inspection
    #wx.lib.inspection.InspectionTool().Show()
    application.MainLoop()
    

if __name__ == '__main__':
##    import wx.lib.inspection
##    wx.lib.inspection.InspectionTool().Show()
    main()
     
