# -*- coding: utf-8 -*-
"""
Created on Thu Jul 15 17:59:03 2021

@author: Ravi Teja Pekala
@company: OPJGU
"""

from math import ceil
from os import mkdir
from time import sleep
from datetime import datetime
from requests import get
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm

QUERY = input("Please enter a search query: ")
QUERY = QUERY.replace(' ', '+')

URL = "http://judgmenthck.kar.nic.in/judgmentsdsp/simple-search?query={}&submit=Go".format(QUERY)
BASE_URL = 'http://judgmenthck.kar.nic.in/'
RPP = 10

RESPONSE = get(URL).content
soup = BeautifulSoup(RESPONSE, "html.parser")

RESULTS = soup.find_all('p')[1].text
RESULTS = RESULTS.split(' ')[3]
try:
    RESULTS = int(RESULTS)
except ValueError:
    print("No results found")
    exit(0)
PAGES = ceil(RESULTS/RPP)

print(f"Total number of results: {RESULTS}")
def dspace_scraper():
    """
    Scrapes data from the current result page and
    stores it in a dataframe.
    Returns
    -------
    Pandas Dataframe
        Current page results that include Date, Link to document,
        Document name, Judge(s), Petitioner(s), Respondent and Bench
    """
    dates = []
    for child in soup.find_all(headers='t1'):
        dates.append(child.text)

    links = []
    file_names = []
    for child in soup.find_all(headers='t2'):
        links.append(BASE_URL+child.a.get_attribute_list('href')[0])
        file_names.append(child.a.text)

    _ = pd.DataFrame()
    _['Date'] = dates
    _['Link'] = links
    _['File Name'] = file_names

    data = {'Judge(s)':[], 'Petitioner':[], 'Respondent':[], 'Bench':[]}
    for child in soup.find_all('em')[0::4]:
        data['Judge(s)'].append(child.text)
    for child in soup.find_all('em')[1::4]:
        data['Petitioner'].append(child.text)
    for child in soup.find_all('em')[2::4]:
        data['Respondent'].append(child.text)
    for child in soup.find_all('em')[3::4]:
        data['Bench'].append(child.text)

    return _.merge(pd.DataFrame(data), on=_.index)

START = ''
FINAL = pd.DataFrame()
FINAL_DATA = pd.DataFrame()
for page in tqdm(range(PAGES), desc="Consolidating links"):
    START = page*10
    message = (
        'http://judgmenthck.kar.nic.in/judgmentsdsp/simple-search'
        f'?query={QUERY}&sort_by=0&order=DESC&rpp={RPP}&etal=0&start={START}'
        )
    URL = message
    RESPONSE = get(URL).content
    soup = BeautifulSoup(RESPONSE, "html.parser")
    FINAL = dspace_scraper()
    FINAL_DATA = FINAL_DATA.append(FINAL)
FINAL_DATA.drop('key_0', axis=1, inplace=True)
d = str(datetime.now()).split()[-1]
d = d.replace(':', '').split('.')[0]
mkdir(d)
FINAL_DATA.to_csv(f'{d}/{d}.csv', header=True, index=False)

# To fetch documents using the link
for i in tqdm(range(FINAL_DATA['Link'].shape[0]), desc="Processing"):
    doc_url = FINAL_DATA['Link'].iloc[i]
    try:
        doc_response = get(doc_url).content
    except TimeoutError:
        sleep(45)
        doc_response = get(doc_url).content
    doc_soup = BeautifulSoup(doc_response, 'html.parser')
    doc_links = doc_soup.find_all(target='_blank')[1]
    doc_title = str(i)+'_'+doc_links.text
    doc_link = BASE_URL+doc_links.get_attribute_list('href')[0]
    r = get(doc_link)
    with open(f'{d}/{doc_title}', "wb") as f:
        f.write(r.content)
