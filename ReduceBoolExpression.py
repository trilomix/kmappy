
def walk_branches(tree,root):
    """ a generator that recursively yields child nodes of a wx.TreeCtrl """
    item, cookie = tree.GetFirstChild(root)
    while item.IsOk():
        yield item
        if tree.ItemHasChildren(item):
            walk_branches(tree,item)
        item,cookie = tree.GetNextChild(root,cookie)

class ReduceSol(object):
    def Length(self, a):
        """ return the number of 0 and 1 in a
        """
    	c=0
    	for i in range(0,len(a)):
    	 
    		if (a[i]!= 2):
    		 
    			c +=1
    	return c	 
        
    def __init__(self, parent, AllSolutions,vars,outs):
        self.outs = outs
        self.vars = vars
        self.parent = parent
        self.SolOuts = []
        self.AllSolutions = self.SetSolutions(AllSolutions)
        
    def SetSolutions(self, AllSolutions):
        """ Get the solution from the tree
            For each Outputs [Solution0, ..., SolutionN]
            For each Solution [Var0, ..., VarN, Out0Equ0, ..., Out0EquN, OutNEqu0, ..., OutNEquN, Equ0, ..., EquN]
            For now OutXEquX are '2' (don't care) and EquX doesn't exist yet
        """
        SolOuts0 = []
        for outSolutions in AllSolutions:
            self.SolOuts.append(len(outSolutions))
            for Solution in outSolutions:
                SolOuts0.append(2)
            
        for outSolutions in AllSolutions:
            for Solution in outSolutions:
                Solution.extend(SolOuts0)
        
        return AllSolutions

    def ReduceEquation(self,Subsol0):
        # Search for same part of equation 
        All = []
        CurrentSubSol0 = list(Subsol0)
        Index = [0]
        for i in range(self.Length(CurrentSubSol0)-1):
            Index.append(-1)
        NbReplace = 1
        while self.Length(CurrentSubSol0) >=2:
            CurrentSubSol0 = list(Subsol0)
            Start = -1
            for i in range(NbReplace-1,-1,-1):
                CurrentSubSol0,Start = self.Replace(CurrentSubSol0, Start+1, Index[i])
            All.append( CurrentSubSol0)
            Index[0] += 1
            for i in range(NbReplace):
                offset = 0
                for j in range(i+1,len(Index)):
                    offset += Index[j]+1
                if Index[i] >= self.Length(Subsol0)-(offset+i):
                    #print 'offset : %s' % str(offset)
                    for j in range(i+1):
                        Index[j] = 0
                    Index[i+1] +=1
                    if  NbReplace == i+1:
                        NbReplace += 1
        return All
    def reduce0(self):
        
        AllSolutions = self.AllSolutions
        for index0, Solution0 in enumerate(AllSolutions[:-1]):
            # Seach for same solution
            for  index1, Solution1 in enumerate(AllSolutions[index0+1:],index0+1):
                tree = self.parent.solution[index1]
                root = tree.GetRootItem()
                if Solution0 == Solution1:
                    # Same solution
                    tree.SetItemText(root, '%s = %s' % (OutputsName[index1],OutputsName[index0]))
                    break
                for index10, Subsol in enumerate(SolutionList):
                    if Solution0 == list(Subsol):
                        # Same solution in equation
                        RootText = tree.GetItemText(root)
                        RootTextList = RootText.split(' = ')
                        if(self.solveSOP):
                            AndOr = ' + '
                        else:
                            AndOr = ' . '
                        RootTextList = RootTextList[1].split(AndOr)
                        OldItemText = RootTextList[index10]
                        RootTextList[index10] = self.parent.OutputName(index0)
                        RootText = ' . '.join(RootTextList)
                        tree.SetItemText(root, '%s = %s' % (self.parent.OutputName(index1),RootText))
                        for item in walk_branches(tree,root):
                            sol=(self.parent.solution[out].GetItemData(item)).GetData();
                            if sol == Subsol:
                                tree.SetItemText(item, self.parent.OutputName(index0))
                        break
            for index00, Subsol0 in enumerate(Solution0):
                self.SearchForSame(Subsol0, index0, AllSolutions)
        for out, Solution in enumerate(AllSolutions):
            for index00, Subsol0 in enumerate(Solution):
                self.ReduceEquation(Subsol0)
    def reduce(self):
        AllSolutions = self.AllSolutions
        for NbInputs in range(self.vars,2-1,-1):
            EquationList = [[sol for sol in Solution 
                        if self.Length(sol[:self.vars]) >= NbInputs] 
                             for Solution in AllSolutions]
            BestCommon = []
            NoMoreCommon = False
            while (not NoMoreCommon):
                for out0, Solution0 in enumerate(EquationList):
                    for index0, SubSol0 in enumerate(Solution0):
                        EquationList = [[sol for sol in Solution 
                             if self.Length(sol[:self.vars]) >= NbInputs] 
                                  for Solution in AllSolutions]
                        for out1, Solution1 in enumerate(EquationList):
                            for index1, SubSol1 in enumerate(Solution1):
