import traceback
import wx
from multiprocessing import Process, Lock
from karnaughmap import *

class SolveTask(Process):
    def __init__ (self,parent, out, process_counter):
        Process.__init__(self)
        self.daemon = True
        self.status = -1
        self.parent = parent
        self.out = out
        self.process_counter = process_counter
        self.numberOfVariables
        self.NumberRows
        self.GetNumberCols
        self.solveSOP
        self.kmap = kmap
        self.Kmap = KarnaughMap(numberOfVariables)
    
    def Solve(self, out):
        K= KarnaughMap(self.parent.numberOfVariables.GetValue())
        K=self.Kmap
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
        K.Solve()
        
        self.Kmap = K
            

    def Updateparent(self, K):
        out = self.out
        
        s="X = "
            
        self.parent.solution[out].AddRoot(s)
        
        solutionsList=K.GetSolutions()
        
        if(self.parent.solveSOP):
    		for iter in solutionsList:
    			self.parent.kmap[out].AddSolution(iter.values)
    			
    			b = ''  # A, B, C, D
    			a = ''  # All the rest
    			for i in range(0, len(iter.values)):
    				if(iter.values[i]==1):
    				    a += self.parent.truthTable.GetColLabelValue(i)+'.'
    				if(iter.values[i]==0):
    				    a += "|%s" % self.parent.truthTable.GetColLabelValue(i)+'.'
    			b=b+a
    			
    			if(b==("")): 
    			    b=("1")
    			else:
    			    b = b[0:-1]
    			s+=b
    			
    			#bData = SolveTreeItemData()
    			bData = wx.TreeItemData()
    			bData.SetData(iter.values)
    			self.parent.solution[out].AppendItem(self.parent.solution[out].GetRootItem(), b, -1, -1, bData)
    			
    			if(iter!=solutionsList[-1]): s += ' + '
    		
    		if(s==("X = ")): s=("X = 0")
        else:
    		for iter in solutionsList :
    			self.parent.kmap[out].AddSolution(iter.values)
    			
    			b = ("(")
    			a = ''
    			for i in range(0, len(iter.values)) :
    				if(iter.values[i]==0):
    				    a += self.parent.truthTable.GetColLabelValue(i)+'+'
    				if(iter.values[i]==1):
    				    a += '|'+self.parent.truthTable.GetColLabelValue(i)+'+'
    				
    			b=b+a
    			if(b==("")): 
    			    b=("0")
    			else:
    			    b = b[0:-1] + ')'
    			s += b
    			
    			#bData = SolveTreeItemData()
    			bData = wx.TreeItemData()
    			bData.SetData(iter.values)
    			self.parent.solution[out].AppendItem(self.parent.solution[out].GetRootItem(), b, -1, -1, bData)
    			
    			if(iter!=solutionsList[-1]): s += ' . '
    			
    		if(s==("X = ")): s=("X = 1")
        self.parent.solution[out].Expand(self.parent.solution[out].GetRootItem())
        self.parent.solution[out].SetItemText(self.parent.solution[out].GetRootItem(), s)
        	
    def run(self):
        
        try:
            self.Solve(self.out)
        except:
            traceback.print_exc()
            pass

