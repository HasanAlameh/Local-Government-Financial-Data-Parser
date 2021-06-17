import re
from tkinter.constants import WORD
import pdfplumber
import pandas as pd
from collections import namedtuple
from datetime import date
import csv
from pdfplumber.utils import WordExtractor
import unicodedata

#Each of our required statements will have their corresponding pages stored
statementOfNetPositionPages = []
statementOfNetPositionProprietaryFunds = []
statementOfActivitiesPages = []
balanceSheetGovFundsPages = []
statementOfRevExpendAndChangesGovernmentalFundsPages = []
statementOfRevExpAndChangesProprietaryFundsPages = []

#Grabs the pages needed and stores them
def file_parse(file):
    documentDate = ""
    municipalityName = ""
    balanceSheetFound = False
    statementOfRevGovFundsFound = False
    netPositionProprietaryFundsFound = False
    statementOfActivitiesFound = False
    statementOfRevProprietaryFundsFound = False
    previousPage = None
    previousPageAdded = False
    textFound = False


    #Specifying that the date format used is always (mmmm dd, yyyy)
    dateFilter = re.compile(r'[a-zA-Z]+\s\d\d[,]\s\d\d\d\d')

    #Read the PDF file
    with pdfplumber.open(file) as pdf:

        #Iterate through pages to find the headers we are interested in
        #Each header found gets added to its appropriate array
        for page in pdf.pages:
            extractedText = page.extract_text()
            textFound = False

            #If extracted text is not empty
            if extractedText:
                #In case some PDFs (like Saginaw County's) use unicode characters that mess up the comparisons
                extractedText = unicodedata.normalize('NFKD', extractedText)
                extractedText = extractedText.upper()

                #Each line is placed as a list item
                splitText = extractedText.split('\n')

                #If any page is appended, always append the following one just in case
                if balanceSheetFound:
                    if "RECONCILIATION" not in extractedText:
                        balanceSheetGovFundsPages.append(page)
                    previousPage = page
                    balanceSheetFound = False
                    continue

                if statementOfRevGovFundsFound:
                    statementOfRevExpendAndChangesGovernmentalFundsPages.append(page)
                    previousPage = page
                    statementOfRevGovFundsFound = False
                    continue

                if netPositionProprietaryFundsFound:
                    statementOfNetPositionProprietaryFunds.append(page)
                    previousPage = page
                    netPositionProprietaryFundsFound = False
                    continue

                if statementOfActivitiesFound:
                    statementOfActivitiesPages.append(page)
                    previousPage = page
                    statementOfActivitiesFound = False
                    continue

                if statementOfRevProprietaryFundsFound:
                    statementOfRevExpAndChangesProprietaryFundsPages.append(page)
                    previousPage = page
                    statementOfRevProprietaryFundsFound = False
                    continue
                
                #Skip table of contents pages
                if "TABLE OF CONTENTS" in extractedText or any(line == "CONTENTS" for line in splitText):
                    continue

                for line in splitText:
                    line = line.strip()

                    #Find Statement of Net Position pages
                    if (line == "STATEMENT OF NET POSITION" or line == "STATEMENT OF NET POSITION (CONTINUED)") and not any(line.startswith("FIDUCIARY FUNDS") for line in splitText):
                        #If date has not been found yet
                        if not documentDate:
                            if len(dateFilter.findall(extractedText)):
                                documentDate = dateFilter.findall(extractedText)[0]

                        #If the municipality name has not been found yet
                        if not municipalityName:
                            #Municipality name is always the first line of the page
                            municipalityName = splitText[0]

                        #If statement of net position - proprietary funds is found, place the page in the corresponding list
                        if "PROPRIETARY FUNDS" in extractedText:
                            #Make sure the page is not a "notes to financial statements" page
                            if  not any(line.startswith("COMPONENT UNITS") for line in splitText):
                                #In some formats (like Detroit 2020), the row titles are on the previous page with no page header
                                if previousPageAdded:
                                    previousPageAdded = False
                                else:
                                    #Look for duplucates
                                    if not any(findPage == previousPage for findPage in statementOfNetPositionProprietaryFunds):
                                        statementOfNetPositionProprietaryFunds.append(previousPage)
                                    previousPageAdded = True
                                statementOfNetPositionProprietaryFunds.append(page)
                                textFound = True
                                netPositionProprietaryFundsFound = True

                        #If statement of net position is found, place the page in the corresponding list 
                        #Make sure the page is not a "notes to financial statements" page
                        elif ("NOTES" in splitText[-1] or "NOTES" in splitText[-2] or "NOTES" in splitText[-3]) and not any(line.startswith("COMPONENT UNITS") for line in splitText):
                                statementOfNetPositionPages.append(page)
                                textFound = True

                    #Find statement of activities pages
                    elif (line == "STATEMENT OF ACTIVITIES" or line == "STATEMENT OF ACTIVITIES (CONTINUED)"):
                        #Some formats (like Livingston 2019) have the row titles on a previous page with no page header
                        if previousPageAdded:
                                    previousPageAdded = False
                        else:
                            if not any(findPage == previousPage for findPage in statementOfActivitiesPages):
                                statementOfActivitiesPages.append(previousPage)
                            previousPageAdded = True
                        statementOfActivitiesPages.append(page)
                        statementOfActivitiesFound = True
                        textFound = True

                    #Some formats have "balance sheet" and "governmental funds" on separate lines
                    elif line.startswith("BALANCE SHEET") and (any (findLine.startswith("GOVERNMENTAL FUNDS") for findLine in splitText) or line.endswith("GOVERNMENTAL FUNDS")):
                        balanceSheetGovFundsPages.append(page)
                        #Some balance sheets extend to a second page, so get it just in case
                        balanceSheetFound = True
                        textFound = True

                    #Some formats have "statement of revenue", others have "statement of revenues" 
                    elif  line.startswith("STATEMENT OF REVENUE"):
                        #For statement of revenues, expenditures, and changes in fund balance - governmental funds
                        if "EXPENDITURES" in extractedText and "CHANGE" in extractedText and "FUND BALANCE" in extractedText and (any(line.startswith("GOVERNMENTAL FUNDS") for line in splitText)):
                            statementOfRevExpendAndChangesGovernmentalFundsPages.append(page)
                            #In case it extends to a second page
                            statementOfRevGovFundsFound = True
                            textFound = True
                        #For statement of revenues, expenses and changes in fund net position - proprietary funds
                        elif "EXPENSES" in extractedText and "CHANGE" in extractedText and "NET POSITION" in extractedText and (any(line.startswith("PROPRIETARY FUNDS") for line in splitText)):
                            if previousPageAdded:
                                previousPageAdded = False
                            else:
                                if not any(findPage == previousPage for findPage in statementOfRevExpAndChangesProprietaryFundsPages):
                                    statementOfRevExpAndChangesProprietaryFundsPages.append(previousPage)
                                previousPageAdded = True
                            statementOfRevExpAndChangesProprietaryFundsPages.append(page)
                            statementOfRevProprietaryFundsFound = True
                            previousPageAdded = True
                            textFound = True
            if not textFound:
                previousPageAdded = False
            previousPage = page
        
        #These prints are placeholders for now, use them to check if page extraction was successful
        """
        print("Municipality: ", municipalityName)
        print("Date of document: ", documentDate)
        print("\nSTATEMENT OF NET POSITION PAGES\n")
        print("---------------------------------------------------")
        for currentPage in statementOfNetPositionPages:
            textFromPage = (currentPage.extract_text()).upper()
            textFromPage = textFromPage.replace('$', '')
            print("----------------------------------------------------------------------------")
            print(textFromPage)

        print("\nSTATEMENT OF NET POSITION - PROPRIETARY FUNDS PAGES\n")
        print("---------------------------------------------------")
        for currentPage in statementOfNetPositionProprietaryFunds:
            textFromPage = (currentPage.extract_text()).upper()
            textFromPage = textFromPage.replace('$', '')
            print("----------------------------------------------------------------------------")
            print(textFromPage) 
        print("\nSTATEMENT OF ACTIVITIES PAGES\n")
        print("---------------------------------------------------")
        for currentPage in statementOfActivitiesPages:
            textFromPage = (currentPage.extract_text()).upper()
            textFromPage = textFromPage.replace('$', '')
            print("----------------------------------------------------------------------------")
            print(textFromPage) 
        print("\nBALANCE SHEET - GOV FUNDS PAGES\n")
        print("---------------------------------------------------")
        for currentPage in balanceSheetGovFundsPages:
            textFromPage = (currentPage.extract_text()).upper()
            textFromPage = textFromPage.replace('$', '')
            print("----------------------------------------------------------------------------")
            print(textFromPage) 
        print("\nSTATEMENT OF REVENUE PAGES\n")
        print("---------------------------------------------------")
        for currentPage in statementOfRevExpendAndChangesGovernmentalFundsPages:
            textFromPage = (currentPage.extract_text()).upper()
            textFromPage = textFromPage.replace('$', '')
            print("----------------------------------------------------------------------------")
            print(textFromPage)
        print("\nSTATEMENT OF REVENUE PROPRIETARY FUNDS PAGES\n")
        print("---------------------------------------------------")
        for currentPage in statementOfRevExpAndChangesProprietaryFundsPages:
            textFromPage = (currentPage.extract_text()).upper()
            textFromPage = textFromPage.replace('$', '')
            print("----------------------------------------------------------------------------")
            print(textFromPage)"""

        parseStoredPages()
        return file

        #with open('newOutput.csv', 'w') as f:
        #    writer = csv.writer(f, delimiter='\n')
        #    writer.writerow(text)

