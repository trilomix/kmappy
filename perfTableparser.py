#! /usr/bin/env python

#from exception import exception
import re



"""
  Python class that parses a perftable file from GoldenGate
  see 'help(perfTableParser.perfTableParser)' for details
"""

class localException(Exception):
    pass


class perfTableParser:
    """
    Classe permettant de parser les fichiers de perf de GoldenGate
    Retourne une structure contenant les performances ( @TODO classe a definir)
    """

    # Expression reguliere permettant de parser les noms de variables - cf 'processDeclarationName'
    re_varName = re.compile(r"([a-zA-Z0-9_][a-zA-Z0-9_@<>]*)(\([a-zA-Z0-9_][a-zA-Z0-9_@<>]*\))?$")

    def parseFile(self, parent, fileName):
        """
          Parse le fichier dont le path est en argument
          Met a jour le parent
        """

        # Initialisation du parser
        self.i__init()
        self.parent = parent

        try:
            fHandle = open(fileName, 'r')
        except:
            self.errorMsg = "Unable to open file '" + fileName + "'"
            raise exception(self.errorMsg)

        try:
            # Fonction interne de parse
            self.i__parseFile(fHandle)
        except localException ,e:
            print "parsing failed at line ", self.lineNumber
            print e
        except ValueError, e:
            print "parsing failed at line ", self.lineNumber
            print e
    #    except Exception, e :
    #      print " INTERNAL[perfTableParser] : unknown exception found; please report bug"
    #      print e
    #      #raise e
        else:
            # Parsing seems OK
            self.valid = True

        fHandle.close()

        return self.valid

    def parseClipboard(self, parent, TextObject):
        """
          Parse le text en argument
          Met a jour le parent
        """

        # Initialisation du parser
        self.i__init()
        self.parent = parent

        try:
            # Fonction interne de parse
            self.i__parseText(TextObject)
        except localException ,e:
            print "parsing failed at line ", self.lineNumber
            print e
        except ValueError, e:
            print "parsing failed at line ", self.lineNumber
            print e
    #    except Exception, e :
    #      print " INTERNAL[perfTableParser] : unknown exception found; please report bug"
    #      print e
    #      #raise e
        else:
            # Parsing seems OK
            self.valid = True

        return self.valid

    def i__init(self):
        """
          Initializes the parsing - called by self.parse
        """
        # Numero de ligne courant
        self.lineNumber = 0
        # Liste des variables
        self.variablesList = None
        # Number of datas per line
        self.datasPerLine = 0
        # Flag pour savoir si le parsing a reussi ou non
        self.valid = False
        # Message d'erreur
        self.errorMsg = "?"
        # Tableau final
        self.myArray = []
        # specification variable
        self.specVarName = None
        # performances
        self.performancesNames =[]

    def i__parseFile(self, fHandle):
        """
          Fonction interne de parsing appelee par self.parseFile, qui retourne des exceptions en cas d'erreur
        """
        numbersParse = False             # True si on est en train de parser les datas
        lastCommentLine = "%"           # String de la derniere ligne de commentaires parsee
        for line in fHandle:
            self.lineNumber = self.lineNumber+1
            # On debarasse la ligne des espaces & tabulations redondants et des caracs de fin de ligne
            line = self.cleanUpLine(line)
            if 0 <> len( line):
                if numbersParse:
                    # Ligne de datas
                    self.processDataLine(line)
                else:
                    # Ligne de 'commentaires'
                    if self.processCommentLine(line):
                        lastCommentLine = line
                    else:
                        # On est en train de commencer le parsing des datas
                        numbersParse = True
                        # La derniere ligne de commentaires contient les noms des variables
                        self.processDeclarationLine(lastCommentLine)
                        # On parse la premiere ligne de datas
                        self.processDataLine(line)


    def i__parseText(self, TextObject):
        """
          Fonction interne de parsing appelee par self.parseText, qui retourne des exceptions en cas d'erreur
        """
        numbersParse = False             # True si on est en train de parser les datas
        for line in TextObject.split('\n'):
            self.lineNumber = self.lineNumber+1
            # On debarasse la ligne des espaces & tabulations redondants et des caracs de fin de ligne
            line = self.cleanUpLine(line)
            if 0 <> len( line):
                if numbersParse:
                    # Ligne de datas
                    self.processDataLine(line)
                else:
                    resultList = []
                    tokens = line.split()
                    for token in tokens:
                        myTupple = self.processDeclarationName(token)
                        resultList.append(myTupple)
                    self.variablesList = resultList
                    
                    # On va maintenant calculer le nombre de datas attendues par ligne
                    finalSize = 0
                    for elt in resultList:
                        finalSize = finalSize + elt[2]
                    self.datasPerLine = finalSize
                    # On est en train de commencer le parsing des datas
                    numbersParse = True


