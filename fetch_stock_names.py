from bs4 import BeautifulSoup
import requests
import sys
import pandas as pd
from selenium import webdriver
import time
import random
from selenium.webdriver.chrome.options import Options

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"

def get_stocks_in_sector(sector, link, df, company_count):
    print(f"Starting for sector {sector}")
    url = f"https://ticker.finology.in/sector{link}"
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)

    time.sleep(random.randint(15, 20))

    html = driver.page_source
    driver.quit()
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find("table", id="companylist").find("tbody")

    # [1] href and text
    # [4] Market cap
    table_rows = table.find_all("tr")
    if len(table_rows) < company_count:
        print(f"Fetched rows {len(table_rows)} are less than total companies in sector: {company_count}")
        sys.exit(1)

    print(f"Total rows for sector {sector} are {len(table_rows)}")
    for row in table_rows:
        try:
            table_data = row.find_all('td')
            if len(table_data) != 7:
                return
            company_link = table_data[1].find('a', href=True)['href']
            company_name = table_data[1].text
            market_cap = table_data[4].text
            ticker_symbol = company_link.split("/")[2]
        except Exception as e:
            print(f"Unexpected errors: {e}")
            sys.exit(1)

        df.loc[len(df)] = [sector, ticker_symbol, company_name, market_cap, company_link]
    print(f"Done for sector {sector}")


def main():
    df = pd.DataFrame(columns=["sector", "ticker_symbol", "company_name", "market_cap", "company_link"])
    data = pd.read_csv("./fetched-data/stock-sectors.csv")
    sectors = data.sector.values
    sector_links = data.link.values

    for sector, link in zip(sectors, sector_links):
        company_count = int(data[data.sector == sector].total_companies.values[0])
        get_stocks_in_sector(sector, link, df, company_count)
        df.to_csv("./fetched-data/stock-names.csv", index=False)

if __name__=="__main__":
    main()