#Clean an extracted row & combine its headers 
def cleanCombineRow(listName):
    numberStart = 0
    
    #Remove '$' symbols, if applicable
    if ('$' in listName):
        for index, ele in enumerate(listName):
            if ele == '$':
                listName.pop(index)
    
    #Combine seperated label
    for index, ele in enumerate(listName):
        try:
            if (ele[0].isdigit() or ele[1].isdigit()):   #((ele[0].isdigit() and ele[1] != ')')  or ele[1].isdigit()):  (for case when e.g. "5)"? ")
                numberStart = index
                break
        except IndexError:
            print("Err: Index out of range")
    listName[0:numberStart] = [' '.join(listName[0:numberStart])]

    #Combine seperated numbers (single digits only)
    for index, ele in enumerate(listName):
        try:
            if(len(ele) == 1 and ele.isdigit()):
                if(listName[index+1][0].isdigit or listName[index+1][1].isdigit):
                    listName[index : index+2] = [''.join(listName[index : index+2])]
                    print("Joined numbers!")
                
        except IndexError:
            print("Err: Index out of range")

def storeRow(txtLine):
    ##txtLine = re.sub('(?<=\d) (?=\d)', '', txtLine) #TODO: This line is a BAND-AID fix for e.g. Wayne County that may have "mystery spaces" in their numbers
    tempRow = txtLine.split()
    cleanCombineRow(tempRow)
    rowList.append(tempRow)