##        # On reconstruit la liste des inputs
##        # Cas particulier sans sweep principal
##        if None != self.specVarName:
##            self.sweepVarNames.append(self.specVarName )


    def cleanUpLine(self, line):
        """
        Remove whitespaces, carriage return at the beginnig and at the end of the line
        """
        line = line.expandtabs()
        line = line.strip(None)
        # Remove duplicate space
        line = ' '.join(line.split())

        return line

    def processCommentLine(self, line):
        """
        Parses the 'comment' line at the beginning of the file
        returns True if it matches, else False
        We also try to detect the sweep variables names
        """
        if '%' <> line[0]:
            return False

        if line.startswith('% specification_variable'):
            tmp = line.partition('% specification_variable')
            tmpName = tmp[2].strip()
            # Cas particulier ou aucun sweep principal n'est defini
            if "<notDefined>"  != tmpName:
                self.specVarName = tmpName
        elif line.startswith('% sweep_variables'):
            tmp = line.partition('% sweep_variables')
            tmpName = tmp[2]
            # Cas particulier ou aucun sweep secondaire n'est defini
            if " <notDefined>"  != tmpName:
                self.sweepVarNames = tmpName.split()
            else:
                self.sweepVarNames = []

        elif line.startswith('%performance'):
            tmp = line.split()
            self.performancesNames.append(tmp[1])
        return True


    def processDeclarationLine(self, line):
        """
        Processes the line that declares the variables , ie
        %             PIN                    PAE_c(RI)         ACPR_left        ACPR_right               Pin              Pout               Pdc
        % nom1 nom2 nom3(RI) nom4
        si le nom n'est pas suivant d'une declaration entre parentheses, c'est un float
        si le nom est suivi d'une decalaration entre parenthese, on attend (RI) ( reel / imaginaire)
        Returns an array of tupples : [ (name, type, size), ...]
        """
        resultList = []
        tokens = line.split()
        if '%' <> tokens.pop(0):
            throw( "'%' expected at the begining of the variables declaration")
        for token in tokens:
            myTupple = self.processDeclarationName(token)
            resultList.append(myTupple)

        self.variablesList = resultList

        # On va maintenant calculer le nombre de datas attendues par ligne
        finalSize = 0
        for elt in resultList:
            finalSize = finalSize + elt[2]
        self.datasPerLine = finalSize
        return

    def processDeclarationName(self, name):
        """
        Traite une decalaration de nom dans la ligne de declaration des variables
        Ex: "PIN" "PAE_c(RI)" ...
        Returns a tupple : (name, type, size)
        where:
          'name' is the base name
          'type' is the corresponding python type
          'size' is the number of corresponding numbers of datas in the result array
        """
        # On analyse chaque nom et on regarde si c'est un reel ou un complexe
        myMatch = self.re_varName.match(name)
        if None == myMatch:
            raise localException( "Un-recognized variable declaration : '" + str(name) + "'" )
        varName     = myMatch.group(1)
        myExtension = myMatch.group(2)
        if None == myExtension:
            myType = float
            mySize = 1
        elif "(RI)" == myExtension:
            myType = complex
            mySize = 2
        else:
            raise localException("Sorry, type '"+myExtension+"' is not supported")
        return varName, myType, mySize

    def processDataLine(self, line):
        """
        Processes a line of datas
        Checks that there is the right number of elements and that they are all floats
        Returns a list of values corresponding to the variable types
        """
        tokens = line.split()
        if len(tokens) < self.datasPerLine:
            raise localException( str(self.datasPerLine) + " values were expected, but I found " + str( len(tokens)) )
        myList = []
        for myTupple in self.variablesList:
            lType = myTupple[1]
            lSize = myTupple[2]
            lArray = []
            for i in range(lSize):
                tmp = tokens.pop(0)
                if tmp == '?':
                    # conversion des ? en 2
                    myFloat = float('2')
                    lArray.append(myFloat)
                    myNumber = lType(*lArray)
                    myList.append(myNumber)
                elif tmp != 'X' and tmp != 'x':
                    # This will throw an error if data is not a float
                    myFloat = float(tmp)
                    lArray.append(myFloat)
    
                    # On convertit dans le type
                    myNumber = lType(*lArray)
                    myList.append(myNumber)
                else:
                    myList.append(tmp.upper())
        self.myArray.append(tuple(myList) )

        return



    def getSweepsNames(self):
        return self.sweepVarNames

    def getPerfsNames(self):
        return self.performancesNames


    ################################################################################
