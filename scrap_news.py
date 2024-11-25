from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta
from firebase_admin import credentials, firestore
import firebase_admin
import time
import random

current_date = datetime(2024, 10, 4)
page_suffix = 45569

cred = credentials.Certificate("./key.json")
firebase_admin.initialize_app(cred)


def get_all_news(i):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }
    url = f"https://timesofindia.indiatimes.com/archivelist/starttime-{i}.cms"
    response = requests.get(url, headers=headers)
    response.encoding = 'utf-8'  # Example of setting a different encoding
    content = response.text
    
    soup = BeautifulSoup(content, 'html.parser')
    soup = soup.find_all('td')
    soup = soup[4:6]
    link_headlines_tuples = []
    for td in soup:
        a_tags = td.find_all('a')
        for a in a_tags:
            link = ""
            if "https" in a['href'] or "http" in a['href']:
                link = a['href']
            else:
                link = f"https://timesofindia.indiatimes.com{a['href']}"
            headline = a.text
            link_headlines_tuples.append((link, headline))
    return link_headlines_tuples

def get_single_news_content(link):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }
    response = requests.get(link, headers=headers)
    response.encoding = 'utf-8'  # Example of setting a different encoding
    content = response.text
    soup = BeautifulSoup(content, 'html.parser')
    div_content = soup.find('div', class_='_s30J clearfix')

    if div_content:
        content = div_content
        return content.text
    else:
        print("Div with the specified class not found.")

def fetch_tags(link):
    splits = link.split("/")
    tags = splits[3:-3]
    return tags, splits[-1].replace(".cms", "")

def get_article_as_json(link, headline, content, tags):
    news_data = {
        "link": link,
        "headline": headline,
        "content": content,
        "tags": tags
    }
    return news_data

def add_news_to_firebase(collection, document, data):
    db = firestore.client()

    doc_ref = db.collection(collection).document(document)
    doc_ref.set(data)
    
for i in range(page_suffix, 40086, -1):
    time.sleep(random.uniform(1, 2))
    scrap_news_for_date = current_date.strftime("%Y-%m-%d")
    print(f"Starting scraping for date: {scrap_news_for_date} with suffix: {i}")
    try:
        link_headlines_tuples = get_all_news(i)
    except Exception as e:
        print(f"Current date is: {scrap_news_for_date} and numerical page number is: {i}")
        print(f"Exception caught while calling get_all_news: {e}")
    print(f"Starting fetching content for news for date: {scrap_news_for_date}")
    for link_headline in link_headlines_tuples:
        if (link_headline[0] is None):
            print(f"Link is None, skipping article for date: {scrap_news_for_date}")
            continue
        try:
            link = link_headline[0]
            headline = link_headline[1]
            content = get_single_news_content(link)
            tags, article_number = fetch_tags(link)
            news_json = get_article_as_json(link, headline, content, tags)

            try:
                add_news_to_firebase(f"toi_news_{scrap_news_for_date}", f"article_{article_number}", news_json)
            except Exception as e:
                print(f"Unable to add data to firestore DB for date: {scrap_news_for_date} with error: {e}")
        except Exception as e:
            print(f"Current date is: {scrap_news_for_date} and numerical page number is: {i} and link: {link_headline[0]}")
            print(f"Exception caught while calling get_single_news_content: {e}")

    
    print(f"Done for date: {scrap_news_for_date}!")
    current_date = current_date - timedelta(days=1)