rowList = []

#After finding and storing the needed pages, start finding the numbers we need
def parseStoredPages():
    dataWantedFound = False
    #This array will be used to follow the tabs of the different rows to keep track of categories that are broken down
    tabValues = []
    defaultTabValue = None
    firstCharInLine = None

    for page in statementOfNetPositionPages:
        previousLine = None
        prefix = []
        printNextLine = False
        extractedText = page.extract_text(y_tolerance=5)
        extractedText = unicodedata.normalize('NFKD', extractedText)
        #extractedText = re.sub('\(.*?\)','', extractedText)
        splitText = extractedText.split('\n')
        previousFirstChar = None
        #page.chars is a list of the page's charachters, each character in the list is a dictionary with multiple keys
        #So we can extract the text values from the dictionaries into a list of chars
        pageChars = []
        for charObject in page.chars:
            pageChars.append(charObject.get('text'))

        for line in splitText:
            #Find the index of the matched line in page.chars, will be used to get the tab value
            splitCharacters = [x for x in line[0:10]]
            for i, j in enumerate(page.chars):
                 if splitCharacters == pageChars[i:i+len(splitCharacters)]:
                    firstCharInLine = page.chars[i]
                
            upperCaseLine = line.upper()

            if len(tabValues) == 1 and not defaultTabValue:
                defaultTabValue = float(firstCharInLine.get('x0')) - float(tabValues[-1])

            #Only print lines that contain numbers in them
            lineContainsNumbers = bool(re.search(r'-?\d+', re.sub('\(.*?\)','', upperCaseLine)))

            if tabValues:
                #This calculates the difference between the distances of the current row and the one before it from the left of the page
                #We will use it to know whether this row is tabbed more (meaning a value/category is broken down)
                tabDifference = float(firstCharInLine.get('x0')) - float(tabValues[-1])
                if previousFirstChar:
                    heightDifference = float(firstCharInLine.get('top')) - float(previousFirstChar.get('top'))
                #print("Tab difference at line: " + line + "\n" + str((tabDifference)))
                #print(prefix)
                #print(tabValues)
                if tabDifference > (defaultTabValue + 1):
                    prefix.append(previousLine + " - ")
                    tabValues.append(firstCharInLine.get('x0'))
                    #print("PUSHED " + prefix[-1])
                    #print("Tab difference: " + str(tabDifference) + " Default value: " + str(defaultTabValue))
                elif tabDifference < -1:
                    if prefix:
                        #print("POPPED " + prefix[-1])
                        prefix.pop()
                        dataWantedFound = False
                    if len(tabValues) > 1:
                        tabValues.pop()
                    while len(tabValues) > 1 and float(firstCharInLine.get('x0')) - float(tabValues[-1]) < -1:
                        tabValues.pop()
                        if prefix:
                            prefix.pop()

            if dataWantedFound and len(tabValues) > 1 and "TOTAL" not in upperCaseLine:
                print(''.join(prefix) + upperCaseLine)
            #Cash and pooled investments/cash equivalents
            elif "CASH" in upperCaseLine:
                if "INVESTMENT" in upperCaseLine or "EQUIVALENT" in upperCaseLine:
                    if lineContainsNumbers:
                        print("Assets - " + prefix[-1] + upperCaseLine) if prefix else print("Assets - " + upperCaseLine)
                    #Since it is always the first line in the table, its tab value will be used as an initial value for comparison with other lines
                    #initialTabValue = firstCharInLine.get('x0')
                    if not tabValues:
                        tabValues.append(firstCharInLine.get('x0'))
                    dataWantedFound = True
            #Some have investments on a separate row
            elif upperCaseLine.startswith("INVESTMENT"):
                if lineContainsNumbers:
                    print("Assets - " + prefix[-1] + upperCaseLine) if prefix else print("Assets - " + upperCaseLine)
                dataWantedFound = True
            #Capital assets being/not being depreciated
            elif "ASSETS" in upperCaseLine and ("DEPRECIATED" in upperCaseLine or "DEPRECIATION" in upperCaseLine or "DEPRECIABLE" in upperCaseLine):
                if lineContainsNumbers:
                    print("Assets - " + prefix[-1] + upperCaseLine) if prefix else print("Assets - " + upperCaseLine)
                dataWantedFound = True
            #Sometimes capital assets are broken down
            elif "CAPITAL" in upperCaseLine and "ASSETS" in upperCaseLine and not lineContainsNumbers:
                dataWantedFound = True
            #Total assets
            elif upperCaseLine.startswith("TOTAL ASSETS"):
                if lineContainsNumbers:
                    print("Assets - " + upperCaseLine)
                dataWantedFound = True
            #Some formats have "due within one year:" broken down, if so print the rows under
            elif ("DUE" in upperCaseLine and "YEAR" in upperCaseLine) or ("CURRENT" in upperCaseLine and "LIABILITIES" in upperCaseLine):
                if lineContainsNumbers:
                    print("Liabilities - " + prefix[-1] + upperCaseLine) if prefix else print("Liabilities - " + upperCaseLine)
                dataWantedFound = True
            #Total liabilities
            elif upperCaseLine.startswith("TOTAL LIABILITIES"):
                if lineContainsNumbers:
                    print("Liabilities - " + upperCaseLine)
                dataWantedFound = True
            elif "NET" in upperCaseLine:
                #Total net position
                if upperCaseLine.startswith("TOTAL NET POSITION"):
                    if lineContainsNumbers:
                        print(upperCaseLine)
                    dataWantedFound = True
                #Net pension liability
                if "PENSION" in upperCaseLine and "LIABILITY" in upperCaseLine:
                    if lineContainsNumbers:
                        print("Liabilities - " + prefix[-1] + upperCaseLine) if prefix else print("Liabilities - " + upperCaseLine)
                    dataWantedFound = True
                #Postemployment benefits or OPEB
                elif (("OTHER" in upperCaseLine and "POSTEMPLOYMENT" in upperCaseLine and "BENEFITS" in upperCaseLine) or "OPEB" in upperCaseLine) and "LIABILITY" in upperCaseLine:
                    if lineContainsNumbers:
                        print("Liabilities - " + prefix[-1] + upperCaseLine) if prefix else print("Liabilities - " + upperCaseLine)
                    dataWantedFound = True
                #Net investment in capital assets
                elif "INVESTMENT" in upperCaseLine and "CAPITAL" in upperCaseLine and "ASSET" in upperCaseLine:
                    if lineContainsNumbers:
                        print("Net position - " + prefix[-1] + upperCaseLine) if prefix else print("Net position - " + upperCaseLine)
                    dataWantedFound = True
            #Unrestricted (deficit)
            elif "UNRESTRICTED" in upperCaseLine:
                #if lineContainsNumbers:
                print("Net position - " + prefix[-1] + upperCaseLine) if prefix else print("Net position - " + upperCaseLine)
                dataWantedFound = True
            else:
                dataWantedFound = False


            previousLine = ((re.sub('[,-]', '', (re.sub('\d', '', line)))).replace('$','')).strip()
            if firstCharInLine:
                previousFirstChar = firstCharInLine
                
