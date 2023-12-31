# -*- coding: utf-8 -*-
"""WIFIA_Data_Collect.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1tA_5XMFokqDMDw07ftGKnSymIO40NUua
"""

import numpy as np
import pandas as pd
!pip install PyPDF2 openpyxl
import PyPDF2
import re
import os
!pip install xlsxwriter
import xlsxwriter
#!pip install geopy
#!pip install Nominatim

import plotly.express as px
from plotly.offline import plot
#!pip install folium
import folium

def textscrape (pdf_file_in):
  pdf_file = open(pdf_file_in, 'rb')
  reader = PyPDF2.PdfReader(pdf_file)
  text = ''
  for page_num in range(len(reader.pages)):
    text += reader.pages[page_num].extract_text()

  def remove(string):
    return string.replace(" ", "").replace("\n", "")

  text = text.replace(" ", "").replace("\n", ",")
  pdf_file.close()
  return text

#number search, not $ though
def search_num (pdf_file, pattern1):
  def remove(string):
   return string.replace(" ", "").replace("\n", "")

  text = textscrape(pdf_file)
  pattern1 = remove(pattern1)

  pattern = pattern1 + r'\s*([\d,]+(?:\.\d+)?(?:\s*(?:million|billion))?)?'   #r'\s*([\d,]+(?:\.\d*0)?)'
  matches = re.findall(pattern, text, re.IGNORECASE)

  return(matches)

#name search
def search_name (pdf_file, pattern1):
  def remove(string):
   return string.replace(" ", "").replace("\n", "")

  text = textscrape(pdf_file)
  pattern1 = remove(pattern1)

  pattern = pattern1 + r'\s*([^,]*,[^,]*)'      #r'\s*([^,]+[,])'
  matches = re.findall(pattern, text, re.IGNORECASE)

  return(matches)

#number search for $ only
def search_num_dol (pdf_file1, pattern1):
  def remove(string):
   return string.replace(" ", "")

  text = textscrape(pdf_file1)
  pattern1 = remove(pattern1)

  pattern = pattern1 + r'\s*(\$[\d,]+(?:\.\d+)?(?:\s*(?:million|billion))?)?'             #r'\s*\$([\d,]+(?:\.\d+)?\s*(?:million|billion))'
  matches = re.findall(pattern, text, re.IGNORECASE)

  return(matches)

def converttonum (x):
  ins = []
  for value in x:
    if 'million'in value:
        numeric_part = float(re.search(r'([\d,]+(?:\.\d+)?)\s*million', value).group(1))
        ints.append(numeric_part * 1000000)
    elif 'billion' in value:
        numeric_part = float(re.search(r'([\d,]+(?:\.\d+)?)\s*billion', value).group(1))
        ints.append(numeric_part * 1000000000)
    elif "NA" in value:
        ints.append("NA")
    else:
        ints.append(value)
  return ints

def test(pdfname1):
    keywords = ['BORROWER:', 'LOCATION:', 'WIFIA LOAN AMOUNT[s]?:',
                'TOTAL WIFIA PROJECT COSTS:', 'POPULATION SERVED BY \s*(?:system|project[s]?)? :', 'NUMBER OF JOBS CREATED:']

    data = []

    for keyword in keywords:
      if keyword in ['BORROWER:', 'LOCATION:']:
        values = search_name(pdfname1, keyword)
      elif keyword in ['WIFIA LOAN AMOUNT[s]?:', 'TOTAL WIFIA PROJECT COSTS:']:
        values = search_num_dol(pdfname1, keyword)
      elif keyword in ['POPULATION SERVED BY \s*(?:system|project[s]?)? :', 'NUMBER OF JOBS CREATED:']:
        values = search_num(pdfname1, keyword)
      else:
        values = []

      for value in values:
          if value != "NoneType":
                data.append({'Keyword': keyword, pdfname1: value})
          if value == "NoneType":
                  break
    return pd.DataFrame(data)

file_names = os.listdir()
#file_names.remove('.ipynb_checkpoints')
file_names = file_names[1:(len(file_names)-1)]

keywords = ['BORROWER:', 'LOCATION:', 'WIFIA LOAN AMOUNT[s]?:',
            'TOTAL WIFIA PROJECT COSTS:', 'POPULATION SERVED BY \s*(?:system|project[s]?)? :', 'NUMBER OF JOBS CREATED:']