##                                if (SubSol1 == SubSol0) and (out0 != out1):
##                                    # Same equation as other out
##                                    SubSol1 = self.mask(SubSol0, SubSol0)
##                                    out,index = self.CommonFound(SubSol0)
##                                    SubSol1[self.vars+sum(self.SolOuts[:out])+index]=1
                                if (index0 != index1 or out0 != out1):
                                    c = self.comp(SubSol0, SubSol1)
                                    if (self.Length(c) >= 2):
                                        # common exist
                                        if self.Length(BestCommon) < self.Length(c):
                                            BestCommon = c
                if BestCommon:
                    out,index = self.CommonFound(BestCommon)
                    EquationList0 = []
                    for Solution in AllSolutions:
                        SubSollist = [sol for sol in Solution 
                                       if self.Length(sol) >= self.Length(BestCommon)
                                        and self.comp(BestCommon, sol) == BestCommon]
                        EquationList0.append(SubSollist)
##                    EquationList0 = [[sol for sol in Solution 
##                       if self.Length(sol) >= self.Length(BestCommon)] 
##                          for Solution in AllSolutions]
                    for outindex, Equ in enumerate(EquationList0):
                        for SubSol in Equ:
                            if outindex != out or SubSol != BestCommon:
                                SubSol = self.mask(SubSol, BestCommon)
                                if out == self.outs:
                                    # It's an equation
                                    SubSol[self.vars+sum(self.SolOuts)+index]=1
                                else:
                                    # It's an output equation
                                    SubSol[self.vars+sum(self.SolOuts[:out])+index]=1
