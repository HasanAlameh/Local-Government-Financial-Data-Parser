import re
import pdfplumber
import pandas as pd
from collections import namedtuple
from datetime import date

mainDF = pd.DataFrame()

statementOfNetPositionPages = [] 
statementOfActivitiesPages = []
balanceSheetPages = []
statementOfRevsExFundBalancesPages = []
statementOfRevExFundNetPositionPages = []
requiredSuppInfoEmpRetirementSysPages = []
requiredSuppInfoVolEmpBenePages = []
requiredSuppInfoMunicipalEmpRetSysPages = []


#Usage Example: fillDF(FINAL_PAGE_DATA, ['Date', 'Subheader'])..
def fillDF(PAGE_DATA, PAGE_DATA_COLUMNS):
    pageDF = pd.DataFrame(PAGE_DATA, columns=PAGE_DATA_COLUMNS)
    global mainDF
    if mainDF.empty:
        mainDF = mainDF.append(pageDF)
    else:
        mainDF = pd.concat([mainDF, pageDF])
    print(mainDF)
    print("__________________________DATAFRAME UPDATED______________________")

def getCurrentYear():
    return date.today().year
    
#write to CSV func, manipulates with the dataframe
def conv_to_csv():
    global mainDF
    saveCSVfilepath = r'./parseRESULT.csv'
    mainDF.to_csv(saveCSVfilepath, index=False)
    print("\n\nMESSAGE: Your csv file is ready, go to " + saveCSVfilepath + " to take a look at!")
    return saveCSVfilepath

def nextPageContinued(nextPagetext):
    nextPageContinued = True
    #------------------Filters----------------------------------------
    county_filter = re.compile(r'county|COUNTY|County$')
    blankPageFilter = re.compile(r'This page intentionally left blank.')
    #------------------Break each line based on \n found--------------
    fullPagetext = nextPagetext.split('\n')
    #-----------------Iterate through the page------------------------
    lineIndex = 0
    while lineIndex in range(len(fullPagetext)):
        #------------------Look for these flags while iterating through the nextPage -----------------
        countyFound = county_filter.search(fullPagetext[lineIndex])
        blankPageFound = blankPageFilter.search(fullPagetext[lineIndex])

        if countyFound:
            nextPageContinued = False
        elif blankPageFound: 
            nextPageContinued = False
        
        #Line by Line iteration over the page
        lineIndex+=1

    #Check if the next page actually has a significant amount of data... if not it's not continuing..
    if(nextPageContinued):
        if(not(len(fullPagetext) > 5)):
            nextPageContinued = False
    return nextPageContinued

def page_scan(file):
    print("#################################...PAGES ARE BEING SCANNED AS PER HEADERS...###################################")
    with pdfplumber.open(file) as pdf:
        pages = pdf.pages
        for i, page in enumerate(pdf.pages):
            text = pages[i].extract_text()
            if text is not None:
                fullPagetext = text.split('\n')
                if len(fullPagetext) > 2 and fullPagetext[1] == 'Statement of Net Position':
                    statementOfNetPositionPages.append(i)
                elif len(fullPagetext) > 2 and fullPagetext[1] == 'Statement of Activities':
                    statementOfActivitiesPages.append(i)
                elif len(fullPagetext) > 2 and fullPagetext[1] == 'Balance Sheet - Governmental Funds':
                    balanceSheetPages.append(i)
                elif len(fullPagetext) > 2 and fullPagetext[1] == 'Statement of Revenues, Expenditures and Changes in Fund Balances':
                    statementOfRevsExFundBalancesPages.append(i)
                elif len(fullPagetext) > 2 and fullPagetext[1] == 'Statement of Revenues, Expenses and Changes in Fund Net Position':
                    statementOfRevExFundNetPositionPages.append(i)
                elif len(fullPagetext) > 2 and fullPagetext[1] == 'Required Supplementary Information' and fullPagetext[2] == 'Employees\' Retirement System':
                    requiredSuppInfoEmpRetirementSysPages.append(i)
                elif len(fullPagetext) > 2 and fullPagetext[1] == 'Required Supplementary Information' and fullPagetext[2] == 'Voluntary Employees\' Beneficiary Association':
                    requiredSuppInfoVolEmpBenePages.append(i)
                elif len(fullPagetext) > 2 and fullPagetext[1] == 'Required Supplementary Information' and fullPagetext[2] == 'Municipal Employees\' Retirement System of Michigan':
                    requiredSuppInfoMunicipalEmpRetSysPages.append(i)

def cleanSpecialChars(index):
	#Replace or remove special chars "(", ")", and "$"; only keeping numbers
	fullPagetext[index] = fullPagetext[index].replace("$", "")
	fullPagetext[index] = fullPagetext[index].replace("-", "0")
	fullPagetext[index] = fullPagetext[index].replace("(", "-")
	fullPagetext[index] = fullPagetext[index].replace(")", "")
	
def storeInList(list, date, county, header, pgHeader, row):
	#Store data into a list
	list.append(date)
	list.append(county)
	list.append(header)
	list.append(pgHeader)
	list.append(row)
					