words = ["wastewater", "drinking water", "stormwater", "reuse"]

master_df = pd.DataFrame(keywords)
master_df.columns = ["Keyword"]

for i in range(0, len(file_names)):
    df = test(file_names[i])
    master_df = master_df.merge(df, on= "Keyword", how='left')

master_dfT = master_df.set_index('Keyword').T

temp_df = []
for file_name in file_names:
    found_keywords = []

    for keyword in words:
        if search_name(file_name, keyword):
            found_keywords.append(keyword)

    temp_df.append((found_keywords, file_name))

temp_df = pd.DataFrame(temp_df)
temp_df.columns = ["Project Type", "Keyword"]
master_dfT = master_dfT.merge(temp_df, on='Keyword')

master_dfT.iloc['Keyword']

master_dfT.to_csv('12data.csv', index=False)

data = pd.read_excel('Clean_WIFIA - Copy.xlsx')

coordinate_df = []
loc_list = data['LOCATION:']
from geopy.geocoders import Nominatim

for i in range(0, len(loc_list)):
  cell = loc_list[i]
  address= cell
  geolocator = Nominatim(user_agent="Your_Name")
  location = geolocator.geocode(address)
  print(location.address)
  print((location.latitude, location.longitude))
  coordinate_df.append([location.address, location.latitude, location.longitude])

data = pd.read_excel('Final_Clean.xlsx')

jitter = .09

data["LAT_jittered"] = data["LAT"] + (2 * (pd.np.random.rand(len(data)) - 0.5) * jitter)
data["LONG_jittered"] = data["LONG"] + (2 * (pd.np.random.rand(len(data)) - 0.5) * jitter)

data.columns

#WIFIA Loan Amount Map
custom_colors = {
    'Stormwater':'lime',
    'Drinking water':'cyan',
    'Wastewater':'red',
    'Reuse': 'purple',
}

fig = px.scatter_mapbox(data, lat="LAT_jittered", lon="LONG_jittered",
                        color="PROJECT TYPE:",
                        size='WIFIA LOAN AMOUNT:',                  #'POPULATION SERVED BY PROJECT :' , 'NUMBER OF JOBS CREATED:', 'WIFIA LOAN AMOUNT:', 'TOTAL WIFIA PROJECT COSTS:', 'Loan Percapita'
                        size_max = 30,
                        zoom=3,
                        color_discrete_map = custom_colors,
                        mapbox_style='carto-positron',
                        opacity=.7)

fig.update_layout(legend=dict(
    title="Project Type",
    traceorder="reversed",
    itemsizing="constant",
    itemclick="toggleothers"
))

plot(fig, auto_open=True)

#Population Map
custom_colors = {
    'Stormwater':'lime',
    'Drinking water':'cyan',
    'Wastewater':'red',
    'Reuse': 'purple',
}

fig = px.scatter_mapbox(data, lat="LAT_jittered", lon="LONG_jittered",
                        color="PROJECT TYPE:",
                        size='POPULATION SERVED BY PROJECT :', #'NUMBER OF JOBS CREATED:', 'WIFIA LOAN AMOUNT:', 'TOTAL WIFIA PROJECT COSTS:', 'Loan Percapita'
                        size_max = 30,
                        zoom=3,
                        color_discrete_map = custom_colors,
                        mapbox_style='carto-positron',
                        opacity=.7)

fig.update_layout(legend=dict(
    title="Project Type",
    traceorder="reversed",
    itemsizing="constant",
    itemclick="toggleothers"
))

plot(fig, auto_open=True)

#Jobs Map
custom_colors = {
    'Stormwater':'lime',
    'Drinking water':'cyan',
    'Wastewater':'red',
    'Reuse': 'purple',
}

fig = px.scatter_mapbox(data, lat="LAT_jittered", lon="LONG_jittered",
                        color="PROJECT TYPE:",
                        size='NUMBER OF JOBS CREATED:', #'WIFIA LOAN AMOUNT:', 'TOTAL WIFIA PROJECT COSTS:', 'Loan Percapita'
                        size_max = 30,
                        zoom=3,
                        color_discrete_map = custom_colors,
                        mapbox_style='carto-positron',
                        opacity=.7)

