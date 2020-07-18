'''
Module goes to www.pro-football-reference.com/ to:
1) Imports list of QBs
2) Grab stats for those QBs and puts it in a dictionary form {name : stats}
3) Writes the stats to a df
'''

import requests
import time
import random
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from collections import defaultdict
import pandas as pd

# Web url and path where scraped qb_list is stored
base_url = 'https://www.pro-football-reference.com/players/'
# path where qb list pickle created in Scrape_qb_list.py is located.
path = './Project-2-Regression/'

def add_players():
    '''
    Merges list of QBs to return only unique ones for when addtional QBs are added for analysis
    return:
        Dataframe of QBs to be added
    '''
    qb_list_file = './pfr_scraped/master_qb_list.csv'
    qb_list_file2 = './pfr_scraped/added_qb_list.csv'
    qb_df = pd.read_csv(qb_list_file, index_col=0)
    qb_df2 = pd.read_csv(qb_list_file2, index_col=0)
    qb_df3 = qb_df2.merge(qb_df, how='left', indicator=True)
    qb_df3 = qb_df3[qb_df3['_merge'] == 'left_only']
    qb_df3.drop('_merge', axis=1, inplace=True)
    return qb_df3

def get_player_htm(df):
    '''
    Use name to get name for player's html page identifier
    return:
        dict of {first_part_htm_names : player_name}
    '''
    htm_name_dict = {}

    df = df['0'].str.split(n=1, expand=True).copy()
    df[2] = df[0] + ' ' + df[1]
    df.rename({0:'First', 1:'Last', 2:'Full'}, axis=1, inplace=True)
    df['htm_name'] = df['Last'].str.slice(stop=4) + df['First'].str.slice(stop=2)
    htm_name_dict = dict(zip(df['htm_name'], df['Full']))
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
    '''
    Grab stats from player's BS table
    arg:
        BS object containing players info (from scrape_page)
    return:
        List containing [player_name(str), {year: stats}]
    '''
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

def create_player_df(stats_for_df, headers):
    '''
    Reorganizes information from get_stats in format ready for pandas df
    arg:
        1) List of name and dict of stats from get_stats function;
        2) list of stat labels from get_headers
    return:
        Player's stats in pandas df
    '''
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


def create_raw_stat_df(player_page_soups, pkl):
    '''
    Creates 2 pickle files to save players data extracted. 2 dfs to account for players with 32 stats (old)
    vs 33 (current). Functions include, for each player page:
    1) extracting stat headers
    2) extracting raw stats
    3) create player stat to append to master df
    arg:
        1) list of BS;
        2) pkl = True to save pickle
    :return:
        list of players with errors
    '''
    master_raw_df = pd.DataFrame()
    old_headers_df = pd.DataFrame()
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
        if len(headers) > 32:
            master_raw_df = master_raw_df.append(player_df)
        else:
            old_headers_df = old_headers_df.append(player_df)
    if pkl:
        master_raw_df.to_pickle(path + '/Pickles/added_players_df.pkl')
        old_headers_df.to_pickle(path + '/Pickles/old_players_df.pkl')
    return error_list

if __name__ == '__main__':
    added_qbs_df = add_players()
    htm_name_dict = get_player_htm(added_qbs_df)
    player_page_soups = scrape_page(htm_name_dict)
    check = create_raw_stat_df(player_page_soups, True)
    print(check[1])
