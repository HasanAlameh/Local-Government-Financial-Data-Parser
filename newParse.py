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

    #Specifying that the date format used is always (mmmm dd, yyyy)
    dateFilter = re.compile(r'[a-zA-Z]+\s\d\d[,]\s\d\d\d\d')

    #Read the PDF file
    with pdfplumber.open(file) as pdf: 
        #Iterate through pages to find the headers we are interested in
        #Each header found gets added to its appropriate array
        for page in pdf.pages:
            extractedText = page.extract_text()

            #If extracted text is not empty
            if extractedText:
                #In case some PDFs (like Saginaw County's) use unicode characters that mess up the comparisons
                extractedText = unicodedata.normalize('NFKD', extractedText)
                extractedText = extractedText.upper()
                splitText = extractedText.split('\n')

                #If date has not been found yet
                if not documentDate:
                    documentDate = dateFilter.findall(extractedText)
                
                #Find Statement of Net Position pages
                if "\nSTATEMENT OF NET POSITION\n" in extractedText or "\nSTATEMENT OF NET POSITION (CONTINUED)\n" in extractedText:
                    #If the municipality name has not been found yet
                    if not municipalityName:
                        #Municipality name is always the first line of the page
                        municipalityName = splitText[0]
                    #If statement of net position - proprietary funds is found, place the page in the corresponding list
                    if "PROPRIETARY FUNDS" in extractedText:
                        #Make sure the page is not a "notes to financial statements" page
                        if  not any(line.startswith("COMPONENT UNITS") for line in splitText):
                            statementOfNetPositionProprietaryFunds.append(page)
                    #If statement of net position is found, place the page in the corresponding list 
                    else:
                        #Make sure the page is not a "notes to financial statements" page
                        if ("NOTES" in splitText[-1] or "NOTES" in splitText[-2] or "NOTES" in splitText[-3]) and not any(line.startswith("COMPONENT UNITS") for line in splitText):
                            statementOfNetPositionPages.append(page)     
        
        #These prints are placeholders for now, use them to check if extraction was successful
        print("Municipality: ", municipalityName)
        print("Date of document: ", documentDate)
        print("STATEMENT OF NET POSITION PAGES")
        print("---------------------------------------------------")
        for currentPage in statementOfNetPositionPages:
            textFromPage = (currentPage.extract_text()).upper()
            textFrompage = textFromPage.split('\n')
            print("--------------------------------")
            print(textFromPage)
        print("STATEMENT OF NET POSITION - PROPRIETARY FUNDS PAGES")
        print("---------------------------------------------------")
        for currentPage in statementOfNetPositionProprietaryFunds:
            textFromPage = (currentPage.extract_text()).upper()
            textFrompage = textFromPage.split('\n')
            print("--------------------------------")
            print(textFromPage) 
        

        #with open('newOutput.csv', 'w') as f:
        #    writer = csv.writer(f, delimiter='\n')
        #    writer.writerow(text)