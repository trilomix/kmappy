from math import *
import traceback
from multiprocessing import Process, Queue

class KarnaughNode(object):
    def __init__(self):
        self.values = []
        self.numberOfItems = 0
        self.flag = False

class JoinNode(object):
    def __init__(self, newblocks, removeblocks):
        self.newblocks = newblocks
        self.removeblocks = removeblocks

class JoinTask(Process):
    def __init__ (self,parent, blocks, a, i, resultQueue, process_counter):
        Process.__init__(self)
        self.daemon = False
        self.status = -1
        self.parent = parent
        self.blocks = blocks
        self.newblocks = []
        self.a      = a
        self.i      = i
        self.resultQueue = resultQueue
        self.process_counter = process_counter

    def Join(self, blocks, a, i):
        for b in blocks:
            if(     (a.numberOfItems == pow(2.0, i-1)) &
                    (b.numberOfItems == pow(2.0, i-1)) ):
                x=self.parent.IsJoinable(a.values, b.values )
                if(x>0):
                    #/* If they can be joined make a new block with 2 in the place
                    #of the one bit where they a and b are different */
                    n = KarnaughNode()
                    n.numberOfItems=a.numberOfItems*2
                    n.flag = False
                    for j in range(0, len(a.values) ):

                        if(j!=(x-1)):
                            n.values.append(a.values[j] )
                        else:
                            n.values.append( 2 )

                    #/* Mark that a node is part of a larger node */
                    a.flag=True
                    b.flag=True

                    #/* Check if that block already exists in the list */
                    exist=False
                    for c in self.parent.blocks:
                        if(n.values==c.values):
                            exist=True

                    if(not exist):
                        self.newblocks.append(n )

    def run(self):

        try:
            self.Join(self.blocks, self.a, self.i)
            removeblocks = [block for block in self.blocks if (block.flag==True) ]
            self.resultQueue.put(JoinNode(self.newblocks,removeblocks))
        except:
            print "****************process_counter : %s****************" % self.process_counter
            traceback.print_exc()
            pass

