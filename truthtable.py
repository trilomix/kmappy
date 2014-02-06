import wx
from wx import grid

import random
##include <cstdlib>
##include <ctime>
##include <math.h>

##include "truthtable.h"

##DEFINE_EVENT_TYPE(wxEVT_VALUE_CHANGE)
##
##BEGIN_EVENT_TABLE( TruthTable, wxGrid )
##	EVT_GRID_CELL_RIGHT_CLICK( TruthTable::DisplayPopup )
##	EVT_GRID_CELL_CHANGE(TruthTable::OnCellChange)
##	EVT_MENU(MENU_SET1, TruthTable::OnMenuSet1)
##	EVT_MENU(MENU_SET0, TruthTable::OnMenuSet0)
##	EVT_MENU(MENU_SETDC, TruthTable::OnMenuSetDC)
##	EVT_MENU(MENU_SETRAND, TruthTable::OnMenuSetRand)
##END_EVENT_TABLE()
[
MENU_SETDEC,
MENU_SET1,
MENU_SET0, 
MENU_SETDC, 
MENU_SETRAND
] = [wx.NewId() for i in range(5)]
class TruthTable(grid.Grid):
    def __init__(self, parent,  id=wx.NewId(),  vars=4, outs=3,  pos=wx.DefaultPosition,  size=wx.DefaultSize,  style=0, name=""):
        grid.Grid.__init__(self, parent, id, pos, size, style, name)
    	self.showZeros=1
    
    	self.CreateGrid(pow(2, vars), vars+1)
    	
    	self.numberOfVariables=vars
    	self.SetOuts(outs)
    	
    	self.SetVars(vars)
    	
    	self.SetSelectionMode(grid.Grid.wxGridSelectRows)
    	
    	self.EnableDragGridSize(0)
    	
    	self.Bind(grid.EVT_GRID_CELL_CHANGE, self.OnCellChange)
    	
    	self.Bind(grid.EVT_GRID_CELL_RIGHT_CLICK, self.DisplayPopup )
    	
    	self.Bind(grid.EVT_GRID_LABEL_LEFT_CLICK, self.OnLabelColClick)
    	
    	self.stateMenu =   wx.Menu()
    	
    	self.stateMenu.Append(MENU_SETDEC, ("Set Decimale value"))
    	self.stateMenu.Append(MENU_SET1, ("Set to 1"))
    	self.stateMenu.Append(MENU_SET0, ("Set to 0"))
    	self.stateMenu.Append(MENU_SETDC, ("Set to \"don't care\""))
    	self.stateMenu.AppendSeparator()
    	self.stateMenu.Append(MENU_SETRAND, ("Set randomly"))
    	
    	self.Bind(wx.EVT_MENU, self.OnMenuSetValue,   id=MENU_SETDEC)
    	self.Bind(wx.EVT_MENU, self.OnMenuSet1,    id=MENU_SET1)
    	self.Bind(wx.EVT_MENU, self.OnMenuSet0,    id=MENU_SET0)
    	self.Bind(wx.EVT_MENU, self.OnMenuSetDC,   id=MENU_SETDC)
    	self.Bind(wx.EVT_MENU, self.OnMenuSetRand, id=MENU_SETRAND)
    	
    	self.SetDefaultCellAlignment( wx.ALIGN_CENTRE,  wx.ALIGN_CENTRE)

    def DisplayPopup( self, event):
        if(self.IsSelection() ): # && self.GetSelectedRows().Count()>1)  <--- library bug
            self.popup=event.GetPosition()
            self.PopupMenu(self.stateMenu, event.GetPosition())
        else:
            menuRow=event.GetRow()
            menuCol=event.GetCol()
            self.SetGridCursor(menuRow, menuCol)
            self.ClearSelection()
            self.SelectRow(menuRow)
            
            self.popup=event.GetPosition()
            self.PopupMenu(self.stateMenu, event.GetPosition())


    def OnCellChange( self, event=None, Row=0, Col=0):
        if event:
            Row = event.GetRow()
            Col = event.GetCol()
        if Col ==  self.numberOfVariables+self.numberOfOutputs:
            # DEC column
            current_dec_value = 0
            for col in range( Col-1, self.numberOfVariables-1, -1):
                if self.GetCellValue(Row, col) == '1':
                    current_dec_value += pow(2, (Col-1) -col)
                if self.GetCellValue(Row, col) == '?':
                    current_dec_value =None
                    break
            val = self.GetCellValue(Row, Col)
            if current_dec_value != None and  val !='?':
                try:
                    val = int(self.GetCellValue(Row, Col))
                except:
                    self.SetCellValue(Row, Col,  str(current_dec_value))
                    val = current_dec_value
            
                # Test limit values
                if val < pow(2, self.numberOfOutputs) and val >=0:
                    # Do we need change
                    if (val != current_dec_value):
                        val_bin = val
                        for col in range( Col-1, self.numberOfVariables-1, -1):
                            if val_bin % 2 :
                                self.SetCellValueEvent(Row, col, '1')
                            else:
                                self.SetCellValueEvent(Row, col, '0')
                            val_bin = val_bin /2
                else:
                    self.SetCellValue(Row, Col,  str(current_dec_value))
            else:
                for col in range( Col-1, self.numberOfVariables-1, -1):
                    self.SetCellValueEvent(Row, col, '?')
        else:
            if( (self.GetCellValue(Row, Col)!= ("1")) &
              (self.GetCellValue(Row, Col)!= ("")) &
    		  (self.GetCellValue(Row, Col)!= ("0")) ):
    		      self.SetCellValue(Row, Col,  ("?"))
            
            if(self.GetCellValue(Row, Col)== ("")) & Row>self.numberOfVariables:
                if(self.showZeros): 
                    self.SetCellValue(Row, Col,  ("0"))
            
            if(self.GetCellValue(Row, Col)== ("0"))& Row>self.numberOfVariables:
                if(not self.showZeros): 
                    self.SetCellValue(Row, Col,  (""))
            
            # Update DC column
            self.UpdateDCRow( Row)
            
        if event:
            event.Skip(1)

    def OnMenuSetValue( self, event):
        outs = self.numberOfOutputs
        if outs > 2:
            #ColLabel = self.GetColLabelValue(Col)
            dlg = wx.TextEntryDialog(
                    self, 'Set Decimale Value',
                    '', '')
    
            #dlg.SetValue(ColLabel)
    
            if dlg.ShowModal() == wx.ID_OK:
                for i in range(0,(pow(2, self.numberOfVariables)) ):
                    if(self.IsInSelection(i, 0)) :
                        self.SetCellValueEvent(i, self.GetNumberCols()-1,  str(dlg.GetValue()))
    
            dlg.Destroy()
    def OnMenuSet1( self, event):
        for i in range(0,(pow(2, self.numberOfVariables)) ):
            if(self.IsInSelection(i, 0)) :
                for j in range(0, self.numberOfOutputs):
                    self.SetCellValueEvent(i, self.numberOfVariables+j,  ("1"))
                    #evt = wx.grid.GridEvent(self.GetId(), wx.grid.wxEVT_GRID_CELL_CHANGE, self, i, self.numberOfVariables+j)
                    #self.GetEventHandler().ProcessEvent(evt)
                    #self.OnCellChange(None, i, self.numberOfVariables)

    def OnMenuSet0( self, event):
        for i in range(0,(pow(2, self.numberOfVariables)) ):
            if(self.IsInSelection(i, 0)) :
                for j in range(0, self.numberOfOutputs):
                    if(self.showZeros):
                        self.SetCellValueEvent(i, self.numberOfVariables+j,  ("0"))
                    else:
                        self.SetCellValueEvent(i, self.numberOfVariables+j,  (""))
                    #evt = wx.grid.GridEvent(self.GetId(), wx.grid.wxEVT_GRID_CELL_CHANGE, self, i, self.numberOfVariables+j)
                    #self.GetEventHandler().ProcessEvent(evt)
                    #self.OnCellChange(None, i, self.numberOfVariables)

    def OnMenuSetDC( self, event):
        for i in range(0,(pow(2, self.numberOfVariables)) ):
            if(self.IsInSelection(i, 0)) :
                for j in range(0, self.numberOfOutputs):
                    self.SetCellValueEvent(i, self.numberOfVariables+j,  ("?"))
                    #evt = wx.grid.GridEvent(self.GetId(), wx.grid.wxEVT_GRID_CELL_CHANGE, self, i, self.numberOfVariables+j)
                    #self.GetEventHandler().ProcessEvent(evt)
                    #self.OnCellChange(None, i, self.numberOfVariables)

    def OnMenuSetRand( self, event):
        for i in range(0,(pow(2, self.numberOfVariables)) ):
            if(self.IsInSelection(i, 0)) :
                for j in range(0, self.numberOfOutputs):
                    if(random.random()>=0.5):
                        self.SetCellValueEvent(i, self.numberOfVariables+j,  ("1"))
                        #self.OnCellChange(None, i, self.numberOfVariables)
                        #evt = wx.grid.GridEvent(self.GetId(), wx.grid.wxEVT_GRID_CELL_CHANGE, self, i, self.numberOfVariables+j)
                        #self.GetEventHandler().ProcessEvent(evt)
                    else:
                        if(self.showZeros): 
                            self.SetCellValueEvent(i, self.numberOfVariables+j, '0')
                        else: 
                            self.SetCellValueEvent(i, self.numberOfVariables+j, '')
                        #evt = wx.grid.GridEvent(self.GetId(), wx.grid.wxEVT_GRID_CELL_CHANGE, self, i, self.numberOfVariables+j)
                        #self.GetEventHandler().ProcessEvent(evt)
                        #self.OnCellChange(None, i, self.numberOfVariables)

    def OnLabelColClick(self, event):
        Row = event.GetRow()
        Col = event.GetCol()
        if Col > -1:
            ColLabel = self.GetColLabelValue(Col)
            dlg = wx.TextEntryDialog(
                    self, 'Change column name',
                    '', '')
    
            dlg.SetValue(ColLabel)
    
            if dlg.ShowModal() == wx.ID_OK:
                self.SetColLabelValue(Col, dlg.GetValue())
                self.SetColLabelSizefromLabel(Col)
                #evt = wx.grid.GridEvent(self.GetId(), wx.grid.wxEVT_GRID_LABEL_RIGHT_CLICK, self, Row, Col)
                #self.GetEventHandler().ProcessEvent(evt)
    
            dlg.Destroy()
        event.Skip(1)

    def UpdateDCRow(self, Row):        
        # Update DC column
        DC_Col = self.numberOfVariables+self.numberOfOutputs
        current_dec_value = 0
        for col in range( DC_Col-1, self.numberOfVariables-1, -1):
            if self.GetCellValue(Row, col) == '1':
                current_dec_value += pow(2, (DC_Col-1) -col)
        self.SetCellValue(Row, DC_Col,  str(current_dec_value))

    def SetCellValueEvent(self, row, col, value):
        self.SetCellValue(row, col,  value)
        evt = wx.grid.GridEvent(self.GetId(), wx.grid.wxEVT_GRID_CELL_CHANGE, self, row, col)
        self.GetEventHandler().ProcessEvent(evt)

    def SetOuts(self, outs):
        self.numberOfOutputs = outs
        vars = self.numberOfVariables
        
        if(self.GetNumberCols()<(vars+outs+1)): 
            if outs >= 2:
                # Delete DEC col
                self.DeleteCols(self.GetNumberCols()-1, 1)
            InserNbCol = vars+outs-self.GetNumberCols()
            self.InsertCols(vars,InserNbCol)
            for i in range(0, InserNbCol):
                self.SetColLabelValue(vars+i,  'f%d' % (outs-1-i))
        if(self.GetNumberCols()>(vars+outs)): 
            if outs >= 1:
                # Delete DEC col
                self.DeleteCols(self.GetNumberCols()-1, 1)
            ColLabel = []
            for Col in range(self.GetNumberCols()-outs, (vars+outs+1) ):
                ColLabel.append(self.GetColLabelValue(Col))
            self.DeleteCols(vars, self.GetNumberCols()-(vars+outs))
            for Col in range(self.GetNumberCols()-outs, (vars+outs) ):
                if ColLabel:
                    self.SetColLabelValue(Col, ColLabel.pop(0))
    	self.DrawGrid(OverWrite = False)
        
    def SetVars(self, vars):
        #self.ClearGrid()
        self.numberOfVariables=vars
        outs = self.numberOfOutputs
        if outs > 2:
            self.DeleteCols(self.GetNumberCols()-1, 1)
        ColLabel = []
        for Col in range(0, self.GetNumberCols() ):
            ColLabel.append(self.GetColLabelValue(Col))
        if(self.GetNumberCols()<(vars+outs)): 
            InserNbCol = vars+outs-self.GetNumberCols()
            self.InsertCols(0,InserNbCol)
