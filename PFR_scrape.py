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
from IPython.core.display import display, HTML
from collections import defaultdict

base_url = 'https://www.pro-football-reference.com/'
# scrape Jared Goff first. to be replaced by a generated list
test_player = 'players/G/GoffJa00.htm'

def agent_scramble():
    '''
    Mask user-agent
    '''
    ua = UserAgent()
    user_agent = {'User-agent' : ua.random}
    return user_agent

def scrape_page(player):
    '''
    Scrape all stats from a player's page
    arg:
        player = name as it appears on pro-football-reference in string format
    return:
        Player's information and stat as BS object
    '''
    response = requests.get(base_url + player, headers=agent_scramble())
    page_soup = BeautifulSoup(response.text, 'lxml')
    big_table = page_soup.find_all('table', {'id':'passing'})
    return big_table

def get_headers(table):
    '''
    Grab stat headers from player's BS table
    arg:
        BS object containing players info (from scrape_page)
    return:
        stat labels in a list
    '''
    stat_header = []

    stat_table = table[0].find_all('tr')
    header_soup = stat_table[0].find_all('th')
    for header in header_soup:
        stat_header.append(header.text)
    return stat_header

def get_stats(table):
    '''
    Store player stats in dictionary
    arg:
        BS table created from scrape_page
    return:
        Dictionary in {year : stats} format
    '''
    stats = defaultdict(list)
    for ele in table:
        if not ele.find('a'):
            continue
        year = ele.find('a').text
        temp_stat = ele.find_all('td')
        for num in temp_stat:
            stats[year].append(num.text)
    return stats

def create_player_dict(player, stat_dict):
    ''' WORK IN PROGRESS
    Create dict using player name and stats
    arg:
        TBD
    return:
        Dictionary for a single QB in form {name : stats}
    '''
    player_dict = {}
    TEST_SOUP = scrape_page(test_player)
    headers = get_headers(TEST_SOUP)
    pass

def create_player_csv(player_stat):
    csv_file = 'player_name.csv'
    with open(csv_file, 'w') as csvfile:
        csvfile.write(','.join(headers) + '\n')
        for key, value in stats.items():
            csvfile.write(key + ',' + ','.join(value) + '\n')

if __name__ == 'main':
    pass