'''
Module goes to www.pro-football-reference.com/ to:
1) Find list of QBs
2) Grab stats for those QBs and puts it in a dictionary form {name : stats}
3) Writes the stats to a... csv?
'''

import requests
import time
import random
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from collections import defaultdict
import pandas as pd

base_url = 'https://www.pro-football-reference.com/players/'

def get_player_htm():
    '''
    Use name to get name for player's html page identifier
    return:
        dict of {first_part_htm_names : player_name}
    '''
    qb_list_file = './pfr_scraped/master_qb_list.csv'
    qb_df = pd.read_csv(qb_list_file, index_col=0)
    htm_name_dict = {}

    qb_df = qb_df['0'].str.split(n=1, expand=True).copy()
    qb_df[2] = qb_df[0] + ' ' + qb_df[1]
    qb_df.rename({0:'First', 1:'Last', 2:'Full'}, axis=1, inplace=True)
    qb_df['htm_name'] = qb_df['Last'].str.slice(stop=4) + qb_df['First'].str.slice(stop=2)
    htm_name_dict = dict(zip(qb_df['htm_name'], qb_df['Full']))
    return htm_name_dict

def scrape_page(htm_dict):
    '''
    Scrape page and store in a list of soup files
    arg:
        list of qb's name as html identifier
    return:
        list of players pages in soup form
    '''
    ua = UserAgent()
    user_agent = {'User-agent': ua.random}
    player_page_soups = []
    counter = 0

    for qb_htm, qb_name in htm_dict.items():
        for x in range(6):
            position_list = []
            name = qb_htm + '0' + str(x) + '.htm'
            add_url = qb_htm[0] + '/' + name
            response = requests.get(base_url + add_url, headers=user_agent)
            if response.status_code == 200:
                print(str(response.status_code) + ' ' + add_url)
                page_soup = BeautifulSoup(response.text, 'lxml')
                player_name = page_soup.find('h1', {'itemprop': 'name'}).text
                position = page_soup.find_all('td', {'data-stat': 'pos'})
                for pos in position:
                    position_list.append(pos.text.lower())
                if (player_name.strip() != qb_name.strip()) or ('qb' not in position_list):
                    time.sleep(random.random() + random.randint(1, 4))
                    continue
                else:
                    break
            else:
                print('Something\'s wrong with:' + add_url)
                break
        player_page_soups.append(page_soup)
        time.sleep(random.random() + random.randint(1, 4))
    return player_page_soups

def get_player_data(soup):
    '''
    Get player's name (string) and stat table in bs resultset object
    arg:
        BS object of player's web page
    return:
        list containing [player_name, bs4.resultset]
    '''
    name = soup.find('h1', {'itemprop':'name'}).text.strip()
    big_table = soup.find_all('table', {'id':'passing'})
    return name, big_table

def get_stats(player_data):
    name = player_data[0]
    stat_table = player_data[1]
    annual_stat_dict = defaultdict(list)
    player_stat_list = []

    for ele in stat_table:
        stat_block = ele.find_all('tr', class_='full_table')
        for stats_rows in stat_block:
            year = int(stats_rows.find('a').text)
            stats = stats_rows.find_all('td')
            for x in stats:
                annual_stat_dict[year].append(x.text)
    player_stat_list.append(name)
    player_stat_list.append(annual_stat_dict)
    return player_stat_list

def get_headers(player_data):
    '''
    Grab stat headers from player's BS table
    arg:
        BS object containing players info (from scrape_page)
    return:
        stat labels in a list
    '''
    table = player_data[1]
    stat_header = ['name']

    stat_table = table[0].find_all('tr')
    header_soup = stat_table[0].find_all('th')
    for header in header_soup:
        stat_header.append(header.text.strip())
    return stat_header

def create_player_df(stats_for_df):
    agg_stat_list = []

    for key, value in stats_for_df[1].items():
        list_for_df = []
        list_for_df.append(stats_for_df[0])
        list_for_df.append(key)
        for x in value:
            list_for_df.append(x)
        agg_stat_list.append(list_for_df)
    player_df = pd.DataFrame(agg_stat_list,columns=headers)
    return player_df

def create_raw_stat_df(player_page_soups, pkl=False):
    master_raw_df = pd.DataFrame()
    error_list = []
    for player_soup in player_page_soups:
        player_data = get_player_data(player_soup)
        if not player_data[1]:
            error_list.append(player_data[0])
            pass
        else:
            headers = get_headers(player_data)
            player_stats = get_stats(player_data)
            player_df = create_player_df(player_stats, headers)
        master_raw_df = master_raw_df.append(player_df)
        if pkl:
            master_raw_df.to_pickle('./Pickles/master_raw_df.pkl')
    return master_raw_df, error_list

if __name__ == '__main__':
    htm_name_dict = get_player_htm()
    player_page_soups = scrape_page(htm_name_dict)
    create_raw_stat_df(player_page_soups)