##            for i in range(0, InserNbCol):
##                self.SetColLabelValue(i,  chr(65+i))
##            for Col in range(InserNbCol, vars+outs+1):
##                self.SetColLabelValue(Col, ColLabel[Col-InserNbCol] )
            #self.AppendCols(vars+outs-self.GetNumberCols())
            
        if(self.GetNumberCols()>(vars+outs)): 
            NbDeleteCol = self.GetNumberCols()-(vars+outs) 
            self.DeleteCols(0, NbDeleteCol)
            for Col in range(0, vars+outs):
                self.SetColLabelValue(Col, ColLabel[Col+NbDeleteCol] )
        
        if(self.GetNumberRows()<(pow(2, vars))):
            self.AppendRows((pow(2, vars))-self.GetNumberRows())
        if(self.GetNumberRows()>(pow(2, vars))): 
            self.DeleteRows(pow(2, vars), self.GetNumberRows()-(pow(2, vars)))
	
    	self.DrawGrid(OverWrite = False)

    def DrawGrid(self, OverWrite = True):
        vars = self.numberOfVariables
        outs = self.numberOfOutputs
        
    	if  outs >= 2:
    	    self.AppendCols(1)
    	    self.SetColLabelValue(self.GetNumberCols()-1, 'DEC')
    	
    	if OverWrite:
        	for i in range(0, vars):
        	    self.SetColLabelValue(i,  chr(65+i))
        	
        	for i in range(0, outs):
        	    self.SetColLabelValue(vars+i,  'f%d' % (outs-1-i))
        	
        	for i in range(0,(pow(2, vars)) ):
        	    self.SetRowLabelValue(i,  str(i))
        	    if(self.showZeros): 
        		    self.SetCellValue(i, self.numberOfVariables,  ("0"))
    	
    	for i in range(0,(pow(2, vars)) ):
    	    if  outs >= 2:
    	        self.UpdateDCRow( i)

    	    for j in range(0, vars):
    	        self.SetReadOnly(i, j, 1)
    	        if(not(i%2)):
    	            self.SetCellBackgroundColour(i, j,  wx.Colour(245, 245, 245))
    	        else:
    	            self.SetCellBackgroundColour(i, j,  wx.Colour(235, 235, 235))
    	        if((i%(pow(2, vars-j)))<(pow(2, vars-j-1))):
    	            self.SetCellValue(i, j,  ("0"))
    	        else :
    			    self.SetCellValue(i, j,  ("1"))
            for j in range(0, outs):
                if (j%2 ==0):
                    self.SetCellBackgroundColour(i, vars+j,  wx.Colour(215, 225, 255))
                else:
                    self.SetCellBackgroundColour(i, vars+j,  wx.Colour(255, 255, 255))
    	
        dc = wx.ClientDC(self)
    	dc.SetFont(self.GetLabelFont())
    	[w,h] = dc.GetTextExtent(  str( pow(2, vars) ))
    	
    	self.SetRowLabelSize(w+15)
    	
    	self.AutoSizeColumns(1)
    	for i in range(0, outs):
    	    self.SetColSize(vars+i, (1.5*self.GetColSize(0)))
    	
    	self.ForceRefresh()
    	
    	self.AdjustScrollbars()

    def SetColLabelSizefromLabel(self, col):
        #dc = wx.PaintDC(self)
    	dc = wx.ClientDC(self)
    	dc.SetFont(self.GetLabelFont())
    	[w,h] = dc.GetTextExtent( self.GetColLabelValue(col) )
    	
    	#self.SetColLabelSize(w+15)
    	
    	self.AutoSizeColumns(1)
    	
    	self.ForceRefresh()
    	
    	self.AdjustScrollbars()
        
    def SetShowZeros(self, s):
    	self.showZeros=s;
    	for j in range(0, self.numberOfOutputs):
        	for i in range(0, self.GetNumberRows() ):
        	    if(self.showZeros & (self.GetCellValue(i, self.numberOfVariables+j)== (""))) :
        			self.SetCellValue(i, self.numberOfVariables+j,  ("0"))
        	    else:
        	        if((not self.showZeros) & (self.GetCellValue(i, self.numberOfVariables+j)== ("0"))) :
        		        self.SetCellValue(i, self.numberOfVariables+j,  (""))
    	self.ForceRefresh()

    def GetShowZeros(self):
        return self.showZeros
    def Write(self, filePath):
        """
        Genere un fichier a partir d'une table 
        """
        
        fh = open(filePath, "w")
        
        fh.write("%Generated by Kmapreducer\n\n")
        # @TODO Rajouter la date et l'heure
        fh.write("\n")
        
        #sweep variables
        fh.write("% sweep_variables " )
        vars = self.numberOfVariables
        for var in range(0, vars):
            varName = self.GetColLabelValue(var)
            fh.write( varName+" ")
        fh.write("\n\n" )
        
        
        #performances 
        fh.write("% Performance_expressions_table:\n")
        outs = self.numberOfOutputs
        for out in range(0, outs):
            outName = self.GetColLabelValue(vars + out)
            fh.write("%performance "+outName+"= \"not defined\" type = int\n")
        fh.write("\n")
        
        
        # Ligne des variables
        fh.write("% ")
        for col in range(0, vars + outs) :
            name = self.GetColLabelValue(col)
            fh.write(name+" ")
        fh.write("\n")
        
        
        # Datas
        for row in range(0, self.GetNumberRows()) :
            for col in range(0, vars + outs):
                data = self.GetCellValue(row, col)
                if (data == '') | (data == ' '):
                    data = '0'
                if data == '?':
                    data = '2'
                fh.write(data + ' ')
            fh.write('\n')
        fh.close()


class TestFrame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, -1, "Simple Grid Demo", size=(640,480))
        self.grid = TruthTable(self)

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
