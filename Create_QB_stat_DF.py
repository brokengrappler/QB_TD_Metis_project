

def get_big_table(soup_list):
    # for each soup (aka players page), return big_table to get_stats and get_headers
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
    stat_table = table[0].find_all('tr', class_='full_table')
    for ele in stat_table:
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
    # test_player is
    TEST_SOUP = scrape_page(test_player)
    headers = get_headers(TEST_SOUP)
    pass

'''
NOT SURE YET IF I'M GOING TO DO THIS IN THIS MODULE AND IF THIS IS HOW I WANT TO DO IT

def create_player_csv(player_stat):
    csv_file = 'player_name.csv'
    with open(csv_file, 'w') as csvfile:
        csvfile.write(','.join(headers) + '\n')
        for key, value in stats.items():
            csvfile.write(key + ',' + ','.join(value) + '\n')
'''