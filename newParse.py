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

#After finding and storing the needed pages, start finding the numbers we need
def parseStoredPages():
    for page in statementOfNetPositionPages:
        printNextLine = False

        extractedText = page.extract_text()
        extractedText = unicodedata.normalize('NFKD', extractedText)
        extractedText = extractedText.upper()
        splitText = extractedText.split('\n')

        for line in splitText:
            if printNextLine:
                #Needs some fixing so it only prints the lines under the "Due within one/more than one year:" line
                if not line.startswith("DUE"):
                    #Keep printing till you either reach the next "due within" category or reach the total liablities line
                    if line.startswith("TOTAL"):
                        printNextLine = False
                    else:
                        #For easier reading
                        print('\t' + line)
                        continue
                else:
                    printNextLine = False
            
            #Cash and pooled investments
            if "CASH" in line and "INVESTMENT" in line:
                print("Assets - " + line)
            #Some have investments on a separate row
            elif line.startswith("INVESTMENTS"):
                print("Assets - " + line)
            #Capital assets being/not being depreciated
            elif "ASSETS" in line and ("DEPRECIATED" in line or "DEPRECIATION" in line):
                print("Assets - " + line)
            #Total assets
            elif line.startswith("TOTAL ASSETS"):
                print("Assets - " + line)
            #Some formats have "due within one year:" broken down, if so print the rows under
            elif "DUE" in line and "YEAR" in line:
                if 'YEAR:' in line:
                    printNextLine = True
                print("Liabilities - " + line)
            #Total liabilities
            elif line.startswith("TOTAL LIABILITIES"):
                print("Liabilities - " + line)
            elif "NET" in line:
                #Total net position
                if line.startswith("TOTAL NET POSITION"):
                    print(line)
                #Net pension liability
                if "PENSION" in line and "LIABILITY" in line:
                    print("Liabilities - " + line)
                #Postemployment benefits or OPEB
                elif (("OTHER" in line and "POSTEMPLOYMENT" in line and "BENEFITS" in line) or "OPEB" in line) and "LIABILITY" in line:
                    print("Liabilities - " + line)
                #Net investment in capital assets
                elif "INVESTMENT" in line and "CAPITAL" in line and "ASSET" in line:
                    print("Net position - " + line)
            #Unrestricted (deficit)
            elif line.startswith("UNRESTRICTED"):
                print("Net position - " + line)
            #elif "TOTAL" in line and "NET" in line and "POSITION" in line:
             #   print(line)