fig.update_layout(legend=dict(
    title="Project Type",
    traceorder="reversed",
    itemsizing="constant",
    itemclick="toggleothers"
))

plot(fig, auto_open=True)

#Loans Per Capita Map
custom_colors = {
    'Stormwater':'lime',
    'Drinking water':'cyan',
    'Wastewater':'red',
    'Reuse': 'purple',
}


fig = px.scatter_mapbox(data, lat="LAT_jittered", lon="LONG_jittered",
                        color="Loan Percapita",
                        color_continuous_scale="RdBu",
                        size_max=30,
                        zoom=3,
                        color_discrete_map=custom_colors,
                        mapbox_style='carto-positron',
                        opacity=0.7)

# Add a color bar legend for the size
fig.update_layout(coloraxis_colorbar=dict(title="Loan Percapita"))

plot(fig, auto_open=True)

'''
def converttonum (x):
  for value in x:
    if 'million' in value:
        numeric_part = float(re.search(r'([\d,]+(?:\.\d+)?)\s*million', value).group(1))
        ints.append(numeric_part * 1000000)
    elif 'billion' in value:
        numeric_part = float(re.search(r'([\d,]+(?:\.\d+)?)\s*billion', value).group(1))
        ints.append(numeric_part * 1000000000)
    elif 'NA' in value:
        ints.append(value)
    else:
        ints.append(value)
  return ints
'''

#search for keywords
'''
i =0
j = 0
temp_df = []
while j <= len(file_names):
#for j in range(0, len(file_names)):
  for i in range(0, len(words)):
    if(search_name(file_names[j], words[i]) == True):
      cell = words[i]
      temp_df.append(cell)
    j = j + 1
'''

#as needed fixes

'''
temp_list = ['coh_tvwd_wifiaprojectfactsheet_loancloser.pdf', 'cvwd_wifiaprojectfactsheet_loanclose_1.pdf', 'morro_bay_wifiaprojectfactsheet_loanclose.pdf',
             'cortland_wifiaprojectfactsheet_loanclose_0.pdf', 'cityof_oakridgewifiaprojectfactsheet_loanclose.pdf', 'ieua_wifiaprojectfactsheet_loanclose.pdf',
             'nbc_wifiaprojectfactsheet_loanclose.pdf', 'sme_wifiaprojectfactsheet_loancloser.pdf', 'wichita_wifiaprojectfactsheet_loanclose1.pdf',
             'NJI-Bank_WIFIAProjectFactsheet_LoanClose_0.pdf', 'toho_wifiaprojectfactsheet_loanclose_2.pdf', 'factsheet_wagnn.pdf', 'Factsheet_Pflugerville final.pdf',
             'Factsheet - Medford.pdf', 'factsheet-phase-1_joliet.pdf', 'factsheet-phase-2_joliet.pdf', 'spu_wifiaprojectfactsheet_loanclose_1.pdf', 'Factsheet_Oxnard.pdf',
             'city-of-boise.pdf', 'helix-water-district.pdf', 'Factsheet_Howard County.pdf', 'narragansett-bay-water-commission.pdf',
             'factsheet_evanston.pdf', 'WIFIA-Factsheet_Chattanooga.pdf', 'Factsheet_JohnsonCounty.pdf', 'Factsheet_Metro Water(1).pdf', 'milwaukee-factsheet.pdf',
             'Factsheet_San Diego Stormwater.pdf', 'Factsheet_GreshamRockwood.pdf', 'Factsheet - Englewood Wastewater.pdf', 'Factsheet - Englewood Water.pdf',
             'factsheet_new-orleans.pdf', 'Factsheet_DeKalb.pdf', 'factsheet_ieua-ii.pdf', 'factsheet-new-jersey2.pdf']

temp_list = ['coh_tvwd_wifiaprojectfactsheet_loancloser.pdf', 'cvwd_wifiaprojectfactsheet_loanclose_1.pdf',
             'morro_bay_wifiaprojectfactsheet_loanclose.pdf','cortland_wifiaprojectfactsheet_loanclose_0.pdf',
             'cityof_oakridgewifiaprojectfactsheet_loanclose.pdf','ieua_wifiaprojectfactsheet_loanclose.pdf',
             'nbc_wifiaprojectfactsheet_loanclose.pdf','sme_wifiaprojectfactsheet_loancloser.pdf',
             'wichita_wifiaprojectfactsheet_loanclose1.pdf','NJI-Bank_WIFIAProjectFactsheet_LoanClose_0.pdf',
             'toho_wifiaprojectfactsheet_loanclose_2.pdf','spu_wifiaprojectfactsheet_loanclose_1.pdf',
             'Factsheet_GreshamRockwood.pdf']

i =0
temp_df = []
for i in range(0, len(temp_list)):
  cell = search_num_dol(temp_list[i], 'WIFIA LOAN AMOUNTS:')
  #temp_df = temp_df + cell
  temp_df.append({temp_list[i]: cell})
#print(file_names[8])
'''

