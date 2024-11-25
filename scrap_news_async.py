from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta
from firebase_admin import credentials, firestore
import firebase_admin
import time
import random
import asyncio
import aiohttp
import sys

current_date = datetime(2024, 9, 13)
page_suffix = 45548

cred = credentials.Certificate("./key.json")
firebase_admin.initialize_app(cred)


def get_all_news(i):
    user_agents = [
        # "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/89.0",
        # Add more user agents here
    ]
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/89.0",
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
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/89.0",
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

async def fetch(url, headline, session, date):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }
    try:
        async with session.get(url, headers = headers) as response:
            if response.status == 200:
                response.encoding = 'utf-8'  # Example of setting a different encoding
                content = await response.text()
                soup = BeautifulSoup(content, 'html.parser')
                div_content = soup.find('div', class_='_s30J clearfix')

                if div_content:
                    content = div_content
                    content = content.text
                    tags, article_number = fetch_tags(url)
                    news_json = get_article_as_json(url, headline, content, tags)
                    try:
                        add_news_to_firebase(f"toi_news_{date}", f"article_{article_number}", news_json)
                        return True
                    except Exception as e:
                        print(f"Unable to add data to firestore DB for date: {date} with error: {e}")
                        sys.exit(1)
                else:
                    print("Div with the specified class not found.")
            else:
                print(f"Failed to fetch {url}. Status code: {response.status}")
                return None
            
    except Exception as e:
        print(f"An error occurred for {url}: {e}")
        return None
    
async def fetch_all(link_headlines_tuples, date):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for (link, headline) in link_headlines_tuples:
            tasks.append(fetch(link, headline, session, date))
        # Gather all the tasks and wait for them to finish
        responses = await asyncio.gather(*tasks)
        return responses


for i in range(page_suffix, 40086, -1):
    start_time  = time.time()
    scrap_news_for_date = current_date.strftime("%Y-%m-%d")
    print(f"Starting scraping for date: {scrap_news_for_date} with suffix: {i}")
    try:
        link_headlines_tuples = get_all_news(i)
    except Exception as e:
        print(f"Current date is: {scrap_news_for_date} and numerical page number is: {i}")
        print(f"Exception caught while calling get_all_news: {e}")
    asyncio.run(fetch_all(link_headlines_tuples, scrap_news_for_date))

    
    print(f"Done for date: {scrap_news_for_date}!")
    current_date = current_date - timedelta(days=1)
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Time taken to run the function: {elapsed_time:.4f} seconds")
    print("\n\n")