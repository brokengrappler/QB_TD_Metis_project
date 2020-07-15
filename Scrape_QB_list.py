'''
Compile list of active quarterbacks (default was 2010-2019)
'''


import requests
import time, os
import random
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import pandas as pd


def qb_soup_scraper():
    '''
    Create a list of soup files to search through. Adjust years_list variable to adjust years to scrape.
    return:
        list of soup files that contain QB names
    '''
    base_url = 'https://www.pro-football-reference.com/years/'
    html = '/passing.htm'
    years_list = list(map(str, [x for x in range(1998, 2009)]))
    ua = UserAgent()
    user_agent = {'User-agent': ua.random}

    soup_list = []

    for year in years_list:
        response = requests.get(base_url + year + html, headers=user_agent)
        # I would insert a try and raise test here to
        # check response but nervous about scraping page repeatedly. Try later.
        soup = BeautifulSoup(response.text, 'lxml')
        soup_list.append(soup)
        time.sleep(.5 + 2 * random.random())
    return soup_list

def raw_qb_list(soup):
    '''
    Compile list of all players with passing stats (incl non-QBs) for years specified in qb_soup_scraper.
    arg:
        soup file of season passing stats page on pro-football-reference.com
    return:
        list containing all players with passing stats. Each element is in form 'first_name last_name'
    '''
    qb_list = []
    links = soup.find_all('tbody')
    for qbpos in links:
        qb_names = qbpos.find_all('a')
        for names in qb_names:
            str_test = names.text.split()
            if len(str_test) > 1:
                qb_list.append(str_test)
    qb_list = [' '.join(name) for name in qb_list]
    return qb_list

def raw_pos_list(soup):
    '''
    Get position data for players on the page
    arg:
        soup file of season passing stats page on pro-football-reference.com
    return:
        list containing position info for every player on the page
    '''
    position_list=[]
    pos_soup = soup.find_all('td', {'data-stat':'pos'})
    for x in pos_soup:
        position_list.append(x.text.lower())
    return position_list

def raw_scrape(soup_list):
    '''
    Filter list of passing players to only non-scrub QBs
    arg:
        list of soup files scraping season passing stats.
    return
        list aggregating QBs active in the years specified in qb_soup_scraper.
    '''
    qb_master_list = []

    for soup in soup_list:
        qb_temp_list = raw_qb_list(soup)
        pos_list = raw_pos_list(soup)
        # Create df to filter either obscure or non-QBs
        filter_df = pd.DataFrame()
        filter_df['name'] = qb_temp_list
        filter_df['pos'] = pos_list
        filter_df = filter_df[filter_df['pos'] == 'qb']
        qb_temp_list = list(filter_df['name'])
        for qb in qb_temp_list:
            if qb not in qb_master_list:
                qb_master_list.append(qb)
    return qb_master_list

def write_list_to_file(master_list):
    csv_file = './pfr_scraped/added_qb_list.csv'
    qb_list_series = pd.Series(master_list)
    qb_list_series.to_csv(csv_file)

if __name__ == '__main__':
    soup_list = qb_soup_scraper()
    master_list = raw_scrape(soup_list)
    write_list_to_file(master_list)
