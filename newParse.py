import re
from subprocess import REALTIME_PRIORITY_CLASS
from tkinter.constants import WORD
import pdfplumber
import csv
import unicodedata

#Each of our required statements will have their corresponding pages stored
statementOfNetPositionPages = []
statementOfNetPositionProprietaryFunds = []
statementOfActivitiesPages = []
balanceSheetGovFundsPages = []
statementOfRevExpendAndChangesGovernmentalFundsPages = []
statementOfRevExpAndChangesProprietaryFundsPages = []

documentDate = ""
municipalityName = ""

#Grabs the pages needed and stores them
def file_parse(file):
    global documentDate
    global municipalityName
    global statementOfNetPositionPages 
    global statementOfNetPositionProprietaryFunds 
    global statementOfActivitiesPages 
    global balanceSheetGovFundsPages 
    global statementOfRevExpendAndChangesGovernmentalFundsPages 
    global statementOfRevExpAndChangesProprietaryFundsPages 
    statementOfNetPositionPages = []
    statementOfNetPositionProprietaryFunds = []
    statementOfActivitiesPages = []
    balanceSheetGovFundsPages = []
    statementOfRevExpendAndChangesGovernmentalFundsPages = []
    statementOfRevExpAndChangesProprietaryFundsPages = []

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
                extractedText = extractedText.upper().replace('\u2010', '-')

                #Each line is placed as a list item
                splitText = extractedText.split('\n')

                
                #If any page is appended, always append the following one just in case
                if balanceSheetFound:
                    if 'SATEMENT OF REVENUE' in extractedText or 'TOTAL REVENUE' in extractedText:
                        statementOfRevExpendAndChangesGovernmentalFundsPages.append(page)
                    elif "RECONCILIATION" not in extractedText[0:10]:
                        balanceSheetGovFundsPages.append(page)
                    previousPage = page
                    balanceSheetFound = False
                    continue

                if statementOfRevGovFundsFound:
                    if "RECONCILIATION" not in extractedText[0:10]:
                        statementOfRevExpendAndChangesGovernmentalFundsPages.append(page)
                    previousPage = page
                    statementOfRevGovFundsFound = False
                    continue

                if netPositionProprietaryFundsFound:
                    if 'STATEMENT OF REVENUE' in extractedText or 'OPERATING REVENUE' in extractedText:
                        statementOfRevExpAndChangesProprietaryFundsPages.append(page)
                    elif ("RECONCILIATION" not in extractedText[0:10] and 'STATEMENT OF REVENUE' not in extractedText) or 'TOTAL CURRENT LIABILITIES' in extractedText:
                        statementOfNetPositionProprietaryFunds.append(page)
                    previousPage = page
                    netPositionProprietaryFundsFound = False
                    continue

                if statementOfActivitiesFound:
                    if 'BALANCE SHEET' in extractedText and 'GOVERNMENTAL FUNDS' in extractedText:
                        balanceSheetGovFundsPages.append(page)
                    elif "RECONCILIATION" not in extractedText[0:10]:
                        statementOfActivitiesPages.append(page)
                    previousPage = page
                    statementOfActivitiesFound = False
                    continue
                    

                if statementOfRevProprietaryFundsFound:
                    if "RECONCILIATION" not in extractedText[0:10]:
                        statementOfRevExpAndChangesProprietaryFundsPages.append(page)
                    previousPage = page
                    statementOfRevProprietaryFundsFound = False
                    continue
                
                #Skip table of contents pages
                if "TABLE OF CONTENTS" in extractedText or any(line == "CONTENTS" for line in splitText) or 'RECONCILIATION OF' in extractedText[0:10] or ('MANAGEMENT' in extractedText and 'DISCUSSION' in extractedText and 'ANALYSIS' in extractedText):
                   continue

                for line in splitText:
                    line = line.strip()
                    #Find Statement of Net Position pages
                    if (line.startswith("STATEMENT OF NET POSITION") or line.endswith("STATEMENT OF NET POSITION")) and not any(line.startswith("FIDUCIARY FUND") for line in splitText) and not any(textLine.startswith('RECONCILIATION OF') for textLine in splitText[0:10]):
                        #If date has not been found yet
                        if not documentDate:
                            if len(dateFilter.findall(extractedText)):
                                documentDate = dateFilter.findall(extractedText)[0]
 
                        #If the municipality name has not been found yet
                        if not municipalityName:
                            #Municipality name is always the first line of the page
                            if len(splitText[0]) > 3:
                                municipalityName = splitText[0]  
                            else:
                                municipalityName = splitText[1]

                        #If statement of net position - proprietary funds is found, place the page in the corresponding list
                        if "PROPRIETARY FUND" in extractedText:
                            #Make sure the page is not a "notes to financial statements" page
                            if  not any(line.startswith("COMPONENT UNITS") for line in splitText):
                                #In some formats (like Detroit 2020), the row titles are on the previous page with no page header
                                if previousPageAdded:
                                    previousPageAdded = False
                                else:
                                    #Look for duplicates
                                    if not any(findPage == previousPage for findPage in statementOfNetPositionProprietaryFunds) and 'RECONCILIATION' not in previousPage.extract_text():
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
                    elif (line.startswith("STATEMENT OF ACTIVITIES") or line.endswith("STATEMENT OF ACTIVITIES")) and not any(textLine.startswith('RECONCILIATION OF') for textLine in splitText[0:10]):
                        #Some formats (like Livingston County 2019) have the row titles on a previous page with no page header
                        if previousPageAdded:
                            previousPageAdded = False
                        else:
                            if not any(findPage == previousPage for findPage in statementOfActivitiesPages) and 'RECONCILIATION' not in previousPage.extract_text() and 'STATEMENT OF NET POSITION' not in previousPage.extract_text():
                                statementOfActivitiesPages.append(previousPage)
                                previousPageAdded = True
                        statementOfActivitiesPages.append(page)
                        statementOfActivitiesFound = True
                        textFound = True

                    #Some formats have "balance sheet" and "governmental funds" on separate lines
                    elif (line.startswith("BALANCE SHEET") or line.endswith('BALANCE SHEET')) and (any(findLine.startswith("GOVERNMENTAL FUND") or findLine.endswith("GOVERNMENTAL FUNDS") for findLine in splitText)) and not any(textLine.startswith('RECONCILIATION OF') for textLine in splitText[0:10]) and 'COMBINING' not in line:
                        balanceSheetGovFundsPages.append(page)
                        #Some balance sheets extend to a second page, so get it just in case
                        balanceSheetFound = True
                        textFound = True

                    #Some formats have "statement of revenue", others have "statement of revenues" 
                    elif  ("STATEMENT OF REVENUE" in line) and not any(textLine.startswith('RECONCILIATION OF') for textLine in splitText[0:10]) and 'COMBINING' not in line:
                        #For statement of revenues, expenditures, and changes in fund balance - governmental funds
                        if "EXPENDITURES" in extractedText and "CHANGE" in extractedText and "FUND BALANCE" in extractedText and (any(line.startswith("GOVERNMENTAL FUND") or line.endswith("GOVERNMENTAL FUNDS") for line in splitText)):
                            statementOfRevExpendAndChangesGovernmentalFundsPages.append(page)
                            #In case it extends to a second page
                            statementOfRevGovFundsFound = True
                            textFound = True
                        #For statement of revenues, expenses and changes in fund net position - proprietary funds
                        elif "EXPENSES" in extractedText and "CHANGE" in extractedText and "NET POSITION" in extractedText and (any(line.startswith("PROPRIETARY FUND") or line.endswith("PROPRIETARY FUNDS") for line in splitText)):
                            
                            if previousPageAdded:
                                previousPageAdded = False
                            else:
                                if not any(findPage == previousPage for findPage in statementOfRevExpAndChangesProprietaryFundsPages) and 'RECONCILIATION' not in previousPage.extract_text():
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
            textFromPage = (currentPage.extract_text()).upper().replace('\u2010', '-').replace('\uf0b7', '')
            textFromPage = textFromPage.replace('$', '')
            print("----------------------------------------------------------------------------")
            print(textFromPage)
        
        print("\nSTATEMENT OF NET POSITION - PROPRIETARY FUNDS PAGES\n")
        print("---------------------------------------------------")
        for currentPage in statementOfNetPositionProprietaryFunds:
            textFromPage = (currentPage.extract_text()).upper().replace('\u2010', '-').replace('\uf0b7', '')
            textFromPage = textFromPage.replace('$', '')
            print("----------------------------------------------------------------------------")
            print(textFromPage) 
        print("\nSTATEMENT OF ACTIVITIES PAGES\n")
        print("---------------------------------------------------")
        for currentPage in statementOfActivitiesPages:
            textFromPage = (currentPage.extract_text()).upper().replace('\u2010', '-').replace('\uf0b7', '')
            textFromPage = textFromPage.replace('$', '')
            print("----------------------------------------------------------------------------")
            print(textFromPage) 
        print("\nBALANCE SHEET - GOV FUNDS PAGES\n")
        print("---------------------------------------------------")
        for currentPage in balanceSheetGovFundsPages:
            textFromPage = (currentPage.extract_text()).upper().replace('\u2010', '-').replace('\uf0b7', '')
            textFromPage = textFromPage.replace('$', '')
            print("----------------------------------------------------------------------------")
            print(textFromPage) 
        print("\nSTATEMENT OF REVENUE PAGES\n")
        print("---------------------------------------------------")
        for currentPage in statementOfRevExpendAndChangesGovernmentalFundsPages:
            textFromPage = (currentPage.extract_text()).upper().replace('\u2010', '-').replace('\uf0b7', '')
            textFromPage = textFromPage.replace('$', '')
            print("----------------------------------------------------------------------------")
            print(textFromPage)
        
        print("\nSTATEMENT OF REVENUE PROPRIETARY FUNDS PAGES\n")
        print("---------------------------------------------------")
        for currentPage in statementOfRevExpAndChangesProprietaryFundsPages:
            textFromPage = (currentPage.extract_text()).upper().replace('\u2010', '-').replace('\uf0b7', '')
            textFromPage = textFromPage.replace('$', '')
            print("----------------------------------------------------------------------------")
            print(textFromPage)
        """
        parseStoredPages()
        return file

#Clean an extracted row & combine its headers 
def cleanCombineRow(line, page_header = ""):
    numberStart = 0
    formattedRow = []

    #Some rows have the text '(Note X)' in a row title where X is a number (see Livingston County 2019's Balance Sheet), and that messes up the parsing, so we find its index to skip over it
    noteIndex = line.find('(NOTE')
    while noteIndex > 0:
        stringToList = list(line)
        del stringToList[noteIndex:noteIndex+8]
        line = ''.join(stringToList)
        noteIndex = line.find('(NOTE')
    
    #Don't add rows that have no numbers
    if not bool(re.search(r'-?\d+', re.sub('\(.*?\)','', line))):
        return

    #Each row in the csv will contain the date, municiplaity name, and page header (if applicable)
    formattedRow.append(documentDate)
    formattedRow.append(municipalityName)
    formattedRow.append(page_header)

    #Find the index where the numbers (or hyphen) start on the line to separate text from numbers
    hyphenFound = False
    hyphenIndex = None
    for index, ele in enumerate(line):
        if ele[0] == ' ':
            continue
        #To check wether the hyphen is part of the row name or if it's meant to be a zero
        #We look at what's after the hyphen
        #If there's a number or another hyphen after it, it's meant to be a zero
        if hyphenFound:
            if ele[0].isalpha():
                hyphenFound = False
            elif ele[0].isdigit() or ele[0] == '-':
                numberStart = hyphenIndex
                break
        elif ele[0].isdigit():
            numberStart = index
            break
        elif ele[0] == '-':
            hyphenFound = True
            hyphenIndex = index
    
    #Add text as separate column
    formattedRow.append(line[0:numberStart].strip())

    #Remove the ',' between the numbers so it doesn't mess up the comparisons
    line = (line[numberStart:len(line)].strip()).replace(',', '')

    lineIndex = 0
    #Iterate through the string
    while lineIndex < len(line):
        #Save current character and copy index (since we will alter it)
        currentChar = line[lineIndex]
        indexCopy = lineIndex
        if currentChar.isdigit():
            #If a digit is found, keep going till a space (end of number) is found
            while lineIndex < len(line) and line[lineIndex] != ' ':
                lineIndex += 1
            if indexCopy == lineIndex:
                formattedRow.append(line[indexCopy].strip()) if line[indexCopy] != '0' else formattedRow.append('0')
            else:
                formattedRow.append(line[indexCopy:lineIndex].strip())
        elif currentChar == '-':
            #If a dash is found, add it to the output row and skip over it
            formattedRow.append('-')
            lineIndex += 1
        else:
            lineIndex += 1

    [x.encode('utf-8') for x in formattedRow]

    #Some columns that have a large number (ex 1,225,501) will be extracted as 1 225501. This looks for single-digit elements and joins them to the next element
    if len(formattedRow) > 4:
        for index, elmnt in enumerate(formattedRow):
            if len(elmnt) == 1 and elmnt[0].isdigit():
                #If the lone number is a zero, do not add it to the next element
                if elmnt[0] != '0':
                    try:
                        formattedRow[index + 1] = formattedRow[index] + formattedRow[index + 1]
                        formattedRow.pop(index)
                    except:
                        print('There was an error processing the following row:\n' + str(line))
                else:
                    #Replace zeros with hyphens
                    try:
                        formattedRow[index] = '-'
                    except:
                        print('There was an error processing the following row:\n' + str(line))
    
    #Do not place the values of pages under the columns of other pages
    #This fills in empty values to the row so it "skips" over columns when writing to the CSV
    if page_header == 'STATEMENT OF NET POSITION' or ('PRIMARY GOV' in page_header and len (formattedRow) <= 8):
        formattedRow[4:4] = ['', '', '', '', '']
        formattedRow[2] = (formattedRow[2].replace('PRIMARY GOV', '')).strip()
    #For the balance sheet- gov funds and statement of revenues - gov funds, we only want the General Fund and Totals columns (which are the first and last columns), so remove everything in between
    #For the Total column, we use the same logic we use for the Proprietary Funds pages below
    elif page_header == 'BALANCE SHEET - GOVERNMENTAL FUNDS' or page_header == 'STATEMENT OF REVENUES, EXPENDITURES, AND CHANGES IN FUND BALANCES - GOV FUNDS':
        try:
            sum = 0
            totalFound = False
            for index, element in enumerate(formattedRow[4:len(formattedRow)]):
                if ')' in element:
                    element = element.replace(')', '')
                    element = str(int(element) * -1)
                    (formattedRow[4:len(formattedRow)])[index] = element
                if element != '-':
                    if int(element) == sum:
                        formattedRow[5] = sum
                        totalFound = True
                        break
                    elif (element.lstrip('-')).isdigit():
                        sum += int(element)
            if not totalFound:
                if sum != 0:
                    formattedRow[5] = sum
                else:
                    formattedRow[5] = '-'
            del formattedRow[6:len(formattedRow)]
        except:
            print('There was an error processing the following row:\n' + str(line))
        formattedRow[4:4] = ['', '', '', '', '', '', '', '', '']
    #For these pages, we only need the Total column
    elif page_header.startswith('STATEMENT OF NET POSITION - PROPRIETARY FUNDS') or page_header.startswith('Statement of Revenues, Expenses, and Changes in Fund Net Position - Proprietary Funds'):
        #The Total column will be the sum of all columns before it, so we start summing them one by one and see if we find a match in the row
        try:
            sum = 0
            totalFound = False
            for index, element in enumerate(formattedRow[4:len(formattedRow)]):
                #Numbers surrounded by paranthesis are negative numbers
                if ')' in element:
                    element = element.replace(')', '')
                    element = str(int(element) * -1)
                    (formattedRow[4:len(formattedRow)])[index] = element
                #Hyphens are Zeros
                if element != '-':
                    if int(element) == sum:
                        formattedRow[4] = sum
                        totalFound = True
                        break
                    elif (element.lstrip('-')).isdigit():
                        sum += int(element)
            #If the total was not found, it means it was not specified in the PDF (see Ottawa County 2020), so we add it since we already have the sum calculated
            if not totalFound:
                #If the last column is internal service funds, it is not a part of the total so remove it
                if 'INTERNAL SERVICE' in page_header:
                    sum -= int(formattedRow[len(formattedRow) - 1])
                if sum != 0:
                    formattedRow[4] = sum
                #If we still have a zero, add a hyphen
                else:
                    formattedRow[4] = '-'
            del formattedRow[5:len(formattedRow)]
        except:
            print('There was an error processing the following row:\n' + str(line))
        formattedRow[4:4] = ['', '', '', '', '', '', '', '', '', '', '']
             
    #Remove internal service and primary gov flags after finishing calculations
    formattedRow[2] = (formattedRow[2].replace(' - INTERNAL SERVICE', '')).replace(' PRIMARY GOV', '')

    for index, element in enumerate(formattedRow):
        #If we find a closing paranthesis, add an opening one at the beginning
        if index >= 4 and len(str(element)) > 0:
            if ')' in str(element):
                formattedRow[index] = '(' + formattedRow[index]
            #For negative numbers, remove the - and add paranthesis
            elif str(element).lstrip('-').isdigit() and int(element) < 0 and ')' not in str(element):
                formattedRow[index] = '(' + str(formattedRow[index]).replace('-', '') + ')'

    #For debugging, print row
    print(formattedRow)

    with open('newOutput.csv', 'a', newline='') as outputFile:
        #Append the formatted row to the end of the file
        writer = csv.writer(outputFile)
        writer.writerow(formattedRow)

#After finding and storing the needed pages, start finding the numbers we need
def parseStoredPages():
    dataWantedFound = False

    #This array will be used to follow the tabs of the different rows to keep track of categories that are broken down
    tabValues = []
    defaultTabValue = None
    firstCharInLine = None
    previousLine = None
    prefix = []
    linesLocations = []
    endOfPages = False

    
    #Statement of net position
    for page in statementOfNetPositionPages:
        extractedText = page.extract_text(y_tolerance=5)
        extractedText = unicodedata.normalize('NFKD', extractedText)
        extractedText = (extractedText.replace('\u2010', '-')).replace('-0-', '-').replace('\uf0b7', '')
        splitText = extractedText.split('\n')
        #page.chars is a list of the page's charachters, each character in the list is a dictionary with multiple keys
        #So we can extract the text values from the dictionaries into a list of chars
        pageChars = []
        for charObject in page.chars:
            #Extract the text key from the dictionary since we won't need the other properties
            pageChars.append(charObject.get('text'))
        
        #Every line with a lowercase first letter is a continuation of the line before it
        #First go through the text and join separated sentences
        for index, line in enumerate(splitText):
            line = line.strip()
            splitText[index] = line
            if len(line) > 2 and (line[0].islower() or (not line[0].isalnum() and line[1].islower())):
                lineIndex = splitText.index(line)
                splitText[lineIndex - 1] = splitText[lineIndex - 1] + ' ' + splitText[lineIndex]
                splitText.pop(lineIndex)

        for line in splitText:
            #Find the index of the matched line in page.chars, will be used to get the tab value
            splitCharacters = [x for x in line[0:10]]
            for i, j in enumerate(page.chars):
                 if splitCharacters == pageChars[i:i+len(splitCharacters)]:
                    firstCharInLine = page.chars[i]
            
            line = (line.replace('$', '')).replace('\u2010', '-')
            upperCaseLine = line.upper()

            #If we have the initial tab value stored,
            #Calculate the difference between the tab values of the first two rows
            #The value will be used as a scale for comparison
            if len(tabValues) == 1 and defaultTabValue == None:
                defaultTabValue = float(firstCharInLine.get('x0')) - float(tabValues[-1])

            #Only print lines that contain numbers in them
            lineContainsNumbers = len(line) > 3 and (bool(re.search(r'-?\d+', re.sub('\(.*?\)','', upperCaseLine))) or (line.strip()).endswith('-') or line.count(',') > 3 or (line.replace(')', ''))[-1].isdigit())

            if tabValues:
                #This calculates the difference between the distances of the current row and the one before it from the left of the page
                #We will use it to know whether this row is tabbed more (meaning a value/category is broken down)
                tabDifference = float(firstCharInLine.get('x0')) - float(tabValues[-1])

                #If this line is tabbed more than the default tab value
                if tabDifference > (defaultTabValue + 1):
                    prefix.append(previousLine + " - ")
                    tabValues.append(firstCharInLine.get('x0'))
                #If this line is tabbed less than the line before it
                elif tabDifference < -1:
                    if prefix:
                        prefix.pop()
                    if len(tabValues) > 1:
                        tabValues.pop()
                    while len(tabValues) > 1 and float(firstCharInLine.get('x0')) - float(tabValues[-1]) < -1:
                        tabValues.pop()
                        if prefix:
                            prefix.pop()

            if dataWantedFound and len(tabValues) > 1 and "TOTAL" not in upperCaseLine and len(line) > 1:
                cleanCombineRow(''.join(prefix) + previousLine + ' ' + upperCaseLine, "STATEMENT OF NET POSITION") if (line[0].islower() and tabDifference <= (defaultTabValue + 1)) else cleanCombineRow(''.join(prefix) + upperCaseLine, "STATEMENT OF NET POSITION")
            #Cash and pooled investments/cash equivalents
            elif "CASH" in upperCaseLine or 'INVESTMENT' in upperCaseLine:
                if lineContainsNumbers:
                    cleanCombineRow(''.join(prefix) + upperCaseLine, "STATEMENT OF NET POSITION")
                #Since it is always the first line in the table, its tab value will be used as an initial value for comparison with other lines
                if not tabValues:
                    tabValues.append(firstCharInLine.get('x0'))
                    dataWantedFound = True
            #Some have investments on a separate row
            elif upperCaseLine.startswith("INVESTMENT"):
                if lineContainsNumbers:
                    cleanCombineRow(''.join(prefix) + upperCaseLine, "STATEMENT OF NET POSITION")
                dataWantedFound = True
            #Capital assets being/not being depreciated
            elif "ASSETS" in upperCaseLine and ("DEPRECIATED" in upperCaseLine or "DEPRECIATION" in upperCaseLine or "DEPRECIABLE" in upperCaseLine):
                if lineContainsNumbers:
                    cleanCombineRow(''.join(prefix) + upperCaseLine, "STATEMENT OF NET POSITION")
                dataWantedFound = True
            #Sometimes capital assets are broken down
            elif "CAPITAL" in upperCaseLine and "ASSETS" in upperCaseLine and not lineContainsNumbers:
                dataWantedFound = True
            #Total assets
            elif 'TOTAL' in upperCaseLine and 'ASSETS' in upperCaseLine: #upperCaseLine.startswith("TOTAL ASSETS"):
                if lineContainsNumbers:
                   cleanCombineRow(upperCaseLine, "STATEMENT OF NET POSITION")
                dataWantedFound = True
            #Some formats have "due within one year:" broken down, if so print the rows under
            elif ("DUE" in upperCaseLine and "YEAR" in upperCaseLine) or ("CURRENT" in upperCaseLine and "LIABILITIES" in upperCaseLine):
                if lineContainsNumbers:
                    cleanCombineRow(''.join(prefix) + upperCaseLine, "STATEMENT OF NET POSITION") if 'TOTAL' not in upperCaseLine else cleanCombineRow(upperCaseLine, "STATEMENT OF NET POSITION")
                dataWantedFound = True
            #Total liabilities
            elif upperCaseLine.startswith("TOTAL LIABILITIES"):
                if lineContainsNumbers:
                    cleanCombineRow(upperCaseLine, "STATEMENT OF NET POSITION")
                dataWantedFound = True
            elif "NET" in upperCaseLine:
                #Total net position
                if upperCaseLine.startswith("TOTAL NET POSITION"):
                    if lineContainsNumbers:
                        cleanCombineRow(upperCaseLine, "STATEMENT OF NET POSITION")
                    dataWantedFound = True
                #Net pension liability
                if "PENSION" in upperCaseLine and "LIABILITY" in upperCaseLine:
                    if lineContainsNumbers:
                        cleanCombineRow(''.join(prefix) + upperCaseLine, "STATEMENT OF NET POSITION")
                    dataWantedFound = True
                #Postemployment benefits or OPEB
                elif (("OTHER" in upperCaseLine and "POSTEMPLOYMENT" in upperCaseLine and "BENEFITS" in upperCaseLine) or "OPEB" in upperCaseLine) and "LIABILITY" in upperCaseLine:
                    if lineContainsNumbers:
                        cleanCombineRow(''.join(prefix) + upperCaseLine, "STATEMENT OF NET POSITION")
                    dataWantedFound = True
                #Net investment in capital assets
                elif "INVESTMENT" in upperCaseLine and "CAPITAL" in upperCaseLine and "ASSET" in upperCaseLine:
                    if lineContainsNumbers:
                        cleanCombineRow(''.join(prefix) + upperCaseLine, "STATEMENT OF NET POSITION")
                    dataWantedFound = True
            #Unrestricted (deficit)
            elif "UNRESTRICTED" in upperCaseLine:
                #if lineContainsNumbers:
                cleanCombineRow(''.join(prefix) + upperCaseLine, "STATEMENT OF NET POSITION")
                dataWantedFound = True
            else:
                dataWantedFound = False

            #Remove the numbers, commas, and $ symbol and store the line for comparison in next loop
            previousLine = ((re.sub('[,-]', '', (re.sub('\d', '', upperCaseLine)))).replace('$','')).strip()
    
    prefix.clear()

    #Statement of Activities
    for page in statementOfActivitiesPages:
        currentLinePosition = 0
        additionFlag = False
        exitFlag = False

        if endOfPages:
            break

        extractedText = page.extract_text(y_tolerance=5)
        extractedText = unicodedata.normalize('NFKD', extractedText)
        extractedText = (extractedText.replace('\u2010', '-')).replace('-0-', '-').replace('\uf0b7', '')
        splitText = extractedText.split('\n')

        #Make sure we are not on the wrong page
        if ('Statement of' in extractedText and 'Statement of Activities' not in extractedText) or 'Balance Sheet' in extractedText:
            continue

        #Every line with a lowercase first letter is a continuation of the line before it
        #First go through the text and join separated sentences
        for index, line in enumerate(splitText):
            line = line.strip()
            splitText[index] = line
            if len(line) > 2 and (line[0].islower() or (not line[0].isalnum() and line[1].islower())):
                lineIndex = splitText.index(line)
                splitText[lineIndex - 1] = splitText[lineIndex - 1] + ' ' + splitText[lineIndex]
                splitText.pop(lineIndex)
        
        #If we go to the next page and we have values in linesLocations
        #That means we have one page with rows and the other with values
        if linesLocations:
            for line in splitText:
                if not linesLocations:
                    break
                line = (line.replace('$', '')).replace('\u2010', '-')
                lineContainsNumbers = len(line) > 3 and (len(line) > 3 and (bool(re.search(r'-?\d+', re.sub('\(.*?\)','', upperCaseLine))) or (line.strip()).endswith('-') or line.count(',') > 3 or (line.replace(')', ''))[-1].isdigit()))
                #Only rows that have numbers are counted (to match the ones from the previous page)
                if lineContainsNumbers and documentDate not in line.upper():
                    if linesLocations[0] == currentLinePosition:
                        #When a match is found, clean it and add to CSV
                        cleanCombineRow(prefix[0] + line, 'STATEMENT OF ACTIVITIES PRIMARY GOV')
                        prefix.pop(0)
                        linesLocations.pop(0)
                    currentLinePosition += 1
            exitFlag = True
        
        if exitFlag:
            break

        for line in splitText:
            #Remove $ characters for better comparison
            line = (line.replace('$', '')).replace('\u2010', '-')
            upperCaseLine = line.upper()

            if ':' in line:
                continue

            lineContainsNumbers = len(line) > 3 and (len(line) > 3 and (bool(re.search(r'-?\d+', re.sub('\(.*?\)','', upperCaseLine))) or (line.strip()).endswith('-') or line.count(',') > 3 or (line.replace(')', ''))[-1].isdigit()))

            #We only consider lines that have values in our iteration
            if lineContainsNumbers or additionFlag:
                currentLinePosition += 1

            #Make sure we are extracting from Program Revenues column
            if 'TOTAL GOVERNMENTAL ACTIVITIES' in upperCaseLine or 'TOTAL BUSINESS-TYPE ACTIVITIES' in upperCaseLine or 'TOTAL PRIMARY GOVERNMENT' in upperCaseLine:
                cleanCombineRow(upperCaseLine, 'STATEMENT OF ACTIVITIES')
            elif 'TAX' in upperCaseLine or 'PROPERTY' in upperCaseLine:
                if lineContainsNumbers:
                    cleanCombineRow(upperCaseLine, 'STATEMENT OF ACTIVITIES PRIMARY GOV')
                else:
                    #If one page has the column names while the numbers are on the other, save the location of the line to grab the values from the second page
                    linesLocations.append(currentLinePosition)
                    prefix.append(upperCaseLine)
                    if not additionFlag:
                        additionFlag = True
            elif ('GRANTS' in upperCaseLine and 'CONTRIBUTIONS' in upperCaseLine) or ('STATE' in upperCaseLine and 'REVENUE' in upperCaseLine) or ('STATE' in upperCaseLine and 'GRANTS' in upperCaseLine):
                if lineContainsNumbers:
                    cleanCombineRow(upperCaseLine, "STATEMENT OF ACTIVITIES PRIMARY GOV")
                else:
                    
                    linesLocations.append(currentLinePosition)
                    prefix.append(upperCaseLine)
            elif 'TOTAL' in upperCaseLine and 'GENERAL' in upperCaseLine and 'REVENUE' in upperCaseLine:
                if lineContainsNumbers:
                    cleanCombineRow(upperCaseLine, 'STATEMENT OF ACTIVITIES PRIMARY GOV')
                else:
                    linesLocations.append(currentLinePosition)
                    prefix.append(upperCaseLine)
            elif 'CHANGE' in upperCaseLine and 'NET' in upperCaseLine and 'POSITION' in upperCaseLine:
                if lineContainsNumbers:
                    cleanCombineRow(upperCaseLine, 'STATEMENT OF ACTIVITIES PRIMARY GOV')
                    endOfPages = True
                else:
                    linesLocations.append(currentLinePosition)
                    prefix.append(upperCaseLine)
    
    prefix.clear()
    tabValues.clear()
    linesLocations.clear()
    linesToAppend = []
    firstCharInLine = None

    #Balance Sheet - Governmental Funds
    for pageIndex, page in enumerate(balanceSheetGovFundsPages):
        currentLinePosition = 0
        pageChars = []
        totalsOnSamePage = False
        additionFlag = False
        extractedText = page.extract_text(y_tolerance=5)
        extractedText = (extractedText.replace('\u2010', '-')).replace('-0-', '-').replace('\uf0b7', '')
        extractedText = unicodedata.normalize('NFKD', extractedText)
        splitText = extractedText.split('\n')
        #Every line with a lowercase first letter is a continuation of the line before it
        #First go through the text and join separated sentences
        for index, line in enumerate(splitText):
            line = line.strip()
            splitText[index] = line
            if len(line) > 2 and (line[0].islower() or (not line[0].isalnum() and line[1].islower())):
                lineIndex = splitText.index(line)
                splitText[lineIndex - 1] = splitText[lineIndex - 1] + ' ' + splitText[lineIndex]
                splitText.pop(lineIndex)
        
        #Store all of the Page characters
        for charObject in page.chars:
            pageChars.append(charObject.get('text'))

        #Figure out if the Totals column is on the same page
        page_headers = []
        for line in splitText:
            line = line.upper()
            page_headers.append(line)
            if 'ASSETS' in line or 'LIABILITIES' in line:
                break
            elif '$' in line or line.count(',') >= 3:
                page_headers.pop()
                break
        if any(headerLine.startswith('RECONCILIATION OF') for headerLine in page_headers):
            continue
        if any('TOTAL' in headerLine for headerLine in page_headers):
            totalsOnSamePage = True
        
        #if we reach a page and we have line locations stored, that means we want to continue the rows stored from the prior page
        if linesLocations:
            if totalsOnSamePage:
                for line in splitText:
                    if not linesLocations:
                        break
                    line = (line.replace('$', '')).replace('\u2010', '-')
                    lineContainsNumbers = len(line) > 3 and (bool(re.search(r'-?\d+', re.sub('\(.*?\)','', upperCaseLine))) or (line.strip()).endswith('-') or line.count(',') > 3 or (line.replace(')', ''))[-1].isdigit())
                    #Only rows that have numbers are counted (to match the ones from the previous page)
                    if lineContainsNumbers and documentDate not in line.upper() and 'EXHIBIT' not in line.upper() and not any(line.upper() == headerLine for headerLine in page_headers):
                        if linesLocations[0] == currentLinePosition:
                            #When a match is found, clean it and add to CSV
                            cleanCombineRow(linesToAppend[0] + ' ' + line, 'BALANCE SHEET - GOVERNMENTAL FUNDS')
                            linesToAppend.pop(0)
                            linesLocations.pop(0)
                        currentLinePosition += 1
        for line in splitText:
            #Remove $ characters for better comparison
            line = (line.replace('$', '')).replace('\u2010', '-')
            upperCaseLine = line.upper()


            lineContainsNumbers = len(line) > 3 and (bool(re.search(r'-?\d+', re.sub('\(.*?\)','', upperCaseLine))) or (line.strip()).endswith('-') or line.count(',') > 3  or (line.replace(')', ''))[-1].isdigit())
            if additionFlag and lineContainsNumbers and documentDate not in upperCaseLine and 'EXHIBIT' not in upperCaseLine:
                currentLinePosition += 1
        
            if 'CASH' in upperCaseLine or 'INVESTMENT' in upperCaseLine:
                if totalsOnSamePage:
                    cleanCombineRow(upperCaseLine, 'BALANCE SHEET - GOVERNMENTAL FUNDS')
                else:
                    if not additionFlag:
                        currentLinePosition = 0
                        additionFlag = True
                    linesLocations.append(currentLinePosition)
                    linesToAppend.append(upperCaseLine) if not pageIndex == len(balanceSheetGovFundsPages)-1 else cleanCombineRow(upperCaseLine, 'BALANCE SHEET - GOVERNMENTAL FUNDS')
            elif 'TOTAL' in upperCaseLine and ('LIABILITIES' in upperCaseLine or 'ASSETS' in upperCaseLine or 'FUND BALANCES' in upperCaseLine):
                if totalsOnSamePage:
                    cleanCombineRow(upperCaseLine, 'BALANCE SHEET - GOVERNMENTAL FUNDS')
                else:
                    linesToAppend.append(upperCaseLine) if not pageIndex == len(balanceSheetGovFundsPages)-1 else cleanCombineRow(upperCaseLine, 'BALANCE SHEET - GOVERNMENTAL FUNDS')
                    linesLocations.append(currentLinePosition)
            elif 'UNASSIGNED' in upperCaseLine:
                if totalsOnSamePage:
                    cleanCombineRow('Fund Balances: ' + upperCaseLine, 'BALANCE SHEET - GOVERNMENTAL FUNDS')
                else:
                    linesToAppend.append(upperCaseLine) if not pageIndex == len(balanceSheetGovFundsPages)-1 else cleanCombineRow(upperCaseLine, 'BALANCE SHEET - GOVERNMENTAL FUNDS')
                    linesLocations.append(currentLinePosition)
            elif 'NON' in upperCaseLine and 'SPENDABLE' in upperCaseLine:
                if lineContainsNumbers:
                    if totalsOnSamePage:
                        cleanCombineRow('Fund Balances: ' + upperCaseLine, 'BALANCE SHEET - GOVERNMENTAL FUNDS')
                    else:
                        linesToAppend.append(upperCaseLine) if not pageIndex == len(balanceSheetGovFundsPages)-1 else cleanCombineRow(upperCaseLine, 'BALANCE SHEET - GOVERNMENTAL FUNDS')
                        linesLocations.append(currentLinePosition)
            elif 'RESTRICTED' in upperCaseLine:
                if lineContainsNumbers:
                    if totalsOnSamePage:
                        cleanCombineRow('Fund Balances: ' + upperCaseLine, 'BALANCE SHEET - GOVERNMENTAL FUNDS')
                    else: 
                        linesToAppend.append(upperCaseLine) if not pageIndex == len(balanceSheetGovFundsPages)-1 else cleanCombineRow(upperCaseLine, 'BALANCE SHEET - GOVERNMENTAL FUNDS')
                        linesLocations.append(currentLinePosition)
            elif 'COMMITTED' in upperCaseLine:
                if lineContainsNumbers:
                    if totalsOnSamePage:
                        cleanCombineRow('Fund Balances: ' + upperCaseLine, 'BALANCE SHEET - GOVERNMENTAL FUNDS')
                    else:
                        linesToAppend.append(upperCaseLine) if not pageIndex == len(balanceSheetGovFundsPages)-1 else cleanCombineRow(upperCaseLine, 'BALANCE SHEET - GOVERNMENTAL FUNDS')
                        linesLocations.append(currentLinePosition)
            elif 'ASSIGNED' in upperCaseLine:
                if lineContainsNumbers:
                    if totalsOnSamePage:
                        cleanCombineRow('Fund Balances: ' + upperCaseLine, 'BALANCE SHEET - GOVERNMENTAL FUNDS')
                    else:
                        linesToAppend.append(upperCaseLine) if not pageIndex == len(balanceSheetGovFundsPages)-1 else cleanCombineRow(upperCaseLine, 'BALANCE SHEET - GOVERNMENTAL FUNDS')
                        linesLocations.append(currentLinePosition)

    
    prefix.clear()
    tabValues.clear()
    linesLocations.clear()
    linesToAppend = []
    firstCharInLine = None

    #Statement of Revenue, Expenditures, and Changes in Fund Balances - Governmental Funds

    for pageIndex, page in enumerate(statementOfRevExpendAndChangesGovernmentalFundsPages):
        currentLinePosition = 0
        pageChars = []
        totalsOnSamePage = False
        additionFlag = False
        extractedText = page.extract_text(y_tolerance=5)
        extractedText = (extractedText.replace('\u2010', '-')).replace('-0-', '-').replace('\uf0b7', '')
        extractedText = unicodedata.normalize('NFKD', extractedText)
        splitText = extractedText.split('\n')
        skipFlag = False

        #Every line with a lowercase first letter is a continuation of the line before it
        #First go through the text and join separated sentences
        for index, line in enumerate(splitText):
            line = line.strip()
            splitText[index] = line
            if len(line) > 2 and (line[0].islower() or (not line[0].isalnum() and line[1].islower())):
                lineIndex = splitText.index(line)
                splitText[lineIndex - 1] = splitText[lineIndex - 1] + ' ' + splitText[lineIndex]
                splitText.pop(lineIndex)
    
        #Figure out if the Totals column is on the same page
        page_headers = []
        for line in splitText:
            line = line.upper()
            if 'TAX' in line or '$' in line:
                break
            page_headers.append(line)
            if line.count(',') >= 3:
                page_headers.pop()
                break
        if any('TOTAL' in headerLine for headerLine in page_headers):
            totalsOnSamePage = True

        #If we moved to a new page and we have locations of lines stored, that means the totals column is on a separate page
        if linesLocations:
            if totalsOnSamePage:
                for line in splitText:
                    if not linesLocations:
                        break
                    line = (line.replace('$', '')).replace('\u2010', '-')
                    lineContainsNumbers = len(line) > 3 and (bool(re.search(r'-?\d+', line)) or (line.strip()).endswith('-') or line.count(',') > 3 or (line.replace(')', ''))[-1].isdigit())
                    #Only rows that have numbers are counted (to match the ones from the previous page)
                    if lineContainsNumbers and documentDate not in line.upper() and 'EXHIBIT' not in line.upper() and not any(line.upper() == headerLine for headerLine in page_headers):
                        if linesLocations[0] == currentLinePosition:
                            #When a match is found, clean it and add to CSV
                            cleanCombineRow(linesToAppend[0] + ' ' + line, 'STATEMENT OF REVENUES, EXPENDITURES, AND CHANGES IN FUND BALANCES - GOV FUNDS')
                            linesToAppend.pop(0)
                            linesLocations.pop(0)
                        currentLinePosition += 1
            else:
                while linesLocations:
                    cleanCombineRow(linesToAppend[0], 'STATEMENT OF REVENUES, EXPENDITURES, AND CHANGES IN FUND BALANCES - GOV FUNDS')
                    linesToAppend.pop(0)
                    linesLocations.pop(0)
                    currentLinePosition += 1
                skipFlag = True
        if skipFlag:
            continue
        
        for line in splitText:
            #Remove $ characters for better comparison
            line = (line.replace('$', '')).replace('\u2010', '-')
            upperCaseLine = line.upper()

            lineContainsNumbers = len(line) > 3 and (bool(re.search(r'-?\d+', re.sub('\(.*?\)','', upperCaseLine))) or (line.strip()).endswith('-') or line.count(',') > 3 or (line.replace(')', ''))[-1].isdigit())
            if additionFlag and lineContainsNumbers and documentDate not in upperCaseLine and 'EXHIBIT' not in upperCaseLine:
                currentLinePosition += 1
            
            #For this kind of page, Debt Service is the only column that may be broken down
            #If it's broken down, it is always into two rows, Principal and Interest&Fiscal Charges
            if dataWantedFound:
                if 'PRINCIPAL' in upperCaseLine or 'INTEREST' in upperCaseLine:
                    if lineContainsNumbers:
                        if totalsOnSamePage:
                            cleanCombineRow(''.join(prefix) + upperCaseLine, 'STATEMENT OF REVENUES, EXPENDITURES, AND CHANGES IN FUND BALANCES - GOV FUNDS')
                        else:
                            linesToAppend.append(''.join(prefix) + upperCaseLine)
                            linesLocations.append(currentLinePosition)
                    else:
                        prefix.append(upperCaseLine + ' - ')
                else:
                    dataWantedFound = False
                    if prefix:
                        prefix.pop()
        
            if 'TAXES' in upperCaseLine or 'PROPERTY' in upperCaseLine:
                if lineContainsNumbers:
                    if totalsOnSamePage:
                        cleanCombineRow(upperCaseLine, 'STATEMENT OF REVENUES, EXPENDITURES, AND CHANGES IN FUND BALANCES - GOV FUNDS')
                    else:
                        if not additionFlag:
                            currentLinePosition = 0
                            additionFlag = True
                        
                        linesLocations.append(currentLinePosition)
                        linesToAppend.append(upperCaseLine) if not pageIndex == len(statementOfRevExpendAndChangesGovernmentalFundsPages)-1 else cleanCombineRow(upperCaseLine, 'STATEMENT OF REVENUES, EXPENDITURES, AND CHANGES IN FUND BALANCES - GOV FUNDS')
            elif 'TOTAL' in upperCaseLine: #and ('REVENUE' in upperCaseLine or 'EXPENDITURE' in upperCaseLine or ('OTHER' in upperCaseLine and 'FINANCING' in upperCaseLine)):
                if lineContainsNumbers:
                    if totalsOnSamePage:
                        cleanCombineRow(upperCaseLine, 'STATEMENT OF REVENUES, EXPENDITURES, AND CHANGES IN FUND BALANCES - GOV FUNDS')
                    else:
                        linesToAppend.append(upperCaseLine) if not pageIndex == len(statementOfRevExpendAndChangesGovernmentalFundsPages)-1 else cleanCombineRow(upperCaseLine, 'STATEMENT OF REVENUES, EXPENDITURES, AND CHANGES IN FUND BALANCES - GOV FUNDS')
                        linesLocations.append(currentLinePosition)
            elif 'DEBT' in upperCaseLine and 'SERVICE' in upperCaseLine:
                if lineContainsNumbers:
                    if totalsOnSamePage:
                        cleanCombineRow(upperCaseLine, 'STATEMENT OF REVENUES, EXPENDITURES, AND CHANGES IN FUND BALANCES - GOV FUNDS')
                    else:
                        linesToAppend.append(upperCaseLine) if not pageIndex == len(statementOfRevExpendAndChangesGovernmentalFundsPages)-1 else cleanCombineRow(upperCaseLine, 'STATEMENT OF REVENUES, EXPENDITURES, AND CHANGES IN FUND BALANCES - GOV FUNDS')
                        linesLocations.append(currentLinePosition) 
                #If Debt Service is found but the line has no numbers (it is broken down further)
                else:
                    dataWantedFound = True
                    prefix.append(upperCaseLine + ' - ')
            elif 'CAPITAL' in upperCaseLine and 'OUTLAY' in upperCaseLine:
                if lineContainsNumbers:
                    if lineContainsNumbers:
                        if totalsOnSamePage:
                            cleanCombineRow(upperCaseLine, 'STATEMENT OF REVENUES, EXPENDITURES, AND CHANGES IN FUND BALANCES - GOV FUNDS')
                        else:
                            linesToAppend.append(upperCaseLine) if not pageIndex == len(statementOfRevExpendAndChangesGovernmentalFundsPages)-1 else cleanCombineRow(upperCaseLine, 'STATEMENT OF REVENUES, EXPENDITURES, AND CHANGES IN FUND BALANCES - GOV FUNDS')
                            linesLocations.append(currentLinePosition)
            elif 'NET' in upperCaseLine and 'FUND' in upperCaseLine:
                if lineContainsNumbers:
                    if totalsOnSamePage:
                        cleanCombineRow(upperCaseLine, 'STATEMENT OF REVENUES, EXPENDITURES, AND CHANGES IN FUND BALANCES - GOV FUNDS')
                    else:
                        linesToAppend.append(upperCaseLine) if not pageIndex == len(statementOfRevExpendAndChangesGovernmentalFundsPages)-1 else cleanCombineRow(upperCaseLine, 'STATEMENT OF REVENUES, EXPENDITURES, AND CHANGES IN FUND BALANCES - GOV FUNDS')
                        linesLocations.append(currentLinePosition)
        
    
    prefix.clear()
    linesLocations.clear()
    linesToAppend = []
    internalServiceFundsInPage = False
   
    #Statement of Net Position - Proprietary Funds
    #   These pages have very different formats between different PDFs
    #   Each PDF has a different number of columns, the only common column is the Totals
    #   There are different ways the Totals column is formatted based on the sample PDFs observed
    #   1. The Total column can be the last rightmost column
    #   2. The Total column can be the second-to-last column (before the Internal Service Funds column)
    #   3. The Total column can be on a separate page (one page has the row names and the other has the values)
    #   4. The Total column is not included at all, meaning we will have to add up all the columns to calculate it
    for page in statementOfNetPositionProprietaryFunds:
        totalsOnSamePage = False
        additionFlag = False
        skipFlag = False
        currentLinePosition = 0
        extractedText = page.extract_text(y_tolerance=5)
        extractedText = (extractedText.replace('\u2010', '-')).replace('-0-', '-').replace('\uf0b7', '')
        extractedText = unicodedata.normalize('NFKD', extractedText)
        splitText = extractedText.split('\n')

        #Every line with a lowercase first letter is a continuation of the line before it
        #First go through the text and join separated sentences
        for index, line in enumerate(splitText):
            line = (line.replace('$', '')).replace('\u2010', '-')
            line = line.strip()
            splitText[index] = line
            if len(line) > 2 and (line[0].islower() or (not line[0].isalnum() and line[1].islower())):
                lineIndex = splitText.index(line)
                splitText[lineIndex - 1] = splitText[lineIndex - 1] + ' ' + splitText[lineIndex]
                splitText.pop(lineIndex)
        
        #Figure out if the Totals column is on the same page
        page_headers = []
        for line in splitText:
            line = line.upper()
            page_headers.append(line)
            if 'ASSETS' in line or 'LIABILITIES' in line:
                break
            elif '$' in line or line.count(',') >= 3:
                page_headers.pop()
                break
        if any('RECONCILIATION' in headerLine for headerLine in page_headers):
            continue
        if any('TOTAL' in headerLine for headerLine in page_headers):
            totalsOnSamePage = True
        if any('INTERNAL' in headerLine for headerLine in page_headers) and any('SERVICE' in headerLine for headerLine in page_headers):
            internalServiceFundsInPage = True

        #If we moved to a new page and we have locations of lines stored, that means the totals column is on a separate page
        if linesLocations:
            if totalsOnSamePage:
                for line in splitText:
                    if not linesLocations:
                        skipFlag = True
                        break
                    line = (line.replace('$', '')).replace('\u2010', '-')
                    lineContainsNumbers = len(line) > 3 and (bool(re.search(r'-?\d+', line)) or (line.strip()).endswith('-') or line.count(',') > 3 or (line.replace(')', ''))[-1].isdigit())
                    #Only rows that have numbers are counted (to match the ones from the previous page)
                    if lineContainsNumbers and documentDate not in line.upper() and 'EXHIBIT' not in line.upper() and not any(line.upper() == headerLine for headerLine in page_headers):
                        if linesLocations[0] == currentLinePosition:
                            #If we found the rest of the row on the second page, but the second row also starts with a row title (not just the numbers) (see City of Dearborn 2020)
                            if not any(character.isnumeric() for character in (line.replace(' ', ''))[0:10]) and (linesToAppend[0][0:10] == line.upper()[0:10]):
                                hyphenFound = False
                                hyphenIndex = None
                                for index, ele in enumerate(line):
                                    if ele[0] == ' ':
                                        continue
                                    #To check wether the hyphen is part of the row name or if it's meant to be a zero
                                    #We look at what's after the hyphen
                                    #If there's a number or another hyphen after it, it's meant to be a zero
                                    if hyphenFound:
                                        if ele[0].isalpha():
                                            hyphenFound = False
                                        elif ele[0].isdigit() or ele[0] == '-':
                                            numberStart = hyphenIndex
                                            break
                                    elif ele[0].isdigit():
                                        numberStart = index
                                        break
                                    elif ele[0] == '-':
                                        hyphenFound = True
                                        hyphenIndex = index
                                #Remove the text part
                                line = line[numberStart:len(line)]
                                #When a match is found, clean it and add to CSV
                                cleanCombineRow(linesToAppend[0] + ' ' + line, 'STATEMENT OF NET POSITION - PROPRIETARY FUNDS')
                                linesToAppend.pop(0)
                                linesLocations.pop(0)
                            elif any(character.isnumeric() for character in (line.replace(' ', ''))[0:10]):
                                cleanCombineRow(linesToAppend[0] + ' ' + line, 'STATEMENT OF NET POSITION - PROPRIETARY FUNDS')
                                linesToAppend.pop(0)
                                linesLocations.pop(0)
                            else:
                                while linesLocations:
                                    cleanCombineRow(linesToAppend[0] + ' ' + line, 'STATEMENT OF NET POSITION - PROPRIETARY FUNDS')
                                    linesToAppend.pop(0)
                                    linesLocations.pop(0)
                                    currentLinePosition += 1
                                skipFlag = True
                                break
                        currentLinePosition += 1
            else:
                while linesLocations:
                    if internalServiceFundsInPage:
                        cleanCombineRow(linesToAppend[0] + ' ' + line, 'STATEMENT OF NET POSITION - PROPRIETARY FUNDS - INTERNAL SERVICE')
                    else:
                        cleanCombineRow(linesToAppend[0] + ' ' + line, 'STATEMENT OF NET POSITION - PROPRIETARY FUNDS')
                    linesToAppend.pop(0)
                    linesLocations.pop(0)
                    currentLinePosition += 1
                skipFlag = True
        if skipFlag:
            continue
        
        for line in splitText:
            #Remove $ characters for better comparison
            line = (line.replace('$', '')).replace('\u2010', '-')
            upperCaseLine = line.upper()

            lineContainsNumbers = len(line) > 3 and (bool(re.search(r'-?\d+', re.sub('\(.*?\)','', upperCaseLine))) or (line.replace(' ', '')).endswith('--') or 'TOTAL' in upperCaseLine or line.count(',') > 3 or (line.replace(')', ''))[-1].isdigit())
            if lineContainsNumbers and documentDate not in upperCaseLine and 'EXHIBIT' not in upperCaseLine and not any(upperCaseLine == headerLine for headerLine in page_headers):
                currentLinePosition += 1
        
            if 'CASH' in upperCaseLine:
                if lineContainsNumbers:
                    if totalsOnSamePage:
                        cleanCombineRow(upperCaseLine, 'STATEMENT OF NET POSITION - PROPRIETARY FUNDS')
                    else:
                        if not additionFlag:
                            currentLinePosition = 0
                            additionFlag = True
                        linesToAppend.append(upperCaseLine) if page != statementOfNetPositionProprietaryFunds[-1] else cleanCombineRow(upperCaseLine, 'STATEMENT OF NET POSITION - PROPRIETARY FUNDS')
                        linesLocations.append(currentLinePosition)
                else:
                    if not additionFlag:
                        currentLinePosition = 0
                        additionFlag = True
            elif ('TOTAL' in upperCaseLine or 'NET' in upperCaseLine) and 'ASSETS' in upperCaseLine:
                if lineContainsNumbers:
                    if totalsOnSamePage:
                        cleanCombineRow(upperCaseLine, 'STATEMENT OF NET POSITION - PROPRIETARY FUNDS')
                    else:
                        if not linesLocations:
                            currentLinePosition -= 1
                        linesToAppend.append(upperCaseLine) if page != statementOfNetPositionProprietaryFunds[-1] else cleanCombineRow(upperCaseLine, 'STATEMENT OF NET POSITION - PROPRIETARY FUNDS')
                        linesLocations.append(currentLinePosition)
            elif 'NET' in upperCaseLine and ('OPEB' in upperCaseLine or 'PENSION' in upperCaseLine):
                if lineContainsNumbers:
                    if totalsOnSamePage:
                        cleanCombineRow(upperCaseLine, 'STATEMENT OF NET POSITION - PROPRIETARY FUNDS')
                    else:
                        if not linesLocations:
                            currentLinePosition -= 1
                        linesToAppend.append(upperCaseLine) if page != statementOfNetPositionProprietaryFunds[-1] else cleanCombineRow(upperCaseLine, 'STATEMENT OF NET POSITION - PROPRIETARY FUNDS')
                        linesLocations.append(currentLinePosition)
            elif 'TOTAL' in upperCaseLine and 'LIABILITIES' in upperCaseLine:
                if lineContainsNumbers:
                    if totalsOnSamePage:
                        cleanCombineRow(upperCaseLine, 'STATEMENT OF NET POSITION - PROPRIETARY FUNDS')
                    else:
                        if not linesLocations:
                            currentLinePosition -= 1
                        linesToAppend.append(upperCaseLine) if page != statementOfNetPositionProprietaryFunds[-1] else cleanCombineRow(upperCaseLine, 'STATEMENT OF NET POSITION - PROPRIETARY FUNDS')
                        linesLocations.append(currentLinePosition)
            elif 'UNRESTRICTED' in upperCaseLine:
                if lineContainsNumbers:
                    if totalsOnSamePage:
                        cleanCombineRow(upperCaseLine, 'STATEMENT OF NET POSITION - PROPRIETARY FUNDS')
                    else:
                        if not linesLocations:
                            currentLinePosition -= 1
                        linesToAppend.append(upperCaseLine) if page != statementOfNetPositionProprietaryFunds[-1] else cleanCombineRow(upperCaseLine, 'STATEMENT OF NET POSITION - PROPRIETARY FUNDS')
                        linesLocations.append(currentLinePosition)
            elif 'TOTAL' in upperCaseLine and 'NET' in upperCaseLine and 'POSITION' in upperCaseLine:
                if lineContainsNumbers:
                    if totalsOnSamePage:
                        cleanCombineRow(upperCaseLine, 'STATEMENT OF NET POSITION - PROPRIETARY FUNDS')
                    else:
                        if not linesLocations:
                            currentLinePosition -= 1
                        linesToAppend.append(upperCaseLine) if page != statementOfNetPositionProprietaryFunds[-1] else cleanCombineRow(upperCaseLine, 'STATEMENT OF NET POSITION - PROPRIETARY FUNDS')
                        linesLocations.append(currentLinePosition)

    
    prefix.clear()
    linesLocations.clear()
    linesToAppend = []
    internalServiceFundsInPage = False

    #Statement of Revenues, Expenses, and Changes in Fund Net Position - Proprietary Funds
    for page in statementOfRevExpAndChangesProprietaryFundsPages:
        totalsOnSamePage = False
        additionFlag = False
        skipFlag = False
        
        currentLinePosition = 0

        extractedText = page.extract_text(y_tolerance=5)
        extractedText = (extractedText.replace('\u2010', '-')).replace('-0-', '-').replace('\uf0b7', '')
        extractedText = unicodedata.normalize('NFKD', extractedText)
        splitText = extractedText.split('\n')
        #Every line with a lowercase first letter is a continuation of the line before it
        #First go through the text and join separated sentences
        for index, line in enumerate(splitText):
            line = (line.replace('$', '')).replace('\u2010', '-')
            line = line.strip()
            splitText[index] = line
            if len(line) > 2 and (line[0].islower() or (not line[0].isalnum() and line[1].islower())):
                lineIndex = splitText.index(line)
                splitText[lineIndex - 1] = splitText[lineIndex - 1] + ' ' + splitText[lineIndex]
                splitText.pop(lineIndex)
        
        #Figure out if the Totals column is on the same page
        page_headers = []
        for line in splitText:
            line = line.upper()
            page_headers.append(line)
            if 'OPERATING' in line: #or (bool(re.search(r'-?\d+', line)) or (line.replace(' ', '')).endswith('--')):
                break
            elif '$' in line or line.count(',') >= 3:
                page_headers.pop()
                break

        if any('TOTAL' in headerLine for headerLine in page_headers):
            totalsOnSamePage = True
        if any('INTERNAL' in headerLine for headerLine in page_headers) and any('SERVICE' in headerLine for headerLine in page_headers):
            internalServiceFundsInPage = True

        #If we moved to a new page and we have locations of lines stored, that means the totals column is on a separate page
        if linesLocations:
            if totalsOnSamePage:
                for line in splitText:
                    if not linesLocations:
                        skipFlag = True
                        break
                    line = (line.replace('$', '')).replace('\u2010', '-')
                    lineContainsNumbers = len(line) > 3 and (bool(re.search(r'-?\d+', line)) or (line.strip()).endswith('-') or line.count(',') > 3 or (line.replace(')', ''))[-1].isdigit())
                    #Only rows that have numbers are counted (to match the ones from the previous page)
                    if lineContainsNumbers and documentDate not in line.upper() and 'EXHIBIT' not in line.upper() and not any(line.upper() == headerLine for headerLine in page_headers):
                        if linesLocations[0] == currentLinePosition:
                            #If we found the rest of the row on the second page, but the second row also starts with a row title (not just the numbers) (see City of Dearborn 2020)
                            if not any(character.isnumeric() for character in (line.replace(' ', ''))[0:10]) and (linesToAppend[0][0:10] == line.upper()[0:10]):
                                hyphenFound = False
                                hyphenIndex = None
                                for index, ele in enumerate(line):
                                    if ele[0] == ' ':
                                        continue
                                    #To check wether the hyphen is part of the row name or if it's meant to be a zero
                                    #We look at what's after the hyphen
                                    #If there's a number or another hyphen after it, it's meant to be a zero
                                    if hyphenFound:
                                        if ele[0].isalpha():
                                            hyphenFound = False
                                        elif ele[0].isdigit() or ele[0] == '-':
                                            numberStart = hyphenIndex
                                            break
                                    elif ele[0].isdigit():
                                        numberStart = index
                                        break
                                    elif ele[0] == '-':
                                        hyphenFound = True
                                        hyphenIndex = index
                                #Remove the text part
                                line = line[numberStart:len(line)]
                                #When a match is found, clean it and add to CSV
                                cleanCombineRow(linesToAppend[0] + ' ' + line, 'Statement of Revenues, Expenses, and Changes in Fund Net Position - Proprietary Funds')
                                linesToAppend.pop(0)
                                linesLocations.pop(0)
                            elif any(character.isnumeric() for character in (line.replace(' ', ''))[0:10]):
                                cleanCombineRow(linesToAppend[0] + ' ' + line, 'Statement of Revenues, Expenses, and Changes in Fund Net Position - Proprietary Funds')
                                linesToAppend.pop(0)
                                linesLocations.pop(0)
                            else:
                                while linesLocations:
                                    cleanCombineRow(linesToAppend[0] + ' ' + line, 'Statement of Revenues, Expenses, and Changes in Fund Net Position - Proprietary Funds')
                                    linesToAppend.pop(0)
                                    linesLocations.pop(0)
                                    currentLinePosition += 1
                                skipFlag = True
                                break
                        currentLinePosition += 1
            else:
                while linesLocations:
                    if internalServiceFundsInPage:
                        cleanCombineRow(linesToAppend[0], 'Statement of Revenues, Expenses, and Changes in Fund Net Position - Proprietary Funds - INTERNAL SERVICE')
                    else:
                        cleanCombineRow(linesToAppend[0], 'Statement of Revenues, Expenses, and Changes in Fund Net Position - Proprietary Funds')
                    linesToAppend.pop(0)
                    linesLocations.pop(0)
                    currentLinePosition += 1
                skipFlag = True
        if skipFlag:
            continue
        
        for line in splitText:
            #Remove $ characters for better comparison
            line = (line.replace('$', '')).replace('\u2010', '-')
            upperCaseLine = line.upper()

            lineContainsNumbers = len(line) > 3 and (bool(re.search(r'-?\d+', re.sub('\(.*?\)','', upperCaseLine))) or ((re.sub('\(.*?\)','', upperCaseLine)).replace(' ', '')).endswith('--') or 'TOTAL' in upperCaseLine or line.count(',') > 3 or (line.replace(')', ''))[-1].isdigit())
            if lineContainsNumbers and documentDate not in upperCaseLine and 'EXHIBIT' not in upperCaseLine and not any(upperCaseLine == headerLine for headerLine in page_headers):
                currentLinePosition += 1
        
            if ('TOTAL' in upperCaseLine or 'NET' in upperCaseLine) and ('REVENUE' in upperCaseLine or 'EXPENSE' in upperCaseLine):
                if lineContainsNumbers:
                    if totalsOnSamePage or len(statementOfRevExpAndChangesProprietaryFundsPages) == 1:
                        cleanCombineRow(upperCaseLine, 'Statement of Revenues, Expenses, and Changes in Fund Net Position - Proprietary Funds') if not internalServiceFundsInPage else cleanCombineRow(upperCaseLine, 'Statement of Revenues, Expenses, and Changes in Fund Net Position - Proprietary Funds - INTERNAL SERVICE')
                    else:
                        linesToAppend.append(upperCaseLine)
                        linesLocations.append(currentLinePosition - 1)
            elif 'CHANGE' in upperCaseLine and 'NET' in upperCaseLine and 'POSITION' in upperCaseLine:
                if lineContainsNumbers:
                    if totalsOnSamePage or len(statementOfRevExpAndChangesProprietaryFundsPages) == 1:
                        cleanCombineRow(upperCaseLine, 'Statement of Revenues, Expenses, and Changes in Fund Net Position - Proprietary Funds') if not internalServiceFundsInPage else cleanCombineRow(upperCaseLine, 'Statement of Revenues, Expenses, and Changes in Fund Net Position - Proprietary Funds - INTERNAL SERVICE')
                    else:
                        linesToAppend.append(upperCaseLine)
                        linesLocations.append(currentLinePosition - 1)
            