'''
Module goes to www.pro-football-reference.com/ to:
1) Find list of QBs
2) Grab stats for those QBs and puts it in a dictionary form {name : stats}
3) Writes the stats to a... csv?
'''

import requests
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import time
import random
import pandas as pd

base_url = 'https://www.pro-football-reference.com/players/'

def get_player_htm():
    '''
    Use name to get name for player's html page identifier
    return:
        dict of {player_page_htm_label : player_name}
    '''
    qb_list_file = './pfr_scraped/master_qb_list.csv'
    qb_df = pd.read_csv(qb_list_file, index_col=0)

    qb_df = qb_df['0'].str.split(expand=True).copy()
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
    user_agent = {'User-agent' : ua.random}
    player_page_soups = []
    error_list = []

    for qb_htm, qb_name in htm_dict.items():
        for x in range(6):
            # iterate player to page mismatch
            # e.g. BradSa00.htm might be Sage Brady instead of Sam Bradford so check BradSa0x.htm
            name = qb_htm + '0' + str(x) + '.htm'
            add_url = qb_htm[0] + '/' + name
            response = requests.get(base_url + add_url, headers=user_agent)
            if response.status_code == 200:
                print(str(response.status_code) + add_url)
                page_soup = BeautifulSoup(response.text, 'lxml')
                page_name = page_soup.find('h1',{'itemprop':'name'}).text
                if page_name != qb_name:
                    # If there's a mismatch iterate for next x
                    time.sleep(random.random() + random.randint(1,4))
                    continue
                else:
                    break
            else:
                # Something was actually wrong with this but function ended up grabbing all the data I needed anyway
                print('Something\'s wrong with:' + add_url)
                error_list.append(qb_name)
                break
        player_page_soups.append(page_soup)
        time.sleep(random.random() + random.randint(1,4))
    return player_page_soups

def save_scrape_page(soup_list):
    '''
    Save list of soups to text file to avoid scraping again
    arg:
        list of pages scraped in soup form
    '''
    qb_soup_list = [k.prettify() for k in soup_list]
    # key word BREAKHERE is splitter between soups
    list_with_breaks = [m+'BREAKHERE' for m in qb_soup_list]
    compiled_list = "".join(list_with_breaks)
    with open('./pfr_scraped/qb_soup_list.txt', 'w') as file:
        file.write(compiled_list)


if __name__ == '__main__':
    htm_name_dict = get_player_htm()
    player_page_soups = scrape_page(htm_name_dict)