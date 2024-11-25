from bs4 import BeautifulSoup
import requests
import re
import pandas as pd
import sys

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/601.3.9 (KHTML, like Gecko) Version/9.0.2 Safari/601.3.9"

def create_id(input_string):
    cleaned_string = re.sub(r'[^a-zA-Z\s]', '', input_string)
    cleaned_string = cleaned_string.strip()
    words = cleaned_string.split()
    result = '_'.join(words)
    return result

def remove_extra_spaces(input_string):
    cleaned_string = re.sub(r'[^a-zA-Z\s]', '', input_string)
    cleaned_string = cleaned_string.strip()
    return cleaned_string

def get_sectors_and_save():
    df = pd.DataFrame(columns=["sector", "description", "total_companies", "link"])
    headers = {
        "User-Agent": USER_AGENT,
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }
    url = "https://ticker.finology.in/sector"
    response = requests.get(url, headers=headers)
    response.encoding = 'utf-8'
    content = response.text
    
    soup = BeautifulSoup(content, 'html.parser')
    sector_cards = soup.find_all('div', class_='col-12 col-md-3')

    for card in sector_cards:
        sector = None
        description = None
        total_companies = None
        link = None
        if card.find('h4'):
            sector = card.find('h4').text
        if card.find('p'):
            description = card.find('p').text
        if card.find('span'):
            total_companies = card.find('span').text
        if len(card.find_all('a')):
            link = card.find_all('a', href=True)[0]['href']
        if sector == None:
            continue
        sector = create_id(sector).lower()
        description = remove_extra_spaces(description)
        total_companies = int(total_companies)
        link = link.replace("/sector", "")
        df.loc[len(df)] = [sector, description, total_companies, link]
        df.to_csv("./fetched-data/stock-sectors.csv", index=False)


def main():
    get_sectors_and_save()
    print("Done")
    sys.exit(0)

if __name__=="__main__":
    main()