#as needed fixes
'''
temp_list = ['st._louis_wifiaprojectfactsheet_loanclose_final_0.pdf', 'miami_wifiaprojectfactsheet_loancloser.pdf',
             'tacoma_wifiaprojectfactsheet_loanclose.pdf','cityof_oakridgewifiaprojectfactsheet_loanclose.pdf',
             'omaha_wifiaprojectfactsheet_loanclose.pdf','miami_iii_wifiaprojectfactsheet_loanclose.pdf',
             'toho_wifiaprojectfactsheet_loanclose_2.pdf','miami_ii_wifiaprojectfactsheet_loancloser.pdf',
             'nmb_wifiaprojectfactsheet_loanclose.pdf','cvwd_wifiaprojectfactsheet_loanclose_1.pdf',
             'slc_wifiaprojectfactsheet_loanclose.pdf','san_diego_wifiaprojectfactsheet_loanclosefinal.pdf',
             'svcw-ww_wifiaprojectfactsheet_loanclose_0.pdf','beaverton_wifiaprojectfactsheet_loanclose.pdf',
             'san_mateo_2019_wifiaprojectfactsheet_loanclose.pdf','soquel_wifiaprojectfactsheet_loanclose.pdf',
             'oceanside_wifiaprojectfactsheet_loanclose.pdf','louisville_and_jefferson_county_msd_biosolids.pdf',
             'ocwd_wifiaprojectfactsheet_loanclosefinal.pdf','stockton_wifiaprojectfactsheet_loancloser.pdf',
             'ocwd-pfas_wifiaprojectfactsheet_loanclosefinal.pdf','waukesha_wifiaprojectfactsheet_loanclose.pdf',
             'hrsd_wifiaprojectfactsheet_loanclose.pdf','sunnyvale_wifiaprojectfactsheet_loanclose2.pdf',
             'sme_wifiaprojectfactsheet_loancloser.pdf','NJI-Bank_WIFIAProjectFactsheet_LoanClose_0.pdf',
             'svcw-rescu-ii_wifiaprojectfactsheet_loanclose_0.pdf','dekalb_wifiaprojectfactsheet_loanclose.pdf',
             'ifa_wifiaprojectfactsheet_loanclose2.pdf','sfpu_wifiaprojectfactsheet_loanclosev2.pdf',
             'sfpuc_ii_wifiaprojectfactsheet_loanclose.pdf','coh_tvwd_wifiaprojectfactsheet_loancloser.pdf',
             'mfda_wifiaprojectfactsheet_loanclose_0.pdf','hrsd_wifiaprojectfactsheet_loanclose_tranche2.pdf',
             'portland_wifiaprojectfactsheet_loanclose.pdf','san-diego_wifiaprojectfactsheet_loanclosefinal2.pdf',
             'factsheet-new-jersey2.pdf','baltimore_wifiaprojectfactsheet_loanclose.pdf']
i =0
temp_df = []
for i in range(0, len(temp_list)):
  cell = search_num(temp_list[i], 'Population Served by System:')
  temp_df = temp_df + cell
#print(file_names[8])
'''