##                    SubSol0 = self.mask(SubSol0, c)
##                    if out == self.outs:
##                        # It's an equation
##                        SubSol0[self.vars+self.outs+index]=1
##                    else:
##                        # It's an output equation
##                        SubSol0[self.vars+sum(self.SolOuts[:out])+index]=1
                    
                    BestCommon = []
                else:
                    NoMoreCommon = True
                            
    def ColName(self, index):
        names= ['VRAMP@VBAT','PA_EN','BD_SW','EDGE','EN_HB_B2','EN_LB_B1','MODE_SEL_B8','MODE2_B5','MODE1_VM0','MODE0_VM1']
        return names[index]
    def OutputName(self, index):
        names= ['MODE<0>','MODE<1>','MODE<2>','MODE<3>','MODE<4>','','','','','']
        return names[index]
    def solutionStr(self, values, OP ='.'):
        outs = self.SolOuts
        vars = self.vars
        if OP == '.':
            b = ''  # A, B, C, D
        else:
            b = '('
            
        a = ''  # All the rest
        for i in range(0, len(values)):
            if values[i] != 2:
                if i < vars:
                    if(values[i]==0):
                        a += '|'
                    a += self.ColName(i)+OP
                elif i >=vars and i < sum(outs)+vars:
                    for outindex in range(len(outs)):
                        if i >= vars+sum(outs[:outindex]) and i < vars+sum(outs[:outindex+1]):
                            if(values[i]==0):
                                a += '|'
                            a += '%s_Equ%s' % (self.OutputName(outindex),str(i- (vars+sum(outs[:outindex])) ))+OP
                elif i >= sum(outs)+vars:
                    if(values[i]==0):
                        a += '|'
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
    
    def CommonFound(self, a):
        AllSolutions = self.AllSolutions
        NbInputs = self.Length(a[:self.vars])
        EquationList = [[sol for sol in Solution 
                        if self.Length(sol[:self.vars]) == NbInputs] 
                             for Solution in AllSolutions]
        for index, Solution in enumerate(EquationList):
            if a in Solution:
                return index, AllSolutions[index].index(a)
        # The equation is new
        if len(AllSolutions) == self.outs:
            # Create the equations entry
            AllSolutions.append([a])
        else:
            AllSolutions[-1].append(a)
        for outSolutions in AllSolutions:
            for Solution in outSolutions:
                Solution.append(2)
        return self.outs, AllSolutions[-1].index(a)
    
    def mask(self, a, mask):
        for i in range(0,self.vars):
            if mask[i] !=2:
                a[i] = 2
        return a
    
    def comp(self, a, b):
        c = []
    	for i in range(0,len(a)):
    		if(a[i]!=b[i]):
    		    c.append(2)
    		else:
    		    c.append(a[i])
        return c
    
    def GetSimpleValue(self, values):
        def Add(a, b):
            c =[]
            for i in range(len(a)):
                if a[i] == b[i]:
                    c.append(a[i])
                elif a[i] == 2:
                    c.append(b[i])
                elif b[i] == 2:
                    c.append(a[i])
                else:
                    raise()
            return c
        outs = self.SolOuts
        vars = self.vars
        if self.Length(values[vars:]) != 0:
            newvalues = values[:vars] 
            for i in range(vars, len(values)):
                if values[i] != 2:
                    if i < vars:
                        subValues = newvalues
                    elif i >=vars and i < sum(outs)+vars:
                        for outindex in range(len(outs)):
                            if i >= vars+sum(outs[:outindex]) and i < vars+sum(outs[:outindex+1]):
                                subValues = self.GetSimpleValue(self.AllSolutions[outindex][i- (vars+sum(outs[:outindex]))])
                    elif i >= sum(outs)+vars:
                        #Select the Equation solution
                        subValues = self.GetSimpleValue(self.AllSolutions[-1][i- (vars+sum(outs))])
                    newvalues = Add(newvalues[:vars],subValues)
            
            return newvalues[:vars]
        else:
            return values[:vars]
    
    def GetSubValues(self, values):
        outs = self.SolOuts
        vars = self.vars
        if self.Length(values[vars:]) != 0:
            Subvalues = [] 
            for i in range(vars, len(values)):
                if values[i] != 2:
##                    if i < vars:
##                        subValues = newvalues
                    if i >=vars and i < sum(outs)+vars:
                        for outindex in range(len(outs)):
                            if i >= vars+sum(outs[:outindex]) and i < vars+sum(outs[:outindex+1]):
                                Subvalues.append(self.AllSolutions[outindex][i- (vars+sum(outs[:outindex]))])
                                Subvalues.extend(self.GetSubValues(Subvalues[-1]))
                    elif i >= sum(outs)+vars:
                        #Select the Equation solution
                        Subvalues.append( self.AllSolutions[-1][i- (vars+sum(outs))] )
                        Subvalues.extend( self.GetSubValues(Subvalues[-1]) )
            
            return Subvalues
        else:
            return [values]
    
    def SearchForSame(self, sol, out, AllSolutions):
        for  index1, SolutionList in enumerate(AllSolutions[out+1:],1):
            tree = self.parent.solution[index1+out]
            root = tree.GetRootItem()
            #print SolutionList
            for index10, Subsol in enumerate(SolutionList):
                if sol == Subsol:
                    # Same solution in equation
                    RootText = tree.GetItemText(root)
                    RootTextList = RootText.split(' = ')
                    if(self.parent.solveSOP):
                        AndOr = ' + '
                    else:
                        AndOr = ' . '
                    RootTextList = RootTextList[1].split(AndOr)
                    #print RootTextList
                    if len(RootTextList) >= index10:
                        OldItemText = RootTextList[index10]
                        #print out , AllSolutions[out]
                        RootTextList[index10] = '%s_%s' % (self.parent.OutputName(out),AllSolutions[out].index(sol))
                        RootText = AndOr.join(RootTextList)
                        tree.SetItemText(root, '%s = %s' % (self.parent.OutputName(index1+out),RootText))
                    for item in walk_branches(tree,root):
                        sol0=(self.parent.solution[out].GetItemData(item)).GetData();
                        if sol0 == Subsol:
                            tree.SetItemText(item, '%s_%s' % (self.parent.OutputName(out),AllSolutions[out].index(sol)))
                            break
                    break
        
    def GetValue(self,sol,Index):
        searchindex = 0
        for i in range(0,len(sol)):
            if (sol[i] != 2) :
                if searchindex==Index:
                    break
                else:
                    searchindex += 1
        return sol[i]
    
    def Replace(self, sol, Start, Index, Value = 2):
        searchindex = 0
        i = -1
        for i in range(Start,len(sol)):
            if type(Value) == list:
                if (Value[i] != 2):
                    if searchindex==Index  and sol[i] == 2:
                        sol[i] = Value[i]
                        break
                    else:
                        searchindex += 1
            else:
                if (sol[i] != 2):
                    if searchindex==Index:
                        sol[i] = Value
                        break
                    else:
                        searchindex += 1
        return sol,i
                

    def IsPartOf(self, a, b):
        """ Checks if a node is part of b 
        """
     
    	c=0
    	for i in range(0,len(a)):
    	 
    		if not (a[i]!= 2 and a[i]==b[i]):
    		 
    			return False
    	return True	 