class KarnaughMap(object):

    def __init__(self, n, MaxProcess=16384):

        self.blocks = []
        self.kmap = {}
        self.kmapDCare = {}
        self.kmapValues = {}

        self.MaxProcess = MaxProcess
        print "MaxProcess %d" % MaxProcess
        # Set number of variables
        self.numberOfVariables=n
        self.numberOfDCares=0
        # Determine width and height from n. of vars
        self.width=int(pow(2, ceil(n/2.0)))
        self.height=int(pow(2, floor(n/2.0)))

        # Fill map with 0s and clear the list of KarnaughNodes
        self.Reset()

        # Fill map kmapValues with values that each cell in the map
        # has. Look here for rules:
        # http:#www.allaboutcircuits.com/vol_4/chpt_8/3.html
        if(self.numberOfVariables>2):
            for i in range(0,self.height):
                for j in range(0,self.width):
                    if(i%2 ==0 ):
                        self.kmapValues[(j, i)]=self.GrayEncode(j+((i)*self.width))
                    else:
                        self.kmapValues[(j, i)]=self.GrayEncode(self.width-1-j+((i)*self.width))
        else:
            if(self.numberOfVariables==2):

                self.kmapValues[(0, 0)]=0
                self.kmapValues[(1, 0)]=1
                self.kmapValues[(0, 1)]=2
                self.kmapValues[(1, 1)]=3

            if(self.numberOfVariables==1):

                self.kmapValues[(0, 0)]=0
                self.kmapValues[(1, 0)]=1




    def Reset(self):

        """ Fills map with zeros and deletes all nodes from the solution list """

        for i in range(0,self.height):
            for j in range(0,self.width):
                self.Set(j, i, 0 )
        self.blocks=[]


    def Solve(self):

        """ Iterates through all possible ways that 'Don't cares' can be
        arranged, and finds one with fewest number of nodes in the solution
        (bestc). If there are more ways that give the same number of nodes
        in the solution choose the one with biggest nodes (bestsc) """

        best = []
        bestc=-1
        bestsc=0
        #for i in range(0, int(pow(2.0, self.numberOfDCares )) ):
        for i in range(0, 1 ):

            b = []
            j=i
            while(j>0):

                b.insert(0, (j%2) )
                j=j/2

            for j in range(len(b), self.numberOfDCares):
                b.insert(0, 0 )

            self.blocks= []

            c=0
            for k in range(0, self.height):

                for l in range(0, self.width):

                    if(self.kmapDCare[(l, k)]==1):

                        self.kmap[(l, k)]=1
                        #if(b[c]==1):
                        #    self.kmap[(l, k)]=1
                        #else:
                        #     self.kmap[(l, k)]=0;
                        c += 1




            self.Solve2( )

            if( (bestc==-1) | (len(self.blocks)<=bestc) ):

                sc=0
                for iter in self.blocks:

                    for i in range(0,len(iter.values) ):
                        if(iter.values[i]==2):
                            sc += 1


                if( (bestc==-1) | (len(self.blocks)<bestc) ):

                    best=self.blocks
                    bestc=len(best)
                    bestsc=sc

                else:

                    if( sc>bestsc ):

                        best=self.blocks
                        bestc=len(best)
                        bestsc=sc




        self.blocks=best


    def Solve2(self):

        def Join():
            blocks.remove(a)
            for b in blocks:
                if(     (a.numberOfItems == pow(2.0, sizeloop-1)) &
                        (b.numberOfItems == pow(2.0, sizeloop-1)) ):
                    x=self.IsJoinable(a.values, b.values )
                    if(x>0):
                        #/* If they can be joined make a new block with 2 in the place
                        #of the one bit where they a and b are different */
                        n = KarnaughNode()
                        n.numberOfItems=a.numberOfItems*2
                        n.flag = False
                        for j in range(0, len(a.values) ):

                            if(j!=(x-1)):
                                n.values.append(a.values[j] )
                            else:
                                n.values.append( 2 )

                        #/* Mark that a node is part of a larger node */
                        a.flag=True
                        b.flag=True

                        #/* Check if that block already exists in the list */
                        exist=False
                        for c in self.blocks:
                            if(n.values==c.values):
                                exist=True

                        if(not exist):
                            self.blocks.append(n )

        def CleanProcess():
            for process in ProcessList:
                process.join()

            for process in ProcessList:
                jn = resultQueue.get()
                for n in jn.newblocks:
                    exist = False
                    for c in self.blocks:
                        if(n.values==c.values):
                            exist=True
                    if(not exist):
                        self.blocks.append(n )
                for b in jn.removeblocks:
                    for c in self.blocks:
                        if(b.values==c.values):
                            self.blocks.remove(c)

        """ Check for special case that all cells in the map are the same """
        a=1
        for i in range(0,self.height):
            if(a==0):
                break
            for j in range(0,self.width):
                if( self.kmap[(j, i)]!=self.kmap[(0, 0)] ):
                    a=0
                    break
        if(a==1):

            #/* Clear the list so that all those nodes with one item are deleted */
            self.blocks=[]

            # If there are only zeros in the map there's nothing to solve
            if (self.kmap[(0, 0)]==0):
                 return
            else:

                # If there are only ones, solution is one element as big as the map
                n=KarnaughNode()
                n.numberOfItems = self.width*self.height
                for j in range(0,self.numberOfVariables):
                    n.values.append( 2 )
                self.blocks.append(n )
                return



        #/* Put all blocks with 1 element in list */
        for i in range(0, self.height):

            for j in range(0, self.width):

                if(self.kmap[(j, i)]==1):

                    n=KarnaughNode()
                    n.numberOfItems=1
                    n.flag=False
                    n.values=self.GetMapBoolValue(j, i )
                    self.blocks.append(n )




        # Joining blocks into blocks with 2^i elements
        for sizeloop in range( 1, int(log(self.width*self.height )/log(2)+1) ):
            #/* Check every block with every other block and see if they can be joined
            #into a bigger block */
            blocks = [block for block in self.blocks if (block.numberOfItems == pow(2.0, sizeloop-1)) ]
            ##  resultQueue = Queue()
            ##  ProcessList = []
            #checked_blocks = []
            for a in blocks:
                #checked_blocks.append(a)
                Join()