#as needed fixes
'''
temp_list = ['factsheet_wagnn.pdf', 'Factsheet_Pflugerville final.pdf', 'Factsheet - Medford.pdf',
             'factsheet-phase-1_joliet.pdf', 'factsheet-phase-2_joliet.pdf', 'spu_wifiaprojectfactsheet_loanclose_1.pdf',
             'Factsheet_Oxnard.pdf', 'city-of-boise.pdf', 'helix-water-district.pdf', 'Factsheet_Howard County.pdf',
             'narragansett-bay-water-commission.pdf', 'factsheet_evanston.pdf', 'WIFIA-Factsheet_Chattanooga.pdf',
             'Factsheet_JohnsonCounty.pdf', 'Factsheet_Metro Water(1).pdf', 'Factsheet_SFPUC III.pdf',
             'milwaukee-factsheet.pdf', 'Factsheet_San Diego Stormwater.pdf', 'Factsheet_GreshamRockwood.pdf',
             'Factsheet - Englewood Wastewater.pdf', 'Factsheet - Englewood Water.pdf', 'factsheet_new-orleans.pdf',
             'Factsheet_DeKalb.pdf', 'factsheet_ieua-ii.pdf', 'soquel_wifiaprojectfactsheet_loanclose.pdf', 'factsheet-new-jersey2.pdf']
i =0
temp_df = []
for i in range(0, len(temp_list)):
  cell = search_num_dol(temp_list[i], 'TOTAL WIFIA PROJECT COSTS:')
  temp_df = temp_df + cell
#print(file_names[8])
'''

''' works
#def data_site (pdf_file11):
pdf_file11 = "atlanta_north_fork_wifiaprojectfactsheet_loanclose_1.pdf"
Case_df = pd.DataFrame()
cell = pd.DataFrame()
keywords = ['BORROWER:', 'LOCATION:', 'WIFIA LOAN AMOUNT:',
              'TOTAL WIFIA PROJECT COSTS:', 'POPULATION SERVED BY PROJECT :', 'NUMBER OF JOBS CREATED:']

for i in range(0, len(keywords)):
    if i in [2,3]:
      cell = pd.DataFrame(search_num_dol(pdf_file11, keywords[i]))
      Case_df = pd.concat([Case_df, cell])

    elif i in [4,5]:
      cell = pd.DataFrame(search_num(pdf_file11, keywords[i]))
      Case_df = pd.concat([Case_df, cell])

  #Case_df = Case_df.assign(name = keywords[2:4])
 # Case_df.columns = [(pdf_file11), "Value"]
#  return Case_df

''' OLD 9/18
def Numbersearch(pdf_file1, pattern1):

 pdf_file = open(pdf_file1, 'rb')
 reader = PyPDF2.PdfReader(pdf_file)
 text = ''
 for page_num in range(len(reader.pages)):
   text += reader.pages[page_num].extract_text()

 def remove(string):
   return string.replace(" ", "").replace("\n", "")

 text = text.replace(" ", "").replace("\n", "")
 pattern1 = remove(pattern1)

 pdf_file.close()
 pattern = pattern1 + r'\s*([\d,]+(?:\.\d*0)?)'  #r'\s*([\d,]+)'
 matches = re.findall(pattern, text, re.IGNORECASE)

 if matches:
      jobs_created = matches
 else:
      jobs_created = None

 return(jobs_created)
 '''

''' OLD
def Numbersearch(pdf_file1, pattern1):
  pdf_file = open(pdf_file1, 'rb')
  reader = PyPDF2.PdfReader(pdf_file)
  text = ''
  for page_num in range(len(reader.pages)):
    text += reader.pages[page_num].extract_text()

  def remove(string):
    return string.replace(" ", "\s+")

  pattern1 = remove(pattern1)

  pdf_file.close()
  pattern = pattern1 + r'\s*([\d,]+(?:\.\d*0)?)'  #r'\s*([\d,]+)'
  matches = re.findall(pattern, text, re.IGNORECASE)

  if matches:
      jobs_created = matches
  else:
      jobs_created = None

  return(jobs_created)
'''

''' OLD
def Namesearch(pdf_file1, pattern1):
  pdf_file = open(pdf_file1, 'rb')
  reader = PyPDF2.PdfReader(pdf_file)
  text = ''
  for page_num in range(len(reader.pages)):
   text += reader.pages[page_num].extract_text()

  def remove(string):
   return string.replace(" ", "\s+")

  text = text.replace(" ", "").replace("\n", "")
  pattern1 = remove(pattern1)

  pdf_file.close()
  pattern = pattern1 + r'\s*(\$[\d,]+)'
  matches = []
  matches = re.findall(pattern, text, re.IGNORECASE)

  return(matches)
'''