def main():
    AllSol = [[[1, 0, 0, 1, 0, 0, 0, 0, 0, 2], [1, 0, 0, 1, 0, 0, 0, 0, 2, 1], [2, 0, 0, 0, 1, 2, 0, 0, 0, 1], [1, 2, 1, 0, 0, 0, 0, 0, 0, 2], [1, 2, 1, 0, 0, 0, 0, 0, 2, 1], [1, 0, 0, 0, 1, 2, 2, 0, 0, 1], [1, 0, 0, 0, 1, 2, 0, 1, 2, 1], [1, 0, 0, 0, 1, 2, 0, 1, 0, 2], [1, 0, 0, 0, 2, 1, 2, 0, 0, 1], [0, 0, 2, 2, 0, 0, 0, 1, 2, 1], [0, 0, 2, 2, 0, 0, 0, 1, 0, 2], [0, 0, 2, 2, 0, 0, 1, 0, 2, 1], [0, 0, 2, 2, 0, 0, 1, 0, 0, 2], [0, 2, 2, 1, 0, 0, 0, 1, 0, 2], [0, 2, 2, 1, 0, 0, 1, 0, 0, 2], [2, 1, 0, 1, 2, 1, 1, 0, 2, 1], [2, 1, 0, 1, 1, 2, 0, 2, 1, 0], [2, 1, 0, 1, 1, 2, 1, 0, 0, 2], [1, 1, 0, 2, 2, 1, 1, 0, 0, 2], [1, 2, 0, 0, 2, 1, 1, 0, 0, 2], [1, 2, 0, 0, 2, 1, 1, 0, 2, 1], [1, 1, 0, 2, 2, 1, 0, 2, 1, 0], [1, 1, 0, 2, 1, 2, 0, 2, 1, 0], [1, 1, 0, 0, 1, 2, 1, 2, 0, 2], [1, 1, 0, 0, 1, 2, 1, 2, 2, 1], [1, 1, 0, 2, 1, 2, 1, 0, 2, 1], [1, 2, 0, 0, 1, 2, 1, 0, 2, 1], [1, 2, 0, 0, 1, 2, 1, 0, 0, 2], [0, 0, 2, 2, 2, 1, 0, 0, 2, 1], [0, 0, 2, 2, 2, 1, 0, 0, 0, 2], [0, 0, 2, 2, 1, 2, 0, 0, 0, 2], [0, 0, 2, 2, 1, 2, 0, 0, 2, 1], [0, 2, 2, 1, 1, 2, 0, 0, 2, 1], [0, 2, 2, 1, 2, 1, 0, 0, 0, 2], [2, 2, 2, 0, 1, 1, 2, 2, 1, 2], [2, 1, 2, 2, 1, 1, 2, 2, 1, 2], [2, 2, 1, 2, 1, 1, 2, 2, 2, 2], [0, 1, 2, 1, 2, 2, 2, 2, 2, 2]], [[1, 0, 0, 1, 0, 0, 0, 0, 1, 2], [1, 2, 0, 0, 2, 1, 0, 0, 0, 1], [1, 2, 0, 0, 1, 2, 0, 0, 0, 1], [1, 2, 1, 0, 0, 0, 0, 0, 1, 2], [1, 0, 0, 0, 1, 2, 0, 0, 0, 2], [1, 0, 0, 0, 1, 2, 0, 1, 1, 2], [1, 0, 0, 0, 2, 1, 0, 0, 0, 2], [0, 0, 2, 2, 0, 0, 0, 1, 1, 2], [0, 0, 2, 2, 0, 0, 1, 0, 1, 2], [1, 1, 0, 2, 2, 1, 1, 0, 1, 2], [1, 2, 0, 0, 2, 1, 1, 0, 1, 2], [1, 1, 0, 2, 0, 1, 0, 2, 0, 2], [1, 1, 0, 2, 0, 1, 0, 2, 2, 0], [1, 1, 0, 2, 2, 1, 0, 2, 0, 1], [1, 1, 0, 2, 1, 0, 0, 2, 0, 2], [1, 1, 0, 2, 1, 2, 0, 2, 0, 1], [1, 1, 0, 2, 1, 2, 0, 2, 1, 0], [1, 1, 0, 2, 1, 2, 0, 1, 2, 0], [1, 1, 0, 0, 1, 2, 1, 2, 1, 2], [1, 1, 0, 2, 1, 2, 1, 0, 1, 2], [1, 2, 0, 0, 1, 2, 1, 0, 1, 2], [1, 1, 0, 1, 1, 2, 0, 2, 2, 0], [1, 1, 0, 1, 2, 1, 0, 2, 2, 0], [0, 0, 2, 2, 2, 1, 0, 0, 1, 2], [0, 0, 2, 2, 1, 2, 0, 0, 1, 2], [2, 2, 2, 0, 1, 1, 2, 2, 1, 2], [2, 1, 2, 2, 1, 1, 2, 2, 1, 2], [2, 2, 1, 2, 1, 1, 2, 2, 2, 2]], [[1, 1, 0, 0, 2, 1, 2, 0, 1, 1], [1, 0, 0, 0, 1, 2, 2, 0, 1, 0], [1, 0, 0, 0, 2, 1, 2, 0, 1, 0], [1, 1, 0, 2, 2, 1, 0, 2, 1, 1], [1, 1, 0, 2, 1, 2, 0, 2, 1, 1], [1, 2, 1, 0, 0, 0, 0, 0, 2, 2], [0, 0, 2, 2, 0, 0, 0, 1, 2, 2], [1, 2, 0, 0, 2, 1, 1, 0, 2, 2], [1, 1, 0, 2, 1, 2, 1, 0, 2, 2], [1, 2, 0, 0, 1, 2, 1, 0, 2, 2], [0, 0, 2, 2, 2, 1, 0, 0, 2, 2], [2, 2, 2, 0, 1, 1, 2, 2, 1, 2], [2, 1, 2, 2, 1, 1, 2, 2, 1, 2], [2, 2, 1, 2, 1, 1, 2, 2, 2, 2]], [[2, 0, 2, 2, 1, 2, 0, 2, 1, 1], [1, 0, 2, 2, 2, 2, 0, 2, 1, 1], [2, 0, 2, 2, 0, 0, 2, 0, 2, 2], [2, 0, 2, 1, 2, 0, 2, 0, 2, 2], [1, 2, 2, 1, 2, 1, 1, 2, 2, 2], [0, 0, 2, 2, 2, 2, 1, 2, 2, 2], [2, 0, 2, 2, 2, 1, 2, 1, 2, 2], [0, 0, 2, 2, 1, 2, 2, 2, 2, 2], [2, 0, 2, 2, 1, 1, 2, 2, 2, 2], [2, 2, 2, 2, 1, 1, 2, 2, 2, 1], [2, 2, 2, 2, 1, 1, 2, 1, 2, 2], [2, 0, 2, 1, 2, 2, 1, 2, 2, 2], [2, 0, 1, 2, 2, 2, 1, 2, 2, 2], [1, 2, 2, 2, 0, 0, 2, 2, 2, 2], [1, 2, 2, 2, 2, 2, 1, 1, 2, 2], [1, 0, 2, 2, 2, 2, 2, 1, 2, 2], [1, 0, 2, 1, 2, 2, 2, 2, 2, 2], [1, 2, 1, 2, 2, 2, 2, 2, 2, 2]], [[1, 0, 1, 0, 0, 0, 0, 0, 2, 2], [2, 0, 0, 0, 1, 2, 0, 0, 2, 0], [1, 2, 0, 0, 1, 0, 2, 0, 0, 2], [1, 2, 0, 0, 1, 0, 2, 0, 2, 0], [1, 2, 0, 0, 1, 2, 2, 0, 0, 1], [1, 2, 0, 0, 1, 2, 2, 0, 1, 0], [1, 0, 0, 0, 1, 2, 2, 0, 0, 2], [1, 0, 0, 0, 1, 2, 2, 0, 2, 0], [1, 1, 0, 2, 1, 0, 0, 2, 2, 2], [1, 1, 0, 0, 1, 2, 2, 2, 2, 1], [1, 1, 0, 2, 1, 2, 2, 0, 2, 1], [1, 1, 0, 2, 1, 2, 0, 2, 1, 2], [1, 1, 0, 0, 1, 2, 2, 1, 2, 2], [1, 2, 0, 0, 1, 2, 0, 1, 2, 2], [1, 1, 0, 2, 1, 2, 1, 0, 2, 2], [1, 2, 0, 0, 1, 2, 1, 0, 2, 2], [1, 1, 0, 1, 1, 2, 2, 0, 2, 2], [0, 0, 2, 2, 2, 1, 0, 0, 2, 2], [0, 0, 2, 2, 1, 2, 0, 0, 2, 2], [0, 2, 1, 2, 1, 2, 0, 0, 2, 2], [2, 2, 2, 0, 1, 1, 2, 2, 1, 2], [2, 1, 2, 2, 1, 1, 2, 2, 1, 2], [2, 2, 1, 2, 1, 1, 2, 2, 2, 2], [0, 1, 1, 2, 2, 2, 2, 2, 2, 2]]]    
    red = ReduceSol(None, AllSol)
    red.reduce()
    red.GetSimpleValue(red.AllSolutions[0][0])
    red.GetSubValues(red.AllSolutions[0][0])
    print [[sol[:10] for sol in Solution] for Solution in red.AllSolutions]
    print [[red.Length(sol) for sol in Solution] for Solution in red.AllSolutions]
    print [sum([red.Length(sol) for sol in Solution]) for Solution in red.AllSolutions]
    
    