##                processblocks = list(blocks)
##                process = JoinTask(self, processblocks, a, i, resultQueue, len(ProcessList))
##                ProcessList.append(process)
##                process.run()
##                process.start()
##                if len(ProcessList) >= self.MaxProcess:
##                    print "Solve2 len(ProcessList) %d" % len(ProcessList)
##                    CleanProcess()
##                    ProcessList = []
##            CleanProcess()

            # Flag block include in other block
            a_blocks = [block for block in self.blocks if (block.flag==False and block.numberOfItems < pow(2.0, sizeloop)) ]
            for a_block in a_blocks:
                b_blocks = [block for block in self.blocks if (block!=a_block and block.numberOfItems > a_block.numberOfItems) ]
                for b_block in b_blocks:
                    flag_block = True
                    for index in range(len(b_block.values)):
                        if a_block.values[index] != b_block.values[index] and b_block.values[index] != 2:
                            flag_block = False
                            break
                    if flag_block:
                        self.blocks.remove(a_block)
                        break

            #/* Deletes nodes that are cointained in larger nodes */
            blocks = [block for block in self.blocks if (block.flag==True) ]
            for a in blocks:
                self.blocks.remove(a)


        # Delete nodes that are Don't care only ones
        blocks = self.blocks
        for block in blocks:
            DCareblock = True
            for i in range(0,self.height):
                for j in range(0,self.width):
                    if(self.IsAtCell(j, i, block.values)):
                        if self.kmapDCare[(j, i)]!=1:
                            DCareblock = False
            if DCareblock:
                self.blocks.remove(block)

        #/* Deletes unneeded nodes. Draws a temp map with all nodes but one
        #and if that map is same as the main map, node that wasn't drawn can be deleted */

        temp = {}
        blocks = self.blocks
        for a in blocks:
            for i in range(0,self.height):
                for j in range(0,self.width):
                    temp[(j, i)]=0

            for b in blocks:
                if(a!=b):
                    for i in range(0,self.height):
                        for j in range(0,self.width):
                            if(self.IsAtCell(j, i, b.values)):
                                temp[(j, i)]=1
            del_var=1
            for i in range(0,self.height):
                for j in range(0,self.width):
                    if(temp[(j, i)]!=self.kmap[(j, i)]) and self.kmapDCare[(j, i)] != 1 :
                        del_var=0
                        break
                if(not del_var):
                    break
            if(del_var):
                self.blocks.remove(a )

    def IsAtCell(self,  x,  y,  a):

        b=self.GetMapBoolValue(x, y )
        for i in range(0, len(a) ):
            if( (a[i]!=b[i]) & (a[i]!=2) ): return 0
        return 1


    def GetMapBoolValue(self, x, y):

        b = []
        i=self.GetMapValue(x, y )
        while(i>0):

            b.insert(0, i%2 )
            i=i/2

        for j in range(len(b), self.numberOfVariables):
            b.insert(0, 0 )
        return b


    def IsJoinable(self, a, b):
        """ Checks if 2 karnaugh nodes with values a and b are joinable (only differ in one bit),
        and if they are returns (place where they differ + 1), otherwise returns 0 """

        c=0
        for i in range(0,len(a)):

            if(a[i]!=b[i]):

                c += 1
                x=i
        if(c==1):
            return x+1
        else:
            return 0


    def GrayEncode(self, g):

        return int(g) ^ (int(g) >> 1 )



    def Set(self, x, y, value):

        self.kmap[(x, y)]=value
        if(value==2) :

            self.kmapDCare[(x, y)]=1
            self.numberOfDCares += 1

        else:
            self.kmapDCare[(x, y)]=0


    def Get(self, x, y):

        if(not self.kmapDCare[(x,y)]):
            return self.kmap[(x,y)]
        else:
            return 2


    def GetMapValue(self, x, y):

        return self.kmapValues[(x,y)]


    def GetWidth(self):

        return self.width


    def GetHeight(self):

        return self.height


    def GetSolutions(self):

        return self.blocks


    def GetNumberOfVars(slef):

        return self.numberOfVariables