def file_parse(file):
    page_scan(file)
    with pdfplumber.open(file) as pdf:
        pages = pdf.pages
        FINAL_PAGE_DATA = []
        for i, page in enumerate(pdf.pages):
            if len(statementOfNetPositionPages) >= 1 and i == statementOfNetPositionPages[0]:
                FINAL_PAGE_DATA.clear()
                text = page.extract_text()
                headerlist = ['DATE', 'COUNTY', 'PAGE_HEADER', 'SUB_DATA_HEADER', 'GOV_ACTIVITIES', 'BUS_ACTIVITY', 'TOTAL']
                #------------------Filters-----------------
                county_filter = re.compile(r'county|COUNTY|County$')
                statementOfNetPositionFilter = re.compile(r'Statement of Net Position|statement of net position|STATEMENT OF NET POSITION')
                dateFilter = re.compile(r'[a-zA-Z]+\s\d\d[,]\s\d\d\d\d')
                
                #--------------------------------------------------DATA FILLER LINE-------------------------------------------------------------------
                dfLine = namedtuple('dfLine', 'date county header pageheader govActivityData busActivityData totalData')
                #--------------------------------------------------Split Lines based on /n and store into list----------------------------------------
                fullPagetext = text.split('\n')
                #--------------------------------------------------Flags to look for in lines---------------------------------------------------------
                #-------------------ASSETS-----------------------------
                cashAndPooledInvestmentsSplit = "Cash and pooled investments"
                #-------------ISSUE (Assets being matched, it's only one word LEFT OFF HERE)-----------------------
                capitalAssetsNotBeingDepricatedSplit = "Capital assets not being depreciated | Capital assets not subject to depreciation"
                capitalAssetsBeingDepcricatedSplit = "Capital assets being depreciated, net | Capital assets being depreciated - net |  Capital assets subject to depreciation, net | Capital assets subject to depreciation - net | Capital assets net of accumulated depreciation | Assets subject to depreciation, net | Assets subject to depreciation - net"
                totalAssetsSplit = "Total assets | Total Assets"
                #-------------------LIABILITIES-----------------------------
                longTermDebtSplit = "Long-term debt: | Long-Term Debt: | Long-term debt"
                # if long term debt meets, then
                dueWithinOneYearSplit = "Due within one year | current portion | current maturities"
                dueInMoreThanOneYearSplit = "Due in more than one year | noncurrent portion | noncurrent maturities"
                netPensionLiabilitySplit = "Net pension liability | Net Pension Liability"
                netOtherPostEmploymentBenefitsLiabilitySplit = "Net other postemployment benefits liability"
                totalLiabilitiesSplit = "Total liabilities | Total Liabilities"
                #------------------NET POSITION ----------------------------
                netInvestmentInCapitalAssetsSplit = "Net investment in capital assets | Net Investment In Capital Assets"
                unrestrictedSplit = "Unrestricted | Unrestricted (deficit)"
                totalNetPositionSplit = "Total net position | Total Net Position"
                #Temp Storage variables
                county = ''
                date = ''
                header = ''

                #each line will be manipulated using index, index starts at 0
                lineIndex = 0
                while lineIndex in range(len(fullPagetext)):
                    #Get rid of $ signs
                    fullPagetext[lineIndex] = fullPagetext[lineIndex].replace("$", " ")
                    #Look for these flags within the page (as we go line by line), if found return true, otherwise false
                    countyFound = county_filter.search(fullPagetext[lineIndex])
                    headerFound = statementOfNetPositionFilter.search(fullPagetext[lineIndex])
                    dateFound = dateFilter.search(fullPagetext[lineIndex])
                    cashAndPooledInvestmentsFound = cashAndPooledInvestmentsSplit.find(fullPagetext[lineIndex].split("  ")[0])
                    capitalAssetsNotBeingDepricatedFound = capitalAssetsNotBeingDepricatedSplit.find(fullPagetext[lineIndex].split("  ")[0])
                    capitalAssetsBeingDepcricatedFound = capitalAssetsBeingDepcricatedSplit.find(fullPagetext[lineIndex].split("  ")[0])
                    totalAssetsFound = totalAssetsSplit.find(fullPagetext[lineIndex].split("  ")[0])
                    longTermDebtFound = longTermDebtSplit.find(fullPagetext[lineIndex].split("  ")[0])
                    netPensionLiabilityFound = netPensionLiabilitySplit.find(fullPagetext[lineIndex].split("  ")[0])
                    netOtherPostEmploymentBenefitsLiabilityFound = netOtherPostEmploymentBenefitsLiabilitySplit.find(fullPagetext[lineIndex].split("  ")[0])
                    totalLiabilitiesFound = totalLiabilitiesSplit.find(fullPagetext[lineIndex].split("  ")[0])
                    netInvestmentInCapitalAssetsFound = netInvestmentInCapitalAssetsSplit.find(fullPagetext[lineIndex].split("  ")[0])
                    unrestrictedFound = unrestrictedSplit.find(fullPagetext[lineIndex].split("  ")[0])
                    totalNetPositionFound = totalNetPositionSplit.find(fullPagetext[lineIndex].split("  ")[0])
                    
                    #If found, then store them into a list
                    if countyFound:
                        county = fullPagetext[lineIndex]
                    elif dateFound:
                        date = fullPagetext[lineIndex].replace("Year Ended", "")
                    elif headerFound:
                        header = fullPagetext[lineIndex]
                    elif cashAndPooledInvestmentsFound != -1:
                        #Check if next line also matches with what we are looking for, if so data falls on second line not first
                        nextLine = fullPagetext[lineIndex+1].split("  ")
                        if cashAndPooledInvestmentsSplit.find(nextLine[0]) != -1:
                            if(len(nextLine) > 3):
                                pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0] + " - ASSETS"
                                #Keep data, remove header
                                fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                #Replace or remove these items and only keep numbers
								cleanSpecialChars(lineIndex+1)
                                #Split numerical data by , based on space detected between each
                                row = fullPagetext[lineIndex+1].split()
                                #Store data into a list
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 4], row[len(row) - 3], row[len(row) - 2]))
                                lineIndex += 1
                        else:
                            thisLine = fullPagetext[lineIndex].split("  ")
                            if(len(thisLine) > 3):
                                pageHeader = fullPagetext[lineIndex].split("   ")[0] + " - ASSETS"
                                #get rid of ( ) and $
								cleanSpecialChars(lineIndex)
                                #Keep data, remove header
                                fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")
                                #Split numerical data by, based on space detected between each
                                row = fullPagetext[lineIndex].split()
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 4], row[len(row) - 3], row[len(row) - 2]))
                    elif capitalAssetsNotBeingDepricatedFound != -1:
                        #Check if next line also matches with what we are looking for, if so data falls on second line not first
                        nextLine = fullPagetext[lineIndex+1].split("  ")
                        if capitalAssetsNotBeingDepricatedSplit.find(nextLine[0]) != -1:
                            if(len(nextLine) > 3):
                                pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0] + " - ASSETS"
                                #Keep data, remove header
                                fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                #Replace or remove these items and only keep numbers
                                cleanSpecialChars(lineIndex+1)
                                #Split numerical data by , based on space detected between each
                                row = fullPagetext[lineIndex+1].split()
                                #Store data into a list
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 4], row[len(row) - 3], row[len(row) - 2]))
                                lineIndex += 1
                        else:
                            thisLine = fullPagetext[lineIndex].split("  ")
                            if(len(thisLine) > 3):
                                pageHeader = fullPagetext[lineIndex].split("   ")[0] + " - ASSETS"
                                #get rid of ( ) and $
                                cleanSpecialChars(lineIndex)
                                #Keep data, remove header
                                fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")
                                #Split numerical data by, based on space detected between each
                                row = fullPagetext[lineIndex].split()
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 4], row[len(row) - 3], row[len(row) - 2]))
                    elif capitalAssetsBeingDepcricatedFound != -1:
                        #Check if next line also matches with what we are looking for, if so data falls on second line not first
                        nextLine = fullPagetext[lineIndex+1].split("  ")
                        if capitalAssetsBeingDepcricatedSplit.find(nextLine[0]) != -1:
                            if(len(nextLine) > 3):
                                pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0] + " - ASSETS"
                                #Keep data, remove header
                                fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                #Replace or remove these items and only keep numbers
                                cleanSpecialChars(lineIndex+1)
                                #Split numerical data by , based on space detected between each
                                row = fullPagetext[lineIndex+1].split()
                                #Store data into a list
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 4], row[len(row) - 3], row[len(row) - 2]))
                                lineIndex += 1
                        else:
                            thisLine = fullPagetext[lineIndex].split("  ")
                            if(len(thisLine) > 3):
                                pageHeader = fullPagetext[lineIndex].split("   ")[0] + " - ASSETS"
                                #get rid of ( ) and $
                                cleanSpecialChars(lineIndex)
                                #Keep data, remove header
                                fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")
                                #Split numerical data by, based on space detected between each
                                row = fullPagetext[lineIndex].split()
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 4], row[len(row) - 3], row[len(row) - 2]))
                    elif totalAssetsFound != -1:
                        #Check if next line also matches with what we are looking for, if so data falls on second line not first
                        nextLine = fullPagetext[lineIndex+1].split("  ")
                        if totalAssetsSplit.find(nextLine[0]) != -1:
                            if(len(nextLine) > 3):
                                pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0]
                                #Keep data, remove header
                                fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                #Replace or remove these items and only keep numbers
                                cleanSpecialChars(lineIndex+1)
                                #Split numerical data by , based on space detected between each
                                row = fullPagetext[lineIndex+1].split()
                                #Store data into a list
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 4], row[len(row) - 3], row[len(row) - 2]))
                                lineIndex += 1
                        else:
                            thisLine = fullPagetext[lineIndex].split("  ")
                            if(len(thisLine) > 3):
                                pageHeader = fullPagetext[lineIndex].split("   ")[0] + " - ASSETS"
                                #get rid of ( ) and $
                                cleanSpecialChars(lineIndex)
                                #Keep data, remove header
                                fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")
                                #Split numerical data by, based on space detected between each
                                row = fullPagetext[lineIndex].split()
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 4], row[len(row) - 3], row[len(row) - 2]))
                    elif longTermDebtFound != -1:
                        nextLine = fullPagetext[lineIndex + 1].split("  ")
                        nextNextLine = fullPagetext[lineIndex + 2].split("  ")
                        mainpageHeader = fullPagetext[lineIndex].split("  ")[0]
                        if dueWithinOneYearSplit.find(nextLine[0]) != -1:
                            if len(nextLine) > 3:
                                pageHeader = mainpageHeader  + " " + nextLine[0] + " - LIABILITIES"
                                #Keep data, remove header
                                fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                #Replace or remove these items and only keep numbers
                                cleanSpecialChars(lineIndex+1)
                                #Split numerical data by , based on space detected between each
                                row = fullPagetext[lineIndex+1].split()
                                #Store data into a list
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 4], row[len(row) - 3], row[len(row) - 2]))

                        if dueInMoreThanOneYearSplit.find(nextNextLine[0]) != -1:
                            if len(nextNextLine) > 3:
                                pageHeader = mainpageHeader + " " + nextNextLine[0] + " - LIABILITIES"
                                #Keep data, remove header
                                fullPagetext[lineIndex+2] = fullPagetext[lineIndex+2].replace(nextNextLine[0], "")
                                #Replace or remove these items and only keep numbers
                                cleanSpecialChars(lineIndex+2)
                                #Split numerical data by , based on space detected between each
                                row = fullPagetext[lineIndex+2].split()
                                #Store data into a list
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 4], row[len(row) - 3], row[len(row) - 2]))
                        lineIndex += 2
                    elif netPensionLiabilityFound != -1:
                         #Check if next line also matches with what we are looking for, if so data falls on second line not first
                        nextLine = fullPagetext[lineIndex+1].split("  ")
                        if netPensionLiabilitySplit.find(nextLine[0]) != -1:
                            if(len(nextLine) > 3):
                                pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0] + " (noncurrent due in one year) - LIABILITIES"
                                #Keep data, remove header
                                fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                #Replace or remove these items and only keep numbers
                                cleanSpecialChars(lineIndex+1)
                                #Split numerical data by , based on space detected between each
                                row = fullPagetext[lineIndex+1].split()
                                #Store data into a list
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 4], row[len(row) - 3], row[len(row) - 2]))
                                lineIndex += 1
                        else:
                            thisLine = fullPagetext[lineIndex].split("  ")
                            if(len(thisLine) > 3):
                                pageHeader = fullPagetext[lineIndex].split("   ")[0] + " (noncurrent due in one year) - LIABILITIES"
                                #get rid of ( ) and $
                                cleanSpecialChars(lineIndex)
                                #Keep data, remove header
                                fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")
                                #Split numerical data by, based on space detected between each
                                row = fullPagetext[lineIndex].split()
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 4], row[len(row) - 3], row[len(row) - 2]))
                    elif netOtherPostEmploymentBenefitsLiabilityFound != -1:
                        #Check if next line also matches with what we are looking for, if so data falls on second line not first
                        nextLine = fullPagetext[lineIndex+1].split("  ")
                        if netOtherPostEmploymentBenefitsLiabilitySplit.find(nextLine[0]) != -1:
                            if(len(nextLine) > 3):
                                pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0]
                                #Keep data, remove header
                                fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                #Replace or remove these items and only keep numbers
                                cleanSpecialChars(lineIndex+1)
                                #Split numerical data by , based on space detected between each
                                row = fullPagetext[lineIndex+1].split()
                                #Store data into a list
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 4], row[len(row) - 3], row[len(row) - 2]))
                                lineIndex += 1
                        else:
                            thisLine = fullPagetext[lineIndex].split("  ")
                            if(len(thisLine) > 3):
                                pageHeader = fullPagetext[lineIndex].split("   ")[0]
                                #get rid of ( ) and $
                                cleanSpecialChars(lineIndex)
                                #Keep data, remove header
                                fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")
                                #Split numerical data by, based on space detected between each
                                row = fullPagetext[lineIndex].split()
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 4], row[len(row) - 3], row[len(row) - 2]))
                    elif totalLiabilitiesFound != -1:
                         #Check if next line also matches with what we are looking for, if so data falls on second line not first
                        nextLine = fullPagetext[lineIndex+1].split("  ")
                        if totalLiabilitiesSplit.find(nextLine[0]) != -1:
                            if(len(nextLine) > 3):
                                pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0]
                                #Keep data, remove header
                                fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                #Replace or remove these items and only keep numbers
                                cleanSpecialChars(lineIndex+1)
                                #Split numerical data by , based on space detected between each
                                row = fullPagetext[lineIndex+1].split()
                                #Store data into a list
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 4], row[len(row) - 3], row[len(row) - 2]))
                                lineIndex += 1
                        else:
                            thisLine = fullPagetext[lineIndex].split("  ")
                            if(len(thisLine) > 3):
                                pageHeader = fullPagetext[lineIndex].split("   ")[0]
                                #get rid of ( ) and $
                                cleanSpecialChars(lineIndex)
                                #Keep data, remove header
                                fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")
                                #Split numerical data by, based on space detected between each
                                row = fullPagetext[lineIndex].split()
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 4], row[len(row) - 3], row[len(row) - 2]))
                    elif netInvestmentInCapitalAssetsFound != -1:
                        #Check if next line also matches with what we are looking for, if so data falls on second line not first
                        nextLine = fullPagetext[lineIndex+1].split("  ")
                        if netInvestmentInCapitalAssetsSplit.find(nextLine[0]) != -1:
                            if(len(nextLine) > 3):
                                pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0] + " - NET POSITION"
                                #Keep data, remove header
                                fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                #Replace or remove these items and only keep numbers
                                cleanSpecialChars(lineIndex+1)
                                #Split numerical data by , based on space detected between each
                                row = fullPagetext[lineIndex+1].split()
                                #Store data into a list
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 4], row[len(row) - 3], row[len(row) - 2]))
                                lineIndex += 1
                        else:
                            thisLine = fullPagetext[lineIndex].split("  ")
                            if(len(thisLine) > 3):
                                pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + "- NET POSITION"
                                #get rid of ( ) and $
                                cleanSpecialChars(lineIndex)
                                #Keep data, remove header
                                fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")
                                #Split numerical data by, based on space detected between each
                                row = fullPagetext[lineIndex].split()
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 4], row[len(row) - 3], row[len(row) - 2]))
                    elif unrestrictedFound != -1:
                        #Check if next line also matches with what we are looking for, if so data falls on second line not first
                        nextLine = fullPagetext[lineIndex+1].split("  ")
                        if unrestrictedSplit.find(nextLine[0]) != -1:
                            if(len(nextLine) > 3):
                                pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0] + " - NET POSITION"
                                #Keep data, remove header
                                fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                #Replace or remove these items and only keep numbers
                                cleanSpecialChars(lineIndex+1)
                                #Split numerical data by , based on space detected between each
                                row = fullPagetext[lineIndex+1].split()
                                #Store data into a list
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 4], row[len(row) - 3], row[len(row) - 2]))
                                lineIndex += 1
                        else:
                            thisLine = fullPagetext[lineIndex].split("  ")
                            if(len(thisLine) > 3):
                                pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + "- NET POSITION"
                                #get rid of ( ) and $
                                cleanSpecialChars(lineIndex)
                                #Keep data, remove header
                                fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")
                                #Split numerical data by, based on space detected between each
                                row = fullPagetext[lineIndex].split()
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 4], row[len(row) - 3], row[len(row) - 2]))
                    elif totalNetPositionFound != -1:
                        #Check if next line also matches with what we are looking for, if so data falls on second line not first
                        nextLine = fullPagetext[lineIndex+1].split("  ")
                        if totalNetPositionSplit.find(nextLine[0]) != -1:
                            if(len(nextLine) > 3):
                                pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0]
                                #Keep data, remove header
                                fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                #Replace or remove these items and only keep numbers
                                cleanSpecialChars(lineIndex+1)
                                #Split numerical data by , based on space detected between each
                                row = fullPagetext[lineIndex+1].split()
                                #Store data into a list
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 4], row[len(row) - 3], row[len(row) - 2]))
                                lineIndex += 1
                        else:
                            thisLine = fullPagetext[lineIndex].split("  ")
                            if(len(thisLine) > 3):
                                pageHeader = fullPagetext[lineIndex].split("   ")[0]
                                #get rid of ( ) and $
                                cleanSpecialChars(lineIndex)
                                #Keep data, remove header
                                fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")
                                #Split numerical data by, based on space detected between each
                                row = fullPagetext[lineIndex].split()
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 4], row[len(row) - 3], row[len(row) - 2]))
                    lineIndex+=1   
                fillDF(FINAL_PAGE_DATA, headerlist)
                print("---------------------DONE PAGE Statement of Net Position 1----------------------\n\n\n")
            elif len(statementOfActivitiesPages) >= 1 and i == statementOfActivitiesPages[0]:
                FINAL_PAGE_DATA.clear()
                text = page.extract_text()
                headerlist = ['DATE', 'COUNTY', 'PAGE_HEADER', 'SUB_DATA_HEADER', 'EXPENSES', 'CHARGES_FOR_SERVICES', 'OPERATING GRANTS AND CONTRIBUTIONS', 'CAPITAL GRANTS AND CONTRIBUTIONS']
                #------------------Filters-----------------
                county_filter = re.compile(r'county|COUNTY|County$')
                statementOfActivitiesFilter = re.compile(r'Statement of Activities|statement of activities|STATEMENT OF ACTIVITIES')
                #CHECK DATE FILTER --> NEXT STEP
                dateFilter = re.compile(r'[a-zA-Z]+\s\d\d[,]\s\d\d\d\d')
                
                #--------------------------------------------------DATA FILLER LINE-------------------------------------------------------------------
                dfLine = namedtuple('dfLine', 'date county header pageheader expenses chargesForServices operatingGrantsAndContributions capitalGrantsAndContributions')
                #--------------------------------------------------Split Lines based on /n and store into list----------------------------------------
                fullPagetext = text.split('\n')
                #--------------------------------------------------Flags to look for in lines---------------------------------------------------------
                totalGovActSplit = "Total governmental activities"
                totalBusActSplit = "Total business-type activities"
                totalPrimaryGovSplit = "Total primary government"

                #Temp Storage variables
                county = ''
                date = ''
                header = ''

                #each line will be manipulated using index, index starts at 0
                lineIndex = 0
                while lineIndex in range(len(fullPagetext)):
                    #Look for these flags within the page (as we go line by line), if found return true, otherwise false
                    countyFound = county_filter.search(fullPagetext[lineIndex])
                    headerFound = statementOfActivitiesFilter.search(fullPagetext[lineIndex])
                    dateFound = dateFilter.search(fullPagetext[lineIndex])
                    totalGovActSplitFound = fullPagetext[lineIndex].find(totalGovActSplit)
                    totalBusActSplitFound = fullPagetext[lineIndex].find(totalBusActSplit)
                    totalPrimaryGovSplitFound = fullPagetext[lineIndex].find(totalPrimaryGovSplit)

                    #If found, then store them into a list
                    if countyFound:
                        county = fullPagetext[lineIndex]
                    elif dateFound:
                        date = fullPagetext[lineIndex].replace("Year Ended", "")
                    elif headerFound:
                        header = fullPagetext[lineIndex]
                    elif totalGovActSplitFound != -1:
                        #Check if next line also matches with what we are looking for, if so data falls on second line not first
                        nextLine = fullPagetext[lineIndex+1].split("  ")[0]
                        if totalGovActSplit.find(nextLine) != -1:
                            pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine
                            
                            #Keep data, remove header
                            fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine, "")

                            #Replace or remove these items and only keep numbers
                            cleanSpecialChars(lineIndex+1)

                            #Split numerical data by , based on space detected between each
                            row = fullPagetext[lineIndex+1].split()
                            
                            #Store data into a list
                            FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 5], row[len(row) - 4], row[len(row) - 3], row[len(row - 2)]))
                            lineIndex += 1
                        else:
                            pageHeader = fullPagetext[lineIndex].split("   ")[0]
                            #get rid of ( ) and $
                            cleanSpecialChars(lineIndex)
                            
                            #Keep data, remove header
                            fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(nextLine, "")
                            
                            #Split numerical data by, based on space detected between each
                            row = fullPagetext[lineIndex].split()

                            FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 5], row[len(row) - 4], row[len(row) - 3], row[len(row)  - 2]))
                            

                    elif totalBusActSplitFound != -1:
                        nextLine = fullPagetext[lineIndex + 1].split("  ")[0]
                        if totalBusActSplit.find(nextLine) != -1:
                            pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine
                            
                            #Keep data, remove header
                            fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine, "")

                            #Replace or remove these items and only keep numbers
                            cleanSpecialChars(lineIndex+1)

                            #Split numerical data by , based on space detected between each
                            row = fullPagetext[lineIndex+1].split()

                            #Store data into a list
                            FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 5], row[len(row) - 4], row[len(row) - 3], row[len(row) - 2]))
                            lineIndex += 1
                        else:
                            pageHeader = fullPagetext[lineIndex].split("   ")[0]
                            #get rid of ( ) and $
                            cleanSpecialChars(lineIndex)
                            
                            #Keep data, remove header
                            fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(nextLine, "")
                            
                            #Split numerical data by, based on space detected between each
                            row = fullPagetext[lineIndex].split()

                            FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 5], row[len(row) - 4], row[len(row) - 3], row[len(row)  - 2]))
                            

                    elif totalPrimaryGovSplitFound != -1:
                        nextLine = fullPagetext[lineIndex + 1].split("  ")[0]
                        if totalPrimaryGovSplit.find(nextLine) != -1:
                            pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine
                            
                            #Keep data, remove header
                            fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine, "")

                            #Replace or remove these items and only keep numbers
                            cleanSpecialChars(lineIndex+1)

                            #Split numerical data by , based on space detected between each
                            row = fullPagetext[lineIndex+1].split()

                            #Store data into a list
                            FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 5], row[len(row) - 4], row[len(row) - 3], row[len(row) - 2]))
                            lineIndex += 1
                        else:
                            pageHeader = fullPagetext[lineIndex].split("   ")[0]
                            #get rid of ( ) and $
                            cleanSpecialChars(lineIndex)
                            
                            #Keep data, remove header
                            fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(nextLine, "")
                            
                            #Split numerical data by, based on space detected between each
                            row = fullPagetext[lineIndex].split()

                            FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 5], row[len(row) - 4], row[len(row) - 3], row[len(row) - 2]))
                            

                    #Move to the next line
                    lineIndex+=1 
                #end of while loop iteration of page
                fillDF(FINAL_PAGE_DATA, headerlist)
                print("---------------------DONE PAGE Statement of Activities----------------------\n\n\n")
            elif len(statementOfActivitiesPages) >= 1 and i == statementOfActivitiesPages[1]: 
                text = page.extract_text()
                FINAL_PAGE_DATA.clear()
                headerlist = ['DATE', 'COUNTY', 'PAGE_HEADER', 'SUB_DATA_HEADER', 'GOV_ACTIVITIES', 'BUS_ACTIVITY', 'TOTAL']
                #Filter County on this page
                county_filter = re.compile(r'county|COUNTY|County$')
                #Filter statementOfActivities on this page
                statementOfActivities = re.compile(r'Statement of Activities|statement of activities|STATEMENT OF ACTIVITIES')
                #Filter date
                dateFilter = re.compile(r'[a-zA-Z]+\s\d\d[,]\s\d\d\d\d')
               
                county  = ''
                header = ''
                date = ''
                pageHeader = ''
                dfLine = namedtuple('dfLine', 'date county header pageheader govActivityData busActivityData totalData')
                govActivityData = 'Government Activities Data'
                busActivityData = ''
                #gets full page split using \n
                fullPagetext = text.split('\n')
                #To fetch the following data (which sometimes are also referred to split by |)
                GrantsRowSplit = "Grants and contributions not restricted to specific programs | Unrestricted state shared revenues | State-shared revenue | State-shared revenue | State grants"
                propertyTaxSplit = "Property taxes"
                totalGenRevTransferSplit = "Total general revenues and transfers"
                ChangeinNetPosSplit = "Change in net position"
                #each line will be accessed using index
                lineIndex = 0
                while lineIndex in range(len(fullPagetext)):
                    countyFound = county_filter.search(fullPagetext[lineIndex])
                    statementOfActivitiesFound = statementOfActivities.search(fullPagetext[lineIndex])
                    dateFound = dateFilter.search(fullPagetext[lineIndex])
                    #See if this line has any data type close to what's in  GrantsFound..
                   #See if this line has any data type close to what's in  GrantsFound..
                    GrantsFound = GrantsRowSplit.find(fullPagetext[lineIndex].split("  ")[0])
                    propertyTaxFound = propertyTaxSplit.find(fullPagetext[lineIndex].split("  ")[0])
                    totalGenRevTransferFound = totalGenRevTransferSplit.find(fullPagetext[lineIndex].split("  ")[0])
                    ChangeinNetPosFound = ChangeinNetPosSplit.find(fullPagetext[lineIndex].split("  ")[0])
                    if countyFound:
                        county = fullPagetext[lineIndex]
                        print('_______________________________________________________________________')
                    elif statementOfActivitiesFound:
                        header = fullPagetext[lineIndex]
                        print('_______________________________________________________________________')
                    elif dateFound:
                        date = fullPagetext[lineIndex].replace("Year Ended", "")
                        print('_______________________________________________________________________')
                    elif GrantsFound != -1:
                        #See if next line also matches (this means double line subheader formatting issue)
                        nextLine = fullPagetext[lineIndex+1].split("  ")[0]
                        if(GrantsRowSplit.find(nextLine) != -1):
                            #Split both lines at more than one space and concatenate them together to make a header
                            pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine
                            #get rid of the subheader (Ex: Property Tax and only keep numericals)
                            fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine, "")
                            #get rid of ( ) and $
                            cleanSpecialChars(lineIndex+1)

                            #Split numerical data by , based on space space
                            row = fullPagetext[lineIndex+1].split()
                            FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 4], row[len(row) - 3], row[len(row) - 2]))
                            lineIndex += 1
                        else:
                            pageHeader = fullPagetext[lineIndex].split("   ")[0]
                            #get rid of ( ) and $
                            cleanSpecialChars(lineIndex)
                            row = fullPagetext[lineIndex].split()

                            FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 4], row[len(row) - 3], row[len(row) - 2]))

                    elif propertyTaxFound != -1:
                        #See if next line also matches (this means double line subheader formatting issue)
                        nextLine = fullPagetext[lineIndex+1].split("  ")[0]
                        if(propertyTaxSplit.find(nextLine) != -1):
                            #Split both lines at more than one space and concatenate them together to make a header
                            pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine
                            fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine, "")
                            #get rid of ( ) and $
                            cleanSpecialChars(lineIndex+1)

                            row = fullPagetext[lineIndex+1].split()

                            FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 4], row[len(row) - 3], row[len(row) - 2]))
                            lineIndex += 1
                        else:
                            pageHeader = fullPagetext[lineIndex].split("   ")[0]
                            #get rid of ( ) and $
                            cleanSpecialChars(lineIndex)

                            row = fullPagetext[lineIndex].split()

                            FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 4], row[len(row) - 3], row[len(row) - 2]))

                    elif totalGenRevTransferFound != -1:
                        #See if next line also matches (this means double line subheader formatting issue)
                        nextLine = fullPagetext[lineIndex+1].split("  ")[0]
                        if(totalGenRevTransferSplit.find(nextLine) != -1):
                            #Split both lines at more than one space and concatenate them together to make a header
                            pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine
                            fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine, "")
                            #get rid of ( ) and $
                            cleanSpecialChars(lineIndex+1)

                            row = fullPagetext[lineIndex+1].split()

                            FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 4], row[len(row) - 3], row[len(row) - 2]))
                            lineIndex += 1
                        else:
                            pageHeader = fullPagetext[lineIndex].split("   ")[0]
                            #get rid of ( ) and $
                            cleanSpecialChars(lineIndex)

                            row = fullPagetext[lineIndex].split()

                            FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 4], row[len(row) - 3], row[len(row) - 2]))

                    elif ChangeinNetPosFound != -1:
                        #See if next line also matches (this means double line subheader formatting issue)
                        nextLine = fullPagetext[lineIndex+1].split("  ")[0]
                        if(ChangeinNetPosSplit.find(nextLine) != -1):
                            #Split both lines at more than one space and concatenate them together to make a header
                            pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine
                            fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine, "")
                            #get rid of ( ) and $
                            cleanSpecialChars(lineIndex+1)


                            row = fullPagetext[lineIndex+1].split()

                            FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 4], row[len(row) - 3], row[len(row) - 2]))
                            lineIndex += 1
                        else:
                            pageHeader = fullPagetext[lineIndex].split("   ")[0]
                            #get rid of ( ) with - and $ with empty
                            cleanSpecialChars(lineIndex)

                            row = fullPagetext[lineIndex].split()
                            FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 4], row[len(row) - 3], row[len(row) - 2]))

                    #Move to the next line
                    lineIndex+=1 
                fillDF(FINAL_PAGE_DATA, headerlist)
                print("---------------------DONE PAGE Statement of Activities----------------------\n\n\n")

            elif len(balanceSheetPages) >= 1 and i == balanceSheetPages[0]:
                FINAL_PAGE_DATA.clear()
                text = page.extract_text()
                
                #CSV headers
                headerlist = ['DATE', 'COUNTY', 'PAGE_HEADER', 'SUB_DATA_HEADER', 'GENERAL', 'TOTAL_GOVERNMENTAL_FUNDS']

                #Datafiller lines
                dfLine = namedtuple('dfLine', 'date county header pageheader govActivityData busActivityData totalData')
                cashAndPooledInvestmentList = []
                totalAssetsList = []
                totalLiabilitiesList = []
                nonspenableList = [] 
                commitedList = [] 
                assignedList = [] 
                unassignedList = [] 
                restrictedList = [] 
                totalFundBalancesList = []

                #GETTING NEXT PAGE TO CHECK IF NEXT PAGE IS A CONTINUATION OR NOT
                nextPagetext = pages[i + 1].extract_text()

                #------------------Filters-----------------
                county_filter = re.compile(r'county|COUNTY|County$')
                balancesheetGovFundsFilter = re.compile(r'Balance Sheet - Governmental Funds|balance sheet - governmental funds|balance sheet - governmental funds')
                dateFilter = re.compile(r'[a-zA-Z]+\s\d\d[,]\s\d\d\d\d')

                 #-------------------ASSETS-----------------------------
                cashAndPooledInvestmentsSplit = "Cash and pooled investments | Cash and Cash equivalents | Cash"
                totalAssetsFilter = "Total assets | Total Assets"

                #-------------------LIABILITIES-----------------------------
                totalLiabilitiesFilter = "Total liabilities"

                #-------------------Fund Balances---------------------------
                nonSpendableFilter = "Nonspendable"
                restrictedFilter = "Restricted"
                commitedFilter = "Commited"
                assignedFilter = "Assigned"
                unassignedFilter = "Unassigned | Unassigned (deficit)"
                totalFundBalancesFilter = "Total fund balances"

                #CHECK IF THIS PAGE CONTINUES TO NEXT PAGE
                isContinued = nextPageContinued(nextPagetext)

                #Temp variables
                county = ''
                date = ''
                header = ''
                #--------------------------------------IF THIS PAGE DATA EXTENDS TO NEXT PAGE-------------------------------------------
                if isContinued:
                    #Divide the whole text based on '\n' found (end of line split)
                    fullPagetext = text.split('\n')
                     #each line will be manipulated using index, index starts at 0
                    lineIndex = 0
                    #this keeps track of datapoints to be grabbed from next page, because there is no flag to look for in the next page (we will assign a line counter). 
                    dataLineCounter = 0
                    dataLineBool = False
                    dataLineIndexes = []

                    while lineIndex in range(len(fullPagetext)):
                         #Get rid of $ signs
                        fullPagetext[lineIndex] = fullPagetext[lineIndex].replace("$", " ")
                        #Look for these flags within the page (as we go line by line), if found return true, otherwise false
                        countyFound = county_filter.search(fullPagetext[lineIndex])
                        headerFound = balancesheetGovFundsFilter.search(fullPagetext[lineIndex])
                        dateFound = dateFilter.search(fullPagetext[lineIndex])
                        cashAndPooledInvestmentsFound = cashAndPooledInvestmentsSplit.find(fullPagetext[lineIndex].split("  ")[0])
                        totalAssetsFound = totalAssetsFilter.find(fullPagetext[lineIndex].split("  ")[0])
                        totalLiabilitiesFound = totalLiabilitiesFilter.find(fullPagetext[lineIndex].split("  ")[0])
                        nonSpendableFound = nonSpendableFilter.find(fullPagetext[lineIndex].split("  ")[0])
                        restrictedFound = restrictedFilter.find(fullPagetext[lineIndex].split("  ")[0])
                        commitedFound = commitedFilter.find(fullPagetext[lineIndex].split("  ")[0])
                        assignedFound = assignedFilter.find(fullPagetext[lineIndex].split("  ")[0])
                        unassignedFound = unassignedFilter.find(fullPagetext[lineIndex].split("  ")[0])
                        totalFundBalancesFound = totalFundBalancesFilter.find(fullPagetext[lineIndex].split("  ")[0])

                        #Making our own numerical flag tracker, for next page (since next page does not have flags to look out for)
                        if dataLineBool:
                            rowItems = fullPagetext[lineIndex].split("  ")
                            #Make sure the lines we are counting actually have data, and they're not simply headers
                            #The lines of the first page which have data will all be given a numerical value, these numerical value will be matched on the next page to correlate with the exact flag
                            if len(rowItems) > 3:
                                dataLineCounter +=1

                        #If found, then store them into a data list
                        if countyFound:
                            county = fullPagetext[lineIndex]
                        elif dateFound:
                            date = fullPagetext[lineIndex].replace("Year Ended", "")
                        elif headerFound:
                            header = fullPagetext[lineIndex]
                        elif cashAndPooledInvestmentsFound != -1:
                            dataLineBool = True
                            dataLineCounter += 1;
                            #Check if next line also matches with what we are looking for, if so data falls on second line not first
                            nextLine = fullPagetext[lineIndex+1].split("  ")
                            if cashAndPooledInvestmentsSplit.find(nextLine[0]) != -1:
                                if(len(nextLine) > 3):
                                    dataLineIndexes.append(dataLineCounter)
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0] + " - ASSETS"
                                    #Keep data, remove header
                                    fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                    #Replace or remove these items and only keep numbers
                                    cleanSpecialChars(lineIndex+1)
                                    #Split numerical data by , based on space detected between each
                                    row = fullPagetext[lineIndex+1].split()
                                    #Store data into a list
									storeInList(cashAndPooledInvestmentList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE
                                    FINAL_PAGE_DATA.append(cashAndPooledInvestmentList)
                                    lineIndex += 1
                            else:
                                thisLine = fullPagetext[lineIndex].split("  ")
                                if(len(thisLine) > 3):
                                    dataLineIndexes.append(dataLineCounter)
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " - ASSETS"
                                    
                                    #Keep data, remove header
                                    fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")
                                    
                                    #get rid of ( ) and $
                                    cleanSpecialChars(lineIndex)
                                    
                                    #Split numerical data by, based on space detected between each
                                    row = fullPagetext[lineIndex].split()
                                    #Store data into a list
                                    storeInList(cashAndPooledInvestmentList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE
                                    FINAL_PAGE_DATA.append(cashAndPooledInvestmentList)
                        elif totalAssetsFound != -1:
                            #Check if next line also matches with what we are looking for, if so data falls on second line not first
                            nextLine = fullPagetext[lineIndex+1].split("  ")
                            if totalAssetsFilter.find(nextLine[0]) != -1:
                                if(len(nextLine) > 3):
                                    dataLineIndexes.append(dataLineCounter)
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0] + " - ASSETS"
                                    #Keep data, remove header
                                    fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                    #Replace or remove these items and only keep numbers
                                    cleanSpecialChars(lineIndex+1)
                                    #Split numerical data by , based on space detected between each
                                    row = fullPagetext[lineIndex+1].split()
                                    #Store data into a list
									storeInList(totalAssetsList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE
                                    FINAL_PAGE_DATA.append(totalAssetsList)
                                    lineIndex += 1
                            else:
                                thisLine = fullPagetext[lineIndex].split("  ")
                                if(len(thisLine) > 3):
                                    dataLineIndexes.append(dataLineCounter)

                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " - ASSETS"
                                    
                                    #Keep data, remove header
                                    fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")
                                    
                                    #get rid of ( ) and $
                                    cleanSpecialChars(lineIndex)
                                    
                                    #Split numerical data by, based on space detected between each
                                    row = fullPagetext[lineIndex].split()
                                    #Store data into a list
                                    storeInList(totalAssetsList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE     
                                    FINAL_PAGE_DATA.append(totalAssetsList)
                        elif totalLiabilitiesFound != -1:
                            #Check if next line also matches with what we are looking for, if so data falls on second line not first
                            nextLine = fullPagetext[lineIndex+1].split("  ")
                            if totalLiabilitiesFilter.find(nextLine[0]) != -1:
                                if(len(nextLine) > 3):
                                    dataLineIndexes.append(dataLineCounter)
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0] + " - LIABILITIES"
                                    #Keep data, remove header
                                    fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                    #Replace or remove these items and only keep numbers
                                    cleanSpecialChars(lineIndex+1)
                                    #Split numerical data by , based on space detected between each
                                    row = fullPagetext[lineIndex+1].split()
                                    #Store data into a list
									storeInList(totalLiabilitiesList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE
                                    FINAL_PAGE_DATA.append(totalLiabilitiesList)
                                    lineIndex += 1
                            else:
                                thisLine = fullPagetext[lineIndex].split("  ")
                                if(len(thisLine) > 3):
                                    dataLineIndexes.append(dataLineCounter)
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " - LIABILITIES"
                                    
                                    #Keep data, remove header
                                    fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")
                                    
                                    #get rid of ( ) and $
                                    cleanSpecialChars(lineIndex)
                                    
                                    #Split numerical data by, based on space detected between each
                                    row = fullPagetext[lineIndex].split()
                                    #Store data into a list
                                    storeInList(totalLiabilitiesList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE
                                    FINAL_PAGE_DATA.append(totalLiabilitiesList)
                        elif nonSpendableFound != -1:
                            #Check if next line also matches with what we are looking for, if so data falls on second line not first
                            nextLine = fullPagetext[lineIndex+1].split("  ")
                            if nonSpendableFilter.find(nextLine[0]) != -1:
                                if(len(nextLine) > 3):
                                    dataLineIndexes.append(dataLineCounter)
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0] + " - FUND BALANCES"
                                    #Keep data, remove header
                                    fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                    #Replace or remove these items and only keep numbers
                                    cleanSpecialChars(lineIndex+1)
                                    #Split numerical data by , based on space detected between each
                                    row = fullPagetext[lineIndex+1].split()
                                    #Store data into a list
									storeInList(nonspenableList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE
                                    FINAL_PAGE_DATA.append(nonspenableList)
                                    lineIndex += 1
                            else:
                                thisLine = fullPagetext[lineIndex].split("  ")
                                if(len(thisLine) > 3):
                                    dataLineIndexes.append(dataLineCounter)
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " - FUND BALANCES"
                                    
                                    #Keep data, remove header
                                    fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")
                                    
                                    #get rid of ( ) and $
                                    cleanSpecialChars(lineIndex)
                                    
                                    #Split numerical data by, based on space detected between each
                                    row = fullPagetext[lineIndex].split()
                                    #Store data into a list
									storeInList(nonspenableList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE
                                    FINAL_PAGE_DATA.append(nonspenableList)
                        elif restrictedFound != -1:
                            #Check if next line also matches with what we are looking for, if so data falls on second line not first
                            nextLine = fullPagetext[lineIndex+1].split("  ")
                            if restrictedFilter.find(nextLine[0]) != -1:
                                if(len(nextLine) > 3):
                                    dataLineIndexes.append(dataLineCounter)
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0] + " - FUND BALANCES"
                                    #Keep data, remove header
                                    fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                    #Replace or remove these items and only keep numbers
                                    cleanSpecialChars(lineIndex+1)
                                    #Split numerical data by , based on space detected between each
                                    row = fullPagetext[lineIndex+1].split()
                                    #Store data into a list
									storeInList(restrictedList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE
                                    FINAL_PAGE_DATA.append(restrictedList)
                                    lineIndex += 1
                            else:
                                thisLine = fullPagetext[lineIndex].split("  ")
                                if(len(thisLine) > 3):
                                    dataLineIndexes.append(dataLineCounter)
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " - FUND BALANCES"
                                    
                                    #Keep data, remove header
                                    fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")
                                    
                                    #get rid of ( ) and $
                                    cleanSpecialChars(lineIndex)
                                    
                                    #Split numerical data by, based on space detected between each
                                    row = fullPagetext[lineIndex].split()
                                    #Store data into a list
									storeInList(restrictedList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE   
                                    FINAL_PAGE_DATA.append(restrictedList) 
                        elif commitedFound != -1:
                            #Check if next line also matches with what we are looking for, if so data falls on second line not first
                            nextLine = fullPagetext[lineIndex+1].split("  ")
                            if commitedFilter.find(nextLine[0]) != -1:
                                if(len(nextLine) > 3):
                                    dataLineIndexes.append(dataLineCounter)
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0] + " - FUND BALANCES"
                                    #Keep data, remove header
                                    fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                    #Replace or remove these items and only keep numbers
                                    cleanSpecialChars(lineIndex+1)
                                    #Split numerical data by , based on space detected between each
                                    row = fullPagetext[lineIndex+1].split()
                                    #Store data into a list
									storeInList(commitedList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE
                                    FINAL_PAGE_DATA.append(commitedList)
                                    lineIndex += 1
                            else:
                                thisLine = fullPagetext[lineIndex].split("  ")
                                if(len(thisLine) > 3):
                                    dataLineIndexes.append(dataLineCounter)
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " - FUND BALANCES"
                                    
                                    #Keep data, remove header
                                    fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")
                                    
                                    #get rid of ( ) and $
                                    cleanSpecialChars(lineIndex)
                                    
                                    #Split numerical data by, based on space detected between each
                                    row = fullPagetext[lineIndex].split()
                                    #Store data into a list
                                    storeInList(commitedList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE 
                                    FINAL_PAGE_DATA.append(commitedList)
                        elif assignedFound != -1:
                            #Check if next line also matches with what we are looking for, if so data falls on second line not first
                            nextLine = fullPagetext[lineIndex+1].split("  ")
                            if assignedFilter.find(nextLine[0]) != -1:
                                if(len(nextLine) > 3):
                                    dataLineIndexes.append(dataLineCounter)
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0] + " - FUND BALANCES"
                                    #Keep data, remove header
                                    fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                    #Replace or remove these items and only keep numbers
                                    cleanSpecialChars(lineIndex+1)
                                    #Split numerical data by , based on space detected between each
                                    row = fullPagetext[lineIndex+1].split()
                                    #Store data into a list
									storeInList(assignedList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE
                                    FINAL_PAGE_DATA.append(assignedList)
                                    lineIndex += 1
                            else:
                                thisLine = fullPagetext[lineIndex].split("  ")
                                if(len(thisLine) > 3):
                                    dataLineIndexes.append(dataLineCounter)
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " - FUND BALANCES"

                                    #Keep data, remove header
                                    fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")

                                    #get rid of ( ) and $
                                    cleanSpecialChars(lineIndex)
                                   
                                    #Split numerical data by, based on space detected between each
                                    row = fullPagetext[lineIndex].split()
                                    #Store data into a list
                                    storeInList(assignedList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE 
                                    FINAL_PAGE_DATA.append(assignedList)
                        elif unassignedFound != -1:
                            #Check if next line also matches with what we are looking for, if so data falls on second line not first
                            nextLine = fullPagetext[lineIndex+1].split("  ")
                            if unassignedFilter.find(nextLine[0]) != -1:
                                if(len(nextLine) > 3):
                                    dataLineIndexes.append(dataLineCounter)
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0] + " - FUND BALANCES"

                                    #Keep data, remove header
                                    fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")

                                    #Replace or remove these items and only keep numbers
                                    cleanSpecialChars(lineIndex+1)
                                    #Split numerical data by , based on space detected between each
                                    row = fullPagetext[lineIndex+1].split()
                                    #Store data into a list
									storeInList(unassignedList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE
                                    FINAL_PAGE_DATA.append(unassignedList)
                                    lineIndex += 1
                            else:
                                thisLine = fullPagetext[lineIndex].split("  ")
                                if(len(thisLine) > 3):
                                    dataLineIndexes.append(dataLineCounter)
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " - FUND BALANCES"

                                    #Keep data, remove header
                                    fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")

                                    #get rid of ( ) and $
                                    cleanSpecialChars(lineIndex)
                                    
                                    #Split numerical data by, based on space detected between each
                                    row = fullPagetext[lineIndex].split()

                                    #Store data into a list
									storeInList(unassignedList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE 
                                    FINAL_PAGE_DATA.append(unassignedList)
                        elif totalFundBalancesFound != -1:
                            #Check if next line also matches with what we are looking for, if so data falls on second line not first
                            nextLine = fullPagetext[lineIndex+1].split("  ")
                            if totalFundBalancesFilter.find(nextLine[0]) != -1:
                                if(len(nextLine) > 3):
                                    dataLineIndexes.append(dataLineCounter)
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0] + " - FUND BALANCES"

                                    #Keep data, remove header
                                    fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")

                                    #Replace or remove these items and only keep numbers
                                    cleanSpecialChars(lineIndex+1)
                                    #Split numerical data by , based on space detected between each
                                    row = fullPagetext[lineIndex+1].split()
                                    #Store data into a list
									storeInList(totalFundBalancesList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE
                                    FINAL_PAGE_DATA.append(totalFundBalancesList)
                                    lineIndex += 1
                            else:
                                dataLineIndexes.append(dataLineCounter)
                                thisLine = fullPagetext[lineIndex].split("  ")
                                if(len(thisLine) > 3):
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " - FUND BALANCES"

                                    #Keep data, remove header
                                    fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")

                                    #get rid of ( ) and $
                                    cleanSpecialChars(lineIndex)

                                    #Split numerical data by, based on space detected between each
                                    row = fullPagetext[lineIndex].split()
                                    #Store data into a list
                                    storeInList(totalFundBalancesList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE 
                                    FINAL_PAGE_DATA.append(totalFundBalancesList)
                        lineIndex+=1

                    #**************************************ITERATE OVER THE NEXT PAGE TO GRAB THOSE MISSING DATAPOINTS**************************
                    fullNextPagetext = nextPagetext.split('\n')
                    lineIndex2 = 0
                    final_page_data_iterator = 0
                    #This is the counter we need to align it with flags in the last page
                    matchCounter = 0
                    counterInitialize = False
                    #---------Number Filter------------
                    numbersFilter = re.compile(r'[\d]+')
                    #this loop is to iterate over the next page data
                    while lineIndex2 in range(len(fullNextPagetext)):

                        numbersFound = numbersFilter.search(fullNextPagetext[lineIndex2])
                        
                        if counterInitialize:
                            matchCounter += 1
                        #FIRST NUMBER DETECTED, then start the counter to match with the counter when it started in the last page
                        if numbersFound and not(counterInitialize):
                            counterInitialize = True
                            matchCounter += 1
                        if matchCounter in dataLineIndexes:
                            #get rid of ( ) and $
                            cleanSpecialChars(lineIndex2)

                            #Split numerical data by, based on space detected between each
                            row = fullNextPagetext[lineIndex2].split()
                            #append this data into the FINAL_PAGE_DATA (it will be in order)
                            FINAL_PAGE_DATA[final_page_data_iterator].append(row[len(row) - 1])
                            final_page_data_iterator+=1
                        lineIndex2+=1
                    print(FINAL_PAGE_DATA)
                #------------------------------------------IF THIS PAGE's DATA DOES NOT EXTEND TO THE NEXT PAGE--------------------------------------------------------
                else: 
                    #Divide the whole text based on '\n' found (end of line split)
                    fullPagetext = text.split('\n')
                     #each line will be manipulated using index, index starts at 0
                    lineIndex = 0

                    while lineIndex in range(len(fullPagetext)):
                        #Get rid of $ signs
                        fullPagetext[lineIndex] = fullPagetext[lineIndex].replace("$", " ")
                        #Look for these flags within the page (as we go line by line), if found return true, otherwise false
                        countyFound = county_filter.search(fullPagetext[lineIndex])
                        headerFound = balancesheetGovFundsFilter.search(fullPagetext[lineIndex])
                        dateFound = dateFilter.search(fullPagetext[lineIndex])
                        cashAndPooledInvestmentsFound = cashAndPooledInvestmentsSplit.find(fullPagetext[lineIndex].split("  ")[0])
                        totalAssetsFound = totalAssetsFilter.find(fullPagetext[lineIndex].split("  ")[0])
                        totalLiabilitiesFound = totalLiabilitiesFilter.find(fullPagetext[lineIndex].split("  ")[0])
                        nonSpendableFound = nonSpendableFilter.find(fullPagetext[lineIndex].split("  ")[0])
                        restrictedFound = restrictedFilter.find(fullPagetext[lineIndex].split("  ")[0])
                        commitedFound = commitedFilter.find(fullPagetext[lineIndex].split("  ")[0])
                        assignedFound = assignedFilter.find(fullPagetext[lineIndex].split("  ")[0])
                        unassignedFound = unassignedFilter.find(fullPagetext[lineIndex].split("  ")[0])
                        totalFundBalancesFound = totalFundBalancesFilter.find(fullPagetext[lineIndex].split("  ")[0])

                        #If found, then store them into a data list
                        if countyFound:
                            county = fullPagetext[lineIndex]
                        elif dateFound:
                            date = fullPagetext[lineIndex].replace("Year Ended", "")
                        elif headerFound:
                            header = fullPagetext[lineIndex]
                        elif cashAndPooledInvestmentsFound != -1:
                            #Check if next line also matches with what we are looking for, if so data falls on second line not first
                            nextLine = fullPagetext[lineIndex+1].split("  ")
                            if cashAndPooledInvestmentsSplit.find(nextLine[0]) != -1:
                                if(len(nextLine) > 3):
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0] + " - ASSETS"
                                    #Keep data, remove header
                                    fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                    #Replace or remove these items and only keep numbers
                                    cleanSpecialChars(lineIndex+1)
                                    #Split numerical data by , based on space detected between each
                                    row = fullPagetext[lineIndex+1].split()
                                    #Store data into a list
                                    cashAndPooledInvestmentList.append(date)
                                    cashAndPooledInvestmentList.append(county)
                                    cashAndPooledInvestmentList.append(header)
                                    cashAndPooledInvestmentList.append(pageHeader)
                                    cashAndPooledInvestmentList.append(row[0])
                                    cashAndPooledInvestmentList.append(row[len(row) - 1])


                                    FINAL_PAGE_DATA.append(cashAndPooledInvestmentList)
                                    lineIndex += 1
                            else:
                                thisLine = fullPagetext[lineIndex].split("  ")
                                if(len(thisLine) > 3):
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " - ASSETS"
                                    
                                    #Keep data, remove header
                                    fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")
                                    
                                    #get rid of ( ) and $
                                    cleanSpecialChars(lineIndex)
                                    
                                    #Split numerical data by, based on space detected between each
                                    row = fullPagetext[lineIndex].split()
                                    #Store data into a list
                                    cashAndPooledInvestmentList.append(date)
                                    cashAndPooledInvestmentList.append(county)
                                    cashAndPooledInvestmentList.append(header)
                                    cashAndPooledInvestmentList.append(pageHeader)
                                    cashAndPooledInvestmentList.append(row[0])
                                    cashAndPooledInvestmentList.append(row[len(row) - 1])


                                    FINAL_PAGE_DATA.append(cashAndPooledInvestmentList)
                        elif totalAssetsFound != -1:
                            #Check if next line also matches with what we are looking for, if so data falls on second line not first
                            nextLine = fullPagetext[lineIndex+1].split("  ")
                            if totalAssetsFilter.find(nextLine[0]) != -1:
                                if(len(nextLine) > 3):
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0] + " - ASSETS"
                                    #Keep data, remove header
                                    fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                    #Replace or remove these items and only keep numbers
                                    cleanSpecialChars(lineIndex+1)
                                    #Split numerical data by , based on space detected between each
                                    row = fullPagetext[lineIndex+1].split()
                                    #Store data into a list
                                    totalAssetsList.append(date)
                                    totalAssetsList.append(county)
                                    totalAssetsList.append(header)
                                    totalAssetsList.append(pageHeader)
                                    totalAssetsList.append(row[0])
                                    totalAssetsList.append(row[len(row) - 1])


                                    FINAL_PAGE_DATA.append(totalAssetsList)
                                    lineIndex += 1
                            else:
                                thisLine = fullPagetext[lineIndex].split("  ")
                                if(len(thisLine) > 3):
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " - ASSETS"
                                    
                                    #Keep data, remove header
                                    fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")
                                    
                                    #get rid of ( ) and $
                                    cleanSpecialChars(lineIndex)
                                    
                                    #Split numerical data by, based on space detected between each
                                    row = fullPagetext[lineIndex].split()
                                    #Store data into a list
                                    totalAssetsList.append(date)
                                    totalAssetsList.append(county)
                                    totalAssetsList.append(header)
                                    totalAssetsList.append(pageHeader)
                                    totalAssetsList.append(row[0])
                                    totalAssetsList.append(row[len(row) - 1])

   
                                    FINAL_PAGE_DATA.append(totalAssetsList)
                        elif totalLiabilitiesFound != -1:
                            #Check if next line also matches with what we are looking for, if so data falls on second line not first
                            nextLine = fullPagetext[lineIndex+1].split("  ")
                            if totalLiabilitiesFilter.find(nextLine[0]) != -1:
                                if(len(nextLine) > 3):
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0] + " - LIABILITIES"
                                    #Keep data, remove header
                                    fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                    #Replace or remove these items and only keep numbers
                                    cleanSpecialChars(lineIndex+1)
                                    #Split numerical data by , based on space detected between each
                                    row = fullPagetext[lineIndex+1].split()
                                    #Store data into a list
                                    totalLiabilitiesList.append(date)
                                    totalLiabilitiesList.append(county)
                                    totalLiabilitiesList.append(header)
                                    totalLiabilitiesList.append(pageHeader)
                                    totalLiabilitiesList.append(row[0])
                                    totalLiabilitiesList.append(row[len(row) - 1])


                                    FINAL_PAGE_DATA.append(totalLiabilitiesList)
                                    lineIndex += 1
                            else:
                                thisLine = fullPagetext[lineIndex].split("  ")
                                if(len(thisLine) > 3):
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " - LIABILITIES"
                                    
                                    #Keep data, remove header
                                    fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")
                                    
                                    #get rid of ( ) and $
                                    cleanSpecialChars(lineIndex)
                                    
                                    #Split numerical data by, based on space detected between each
                                    row = fullPagetext[lineIndex].split()
                                    #Store data into a list
                                    totalLiabilitiesList.append(date)
                                    totalLiabilitiesList.append(county)
                                    totalLiabilitiesList.append(header)
                                    totalLiabilitiesList.append(pageHeader)
                                    totalLiabilitiesList.append(row[0])
                                    totalLiabilitiesList.append(row[len(row) - 1])


                                    FINAL_PAGE_DATA.append(totalLiabilitiesList)
                        elif nonSpendableFound != -1:
                            #Check if next line also matches with what we are looking for, if so data falls on second line not first
                            nextLine = fullPagetext[lineIndex+1].split("  ")
                            if nonSpendableFilter.find(nextLine[0]) != -1:
                                if(len(nextLine) > 3):
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0] + " - FUND BALANCES"
                                    #Keep data, remove header
                                    fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                    #Replace or remove these items and only keep numbers
                                    cleanSpecialChars(lineIndex+1)
                                    #Split numerical data by , based on space detected between each
                                    row = fullPagetext[lineIndex+1].split()
                                    #Store data into a list
                                    nonspenableList.append(date)
                                    nonspenableList.append(county)
                                    nonspenableList.append(header)
                                    nonspenableList.append(pageHeader)
                                    nonspenableList.append(row[0])
                                    nonspenableList.append(row[len(row) - 1])


                                    FINAL_PAGE_DATA.append(nonspenableList)
                                    lineIndex += 1
                            else:
                                thisLine = fullPagetext[lineIndex].split("  ")
                                if(len(thisLine) > 3):
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " - FUND BALANCES"
                                    
                                    #Keep data, remove header
                                    fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")
                                    
                                    #get rid of ( ) and $
                                    cleanSpecialChars(lineIndex)
                                    
                                    #Split numerical data by, based on space detected between each
                                    row = fullPagetext[lineIndex].split()
                                    #Store data into a list
                                    nonspenableList.append(date)
                                    nonspenableList.append(county)
                                    nonspenableList.append(header)
                                    nonspenableList.append(pageHeader)
                                    nonspenableList.append(row[0])
                                    nonspenableList.append(row[len(row) - 1])


                                    FINAL_PAGE_DATA.append(nonspenableList)
                        elif restrictedFound != -1:
                            #Check if next line also matches with what we are looking for, if so data falls on second line not first
                            nextLine = fullPagetext[lineIndex+1].split("  ")
                            if restrictedFilter.find(nextLine[0]) != -1:
                                if(len(nextLine) > 3):
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0] + " - FUND BALANCES"
                                    #Keep data, remove header
                                    fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                    #Replace or remove these items and only keep numbers
                                    cleanSpecialChars(lineIndex+1)
                                    #Split numerical data by , based on space detected between each
                                    row = fullPagetext[lineIndex+1].split()
                                    #Store data into a list
                                    restrictedList.append(date)
                                    restrictedList.append(county)
                                    restrictedList.append(header)
                                    restrictedList.append(pageHeader)
                                    restrictedList.append(row[0])
                                    restrictedList.append(row[len(row) - 1])


                                    FINAL_PAGE_DATA.append(restrictedList)
                                    lineIndex += 1
                            else:
                                thisLine = fullPagetext[lineIndex].split("  ")
                                if(len(thisLine) > 3):
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " - FUND BALANCES"
                                    
                                    #Keep data, remove header
                                    fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")
                                    
                                    #get rid of ( ) and $
                                    cleanSpecialChars(lineIndex)
                                    
                                    #Split numerical data by, based on space detected between each
                                    row = fullPagetext[lineIndex].split()
                                    #Store data into a list
                                    restrictedList.append(date)
                                    restrictedList.append(county)
                                    restrictedList.append(header)
                                    restrictedList.append(pageHeader)
                                    restrictedList.append(row[0])
                                    restrictedList.append(row[len(row) - 1])


                                    FINAL_PAGE_DATA.append(restrictedList) 
                        elif commitedFound != -1:
                            #Check if next line also matches with what we are looking for, if so data falls on second line not first
                            nextLine = fullPagetext[lineIndex+1].split("  ")
                            if commitedFilter.find(nextLine[0]) != -1:
                                if(len(nextLine) > 3):
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0] + " - FUND BALANCES"
                                    #Keep data, remove header
                                    fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                    #Replace or remove these items and only keep numbers
                                    cleanSpecialChars(lineIndex+1)
                                    #Split numerical data by , based on space detected between each
                                    row = fullPagetext[lineIndex+1].split()
                                    #Store data into a list
                                    commitedList.append(date)
                                    commitedList.append(county)
                                    commitedList.append(header)
                                    commitedList.append(pageHeader)
                                    commitedList.append(row[0])
                                    commitedList.append(row[len(row) - 1])


                                    FINAL_PAGE_DATA.append(commitedList)
                                    lineIndex += 1
                            else:
                                thisLine = fullPagetext[lineIndex].split("  ")
                                if(len(thisLine) > 3):
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " - FUND BALANCES"
                                    
                                    #Keep data, remove header
                                    fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")
                                    
                                    #get rid of ( ) and $
                                    cleanSpecialChars(lineIndex)
                                    
                                    #Split numerical data by, based on space detected between each
                                    row = fullPagetext[lineIndex].split()
                                    #Store data into a list
                                    commitedList.append(date)
                                    commitedList.append(county)
                                    commitedList.append(header)
                                    commitedList.append(pageHeader)
                                    commitedList.append(row[0])
                                    commitedList.append(row[len(row) - 1])


                                    FINAL_PAGE_DATA.append(commitedList)
                        elif assignedFound != -1:
                            #Check if next line also matches with what we are looking for, if so data falls on second line not first
                            nextLine = fullPagetext[lineIndex+1].split("  ")
                            if assignedFilter.find(nextLine[0]) != -1:
                                if(len(nextLine) > 3):
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0] + " - FUND BALANCES"
                                    #Keep data, remove header
                                    fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                    #Replace or remove these items and only keep numbers
                                    cleanSpecialChars(lineIndex+1)
                                    #Split numerical data by , based on space detected between each
                                    row = fullPagetext[lineIndex+1].split()
                                    #Store data into a list
                                    assignedList.append(date)
                                    assignedList.append(county)
                                    assignedList.append(header)
                                    assignedList.append(pageHeader)
                                    assignedList.append(row[0])
                                    assignedList.append(row[len(row) - 1])


                                    FINAL_PAGE_DATA.append(assignedList)
                                    lineIndex += 1
                            else:
                                thisLine = fullPagetext[lineIndex].split("  ")
                                if(len(thisLine) > 3):
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " - FUND BALANCES"

                                    #Keep data, remove header
                                    fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")

                                    #get rid of ( ) and $
                                    cleanSpecialChars(lineIndex)
                                   
                                    #Split numerical data by, based on space detected between each
                                    row = fullPagetext[lineIndex].split()
                                    #Store data into a list
                                    assignedList.append(date)
                                    assignedList.append(county)
                                    assignedList.append(header)
                                    assignedList.append(pageHeader)
                                    assignedList.append(row[0])
                                    assignedList.append(row[len(row) - 1])


                                    FINAL_PAGE_DATA.append(assignedList)
                        elif unassignedFound != -1:
                            #Check if next line also matches with what we are looking for, if so data falls on second line not first
                            nextLine = fullPagetext[lineIndex+1].split("  ")
                            if unassignedFilter.find(nextLine[0]) != -1:
                                if(len(nextLine) > 3):
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0] + " - FUND BALANCES"

                                    #Keep data, remove header
                                    fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")

                                    #Replace or remove these items and only keep numbers
                                    cleanSpecialChars(lineIndex+1)
                                    #Split numerical data by , based on space detected between each
                                    row = fullPagetext[lineIndex+1].split()
                                    #Store data into a list
                                    unassignedList.append(date)
                                    unassignedList.append(county)
                                    unassignedList.append(header)
                                    unassignedList.append(pageHeader)
                                    unassignedList.append(row[0])
                                    unassignedList.append(row[len(row) - 1])


                                    FINAL_PAGE_DATA.append(unassignedList)
                                    lineIndex += 1
                            else:
                                thisLine = fullPagetext[lineIndex].split("  ")
                                if(len(thisLine) > 3):
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " - FUND BALANCES"

                                    #Keep data, remove header
                                    fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")

                                    #get rid of ( ) and $
                                    cleanSpecialChars(lineIndex)
                                    
                                    #Split numerical data by, based on space detected between each
                                    row = fullPagetext[lineIndex].split()

                                    #Store data into a list
                                    unassignedList.append(date)
                                    unassignedList.append(county)
                                    unassignedList.append(header)
                                    unassignedList.append(pageHeader)
                                    unassignedList.append(row[0])
                                    unassignedList.append(row[len(row) - 1])


                                    FINAL_PAGE_DATA.append(unassignedList)
                        elif totalFundBalancesFound != -1:
                            #Check if next line also matches with what we are looking for, if so data falls on second line not first
                            nextLine = fullPagetext[lineIndex+1].split("  ")
                            if totalFundBalancesFilter.find(nextLine[0]) != -1:
                                if(len(nextLine) > 3):
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0] + " - FUND BALANCES"

                                    #Keep data, remove header
                                    fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")

                                    #Replace or remove these items and only keep numbers
                                    cleanSpecialChars(lineIndex+1)
                                    #Split numerical data by , based on space detected between each
                                    row = fullPagetext[lineIndex+1].split()
                                    #Store data into a list
                                    totalFundBalancesList.append(date)
                                    totalFundBalancesList.append(county)
                                    totalFundBalancesList.append(header)
                                    totalFundBalancesList.append(pageHeader)
                                    totalFundBalancesList.append(row[0])
                                    totalFundBalancesList.append(row[len(row) - 1])

                                    FINAL_PAGE_DATA.append(totalFundBalancesList)
                                    lineIndex += 1
                            else:
                                thisLine = fullPagetext[lineIndex].split("  ")
                                if(len(thisLine) > 3):
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " - FUND BALANCES"

                                    #Keep data, remove header
                                    fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")

                                    #get rid of ( ) and $
                                    cleanSpecialChars(lineIndex)

                                    #Split numerical data by, based on space detected between each
                                    row = fullPagetext[lineIndex].split()
                                    #Store data into a list
                                    totalFundBalancesList.append(date)
                                    totalFundBalancesList.append(county)
                                    totalFundBalancesList.append(header)
                                    totalFundBalancesList.append(pageHeader)
                                    totalFundBalancesList.append(row[0])
                                    totalFundBalancesList.append(row[len(row) - 1])


                                    FINAL_PAGE_DATA.append(totalFundBalancesList)
                        lineIndex+=1
                print(FINAL_PAGE_DATA)
                fillDF(FINAL_PAGE_DATA, headerlist)
                print("---------------------DONE PAGE Balance Sheet - Governmental Funds----------------------\n\n\n") 

            elif len(statementOfRevsExFundBalancesPages) >= 1 and i == statementOfRevsExFundBalancesPages[0]:
                FINAL_PAGE_DATA.clear()
                text = page.extract_text()
                
                #CSV headers
                headerlist = ['DATE', 'COUNTY', 'PAGE_HEADER', 'SUB_DATA_HEADER', 'GENERAL', 'TOTAL_GOVERNMENTAL_FUNDS']

                #Datafiller lines
                dfLine = namedtuple('dfLine', 'date county header pageheader govActivityData busActivityData totalData')
                propertyTaxesList = []
                taxesList = []
                totalRevenuesList = []
                nonspenableList = [] 
                debtServiceList = [] 
                principalList = [] 
                interestAndFiscalChargesList = [] 
                capitalOutlayList = [] 
                totalExpendituresList = []
                totalOtherFinancingSourcesList = []
                netChangeInFundBalancesList = []

                #GETTING NEXT PAGE TO CHECK IF NEXT PAGE IS A CONTINUATION OR NOT
                nextPagetext = pages[i + 1].extract_text()

                #------------------Filters-----------------
                county_filter = re.compile(r'county|COUNTY|County$')
                statementOfRevenuesExpenandChangesinFundBFilter = re.compile(r'Statement of Revenues, Expenditures and Changes in Fund Balances|statement of revenues, expenditures and changes in fund balances|STATEMENT OF REVENUES, EXPENDITURES AND CHANGES IN FUND BALANCES')
                governmentalFundsFilter = re.compile(r'Governmental Funds')
                dateFilter = re.compile(r'[a-zA-Z]+\s\d\d[,]\s\d\d\d\d')

                 #-------------------REVENUES-----------------------------
                propertyTaxesFilter = "Property taxes"
                taxesFilter = "Taxes"
                totalRevenuesFilter = "Total revenues"

                #-------------------EXPENDITURES-----------------------------
                debtServiceFilter = "Debt Service"
                principalFilter = "Principal"
                interestAndFiscalChargesFilter = "Interest and fiscal charges"
                capitalOutlayFilter = "Capital outlay"
                totalExpendituresFilter = re.compile(r'Total expenditures')
                #-------------------OTHER---------------------------
                totalOtherFinancingSourcesFilter = "Total other financing sources (uses)"
                netChangeInFundBalancesFilter = "Net change in fund balances"

                #CHECK IF THIS PAGE DATA CONTINUES TO NEXT PAGE
                isContinued = nextPageContinued(nextPagetext)

                #Temp variables
                county = ''
                date = ''
                header = ''
                if isContinued:
                    #Divide the whole text based on '\n' found (end of line split)
                    fullPagetext = text.split('\n')
                     #each line will be manipulated using index, index starts at 0
                    lineIndex = 0
                    #this keeps track of datapoints to be grabbed from next page, because there is no flag to look for in the next page (we will assign a line counter). 
                    dataLineCounter = 0
                    dataLineBool = False
                    dataLineIndexes = []

                    while lineIndex in range(len(fullPagetext)):
                         #Get rid of $ signs
                        fullPagetext[lineIndex] = fullPagetext[lineIndex].replace("$", " ")
                        #Look for these flags within the page (as we go line by line), if found return true, otherwise false
                        countyFound = county_filter.search(fullPagetext[lineIndex])
                        headerFound = statementOfRevenuesExpenandChangesinFundBFilter.search(fullPagetext[lineIndex])
                        dateFound = dateFilter.search(fullPagetext[lineIndex])
                        propertyTaxesFound = propertyTaxesFilter.find(fullPagetext[lineIndex].split("  ")[0])
                        taxesFound = taxesFilter.find(fullPagetext[lineIndex].split("  ")[0])
                        totalRevenuesFound = totalRevenuesFilter.find(fullPagetext[lineIndex].split("  ")[0])
                        debtServiceFound = debtServiceFilter.find(fullPagetext[lineIndex].split("  ")[0])
                        principalFound = principalFilter.find(fullPagetext[lineIndex].split("  ")[0])
                        interestAndFiscalChargesFound = interestAndFiscalChargesFilter.find(fullPagetext[lineIndex].split("  ")[0])
                        capitalOutlayFound = capitalOutlayFilter.find(fullPagetext[lineIndex].split("  ")[0])
                        totalExpendituresFound = totalExpendituresFilter.search(fullPagetext[lineIndex].split("  ")[0])
                        totalOtherFinancingSourcesFound = totalOtherFinancingSourcesFilter.find(fullPagetext[lineIndex].split("  ")[0])
                        netChangeInFundBalancesFound = netChangeInFundBalancesFilter.find(fullPagetext[lineIndex].split("  ")[0])
                        #Making our own numerical flag tracker, for next page (since next page does not have flags to look out for)
                        if dataLineBool:
                            rowItems = fullPagetext[lineIndex].split("  ")
                            #Make sure the lines we are counting actually have data, and they're not simply headers
                            #The lines of the first page which have data will all be given a numerical value, these numerical value will be matched on the next page to correlate with the exact flag
                            if len(rowItems) > 3:
                                dataLineCounter +=1

                        #If found, then store them into a data list
                        if countyFound:
                            county = fullPagetext[lineIndex]
                        elif dateFound:
                            date = fullPagetext[lineIndex].replace("Year Ended", "")
                        elif headerFound:
                            header = fullPagetext[lineIndex]
                            if governmentalFundsFilter.search(fullPagetext[lineIndex + 1]):
                                header = header + " - " + fullPagetext[lineIndex + 1]
                                lineIndex+=1
                        elif propertyTaxesFound != -1:
                            dataLineBool = True
                            dataLineCounter += 1;
                            #Check if next line also matches with what we are looking for, if so data falls on second line not first
                            nextLine = fullPagetext[lineIndex+1].split("  ")
                            if propertyTaxesFilter.find(nextLine[0]) != -1:
                                if(len(nextLine) > 3):
                                    dataLineIndexes.append(dataLineCounter)
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0] + " - REVENUES"
                                    #Keep data, remove header
                                    fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                    #Replace or remove these items and only keep numbers
                                    cleanSpecialChars(lineIndex+1)
                                    #Split numerical data by , based on space detected between each
                                    row = fullPagetext[lineIndex+1].split()
                                    #Store data into a list
									storeInList(propertyTaxesList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE
                                    FINAL_PAGE_DATA.append(propertyTaxesList)
                                    lineIndex += 1
                            else:
                                thisLine = fullPagetext[lineIndex].split("  ")
                                if(len(thisLine) > 3):
                                    dataLineIndexes.append(dataLineCounter)
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " - REVENUES"
                                    
                                    #Keep data, remove header
                                    fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")
                                    
                                    #get rid of ( ) and $
                                    cleanSpecialChars(lineIndex)
                                    
                                    #Split numerical data by, based on space detected between each
                                    row = fullPagetext[lineIndex].split()
                                    #Store data into a list
                                    storeInList(propertyTaxesList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE
                                    FINAL_PAGE_DATA.append(propertyTaxesList)
                        elif taxesFound != -1:
                            #Check if next line also matches with what we are looking for, if so data falls on second line not first
                            nextLine = fullPagetext[lineIndex+1].split("  ")
                            if taxesFilter.find(nextLine[0]) != -1:
                                if(len(nextLine) > 3):
                                    dataLineIndexes.append(dataLineCounter)
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0] + " - REVENUES"
                                    #Keep data, remove header
                                    fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                    #Replace or remove these items and only keep numbers
                                    cleanSpecialChars(lineIndex+1)
                                    #Split numerical data by , based on space detected between each
                                    row = fullPagetext[lineIndex+1].split()
                                    #Store data into a list
									storeInList(taxesList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE
                                    FINAL_PAGE_DATA.append(taxesList)
                                    lineIndex += 1
                            else:
                                thisLine = fullPagetext[lineIndex].split("  ")
                                if(len(thisLine) > 3):
                                    dataLineIndexes.append(dataLineCounter)

                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " - REVENUES"
                                    
                                    #Keep data, remove header
                                    fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")
                                    
                                    #get rid of ( ) and $
                                    cleanSpecialChars(lineIndex)
                                    
                                    #Split numerical data by, based on space detected between each
                                    row = fullPagetext[lineIndex].split()
                                    #Store data into a list
                                    storeInList(taxesList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE     
                                    FINAL_PAGE_DATA.append(taxesList)
                        elif totalRevenuesFound != -1:
                            #Check if next line also matches with what we are looking for, if so data falls on second line not first
                            nextLine = fullPagetext[lineIndex+1].split("  ")
                            if totalRevenuesFilter.find(nextLine[0]) != -1:
                                if(len(nextLine) > 3):
                                    dataLineIndexes.append(dataLineCounter)
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0] + " - REVENUES"
                                    #Keep data, remove header
                                    fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                    #Replace or remove these items and only keep numbers
                                    cleanSpecialChars(lineIndex+1)
                                    #Split numerical data by , based on space detected between each
                                    row = fullPagetext[lineIndex+1].split()
                                    #Store data into a list
									storeInList(totalRevenuesList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE
                                    FINAL_PAGE_DATA.append(totalRevenuesList)
                                    lineIndex += 1
                            else:
                                thisLine = fullPagetext[lineIndex].split("  ")
                                if(len(thisLine) > 3):
                                    dataLineIndexes.append(dataLineCounter)
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " - REVENUES"
                                    
                                    #Keep data, remove header
                                    fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")
                                    
                                    #get rid of ( ) and $
                                    cleanSpecialChars(lineIndex)
                                    
                                    #Split numerical data by, based on space detected between each
                                    row = fullPagetext[lineIndex].split()
                                    #Store data into a list
                                    storeInList(totalRevenuesList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE
                                    FINAL_PAGE_DATA.append(totalRevenuesList)
                        elif debtServiceFound != -1:
                            #Check if next line also matches with what we are looking for, if so data falls on second line not first
                            nextLine = fullPagetext[lineIndex+1].split("  ")
                            if debtServiceFilter.find(nextLine[0]) != -1:
                                if(len(nextLine) > 3):
                                    dataLineIndexes.append(dataLineCounter)
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0] + " - EXPENDITURES"
                                    #Keep data, remove header
                                    fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                    #Replace or remove these items and only keep numbers
                                    cleanSpecialChars(lineIndex+1)
                                    #Split numerical data by , based on space detected between each
                                    row = fullPagetext[lineIndex+1].split()
                                    #Store data into a list
									storeInList(debtServiceList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE
                                    FINAL_PAGE_DATA.append(debtServiceList)
                                    lineIndex += 1
                            else:
                                thisLine = fullPagetext[lineIndex].split("  ")
                                if(len(thisLine) > 3):
                                    dataLineIndexes.append(dataLineCounter)
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " - EXPENDITURES"
                                    
                                    #Keep data, remove header
                                    fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")
                                    
                                    #get rid of ( ) and $
                                    cleanSpecialChars(lineIndex)
                                    
                                    #Split numerical data by, based on space detected between each
                                    row = fullPagetext[lineIndex].split()
                                    #Store data into a list
                                    storeInList(debtServiceList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE
                                    FINAL_PAGE_DATA.append(debtServiceList)
                        elif principalFound != -1:
                            #Check if next line also matches with what we are looking for, if so data falls on second line not first
                            nextLine = fullPagetext[lineIndex+1].split("  ")
                            if principalFilter.find(nextLine[0]) != -1:
                                if(len(nextLine) > 3):
                                    dataLineIndexes.append(dataLineCounter)
                                    pageHeader = "Debt Service: " + fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0] + " - EXPENDITURES"
                                    #Keep data, remove header
                                    fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                    #Replace or remove these items and only keep numbers
                                    cleanSpecialChars(lineIndex+1)
                                    #Split numerical data by , based on space detected between each
                                    row = fullPagetext[lineIndex].split("  ")
                                    row = list(filter(None, row))
                                    #Store data into a list
									storeInList(principalList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE
                                    FINAL_PAGE_DATA.append(principalList)
                                    lineIndex += 1
                            else:
                                thisLine = fullPagetext[lineIndex].split("  ")
                                if(len(thisLine) > 3):
                                    dataLineIndexes.append(dataLineCounter)
                                    pageHeader = "Debt Service: " + fullPagetext[lineIndex].split("   ")[0] + " - EXPENDITURES"
                                    
                                    #Keep data, remove header
                                    fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")
                                    
                                    #get rid of ( ) and $
                                    cleanSpecialChars(lineIndex)

                                    #Split numerical data by, based on space detected between each
                                    print(fullPagetext[lineIndex])
                                    row = fullPagetext[lineIndex].split("  ")
                                    row = list(filter(None, row))
                                    #Store data into a list
									storeInList(principalList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE   
                                    FINAL_PAGE_DATA.append(principalList) 
                        elif interestAndFiscalChargesFound != -1:
                            #Check if next line also matches with what we are looking for, if so data falls on second line not first
                            nextLine = fullPagetext[lineIndex+1].split("  ")
                            if interestAndFiscalChargesFilter.find(nextLine[0]) != -1:
                                if(len(nextLine) > 3):
                                    dataLineIndexes.append(dataLineCounter)
                                    pageHeader = "Debt Service: " + fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0] + " - EXPENDITURES"
                                    #Keep data, remove header
                                    fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                    #Replace or remove these items and only keep numbers
                                    cleanSpecialChars(lineIndex+1)
                                    #Split numerical data by , based on space detected between each
                                    row = fullPagetext[lineIndex+1].split()
                                    #Store data into a list
									storeInList(interestAndFiscalChargesList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE
                                    FINAL_PAGE_DATA.append(interestAndFiscalChargesList)
                                    lineIndex += 1
                            else:
                                thisLine = fullPagetext[lineIndex].split("  ")
                                if(len(thisLine) > 3):
                                    dataLineIndexes.append(dataLineCounter)
                                    pageHeader = "Debt Service: " + fullPagetext[lineIndex].split("   ")[0] + " - EXPENDITURES"
                                    
                                    #Keep data, remove header
                                    fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")
                                    
                                    #get rid of ( ) and $
                                    cleanSpecialChars(lineIndex)
                                    
                                    #Split numerical data by, based on space detected between each
                                    row = fullPagetext[lineIndex].split()
                                    #Store data into a list
                                    storeInList(interestAndFiscalChargesList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE 
                                    FINAL_PAGE_DATA.append(interestAndFiscalChargesList)
                        elif capitalOutlayFound != -1:
                            #Check if next line also matches with what we are looking for, if so data falls on second line not first
                            nextLine = fullPagetext[lineIndex+1].split("  ")
                            if capitalOutlayFilter.find(nextLine[0]) != -1:
                                if(len(nextLine) > 3):
                                    dataLineIndexes.append(dataLineCounter)
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0] + " - EXPENDITURES"
                                    #Keep data, remove header
                                    fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                    #Replace or remove these items and only keep numbers
                                    cleanSpecialChars(lineIndex+1)
                                    #Split numerical data by , based on space detected between each
                                    row = fullPagetext[lineIndex+1].split()
                                    #Store data into a list
									storeInList(capitalOutlayList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE
                                    FINAL_PAGE_DATA.append(capitalOutlayList)
                                    lineIndex += 1
                            else:
                                thisLine = fullPagetext[lineIndex].split("  ")
                                if(len(thisLine) > 3):
                                    dataLineIndexes.append(dataLineCounter)
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " - EXPENDITURES"

                                    #Keep data, remove header
                                    fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")

                                    #get rid of ( ) and $
                                    cleanSpecialChars(lineIndex)
                                   
                                    #Split numerical data by, based on space detected between each
                                    row = fullPagetext[lineIndex].split()
                                    #Store data into a list
									storeInList(capitalOutlayList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE 
                                    FINAL_PAGE_DATA.append(capitalOutlayList)
                        elif totalExpendituresFound:
                            #Check if next line also matches with what we are looking for, if so data falls on second line not first
                            nextLine = fullPagetext[lineIndex+1].split("  ")
                            if totalExpendituresFilter.search(nextLine[0]):
                                if(len(nextLine) > 3):
                                    dataLineIndexes.append(dataLineCounter)
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0] + " - EXPENDITURES"

                                    #Keep data, remove header
                                    fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")

                                    #Replace or remove these items and only keep numbers
                                    cleanSpecialChars(lineIndex+1)
                                    #Split numerical data by , based on space detected between each
                                    row = fullPagetext[lineIndex+1].split()
                                    #Store data into a list
									storeInList(totalExpendituresList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE
                                    FINAL_PAGE_DATA.append(totalExpendituresList)
                                    lineIndex += 1
                            else:
                                thisLine = fullPagetext[lineIndex].split("  ")
                                if(len(thisLine) > 3):
                                    dataLineIndexes.append(dataLineCounter)
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " - EXPENDITURES"

                                    #Keep data, remove header
                                    fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")

                                    #get rid of ( ) and $
                                    cleanSpecialChars(lineIndex)
                                    
                                    #Split numerical data by, based on space detected between each
                                    row = fullPagetext[lineIndex].split()

                                    #Store data into a list
                                    storeInList(totalExpendituresList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE 
                                    FINAL_PAGE_DATA.append(totalExpendituresList)
                        elif totalOtherFinancingSourcesFound != -1:
                            #Check if next line also matches with what we are looking for, if so data falls on second line not first
                            nextLine = fullPagetext[lineIndex+1].split("  ")
                            if totalOtherFinancingSourcesFilter.find(nextLine[0]) != -1:
                                if(len(nextLine) > 3):
                                    dataLineIndexes.append(dataLineCounter)
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0]

                                    #Keep data, remove header
                                    fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")

                                    #Replace or remove these items and only keep numbers
                                    cleanSpecialChars(lineIndex+1)
                                    #Split numerical data by , based on space detected between each
                                    row = fullPagetext[lineIndex+1].split()
                                    #Store data into a list
									storeInList(totalOtherFinancingSourcesList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE
                                    FINAL_PAGE_DATA.append(totalOtherFinancingSourcesList)
                                    lineIndex += 1
                            else:
                                dataLineIndexes.append(dataLineCounter)
                                thisLine = fullPagetext[lineIndex].split("  ")
                                if(len(thisLine) > 3):
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] 

                                    #Keep data, remove header
                                    fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")

                                    #get rid of ( ) and $
                                    cleanSpecialChars(lineIndex)

                                    #Split numerical data by, based on space detected between each
                                    row = fullPagetext[lineIndex].split()
                                    #Store data into a list
                                    storeInList(totalOtherFinancingSourcesList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE 
                                    FINAL_PAGE_DATA.append(totalOtherFinancingSourcesList)
                        elif netChangeInFundBalancesFound != -1:
                            #Check if next line also matches with what we are looking for, if so data falls on second line not first
                            nextLine = fullPagetext[lineIndex+1].split("  ")
                            if netChangeInFundBalancesFilter.find(nextLine[0]) != -1:
                                if(len(nextLine) > 3):
                                    dataLineIndexes.append(dataLineCounter)
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0]

                                    #Keep data, remove header
                                    fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")

                                    #Replace or remove these items and only keep numbers
                                    cleanSpecialChars(lineIndex+1)
                                    #Split numerical data by , based on space detected between each
                                    row = fullPagetext[lineIndex+1].split()
                                    #Store data into a list
									storeInList(netChangeInFundBalancesList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE
                                    FINAL_PAGE_DATA.append(netChangeInFundBalancesList)
                                    lineIndex += 1
                            else:
                                dataLineIndexes.append(dataLineCounter)
                                thisLine = fullPagetext[lineIndex].split("  ")
                                if(len(thisLine) > 3):
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] 

                                    #Keep data, remove header
                                    fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")

                                    #get rid of ( ) and $
                                    cleanSpecialChars(lineIndex)

                                    #Split numerical data by, based on space detected between each
                                    row = fullPagetext[lineIndex].split()
                                    #Store data into a list
                                    storeInList(netChangeInFundBalancesList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE 
                                    FINAL_PAGE_DATA.append(netChangeInFundBalancesList)
                        lineIndex+=1

                    #**************************************ITERATE OVER THE NEXT PAGE TO GRAB THOSE MISSING DATAPOINTS**************************
                    fullNextPagetext = nextPagetext.split('\n')
                    lineIndex2 = 0
                    final_page_data_iterator = 0
                    #This is the counter we need to align it with flags in the last page
                    matchCounter = 0
                    counterInitialize = False
                    #---------Number Filter------------
                    numbersFilter = re.compile(r'[\d]+')
                    #this loop is to iterate over the next page data
                    while lineIndex2 in range(len(fullNextPagetext)):

                        numbersFound = numbersFilter.search(fullNextPagetext[lineIndex2])
                        
                        if counterInitialize:
                            matchCounter += 1
                        #FIRST NUMBER DETECTED, then start the counter to match with the counter when it started in the last page
                        if numbersFound and not(counterInitialize):
                            counterInitialize = True
                            matchCounter += 1
                        if matchCounter in dataLineIndexes:
                            #get rid of ( ) and $
                            cleanSpecialChars(lineIndex2)

                            #Split numerical data by, based on space detected between each
                            row = fullNextPagetext[lineIndex2].split("  ") #CHANGEDDD
                            row = list(filter(None, row))  #CHANGEDDD
                            #append this data into the FINAL_PAGE_DATA (it will be in order)
                            FINAL_PAGE_DATA[final_page_data_iterator].append(row[len(row) - 1])
                            final_page_data_iterator+=1
                        lineIndex2+=1
                #------------------------------------------IF THIS PAGE's DATA DOES NOT EXTEND TO THE NEXT PAGE--------------------------------------------------------
                else: 
                    #Divide the whole text based on '\n' found (end of line split)
                    fullPagetext = text.split('\n')
                     #each line will be manipulated using index, index starts at 0
                    lineIndex = 0


                    while lineIndex in range(len(fullPagetext)):
                         #Get rid of $ signs
                        fullPagetext[lineIndex] = fullPagetext[lineIndex].replace("$", " ")
                        #Look for these flags within the page (as we go line by line), if found return true, otherwise false
                        countyFound = county_filter.search(fullPagetext[lineIndex])
                        headerFound = statementOfRevenuesExpenandChangesinFundBFilter.search(fullPagetext[lineIndex])
                        dateFound = dateFilter.search(fullPagetext[lineIndex])
                        propertyTaxesFound = propertyTaxesFilter.find(fullPagetext[lineIndex].split("  ")[0])
                        taxesFound = taxesFilter.find(fullPagetext[lineIndex].split("  ")[0])
                        totalRevenuesFound = totalRevenuesFilter.find(fullPagetext[lineIndex].split("  ")[0])
                        debtServiceFound = debtServiceFilter.find(fullPagetext[lineIndex].split("  ")[0])
                        principalFound = principalFilter.find(fullPagetext[lineIndex].split("  ")[0])
                        interestAndFiscalChargesFound = interestAndFiscalChargesFilter.find(fullPagetext[lineIndex].split("  ")[0])
                        capitalOutlayFound = capitalOutlayFilter.find(fullPagetext[lineIndex].split("  ")[0])
                        totalExpendituresFound = totalExpendituresFilter.search(fullPagetext[lineIndex].split("  ")[0])
                        totalOtherFinancingSourcesFound = totalOtherFinancingSourcesFilter.find(fullPagetext[lineIndex].split("  ")[0])
                        netChangeInFundBalancesFound = netChangeInFundBalancesFilter.find(fullPagetext[lineIndex].split("  ")[0])

                        #If found, then store them into a data list
                        if countyFound:
                            county = fullPagetext[lineIndex]
                        elif dateFound:
                            date = fullPagetext[lineIndex].replace("Year Ended", "")
                        elif headerFound:
                            header = fullPagetext[lineIndex]
                            if governmentalFundsFilter.search(fullPagetext[lineIndex + 1]):
                                header = header + " - " + fullPagetext[lineIndex + 1]
                                lineIndex+=1
                        elif propertyTaxesFound != -1:
                            #Check if next line also matches with what we are looking for, if so data falls on second line not first
                            nextLine = fullPagetext[lineIndex+1].split("  ")
                            if propertyTaxesFilter.find(nextLine[0]) != -1:
                                if(len(nextLine) > 3):
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0] + " - REVENUES"
                                    #Keep data, remove header
                                    fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                    #Replace or remove these items and only keep numbers
                                    cleanSpecialChars(lineIndex+1)
                                    #Split numerical data by , based on space detected between each
                                    row = fullPagetext[lineIndex+1].split()
                                    #Store data into a list
									storeInList(propertyTaxesList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE
                                    FINAL_PAGE_DATA.append(propertyTaxesList)
                                    lineIndex += 1
                            else:
                                thisLine = fullPagetext[lineIndex].split("  ")
                                if(len(thisLine) > 3):
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " - REVENUES"
                                    
                                    #Keep data, remove header
                                    fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")
                                    
                                    #get rid of ( ) and $
                                    cleanSpecialChars(lineIndex)
                                    
                                    #Split numerical data by, based on space detected between each
                                    row = fullPagetext[lineIndex].split()
                                    #Store data into a list
                                    storeInList(propertyTaxesList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE
                                    FINAL_PAGE_DATA.append(propertyTaxesList)
                        elif taxesFound != -1:
                            #Check if next line also matches with what we are looking for, if so data falls on second line not first
                            nextLine = fullPagetext[lineIndex+1].split("  ")
                            if taxesFilter.find(nextLine[0]) != -1:
                                if(len(nextLine) > 3):
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0] + " - REVENUES"
                                    #Keep data, remove header
                                    fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                    #Replace or remove these items and only keep numbers
                                    cleanSpecialChars(lineIndex+1)
                                    #Split numerical data by , based on space detected between each
                                    row = fullPagetext[lineIndex+1].split()
                                    #Store data into a list
									storeInList(taxesList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE
                                    FINAL_PAGE_DATA.append(taxesList)
                                    lineIndex += 1
                            else:
                                thisLine = fullPagetext[lineIndex].split("  ")
                                if(len(thisLine) > 3):

                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " - REVENUES"
                                    
                                    #Keep data, remove header
                                    fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")
                                    
                                    #get rid of ( ) and $
                                    cleanSpecialChars(lineIndex)
                                    
                                    #Split numerical data by, based on space detected between each
                                    row = fullPagetext[lineIndex].split()
                                    #Store data into a list
									storeInList(taxesList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE     
                                    FINAL_PAGE_DATA.append(taxesList)
                        elif totalRevenuesFound != -1:
                            #Check if next line also matches with what we are looking for, if so data falls on second line not first
                            nextLine = fullPagetext[lineIndex+1].split("  ")
                            if totalRevenuesFilter.find(nextLine[0]) != -1:
                                if(len(nextLine) > 3):
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0] + " - REVENUES"
                                    #Keep data, remove header
                                    fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                    #Replace or remove these items and only keep numbers
                                    cleanSpecialChars(lineIndex+1)
                                    #Split numerical data by , based on space detected between each
                                    row = fullPagetext[lineIndex+1].split()
                                    #Store data into a list
									storeInList(totalRevenuesList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE
                                    FINAL_PAGE_DATA.append(totalRevenuesList)
                                    lineIndex += 1
                            else:
                                thisLine = fullPagetext[lineIndex].split("  ")
                                if(len(thisLine) > 3):
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " - REVENUES"
                                    
                                    #Keep data, remove header
                                    fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")
                                    
                                    #get rid of ( ) and $
                                    cleanSpecialChars(lineIndex)
                                    
                                    #Split numerical data by, based on space detected between each
                                    row = fullPagetext[lineIndex].split()
                                    #Store data into a list
									storeInList(totalRevenuesList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE
                                    FINAL_PAGE_DATA.append(totalRevenuesList)
                        elif debtServiceFound != -1:
                            #Check if next line also matches with what we are looking for, if so data falls on second line not first
                            nextLine = fullPagetext[lineIndex+1].split("  ")
                            if debtServiceFilter.find(nextLine[0]) != -1:
                                if(len(nextLine) > 3):
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0] + " - EXPENDITURES"
                                    #Keep data, remove header
                                    fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                    #Replace or remove these items and only keep numbers
                                    cleanSpecialChars(lineIndex+1)
                                    #Split numerical data by , based on space detected between each
                                    row = fullPagetext[lineIndex+1].split()
                                    #Store data into a list
									storeInList(debtServiceList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE
                                    FINAL_PAGE_DATA.append(debtServiceList)
                                    lineIndex += 1
                            else:
                                thisLine = fullPagetext[lineIndex].split("  ")
                                if(len(thisLine) > 3):
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " - EXPENDITURES"
                                    
                                    #Keep data, remove header
                                    fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")
                                    
                                    #get rid of ( ) and $
                                    cleanSpecialChars(lineIndex)
                                    
                                    #Split numerical data by, based on space detected between each
                                    row = fullPagetext[lineIndex].split()
                                    #Store data into a list
                                    storeInList(debtServiceList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE
                                    FINAL_PAGE_DATA.append(debtServiceList)
                        elif principalFound != -1:
                            #Check if next line also matches with what we are looking for, if so data falls on second line not first
                            nextLine = fullPagetext[lineIndex+1].split("  ")
                            if principalFilter.find(nextLine[0]) != -1:
                                if(len(nextLine) > 3):
                                    pageHeader = "Debt Service: " + fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0] + " - EXPENDITURES"
                                    #Keep data, remove header
                                    fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                    #Replace or remove these items and only keep numbers
                                    cleanSpecialChars(lineIndex+1)
                                    #Split numerical data by , based on space detected between each
                                    row = fullPagetext[lineIndex].split("  ")
                                    row = list(filter(None, row))
                                    #Store data into a list
									storeInList(principalList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE
                                    FINAL_PAGE_DATA.append(principalList)
                                    lineIndex += 1
                            else:
                                thisLine = fullPagetext[lineIndex].split("  ")
                                if(len(thisLine) > 3):
                                    pageHeader = "Debt Service: " + fullPagetext[lineIndex].split("   ")[0] + " - EXPENDITURES"
                                    
                                    #Keep data, remove header
                                    fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")
                                    
                                    #get rid of ( ) and $
                                    cleanSpecialChars(lineIndex)
                                    
                                    #Split numerical data by, based on space detected between each
                                    row = fullPagetext[lineIndex].split("  ")
                                    row = list(filter(None, row))
                                    #Store data into a list
                                    storeInList(principalList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE   
                                    FINAL_PAGE_DATA.append(debtServiceList) 
                        elif interestAndFiscalChargesFound != -1:
                            #Check if next line also matches with what we are looking for, if so data falls on second line not first
                            nextLine = fullPagetext[lineIndex+1].split("  ")
                            if interestAndFiscalChargesFilter.find(nextLine[0]) != -1:
                                if(len(nextLine) > 3):
                                    pageHeader = "Debt Service: " + fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0] + " - EXPENDITURES"
                                    #Keep data, remove header
                                    fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                    #Replace or remove these items and only keep numbers
                                    cleanSpecialChars(lineIndex+1)
                                    #Split numerical data by , based on space detected between each
                                    row = fullPagetext[lineIndex+1].split()
                                    #Store data into a list
									storeInList(interestAndFiscalChargesList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE
                                    FINAL_PAGE_DATA.append(interestAndFiscalChargesList)
                                    lineIndex += 1
                            else:
                                thisLine = fullPagetext[lineIndex].split("  ")
                                if(len(thisLine) > 3):
                                    pageHeader = "Debt Service: " + fullPagetext[lineIndex].split("   ")[0] + " - EXPENDITURES"
                                    
                                    #Keep data, remove header
                                    fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")
                                    
                                    #get rid of ( ) and $
                                    cleanSpecialChars(lineIndex)
                                    
                                    #Split numerical data by, based on space detected between each
                                    row = fullPagetext[lineIndex].split()
                                    #Store data into a list
                                    storeInList(interestAndFiscalChargesList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE 
                                    FINAL_PAGE_DATA.append(commitedList)
                        elif capitalOutlayFound != -1:
                            #Check if next line also matches with what we are looking for, if so data falls on second line not first
                            nextLine = fullPagetext[lineIndex+1].split("  ")
                            if capitalOutlayFilter.find(nextLine[0]) != -1:
                                if(len(nextLine) > 3):
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0] + " - EXPENDITURES"
                                    #Keep data, remove header
                                    fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                    #Replace or remove these items and only keep numbers
                                    cleanSpecialChars(lineIndex+1)
                                    #Split numerical data by , based on space detected between each
                                    row = fullPagetext[lineIndex+1].split()
                                    #Store data into a list
									storeInList(capitalOutlayList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE
                                    FINAL_PAGE_DATA.append(capitalOutlayList)
                                    lineIndex += 1
                            else:
                                thisLine = fullPagetext[lineIndex].split("  ")
                                if(len(thisLine) > 3):
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " - EXPENDITURES"

                                    #Keep data, remove header
                                    fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")

                                    #get rid of ( ) and $
                                    cleanSpecialChars(lineIndex)
                                   
                                    #Split numerical data by, based on space detected between each
                                    row = fullPagetext[lineIndex].split()
                                    #Store data into a list
									storeInList(capitalOutlayList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE 
                                    FINAL_PAGE_DATA.append(capitalOutlayList)
                        elif totalExpendituresFound:
                            #Check if next line also matches with what we are looking for, if so data falls on second line not first
                            nextLine = fullPagetext[lineIndex+1].split("  ")
                            if totalExpendituresFilter.search(nextLine[0]):
                                if(len(nextLine) > 3):
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0] + " - EXPENDITURES"

                                    #Keep data, remove header
                                    fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")

                                    #Replace or remove these items and only keep numbers
                                    cleanSpecialChars(lineIndex+1)
                                    #Split numerical data by , based on space detected between each
                                    row = fullPagetext[lineIndex+1].split()
                                    #Store data into a list
									storeInList(totalExpendituresList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE
                                    FINAL_PAGE_DATA.append(totalExpendituresList)
                                    lineIndex += 1
                            else:
                                thisLine = fullPagetext[lineIndex].split("  ")
                                if(len(thisLine) > 3):
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " - EXPENDITURES"

                                    #Keep data, remove header
                                    fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")

                                    #get rid of ( ) and $
                                    cleanSpecialChars(lineIndex)
                                    
                                    #Split numerical data by, based on space detected between each
                                    row = fullPagetext[lineIndex].split()

                                    #Store data into a list
                                    storeInList(totalExpendituresList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE 
                                    FINAL_PAGE_DATA.append(totalExpendituresList)
                        elif totalOtherFinancingSourcesFound != -1:
                            #Check if next line also matches with what we are looking for, if so data falls on second line not first
                            nextLine = fullPagetext[lineIndex+1].split("  ")
                            if totalOtherFinancingSourcesFilter.find(nextLine[0]) != -1:
                                if(len(nextLine) > 3):
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0]

                                    #Keep data, remove header
                                    fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")

                                    #Replace or remove these items and only keep numbers
                                    cleanSpecialChars(lineIndex+1)
                                    #Split numerical data by , based on space detected between each
                                    row = fullPagetext[lineIndex+1].split()
                                    #Store data into a list
									storeInList(totalOtherFinancingSourcesList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE
                                    FINAL_PAGE_DATA.append(totalOtherFinancingSourcesList)
                                    lineIndex += 1
                            else:
                                thisLine = fullPagetext[lineIndex].split("  ")
                                if(len(thisLine) > 3):
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] 

                                    #Keep data, remove header
                                    fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")

                                    #get rid of ( ) and $
                                    cleanSpecialChars(lineIndex)

                                    #Split numerical data by, based on space detected between each
                                    row = fullPagetext[lineIndex].split()
                                    #Store data into a list
									storeInList(totalOtherFinancingSourcesList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE 
                                    FINAL_PAGE_DATA.append(totalOtherFinancingSourcesList)
                        elif netChangeInFundBalancesFound != -1:
                            #Check if next line also matches with what we are looking for, if so data falls on second line not first
                            nextLine = fullPagetext[lineIndex+1].split("  ")
                            if netChangeInFundBalancesFilter.find(nextLine[0]) != -1:
                                if(len(nextLine) > 3):
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0]

                                    #Keep data, remove header
                                    fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")

                                    #Replace or remove these items and only keep numbers
                                    cleanSpecialChars(lineIndex+1)
                                    #Split numerical data by , based on space detected between each
                                    row = fullPagetext[lineIndex+1].split()
                                    #Store data into a list
									storeInList(netChangeInFundBalancesList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE
                                    FINAL_PAGE_DATA.append(netChangeInFundBalancesList)
                                    lineIndex += 1
                            else:
                                thisLine = fullPagetext[lineIndex].split("  ")
                                if(len(thisLine) > 3):
                                    pageHeader = fullPagetext[lineIndex].split("   ")[0] 

                                    #Keep data, remove header
                                    fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")

                                    #get rid of ( ) and $
                                    cleanSpecialChars(lineIndex)

                                    #Split numerical data by, based on space detected between each
                                    row = fullPagetext[lineIndex].split()
                                    #Store data into a list
                                    storeInList(netChangeInFundBalancesList, date, county, header, pageHeader, row[0])

                                    # NEED TO APPEND THIS TO FINAL_DATA_LIST WHEN ITERATING OVER NEXT PAGE 
                                    FINAL_PAGE_DATA.append(netChangeInFundBalancesList)
                        lineIndex+=1
                print(FINAL_PAGE_DATA)
                fillDF(FINAL_PAGE_DATA, headerlist)
                print("---------------------DONE PAGE Statement of Revenues, Expenditures and Changes in Fund Balances  ------------------------------")

            elif len(statementOfNetPositionPages) >= 1 and i == statementOfNetPositionPages[1]:
                FINAL_PAGE_DATA.clear()
                text = page.extract_text()
                headerlist = ['DATE', 'COUNTY', 'PAGE_HEADER', 'SUB_DATA_HEADER','Business-type Activities - Enterprise Funds - TOTAL']
                #------------------Filters-----------------
                county_filter = re.compile(r'county|COUNTY|County$')
                proprietaryFundsSplit = re.compile(r'Proprietary Funds$')
                statementOfNetPositionFilter = re.compile(r'Statement of Net Position|statement of net position|STATEMENT OF NET POSITION')
                dateFilter = re.compile(r'[a-zA-Z]+\s\d\d[,]\s\d\d\d\d')
               
                
                #--------------------------------------------------DATA FILLER LINE-------------------------------------------------------------------
                dfLine = namedtuple('dfLine', 'date county header pageheader totalData')
                #--------------------------------------------------Split Lines based on /n and store into list----------------------------------------
                fullPagetext = text.split('\n')
                #--------------------------------------------------Flags to look for in lines---------------------------------------------------------
                #-------------------ASSETS-----------------------------
                cashAndPooledInvestmentsSplit = "Cash and pooled investments | Cash and cash equivalents"
                nonCurrentAssetsCapitalAssetsSplit = "Noncurrent assets - capital assets, net | Noncurrent assets - capital assets - net"
                totalAssetsSplit = "Total assets | Total Assets"
                #-------------------LIABILITIES-----------------------------
                totalCurrentLiabilitiesSplit = "Total current liabilities | Total Current Liabilities"
                netPensionLiabilitySplit = "Net pension liability | Net OPEB liability"
                totalNonCurrentLiabilitiesSplit = "Total noncurrent liabilities | Total Noncurrent Liabilities"
                totalLiabilitiesSplit = "Total liabilities | Total Liabilities"
                #------------------NET POSITION ----------------------------
                investmentInCapitalAssetsSplit = "Investment in capital assets | Investment In Capital Assets"
                unrestrictedSplit = "Unrestricted | Unrestricted (deficit)"
                totalNetPositionSplit = "Total net position | Total Net Position"
                #Temp Storage variables
                county = ''
                date = ''
                header = ''
                propFund = ''
                #each line will be manipulated using index, index starts at 0
                lineIndex = 0
                while lineIndex in range(len(fullPagetext)):
                    #Get rid of $ signs
                    fullPagetext[lineIndex] = fullPagetext[lineIndex].replace("$", " ")
                    #Look for these flags within the page (as we go line by line), if found return true, otherwise false
                    countyFound = county_filter.search(fullPagetext[lineIndex])
                    headerFound = statementOfNetPositionFilter.search(fullPagetext[lineIndex])
                    dateFound = dateFilter.search(fullPagetext[lineIndex])
                    proprietaryFundsFound = proprietaryFundsSplit.search(fullPagetext[lineIndex])
                    cashAndPooledInvestmentsFound = cashAndPooledInvestmentsSplit.find(fullPagetext[lineIndex].split("  ")[0])
                    nonCurrentAssetsCapitalAssetsFound =  nonCurrentAssetsCapitalAssetsSplit.find(fullPagetext[lineIndex].split("  ")[0])
                    totalAssetsFound = totalAssetsSplit.find(fullPagetext[lineIndex].split("  ")[0])
                    totalCurrentLiabilitiesFound = totalCurrentLiabilitiesSplit.find(fullPagetext[lineIndex].split("  ")[0])
                    netPensionLiabilityFound = netPensionLiabilitySplit.find(fullPagetext[lineIndex].split("  ")[0])
                    totalNonCurrentLiabilitiesFound = totalNonCurrentLiabilitiesSplit.find(fullPagetext[lineIndex].split("  ")[0])
                    totalLiabilitiesFound = totalLiabilitiesSplit.find(fullPagetext[lineIndex].split("  ")[0])
                    investmentInCapitalAssetsFound = investmentInCapitalAssetsSplit.find(fullPagetext[lineIndex].split("  ")[0])
                    unrestrictedFound = unrestrictedSplit.find(fullPagetext[lineIndex].split("  ")[0])
                    totalNetPositionFound = totalNetPositionSplit.find(fullPagetext[lineIndex].split("  ")[0])

                    #If found, then store them into a list
                    if countyFound:
                        county = fullPagetext[lineIndex]
                    elif dateFound:
                        date = fullPagetext[lineIndex].replace("Year Ended", "")
                    elif headerFound:
                        header = fullPagetext[lineIndex]
                    elif proprietaryFundsFound:
                        propFund = fullPagetext[lineIndex]
                        header = propFund + " - " + header
                    elif cashAndPooledInvestmentsFound != -1:
                        #Check if next line also matches with what we are looking for, if so data falls on second line not first
                        nextLine = fullPagetext[lineIndex+1].split("  ")
                        if cashAndPooledInvestmentsSplit.find(nextLine[0]) != -1:
                            if(len(nextLine) > 3):
                                pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0]
                                #Keep data, remove header
                                fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                #Replace or remove these items and only keep numbers
                                cleanSpecialChars(lineIndex+1)
                                #Split numerical data by , based on space detected between each
                                row = fullPagetext[lineIndex+1].split()
                                #Store data into a list
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 2]))
                                lineIndex += 1
                        else:
                            thisLine = fullPagetext[lineIndex].split("  ")
                            if(len(thisLine) > 3):
                                pageHeader = fullPagetext[lineIndex].split("   ")[0]
                                #get rid of ( ) and $
                                cleanSpecialChars(lineIndex)
                                #Keep data, remove header
                                fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")
                                #Split numerical data by, based on space detected between each
                                row = fullPagetext[lineIndex].split()
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 2]))
                    elif nonCurrentAssetsCapitalAssetsFound != -1:
                        #Check if next line also matches with what we are looking for, if so data falls on second line not first
                        nextLine = fullPagetext[lineIndex+1].split("  ")
                        if nonCurrentAssetsCapitalAssetsSplit.find(nextLine[0]) != -1:
                            if(len(nextLine) > 3):
                                pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0]
                                #Keep data, remove header
                                fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                #Replace or remove these items and only keep numbers
                                cleanSpecialChars(lineIndex+1)
                                #Split numerical data by , based on space detected between each
                                row = fullPagetext[lineIndex+1].split()
                                #Store data into a list
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 2]))
                                lineIndex += 1
                        else:
                            thisLine = fullPagetext[lineIndex].split("  ")
                            if(len(thisLine) > 3):
                                pageHeader = fullPagetext[lineIndex].split("   ")[0]
                                #get rid of ( ) and $
                                cleanSpecialChars(lineIndex)
                                #Keep data, remove header
                                fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")
                                #Split numerical data by, based on space detected between each
                                row = fullPagetext[lineIndex].split()
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 2]))
                    elif  totalAssetsFound != -1:
                        #Check if next line also matches with what we are looking for, if so data falls on second line not first
                        nextLine = fullPagetext[lineIndex+1].split("  ")
                        if totalAssetsSplit.find(nextLine[0]) != -1:
                            if(len(nextLine) > 3):
                                pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0]
                                #Keep data, remove header
                                fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                #Replace or remove these items and only keep numbers
                                cleanSpecialChars(lineIndex+1)
                                #Split numerical data by , based on space detected between each
                                row = fullPagetext[lineIndex+1].split()
                                #Store data into a list
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 2]))
                                lineIndex += 1
                        else:
                            thisLine = fullPagetext[lineIndex].split("  ")
                            if(len(thisLine) > 3):
                                pageHeader = fullPagetext[lineIndex].split("   ")[0]
                                #get rid of ( ) and $
                                cleanSpecialChars(lineIndex)
                                #Keep data, remove header
                                fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")
                                #Split numerical data by, based on space detected between each
                                row = fullPagetext[lineIndex].split()
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 2]))
                    elif totalCurrentLiabilitiesFound != -1:
                        #Check if next line also matches with what we are looking for, if so data falls on second line not first
                        nextLine = fullPagetext[lineIndex+1].split("  ")
                        if totalCurrentLiabilitiesSplit.find(nextLine[0]) != -1:
                            if(len(nextLine) > 3):
                                pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0]
                                #Keep data, remove header
                                fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                #Replace or remove these items and only keep numbers
                                cleanSpecialChars(lineIndex+1)
                                #Split numerical data by , based on space detected between each
                                row = fullPagetext[lineIndex+1].split()
                                #Store data into a list
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 2]))
                                lineIndex += 1
                        else:
                            thisLine = fullPagetext[lineIndex].split("  ")
                            if(len(thisLine) > 3):
                                pageHeader = fullPagetext[lineIndex].split("   ")[0]
                                #get rid of ( ) and $
                                cleanSpecialChars(lineIndex)
                                #Keep data, remove header
                                fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")
                                #Split numerical data by, based on space detected between each
                                row = fullPagetext[lineIndex].split()
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 2]))
                    
                    elif netPensionLiabilityFound != -1:
                         #Check if next line also matches with what we are looking for, if so data falls on second line not first
                        nextLine = fullPagetext[lineIndex+1].split("  ")
                        if netPensionLiabilitySplit.find(nextLine[0]) != -1:
                            if(len(nextLine) > 3):
                                pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0] 
                                #Keep data, remove header
                                fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                #Replace or remove these items and only keep numbers
                                cleanSpecialChars(lineIndex+1)
                                #Split numerical data by , based on space detected between each
                                row = fullPagetext[lineIndex+1].split()
                                #Store data into a list
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 2]))
                                lineIndex += 1
                        else:
                            thisLine = fullPagetext[lineIndex].split("  ")
                            if(len(thisLine) > 3):
                                pageHeader = fullPagetext[lineIndex].split("   ")[0]
                                #get rid of ( ) and $
                                cleanSpecialChars(lineIndex)
                                #Keep data, remove header
                                fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")
                                #Split numerical data by, based on space detected between each
                                row = fullPagetext[lineIndex].split()
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 2]))
                    elif totalNonCurrentLiabilitiesFound != -1:
                        #Check if next line also matches with what we are looking for, if so data falls on second line not first
                        nextLine = fullPagetext[lineIndex+1].split("  ")
                        if totalNonCurrentLiabilitiesSplit.find(nextLine[0]) != -1:
                            if(len(nextLine) > 3):
                                pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0]
                                #Keep data, remove header
                                fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                #Replace or remove these items and only keep numbers
                                cleanSpecialChars(lineIndex+1)
                                #Split numerical data by , based on space detected between each
                                row = fullPagetext[lineIndex+1].split()
                                #Store data into a list
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 2]))
                                lineIndex += 1
                        else:
                            thisLine = fullPagetext[lineIndex].split("  ")
                            if(len(thisLine) > 3):
                                pageHeader = fullPagetext[lineIndex].split("   ")[0]
                                #get rid of ( ) and $
                                cleanSpecialChars(lineIndex)
                                #Keep data, remove header
                                fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")
                                #Split numerical data by, based on space detected between each
                                row = fullPagetext[lineIndex].split()
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 2]))
                    elif totalLiabilitiesFound != -1:
                         #Check if next line also matches with what we are looking for, if so data falls on second line not first
                        nextLine = fullPagetext[lineIndex+1].split("  ")
                        if totalLiabilitiesSplit.find(nextLine[0]) != -1:
                            if(len(nextLine) > 3):
                                pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0]
                                #Keep data, remove header
                                fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                #Replace or remove these items and only keep numbers
                                cleanSpecialChars(lineIndex+1)
                                #Split numerical data by , based on space detected between each
                                row = fullPagetext[lineIndex+1].split()
                                #Store data into a list
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 2]))
                                lineIndex += 1
                        else:
                            thisLine = fullPagetext[lineIndex].split("  ")
                            if(len(thisLine) > 3):
                                pageHeader = fullPagetext[lineIndex].split("   ")[0]
                                #get rid of ( ) and $
                                cleanSpecialChars(lineIndex)
                                #Keep data, remove header
                                fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")
                                #Split numerical data by, based on space detected between each
                                row = fullPagetext[lineIndex].split()
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 2]))
                    elif investmentInCapitalAssetsFound != -1:
                        #Check if next line also matches with what we are looking for, if so data falls on second line not first
                        nextLine = fullPagetext[lineIndex+1].split("  ")
                        if investmentInCapitalAssetsSplit.find(nextLine[0]) != -1:
                            if(len(nextLine) > 3):
                                pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0]
                                #Keep data, remove header
                                fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                #Replace or remove these items and only keep numbers
                                cleanSpecialChars(lineIndex+1)
                                #Split numerical data by , based on space detected between each
                                row = fullPagetext[lineIndex+1].split()
                                #Store data into a list
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 2]))
                                lineIndex += 1
                        else:
                            thisLine = fullPagetext[lineIndex].split("  ")
                            if(len(thisLine) > 3):
                                pageHeader = fullPagetext[lineIndex].split("   ")[0]
                                #get rid of ( ) and $
                                cleanSpecialChars(lineIndex)
                                #Keep data, remove header
                                fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")
                                #Split numerical data by, based on space detected between each
                                row = fullPagetext[lineIndex].split()
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 2]))
                    elif unrestrictedFound != -1:
                        #Check if next line also matches with what we are looking for, if so data falls on second line not first
                        nextLine = fullPagetext[lineIndex+1].split("  ")
                        if unrestrictedSplit.find(nextLine[0]) != -1:
                            if(len(nextLine) > 3):
                                pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0]
                                #Keep data, remove header
                                fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                #Replace or remove these items and only keep numbers
                                cleanSpecialChars(lineIndex+1)
                                #Split numerical data by , based on space detected between each
                                row = fullPagetext[lineIndex+1].split()
                                #Store data into a list
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 2]))
                                lineIndex += 1
                        else:
                            thisLine = fullPagetext[lineIndex].split("  ")
                            if(len(thisLine) > 3):
                                pageHeader = fullPagetext[lineIndex].split("   ")[0]
                                #get rid of ( ) and $
                                cleanSpecialChars(lineIndex)
                                #Keep data, remove header
                                fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")
                                #Split numerical data by, based on space detected between each
                                row = fullPagetext[lineIndex].split()
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 2]))
                    elif totalNetPositionFound != -1:
                        #Check if next line also matches with what we are looking for, if so data falls on second line not first
                        nextLine = fullPagetext[lineIndex+1].split("  ")
                        if totalNetPositionSplit.find(nextLine[0]) != -1:
                            if(len(nextLine) > 3):
                                pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0]
                                #Keep data, remove header
                                fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                #Replace or remove these items and only keep numbers
                                cleanSpecialChars(lineIndex+1)
                                #Split numerical data by , based on space detected between each
                                row = fullPagetext[lineIndex+1].split()
                                #Store data into a list
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 2]))
                                lineIndex += 1
                        else:
                            thisLine = fullPagetext[lineIndex].split("  ")
                            if(len(thisLine) > 3):
                                pageHeader = fullPagetext[lineIndex].split("   ")[0]
                                #get rid of ( ) and $
                                cleanSpecialChars(lineIndex)
                                #Keep data, remove header
                                fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")
                                #Split numerical data by, based on space detected between each
                                row = fullPagetext[lineIndex].split()
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 2]))
                    lineIndex+=1
                fillDF(FINAL_PAGE_DATA, headerlist)
                print("---------------------DONE PAGE Statement of Net Position 2----------------------\n\n\n")
            elif len(statementOfRevExFundNetPositionPages) >= 1 and i == statementOfRevExFundNetPositionPages[0]:
                FINAL_PAGE_DATA.clear()
                text = page.extract_text()
                headerlist = ['DATE', 'COUNTY', 'PAGE_HEADER', 'SUB_DATA_HEADER','Business-type Activities - Enterprise Funds - TOTAL']
                #------------------Filters-----------------
                county_filter = re.compile(r'county|COUNTY|County$')
                proprietaryFundsSplit = re.compile(r'Proprietary Funds$')
                statementOfNetPositionFilter = re.compile(r'Statement of Revenues, Expenses and Changes in Fund Net Position|statement of revenues, expenses and changes in fund net position|STATEMENT OF REVENUES, EXPENSES AND CHANGES IN FUND NET POSITION')
                dateFilter = re.compile(r'[a-zA-Z]+\s\d\d[,]\s\d\d\d\d')
                
                #--------------------------------------------------DATA FILLER LINE-------------------------------------------------------------------
                dfLine = namedtuple('dfLine', 'date county header pageheader totalData')
                #--------------------------------------------------Split Lines based on /n and store into list----------------------------------------
                fullPagetext = text.split('\n')
                #--------------------------------------------------Flags to look for in lines---------------------------------------------------------
                #-------------------ASSETS-----------------------------
                totalOperatingRevenuesSplit = "Total operating revenues | Total Operating Revenues"
                totalOperatingExpensesSplit = "Total operating expenses | Total Operating Revenues"
                totalNonOperatingRevenuesSplit = "Total nonoperating revenues | Total nonoperating (expenses) revenues | Total nonoperating revenues (expenses) | Total nonoperating expense"
                changeInNetPositionSplit = "Change in net position | Change In Net Position"
                #Temp Storage variables
                county = ''
                date = ''
                header = ''
                propFund = ''
                #each line will be manipulated using index, index starts at 0
                lineIndex = 0
                while lineIndex in range(len(fullPagetext)):
                    #Get rid of $ signs
                    fullPagetext[lineIndex] = fullPagetext[lineIndex].replace("$", " ")
                    #Look for these flags within the page (as we go line by line), if found return true, otherwise false
                    countyFound = county_filter.search(fullPagetext[lineIndex])
                    headerFound = statementOfNetPositionFilter.search(fullPagetext[lineIndex])
                    dateFound = dateFilter.search(fullPagetext[lineIndex])
                    proprietaryFundsFound = proprietaryFundsSplit.search(fullPagetext[lineIndex])
                    totalOperatingRevenuesFound = totalOperatingRevenuesSplit.find(fullPagetext[lineIndex].split("  ")[0])
                    totalOperatingExpensesFound = totalOperatingExpensesSplit.find(fullPagetext[lineIndex].split("  ")[0])
                    totalNonOperatingRevenuesFound = totalNonOperatingRevenuesSplit.find(fullPagetext[lineIndex].split("  ")[0])
                    changeInNetPositionFound = changeInNetPositionSplit.find(fullPagetext[lineIndex].split("  ")[0])
                    #If found, then store them into a list
                    if countyFound:
                        county = fullPagetext[lineIndex]
                    elif dateFound:
                        date = fullPagetext[lineIndex].replace("Year Ended", "")
                    elif headerFound:
                        header = fullPagetext[lineIndex]
                    elif proprietaryFundsFound:
                        propFund = fullPagetext[lineIndex]
                        header = propFund + " - " + header
                    elif totalOperatingRevenuesFound != -1:
                        #Check if next line also matches with what we are looking for, if so data falls on second line not first
                        nextLine = fullPagetext[lineIndex+1].split("  ")
                        if totalOperatingRevenuesSplit.find(nextLine[0]) != -1:
                            if(len(nextLine) > 3):
                                pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0]
                                #Keep data, remove header
                                fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                #Replace or remove these items and only keep numbers
                                cleanSpecialChars(lineIndex+1)
                                #Split numerical data by , based on space detected between each
                                row = fullPagetext[lineIndex+1].split()
                                #Store data into a list
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 2]))
                                lineIndex += 1
                        else:
                            thisLine = fullPagetext[lineIndex].split("  ")
                            if(len(thisLine) > 3):
                                pageHeader = fullPagetext[lineIndex].split("   ")[0]
                                #get rid of ( ) and $
                                cleanSpecialChars(lineIndex)
                                #Keep data, remove header
                                fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")
                                #Split numerical data by, based on space detected between each
                                row = fullPagetext[lineIndex].split()
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 2]))
                    elif totalOperatingExpensesFound != -1:
                        #Check if next line also matches with what we are looking for, if so data falls on second line not first
                        nextLine = fullPagetext[lineIndex+1].split("  ")
                        if totalOperatingExpensesSplit.find(nextLine[0]) != -1:
                            if(len(nextLine) > 3):
                                pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0]
                                #Keep data, remove header
                                fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                #Replace or remove these items and only keep numbers
                                cleanSpecialChars(lineIndex+1)
                                #Split numerical data by , based on space detected between each
                                row = fullPagetext[lineIndex+1].split()
                                #Store data into a list
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 2]))
                                lineIndex += 1
                        else:
                            thisLine = fullPagetext[lineIndex].split("  ")
                            if(len(thisLine) > 3):
                                pageHeader = fullPagetext[lineIndex].split("   ")[0]
                                #get rid of ( ) and $
                                cleanSpecialChars(lineIndex)
                                #Keep data, remove header
                                fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")
                                #Split numerical data by, based on space detected between each
                                row = fullPagetext[lineIndex].split()
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 2]))
                    elif  totalNonOperatingRevenuesFound != -1:
                        #Check if next line also matches with what we are looking for, if so data falls on second line not first
                        nextLine = fullPagetext[lineIndex+1].split("  ")
                        if totalNonOperatingRevenuesSplit.find(nextLine[0]) != -1:
                            if(len(nextLine) > 3):
                                pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0]
                                #Keep data, remove header
                                fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                #Replace or remove these items and only keep numbers
                                cleanSpecialChars(lineIndex+1)
                                #Split numerical data by , based on space detected between each
                                row = fullPagetext[lineIndex+1].split()
                                #Store data into a list
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 2]))
                                lineIndex += 1
                        else:
                            thisLine = fullPagetext[lineIndex].split("  ")
                            if(len(thisLine) > 3):
                                pageHeader = fullPagetext[lineIndex].split("   ")[0]
                                #get rid of ( ) and $
                                cleanSpecialChars(lineIndex)
                                #Keep data, remove header
                                fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")
                                #Split numerical data by, based on space detected between each
                                row = fullPagetext[lineIndex].split()
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 2]))
                    elif changeInNetPositionFound != -1:
                        #Check if next line also matches with what we are looking for, if so data falls on second line not first
                        nextLine = fullPagetext[lineIndex+1].split("  ")
                        if changeInNetPositionSplit.find(nextLine[0]) != -1:
                            if(len(nextLine) > 3):
                                pageHeader = fullPagetext[lineIndex].split("   ")[0] + " " + nextLine[0]
                                #Keep data, remove header
                                fullPagetext[lineIndex+1] = fullPagetext[lineIndex+1].replace(nextLine[0], "")
                                #Replace or remove these items and only keep numbers
                                cleanSpecialChars(lineIndex+1)
                                #Split numerical data by , based on space detected between each
                                row = fullPagetext[lineIndex+1].split()
                                #Store data into a list
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 2]))
                                lineIndex += 1
                        else:
                            thisLine = fullPagetext[lineIndex].split("  ")
                            if(len(thisLine) > 3):
                                pageHeader = fullPagetext[lineIndex].split("   ")[0]
                                #get rid of ( ) and $
                                cleanSpecialChars(lineIndex)
                                #Keep data, remove header
                                fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(thisLine[0], "")
                                #Split numerical data by, based on space detected between each
                                row = fullPagetext[lineIndex].split()
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, pageHeader, row[len(row) - 2]))
                    lineIndex+=1
                fillDF(FINAL_PAGE_DATA, headerlist)
                print("---------------------DONE PAGE Statement of Revenues, Expenses and Changes in Fund Net Position----------------------\n\n\n")
            #Page 149 because index starts from 0
            elif len(requiredSuppInfoEmpRetirementSysPages) >= 1 and i == requiredSuppInfoEmpRetirementSysPages[0]:
                FINAL_PAGE_DATA.clear()
                text = page.extract_text()
                headerlist = ['DATE', 'COUNTY', 'PAGE_HEADER', 'SUB_DATA_HEADER']
                #--------------------------------------------------DATA FILLER LINE-------------------------------------------------------------------
                dfLine = namedtuple('dfLine', 'date county header subheader data')
                #--------------------------------------------------Split Lines based on /n and store into list----------------------------------------
                fullPagetext = text.split('\n')
                #Temp Storage variables
                county = ''
                date = ''
                header = ''
                propFund = ''

                #------------------------------------------------------FILTERS------------------------------------------------------------------------
                dateFilter = re.compile(r'[a-zA-Z]+\s\d\d[,]')
                headerFilter = re.compile(r'Employees\' Retirement System')
                county_filter = re.compile(r'county|COUNTY|County$')

                scheduleOfChangesInNetPensionLiabilityAndRelatedRatiosSplit = "Schedule of Changes in Net Pension Liability and Related Ratios"
                totalPensionLiabilityEndOfYearSplit = "Total pension liability, end of year"
                planFiduciaryNetPositionEndOfYearSplit = "Plan fiduciary net position, end of year"
                countysNetPensionLiabilitySplit = "County's net pension liability"
                planFiduciaryNetPositionAsaPercentageOfTotalPensionLiabilitySplit = "Plan fiduciary net position as a percentage of total pension liability"

                #Temp Storage variables
                county = ''
                date = ''
                header = ''

                #each line will be manipulated using index, index starts at 0
                lineIndex = 0
                while lineIndex in range(len(fullPagetext)):
                    #Get rid of $ signs
                    fullPagetext[lineIndex] = fullPagetext[lineIndex].replace("$", " ")

                    #Look for these flags within the page as each line is processed
                    headerFound = headerFilter.search(fullPagetext[lineIndex])
                    dateFound = dateFilter.search(fullPagetext[lineIndex])
                    countyFound = county_filter.search(fullPagetext[lineIndex])
                    scheduleOfChangesInNetPensionLiabilityAndRelatedRatiosFound = scheduleOfChangesInNetPensionLiabilityAndRelatedRatiosSplit.find(fullPagetext[lineIndex].split("  ")[0])
                    totalPensionLiabilityEndOfYearFound = totalPensionLiabilityEndOfYearSplit.find(fullPagetext[lineIndex].split("  ")[0])
                    planFiduciaryNetPositionEndOfYearFound = planFiduciaryNetPositionEndOfYearSplit.find(fullPagetext[lineIndex].split("  ")[0])
                    countysNetPensionLiabilityFound = countysNetPensionLiabilitySplit.find(fullPagetext[lineIndex].split("  ")[0])
                    planFiduciaryNetPositionAsaPercentageOfTotalPensionLiabilityFound = planFiduciaryNetPositionAsaPercentageOfTotalPensionLiabilitySplit.find(fullPagetext[lineIndex].split("  ")[0])

                    if dateFound:
                        date = fullPagetext[lineIndex].replace("Fiscal Year Ended", "")
                        years = fullPagetext[lineIndex + 1].split(" ")
                        date = date + " " + years[0]
                        lineIndex+=1 
                    elif headerFound:
                        header = fullPagetext[lineIndex]
                    elif countyFound:
                        county = fullPagetext[lineIndex]
                    elif scheduleOfChangesInNetPensionLiabilityAndRelatedRatiosFound != -1:
                        headerlist.append(fullPagetext[lineIndex].upper())
                    elif totalPensionLiabilityEndOfYearFound != -1:
                        #This works for looking at exact flags
                        if fullPagetext[lineIndex].split("  ")[0] == totalPensionLiabilityEndOfYearSplit:
                            #extract subline header
                            subHeader = fullPagetext[lineIndex].split("  ")[0]
                            #Keep data, remove header
                            fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(subHeader, "")
                            #Replace or remove these items and only keep numbers
                            cleanSpecialChars(lineIndex)
                            #Split numerical data by , based on space detected between each
                            row = fullPagetext[lineIndex].split()
                            #Store data into a list
                            FINAL_PAGE_DATA.append(dfLine(date, county, header, subHeader, row[0]))
                            print(FINAL_PAGE_DATA)
                        else: #concat this line to nextLine and see if the subheader extends to the nextLine
                            subHeader = fullPagetext[lineIndex].split("  ")[0] + " " + fullPagetext[lineIndex + 1].split("  ")[0]
                            if subHeader == totalPensionLiabilityEndOfYearSplit:
                                lineIndex+=1
                                #Keep data, remove header
                                fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(subHeader, "")
                                #Replace or remove these items and only keep numbers
                                cleanSpecialChars(lineIndex)
                                #Split numerical data by , based on space detected between each
                                row = fullPagetext[lineIndex].split()
                                #Store data into a list
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, subHeader, row[0]))
                                print(FINAL_PAGE_DATA)
                    elif planFiduciaryNetPositionEndOfYearFound != -1:
                        #try to match it with the exact flag, if it doesnt then try appending the bottom line and then try matching the flag, if it still doesnt then its not it. 
                        if fullPagetext[lineIndex].split("  ")[0] == planFiduciaryNetPositionEndOfYearSplit:
                            #extract subline header
                            subHeader = fullPagetext[lineIndex].split("  ")[0]
                            #Keep data, remove header
                            fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(subHeader, "")
                            #Replace or remove these items and only keep numbers
                            cleanSpecialChars(lineIndex)
                            #Split numerical data by , based on space detected between each
                            row = fullPagetext[lineIndex].split()
                            #Store data into a list
                            FINAL_PAGE_DATA.append(dfLine(date, county, header, subHeader, row[0]))
                            print(FINAL_PAGE_DATA)
                        else:
                            subHeader = fullPagetext[lineIndex].split("  ")[0] + " " + fullPagetext[lineIndex + 1].split("  ")[0]
                            if subHeader == planFiduciaryNetPositionEndOfYearSplit:
                                lineIndex+=1
                                #Keep data, remove header
                                fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(subHeader, "")
                                #Replace or remove these items and only keep numbers
                                cleanSpecialChars(lineIndex)
                                #Split numerical data by , based on space detected between each
                                row = fullPagetext[lineIndex].split()
                                #Store data into a list
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, subHeader, row[0]))
                                print(FINAL_PAGE_DATA)
                    elif countysNetPensionLiabilityFound != -1:
                        #try to match it with the exact flag, if it doesnt then try appending the bottom line and then try matching the flag, if it still doesnt then its not it. 
                        if fullPagetext[lineIndex].split("  ")[0] == countysNetPensionLiabilitySplit:
                            #extract subline header
                            subHeader = fullPagetext[lineIndex].split("  ")[0]
                            #Keep data, remove header
                            fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(subHeader, "")
                            #Replace or remove these items and only keep numbers
                            cleanSpecialChars(lineIndex)
                            #Split numerical data by , based on space detected between each
                            row = fullPagetext[lineIndex].split()
                            #Store data into a list
                            FINAL_PAGE_DATA.append(dfLine(date, county, header, subHeader, row[0]))
                            print(FINAL_PAGE_DATA)
                        else:
                            subHeader = fullPagetext[lineIndex].split("  ")[0] + " " + fullPagetext[lineIndex + 1].split("  ")[0]
                            if subHeader == countysNetPensionLiabilitySplit:
                                lineIndex+=1
                                #Keep data, remove header
                                fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(subHeader, "")
                                #Replace or remove these items and only keep numbers
                                cleanSpecialChars(lineIndex)
                                #Split numerical data by , based on space detected between each
                                row = fullPagetext[lineIndex].split()
                                #Store data into a list
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, subHeader, row[0]))
                                print(FINAL_PAGE_DATA)
                    elif planFiduciaryNetPositionAsaPercentageOfTotalPensionLiabilityFound != -1:
                        #try to match it with the exact flag, if it doesnt then try appending the bottom line and then try matching the flag, if it still doesnt then its not it. 
                        if fullPagetext[lineIndex].split("  ")[0] == planFiduciaryNetPositionAsaPercentageOfTotalPensionLiabilitySplit:
                            #extract subline header
                            subHeader = fullPagetext[lineIndex].split("  ")[0]
                            #Keep data, remove header
                            fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(subHeader, "")
                            #Replace or remove these items and only keep numbers
                            cleanSpecialChars(lineIndex)
                            #Split numerical data by , based on space detected between each
                            row = fullPagetext[lineIndex].split()
                            #Store data into a list
                            FINAL_PAGE_DATA.append(dfLine(date, county, header, subHeader, row[0]))
                            print(FINAL_PAGE_DATA)
                        else:
                            tempSplitWordsVar = " ".join(re.split("[^a-zA-Z]+", fullPagetext[lineIndex + 1]))
                            subHeader = fullPagetext[lineIndex].split("  ")[0] + " " + tempSplitWordsVar
                            if subHeader.strip() == planFiduciaryNetPositionAsaPercentageOfTotalPensionLiabilitySplit.strip():
                                lineIndex+=1
                                #Keep data, remove header
                                fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(tempSplitWordsVar, "")
                                #Replace or remove these items and only keep numbers
                                cleanSpecialChars(lineIndex)
                                #Split numerical data by , based on space detected between each
                                row = fullPagetext[lineIndex].split()
                                #Store data into a list
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, subHeader, row[0]))
                                print(FINAL_PAGE_DATA)
                    lineIndex+=1 
                fillDF(FINAL_PAGE_DATA, headerlist)
                print("---------------------DONE PAGE Employees' Retirement System----------------------\n\n\n")
            #Page 150 because index starts from 0
            elif len(requiredSuppInfoEmpRetirementSysPages) >= 1 and i == requiredSuppInfoEmpRetirementSysPages[1]:
                FINAL_PAGE_DATA.clear()
                text = page.extract_text()
                headerlist = ['DATE', 'COUNTY', 'PAGE_HEADER', 'SUB_DATA_HEADER']
                #--------------------------------------------------DATA FILLER LINE-------------------------------------------------------------------
                #subheader will be columns for this page
                dfLine = namedtuple('dfLine', 'date county header subheader data')
                #--------------------------------------------------Split Lines based on /n and store into list----------------------------------------
                fullPagetext = text.split('\n')
                #Temp Storage variables
                county = ''
                date = ''
                header = ''

                #------------------------------------------------------FILTERS------------------------------------------------------------------------
                monthFilter = re.compile(r'December')
                dayFilter = re.compile(r'\d\d[,]')
                yearFilter = re.compile(r'\d\d\d\d\s')
                headerFilter = re.compile(r'Employees\' Retirement System')
                county_filter = re.compile(r'county|COUNTY|County$')

                scheduleOfContributionsSplit = "Schedule of Contributions"
                #Temp Storage variables
                county = ''
                date = ''
                header = ''

                #each line will be manipulated using index, index starts at 0
                lineIndex = 0
                while lineIndex in range(len(fullPagetext)):
                    #Get rid of $ signs
                    fullPagetext[lineIndex] = fullPagetext[lineIndex].replace("$", " ")

                    #Look for these flags within the page as each line is processed
                    headerFound = headerFilter.search(fullPagetext[lineIndex])
                    monthFound = monthFilter.search(fullPagetext[lineIndex])
                    yearFound = yearFilter.search(fullPagetext[lineIndex])
                    countyFound = county_filter.search(fullPagetext[lineIndex])
                    scheduleOfContributionsFound = scheduleOfContributionsSplit.find(fullPagetext[lineIndex].split("  ")[0])
                   
                    if monthFound:
                        if dayFilter.search(fullPagetext[lineIndex+1]):
                            date = fullPagetext[lineIndex].replace("Fiscal Year Ended", "")
                            date = date.split()[0]
                            day = fullPagetext[lineIndex+1].split(" ")[0]
                            date = date + " " + day
                        lineIndex+=1 
                    elif headerFound:
                        header = fullPagetext[lineIndex]
                    elif countyFound:
                        county = fullPagetext[lineIndex]
                    elif scheduleOfContributionsFound != -1:
                        headerlist.append(fullPagetext[lineIndex].upper())
                    elif yearFound:
                        #LEFT OFF HERE, GET THE CLOSEST YEAR TO CURRENT YEAR!!! FUNCTION
                        pdfYear = fullPagetext[lineIndex].split("  ")[0]
                        if pdfYear.isnumeric():
                            pdfYear = int(pdfYear)
                            currentYear = getCurrentYear()
                            if ((currentYear - 2) == pdfYear):
                                if yearFilter.search(fullPagetext[lineIndex + 1]):
                                    pdfYear = fullPagetext[lineIndex+1].split("  ")[0]
                                    if pdfYear.is_numeric():
                                        pdfYear = int(pdfYear)
                                        if((currentYear - 1) == pdfYear):
                                            #extract subline header
                                            subHeader1 = "Actuarially Determined Contribution"
                                            subHeader2 = "Contributions in Relation to the Actuarially Determined Contribution"
                                            #Replace or remove these items and only keep numbers
                                            cleanSpecialChars(lineIndex+1)
                                            #Split numerical data by , based on space detected between each
                                            row = fullPagetext[lineIndex + 1].split()
                                            date = date + " " + row[0]
                                            FINAL_PAGE_DATA.append(dfLine(date, county, header, subHeader1, row[1]))
                                            FINAL_PAGE_DATA.append(dfLine(date, county, header, subHeader2, row[2]))
                                            print(FINAL_PAGE_DATA)
                                else:
                                    #extract subline header
                                    subHeader1 = "Actuarially Determined Contribution"
                                    subHeader2 = "Contributions in Relation to the Actuarially Determined Contribution"
                                    #Replace or remove these items and only keep numbers
                                    cleanSpecialChars(lineIndex)
                                    #Split numerical data by , based on space detected between each
                                    row = fullPagetext[lineIndex].split()
                                    date = date + " " + row[0]
                                    FINAL_PAGE_DATA.append(dfLine(date, county, header, subHeader1, row[1]))
                                    FINAL_PAGE_DATA.append(dfLine(date, county, header, subHeader2, row[2]))
                                    print(FINAL_PAGE_DATA)
                    lineIndex+=1 
                fillDF(FINAL_PAGE_DATA, headerlist)
                print("---------------------DONE PAGE Employees' Retirement System----------------------\n\n\n")
            #Page 152 because index starts from 0
            elif len(requiredSuppInfoVolEmpBenePages) >= 1 and i == requiredSuppInfoVolEmpBenePages[0]:
                FINAL_PAGE_DATA.clear()
                text = page.extract_text()
                headerlist = ['DATE', 'COUNTY', 'PAGE_HEADER', 'SUB_DATA_HEADER']
                #--------------------------------------------------DATA FILLER LINE-------------------------------------------------------------------
                dfLine = namedtuple('dfLine', 'date county header subheader data')
                #--------------------------------------------------Split Lines based on /n and store into list----------------------------------------
                fullPagetext = text.split('\n')
                #Temp Storage variables
                county = ''
                date = ''
                header = ''

                #------------------------------------------------------FILTERS------------------------------------------------------------------------
                dateFilter = re.compile(r'[a-zA-Z]+\s\d\d[,]')
                headerFilter = re.compile(r'Voluntary Employees\' Beneficiary Association')
                county_filter = re.compile(r'county|COUNTY|County$')

                scheduleOfChangesInNetOPEBLiabilityAndRelatedRatiosSplit = "Schedule of Changes in Net OPEB Liability and Related Ratios"
                totalOPEBLiabilityEndOfYearSplit = "Total OPEB liability, end of year"
                planFiduciaryNetPositionEndOfYearSplit = "Plan fiduciary net position, end of year"
                countysNetOPEBLiabilitySplit = "County's net OPEB liability"
                planFiduciaryNetPositionAsaPercentageOfTotalOPEBLiabilitySplit = "Plan fiduciary net position as a percentage of total OPEB liability"

                #Temp Storage variables
                county = ''
                date = ''
                header = ''

                #each line will be manipulated using index, index starts at 0
                lineIndex = 0
                while lineIndex in range(len(fullPagetext)):
                    #Get rid of $ signs
                    fullPagetext[lineIndex] = fullPagetext[lineIndex].replace("$", " ")

                    #Look for these flags within the page as each line is processed
                    headerFound = headerFilter.search(fullPagetext[lineIndex])
                    dateFound = dateFilter.search(fullPagetext[lineIndex])
                    countyFound = county_filter.search(fullPagetext[lineIndex])
                    scheduleOfChangesInNetOPEBLiabilityAndRelatedRatiosFound = scheduleOfChangesInNetOPEBLiabilityAndRelatedRatiosSplit.find(fullPagetext[lineIndex].split("  ")[0])
                    totalOPEBLiabilityEndOfYearFound = totalOPEBLiabilityEndOfYearSplit.find(fullPagetext[lineIndex].split("  ")[0])
                    planFiduciaryNetPositionEndOfYearFound = planFiduciaryNetPositionEndOfYearSplit.find(fullPagetext[lineIndex].split("  ")[0])
                    countysNetOPEBLiabilityFound = countysNetOPEBLiabilitySplit.find(fullPagetext[lineIndex].split("  ")[0])
                    planFiduciaryNetPositionAsaPercentageOfTotalOPEBLiabilityFound = planFiduciaryNetPositionAsaPercentageOfTotalOPEBLiabilitySplit.find(fullPagetext[lineIndex].split("  ")[0])

                    if dateFound:
                        date = fullPagetext[lineIndex].replace("Fiscal Year Ended", "")
                        years = fullPagetext[lineIndex + 1].split(" ")
                        date = date + " " + years[0]
                        lineIndex+=1 
                    elif headerFound:
                        header = fullPagetext[lineIndex]
                    elif countyFound:
                        county = fullPagetext[lineIndex]
                    elif scheduleOfChangesInNetOPEBLiabilityAndRelatedRatiosFound != -1:
                        headerlist.append(fullPagetext[lineIndex].upper())
                    elif totalOPEBLiabilityEndOfYearFound != -1:
                        #This works for looking at exact flags
                        if fullPagetext[lineIndex].split("  ")[0] == totalOPEBLiabilityEndOfYearSplit:
                            #extract subline header
                            subHeader = fullPagetext[lineIndex].split("  ")[0]
                            #Keep data, remove header
                            fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(subHeader, "")
                            #Replace or remove these items and only keep numbers
                            cleanSpecialChars(lineIndex)
                            #Split numerical data by , based on space detected between each
                            row = fullPagetext[lineIndex].split()
                            #Store data into a list
                            FINAL_PAGE_DATA.append(dfLine(date, county, header, subHeader, row[0]))
                            print(FINAL_PAGE_DATA)
                        else: #concat this line to nextLine and see if the subheader extends to the nextLine
                            subHeader = fullPagetext[lineIndex].split("  ")[0] + " " + fullPagetext[lineIndex + 1].split("  ")[0]
                            if subHeader == totalOPEBLiabilityEndOfYearSplit:
                                lineIndex+=1
                                #Keep data, remove header
                                fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(subHeader, "")
                                #Replace or remove these items and only keep numbers
                                cleanSpecialChars(lineIndex)
                                #Split numerical data by , based on space detected between each
                                row = fullPagetext[lineIndex].split()
                                #Store data into a list
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, subHeader, row[0]))
                                print(FINAL_PAGE_DATA)
                    elif planFiduciaryNetPositionEndOfYearFound != -1:
                        #try to match it with the exact flag, if it doesnt then try appending the bottom line and then try matching the flag, if it still doesnt then its not it. 
                        if fullPagetext[lineIndex].split("  ")[0] == planFiduciaryNetPositionEndOfYearSplit:
                            #extract subline header
                            subHeader = fullPagetext[lineIndex].split("  ")[0]
                            #Keep data, remove header
                            fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(subHeader, "")
                            #Replace or remove these items and only keep numbers
                            cleanSpecialChars(lineIndex)
                            #Split numerical data by , based on space detected between each
                            row = fullPagetext[lineIndex].split()
                            #Store data into a list
                            FINAL_PAGE_DATA.append(dfLine(date, county, header, subHeader, row[0]))
                            print(FINAL_PAGE_DATA)
                        else:
                            subHeader = fullPagetext[lineIndex].split("  ")[0] + " " + fullPagetext[lineIndex + 1].split("  ")[0]
                            if subHeader == planFiduciaryNetPositionEndOfYearSplit:
                                lineIndex+=1
                                #Keep data, remove header
                                fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(subHeader, "")
                                #Replace or remove these items and only keep numbers
                                cleanSpecialChars(lineIndex)
                                #Split numerical data by , based on space detected between each
                                row = fullPagetext[lineIndex].split()
                                #Store data into a list
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, subHeader, row[0]))
                                print(FINAL_PAGE_DATA)
                    elif countysNetOPEBLiabilityFound != -1:
                        #try to match it with the exact flag, if it doesnt then try appending the bottom line and then try matching the flag, if it still doesnt then its not it. 
                        if fullPagetext[lineIndex].split("  ")[0] == countysNetOPEBLiabilitySplit:
                            #extract subline header
                            subHeader = fullPagetext[lineIndex].split("  ")[0]
                            #Keep data, remove header
                            fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(subHeader, "")
                            #Replace or remove these items and only keep numbers
                            cleanSpecialChars(lineIndex)
                            #Split numerical data by , based on space detected between each
                            row = fullPagetext[lineIndex].split()
                            #Store data into a list
                            FINAL_PAGE_DATA.append(dfLine(date, county, header, subHeader, row[0]))
                            print(FINAL_PAGE_DATA)
                        else:
                            subHeader = fullPagetext[lineIndex].split("  ")[0] + " " + fullPagetext[lineIndex + 1].split("  ")[0]
                            if subHeader == countysNetOPEBLiabilitySplit:
                                lineIndex+=1
                                #Keep data, remove header
                                fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(subHeader, "")
                                #Replace or remove these items and only keep numbers
                                cleanSpecialChars(lineIndex)
                                #Split numerical data by , based on space detected between each
                                row = fullPagetext[lineIndex].split()
                                #Store data into a list
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, subHeader, row[0]))
                                print(FINAL_PAGE_DATA)
                    elif planFiduciaryNetPositionAsaPercentageOfTotalOPEBLiabilityFound != -1:
                        #try to match it with the exact flag, if it doesnt then try appending the bottom line and then try matching the flag, if it still doesnt then its not it. 
                        if fullPagetext[lineIndex].split("  ")[0] == planFiduciaryNetPositionAsaPercentageOfTotalOPEBLiabilitySplit:
                            #extract subline header
                            subHeader = fullPagetext[lineIndex].split("  ")[0]
                            #Keep data, remove header
                            fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(subHeader, "")
                            #Replace or remove these items and only keep numbers
                            cleanSpecialChars(lineIndex)
                            #Split numerical data by , based on space detected between each
                            row = fullPagetext[lineIndex].split()
                            #Store data into a list
                            FINAL_PAGE_DATA.append(dfLine(date, county, header, subHeader, row[0]))
                            print(FINAL_PAGE_DATA)
                        else:
                            tempSplitWordsVar = " ".join(re.split("[^a-zA-Z]+", fullPagetext[lineIndex + 1]))
                            subHeader = fullPagetext[lineIndex].split("  ")[0] + " " + tempSplitWordsVar
                            if subHeader.strip() == planFiduciaryNetPositionAsaPercentageOfTotalOPEBLiabilitySplit.strip():
                                lineIndex+=1
                                #Keep data, remove header
                                fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(tempSplitWordsVar, "")
                                #Replace or remove these items and only keep numbers
                                cleanSpecialChars(lineIndex)
                                #Split numerical data by , based on space detected between each
                                row = fullPagetext[lineIndex].split()
                                #Store data into a list
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, subHeader, row[0]))
                                print(FINAL_PAGE_DATA)
                    lineIndex+=1 
                fillDF(FINAL_PAGE_DATA, headerlist)
                print("---------------------DONE PAGE Voluntary Employees' Beneficiary Association----------------------\n\n\n")
            #Page 153 because index starts from 0
            elif len(requiredSuppInfoVolEmpBenePages) >= 1 and i == requiredSuppInfoVolEmpBenePages[1]:
                FINAL_PAGE_DATA.clear()
                text = page.extract_text()
                headerlist = ['DATE', 'COUNTY', 'PAGE_HEADER', 'SUB_DATA_HEADER']
                #--------------------------------------------------DATA FILLER LINE-------------------------------------------------------------------
                #subheader will be columns for this page
                dfLine = namedtuple('dfLine', 'date county header subheader data')
                #--------------------------------------------------Split Lines based on /n and store into list----------------------------------------
                fullPagetext = text.split('\n')
                #Temp Storage variables
                county = ''
                date = ''
                header = ''

                #------------------------------------------------------FILTERS------------------------------------------------------------------------
                monthFilter = re.compile(r'December')
                dayFilter = re.compile(r'\d\d[,]')
                yearFilter = re.compile(r'\d\d\d\d\s')
                headerFilter = re.compile(r'Voluntary Employees\' Beneficiary Association')
                county_filter = re.compile(r'county|COUNTY|County$')

                scheduleOfContributionsSplit = "Schedule of Contributions"
                #Temp Storage variables
                county = ''
                date = ''
                header = ''

                #each line will be manipulated using index, index starts at 0
                lineIndex = 0
                while lineIndex in range(len(fullPagetext)):
                    #Get rid of $ signs
                    fullPagetext[lineIndex] = fullPagetext[lineIndex].replace("$", " ")

                    #Look for these flags within the page as each line is processed
                    headerFound = headerFilter.search(fullPagetext[lineIndex])
                    monthFound = monthFilter.search(fullPagetext[lineIndex])
                    yearFound = yearFilter.search(fullPagetext[lineIndex])
                    countyFound = county_filter.search(fullPagetext[lineIndex])
                    scheduleOfContributionsFound = scheduleOfContributionsSplit.find(fullPagetext[lineIndex].split("  ")[0])
                   
                    if monthFound:
                        if dayFilter.search(fullPagetext[lineIndex+1]):
                            date = fullPagetext[lineIndex].replace("Fiscal Year Ended", "")
                            date = date.split()[0]
                            day = fullPagetext[lineIndex+1].split(" ")[0]
                            date = date + " " + day
                        lineIndex+=1 
                    elif headerFound:
                        header = fullPagetext[lineIndex]
                    elif countyFound:
                        county = fullPagetext[lineIndex]
                    elif scheduleOfContributionsFound != -1:
                        headerlist.append(fullPagetext[lineIndex].upper())
                    elif yearFound:
                        pdfYear = fullPagetext[lineIndex].split("  ")[0]
                        if pdfYear.isnumeric():
                            pdfYear = int(pdfYear)
                            currentYear = getCurrentYear()
                            if ((currentYear - 2) == pdfYear):
                                if yearFilter.search(fullPagetext[lineIndex + 1]):
                                    pdfYear = fullPagetext[lineIndex+1].split("  ")[0]
                                    if pdfYear.is_numeric():
                                        pdfYear = int(pdfYear)
                                        if((currentYear - 1) == pdfYear):
                                            #extract subline header
                                            subHeader1 = "Actuarially Determined Contribution"
                                            subHeader2 = "Contributions in Relation to the Actuarially Determined Contribution"
                                            #Replace or remove these items and only keep numbers
                                            cleanSpecialChars(lineIndex+1)
                                            #Split numerical data by , based on space detected between each
                                            row = fullPagetext[lineIndex + 1].split()
                                            date = date + " " + row[0]
                                            FINAL_PAGE_DATA.append(dfLine(date, county, header, subHeader1, row[1]))
                                            FINAL_PAGE_DATA.append(dfLine(date, county, header, subHeader2, row[2]))
                                            print(FINAL_PAGE_DATA)
                                else:
                                    #extract subline header
                                    subHeader1 = "Actuarially Determined Contribution"
                                    subHeader2 = "Contributions in Relation to the Actuarially Determined Contribution"
                                    #Replace or remove these items and only keep numbers
                                    cleanSpecialChars(lineIndex)
                                    #Split numerical data by , based on space detected between each
                                    row = fullPagetext[lineIndex].split()
                                    date = date + " " + row[0]
                                    FINAL_PAGE_DATA.append(dfLine(date, county, header, subHeader1, row[1]))
                                    FINAL_PAGE_DATA.append(dfLine(date, county, header, subHeader2, row[2]))
                                    print(FINAL_PAGE_DATA)
                    lineIndex+=1 
                fillDF(FINAL_PAGE_DATA, headerlist)
                print("---------------------DONE PAGE Voluntary Employees' Beneficiary Association----------------------\n\n\n")
            #Page 155 because index starts from 0
            elif len(requiredSuppInfoMunicipalEmpRetSysPages) >= 1 and i == requiredSuppInfoMunicipalEmpRetSysPages[0]:
                FINAL_PAGE_DATA.clear()
                text = page.extract_text()

                headerlist = ['DATE', 'COUNTY', 'PAGE_HEADER', 'SUB_DATA_HEADER']
                #--------------------------------------------------DATA FILLER LINE-------------------------------------------------------------------
                dfLine = namedtuple('dfLine', 'date county header subheader data')
                #--------------------------------------------------Split Lines based on /n and store into list----------------------------------------
                fullPagetext = text.split('\n')
                #Temp Storage variables
                county = ''
                date = ''
                header = ''

                #------------------------------------------------------FILTERS------------------------------------------------------------------------
                dateFilter = re.compile(r'[a-zA-Z]+\s\d\d[,]')
                headerFilter = re.compile(r'Municipal Employees\' Retirement System of Michigan')
                county_filter = re.compile(r'county|COUNTY|County$')

                scheduleOfChangesInNetPensionLiabilityAndRelatedRatiosSplit = "Schedule of Changes in Net Pension Liability and Related Ratios"
                totalPensionLiabilityEndOfYearSplit = "Total pension liability, end of year"
                planFiduciaryNetPositionEndOfYearSplit = "Plan fiduciary net position, end of year"
                planFiduciaryNetPositionAsaPercentageOfTotalPensionLiabilitySplit = "Plan fiduciary net position as a percentage of total pension liability"

                #Temp Storage variables
                county = ''
                date = ''
                header = ''

                #each line will be manipulated using index, index starts at 0
                lineIndex = 0
                while lineIndex in range(len(fullPagetext)):
                    #Get rid of $ signs
                    fullPagetext[lineIndex] = fullPagetext[lineIndex].replace("$", " ")

                    #Look for these flags within the page as each line is processed
                    headerFound = headerFilter.search(fullPagetext[lineIndex])
                    dateFound = dateFilter.search(fullPagetext[lineIndex])
                    countyFound = county_filter.search(fullPagetext[lineIndex])
                    scheduleOfChangesInNetPensionLiabilityAndRelatedRatiosFound = scheduleOfChangesInNetPensionLiabilityAndRelatedRatiosSplit.find(fullPagetext[lineIndex].split("  ")[0])
                    totalPensionLiabilityEndOfYearFound = totalPensionLiabilityEndOfYearSplit.find(fullPagetext[lineIndex].split("  ")[0])
                    planFiduciaryNetPositionEndOfYearFound = planFiduciaryNetPositionEndOfYearSplit.find(fullPagetext[lineIndex].split("  ")[0])
                    planFiduciaryNetPositionAsaPercentageOfTotalPensionLiabilityFound = planFiduciaryNetPositionAsaPercentageOfTotalPensionLiabilitySplit.find(fullPagetext[lineIndex].split("  ")[0])

                    if dateFound:
                        date = fullPagetext[lineIndex].replace("Fiscal Year Ended", "")
                        years = fullPagetext[lineIndex + 1].split(" ")
                        date = date + " " + years[0]
                        lineIndex+=1 
                    elif headerFound:
                        header = fullPagetext[lineIndex]
                    elif countyFound:
                        county = fullPagetext[lineIndex]
                    elif scheduleOfChangesInNetPensionLiabilityAndRelatedRatiosFound != -1:
                        headerlist.append(fullPagetext[lineIndex].upper())
                    elif totalPensionLiabilityEndOfYearFound != -1:
                        #This works for looking at exact flags
                        if fullPagetext[lineIndex].split("  ")[0] == totalPensionLiabilityEndOfYearSplit:
                            #extract subline header
                            subHeader = fullPagetext[lineIndex].split("  ")[0]
                            #Keep data, remove header
                            fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(subHeader, "")
                            #Replace or remove these items and only keep numbers
                            cleanSpecialChars(lineIndex)
                            #Split numerical data by , based on space detected between each
                            row = fullPagetext[lineIndex].split()
                            #Store data into a list
                            FINAL_PAGE_DATA.append(dfLine(date, county, header, subHeader, row[0]))
                            print(FINAL_PAGE_DATA)
                        else: #concat this line to nextLine and see if the subheader extends to the nextLine
                            subHeader = fullPagetext[lineIndex].split("  ")[0] + " " + fullPagetext[lineIndex + 1].split("  ")[0]
                            if subHeader == totalPensionLiabilityEndOfYearSplit:
                                lineIndex+=1
                                #Keep data, remove header
                                fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(subHeader, "")
                                #Replace or remove these items and only keep numbers
                                cleanSpecialChars(lineIndex)
                                #Split numerical data by , based on space detected between each
                                row = fullPagetext[lineIndex].split()
                                #Store data into a list
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, subHeader, row[0]))
                                print(FINAL_PAGE_DATA)
                    elif planFiduciaryNetPositionEndOfYearFound != -1:
                        #try to match it with the exact flag, if it doesnt then try appending the bottom line and then try matching the flag, if it still doesnt then its not it. 
                        if fullPagetext[lineIndex].split("  ")[0] == planFiduciaryNetPositionEndOfYearSplit:
                            #extract subline header
                            subHeader = fullPagetext[lineIndex].split("  ")[0]
                            #Keep data, remove header
                            fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(subHeader, "")
                            #Replace or remove these items and only keep numbers
                            cleanSpecialChars(lineIndex)
                            #Split numerical data by , based on space detected between each
                            row = fullPagetext[lineIndex].split()
                            #Store data into a list
                            FINAL_PAGE_DATA.append(dfLine(date, county, header, subHeader, row[0]))
                            print(FINAL_PAGE_DATA)
                        else:
                            subHeader = fullPagetext[lineIndex].split("  ")[0] + " " + fullPagetext[lineIndex + 1].split("  ")[0]
                            if subHeader == planFiduciaryNetPositionEndOfYearSplit:
                                lineIndex+=1
                                #Keep data, remove header
                                fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(subHeader, "")
                                #Replace or remove these items and only keep numbers
                                cleanSpecialChars(lineIndex)
                                #Split numerical data by , based on space detected between each
                                row = fullPagetext[lineIndex].split()
                                #Store data into a list
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, subHeader, row[0]))
                                print(FINAL_PAGE_DATA)
                    elif planFiduciaryNetPositionAsaPercentageOfTotalPensionLiabilityFound != -1:
                        #try to match it with the exact flag, if it doesnt then try appending the bottom line and then try matching the flag, if it still doesnt then its not it. 
                        if fullPagetext[lineIndex].split("  ")[0] == planFiduciaryNetPositionAsaPercentageOfTotalPensionLiabilitySplit:
                            #extract subline header
                            subHeader = fullPagetext[lineIndex].split("  ")[0]
                            #Keep data, remove header
                            fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(subHeader, "")
                            #Replace or remove these items and only keep numbers
                            cleanSpecialChars(lineIndex)
                            #Split numerical data by , based on space detected between each
                            row = fullPagetext[lineIndex].split()
                            #Store data into a list
                            FINAL_PAGE_DATA.append(dfLine(date, county, header, subHeader, row[0]))
                            print(FINAL_PAGE_DATA)
                        else:
                            tempSplitWordsVar = " ".join(re.split("[^a-zA-Z]+", fullPagetext[lineIndex + 1]))
                            subHeader = fullPagetext[lineIndex].split("  ")[0] + " " + tempSplitWordsVar
                            if subHeader.strip() == planFiduciaryNetPositionAsaPercentageOfTotalPensionLiabilitySplit.strip():
                                lineIndex+=1
                                #Keep data, remove header
                                fullPagetext[lineIndex] = fullPagetext[lineIndex].replace(tempSplitWordsVar, "")
                                #Replace or remove these items and only keep numbers
                                cleanSpecialChars(lineIndex)
                                #Split numerical data by , based on space detected between each
                                row = fullPagetext[lineIndex].split()
                                #Store data into a list
                                FINAL_PAGE_DATA.append(dfLine(date, county, header, subHeader, row[0]))
                                print(FINAL_PAGE_DATA)
                    lineIndex+=1 
                fillDF(FINAL_PAGE_DATA, headerlist)
                print("---------------------DONE PAGE Municipal Employees' Retirement System of Michigan----------------------\n\n\n")
            #Page 156 because index starts from 0
            elif len(requiredSuppInfoMunicipalEmpRetSysPages) >= 1 and i == requiredSuppInfoMunicipalEmpRetSysPages[1]:
                FINAL_PAGE_DATA.clear()
                text = page.extract_text()
                headerlist = ['DATE', 'COUNTY', 'PAGE_HEADER', 'SUB_DATA_HEADER']
                #--------------------------------------------------DATA FILLER LINE-------------------------------------------------------------------
                #subheader will be columns for this page
                dfLine = namedtuple('dfLine', 'date county header subheader data')
                #--------------------------------------------------Split Lines based on /n and store into list----------------------------------------
                fullPagetext = text.split('\n')
                #Temp Storage variables
                county = ''
                date = ''
                header = ''

                #------------------------------------------------------FILTERS------------------------------------------------------------------------
                monthFilter = re.compile(r'December')
                dayFilter = re.compile(r'\d\d[,]')
                yearFilter = re.compile(r'\d\d\d\d\s')
                headerFilter = re.compile(r'Municipal Employees\' Retirement System of Michigan')
                county_filter = re.compile(r'county|COUNTY|County$')

                scheduleOfContributionsSplit = "Schedule of Contributions"
                #Temp Storage variables
                county = ''
                date = ''
                header = ''

                #each line will be manipulated using index, index starts at 0
                lineIndex = 0
                while lineIndex in range(len(fullPagetext)):
                    #Get rid of $ signs
                    fullPagetext[lineIndex] = fullPagetext[lineIndex].replace("$", " ")

                    #Look for these flags within the page as each line is processed
                    headerFound = headerFilter.search(fullPagetext[lineIndex])
                    monthFound = monthFilter.search(fullPagetext[lineIndex])
                    yearFound = yearFilter.search(fullPagetext[lineIndex])
                    countyFound = county_filter.search(fullPagetext[lineIndex])
                    scheduleOfContributionsFound = scheduleOfContributionsSplit.find(fullPagetext[lineIndex].split("  ")[0])
                   
                    if monthFound:
                        if dayFilter.search(fullPagetext[lineIndex+1]):
                            date = fullPagetext[lineIndex].replace("Fiscal Year Ended", "")
                            date = date.split()[0]
                            day = fullPagetext[lineIndex+1].split(" ")[0]
                            date = date + " " + day
                        lineIndex+=1 
                    elif headerFound:
                        header = fullPagetext[lineIndex]
                    elif countyFound:
                        county = fullPagetext[lineIndex]
                    elif scheduleOfContributionsFound != -1:
                        headerlist.append(fullPagetext[lineIndex].upper())
                    elif yearFound:
                        pdfYear = fullPagetext[lineIndex].split("  ")[0]
                        if pdfYear.isnumeric():
                            pdfYear = int(pdfYear)
                            currentYear = getCurrentYear()
                            if ((currentYear - 2) == pdfYear):
                                if yearFilter.search(fullPagetext[lineIndex + 1]):
                                    pdfYear = fullPagetext[lineIndex+1].split("  ")[0]
                                    if pdfYear.is_numeric():
                                        pdfYear = int(pdfYear)
                                        if((currentYear - 1) == pdfYear):
                                            #extract subline header
                                            subHeader1 = "Actuarially Determined Contribution"
                                            #Replace or remove these items and only keep numbers
                                            cleanSpecialChars(lineIndex+1)
                                            #Split numerical data by , based on space detected between each
                                            row = fullPagetext[lineIndex + 1].split()
                                            date = date + " " + row[0]
                                            FINAL_PAGE_DATA.append(dfLine(date, county, header, subHeader1, row[1]))
                                            print(FINAL_PAGE_DATA)
                                else:
                                    #extract subline header
                                    subHeader1 = "Actuarially Determined Contribution"
                                    #Replace or remove these items and only keep numbers
                                    cleanSpecialChars(lineIndex)
                                    #Split numerical data by , based on space detected between each
                                    row = fullPagetext[lineIndex].split()
                                    date = date + " " + row[0]
                                    FINAL_PAGE_DATA.append(dfLine(date, county, header, subHeader1, row[1]))
                                    print(FINAL_PAGE_DATA)
                    lineIndex+=1 
                fillDF(FINAL_PAGE_DATA, headerlist)
                print("---------------------DONE PAGE Municipal Employees' Retirement System of Michigan----------------------\n\n\n") 
    #Convert when while loop is done (outside of while loop)
    csvPath = conv_to_csv()
    return csvPath