if __name__ == '__main__':
    main()

##import sympy
##
##Inputs = sympy.symbols('S3 S4 S5 S6')
##Outputs = sympy.symbols('Th0 Th1 Th2 Th3 Th4')
##Equations=[]
##for out in range(1,outs):
##    tree = parent.solution[out]
##    root = tree.GetRootItem()
##    solution=tree.GetItemText(root)
##    solution = solution.split('=')[1]
##    solution = solution.replace('|','~')
##    solution = solution.replace('.','&')
##    solution = solution.replace('+','|')
##    res = sympy.sympify(solution)
##    print res
##    Equations[out] = res
##
##for index0, Equation0 in enumerate(Equations[:-1]):
##    # Seach for same solution
##    for  index1, Equation1 in enumerate(Equations[index0+1:],index0+1):
##        if Equation0 == Equation1:
##            # Same solution
##            Equations[index1] = Outputs[index0]
##            break
##        for index10, arg in enumerate(Equation1.args):
##            if Equation0 == arg:
##                # Same solution in equation
##                argleft = list(Equation1.args)
##                argleft.remove(arg)
##                argleft.append(Outputs[index0])
##                Equations[index1] = Equation1.func(tuple(argleft))
##                break
##            for index100, arg1 in enumerate(args.args):
##                break
##    # Search for same equation or part of it
##    for index00, arg in enumerate(Equation0.args):
##        break
    
        