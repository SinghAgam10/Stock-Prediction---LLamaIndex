import boto3
from botocore.exceptions import ClientError
import uuid
import sys
from datetime import datetime, timedelta
import time
import aiohttp
from bs4 import BeautifulSoup
import asyncio
import requests
import pandas as pd

TABLE_NAME = "NewsArticles"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/601.3.9 (KHTML, like Gecko) Version/9.0.2 Safari/601.3.9"

def check_if_table_exist(client):
    try:
        # Fetch the list of all tables
        response = client.list_tables()

        # Get the table names from the response
        table_names = response.get('TableNames', [])

        # Print all table names
        if table_names and TABLE_NAME in table_names:
            print("Table already exist.")
            return True
        else:
            print("No tables found in this region.")
            return False
    except ClientError as e:
        print(f"Failed to list tables: {e.response['Error']['Message']}")
        sys.exit(1)

def create_table(client):
    try:
        if check_if_table_exist(client):
            return True
        # Create the DynamoDB table
        table = client.create_table(
            TableName=TABLE_NAME,  # Your table name
            KeySchema=[
                {
                    'AttributeName': 'id',  # Primary key
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'id',
                    'AttributeType': 'S'  # String for UUID
                },
                # Add other attributes here if you plan to use them as indexes
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 25,
                'WriteCapacityUnits': 25
            }
        )

        # Wait until the table exists before proceeding
        table.wait_until_exists()

        print("Table created successfully.")

    except ClientError as e:
        print(f"Failed to create table: {e.response['Error']['Message']}")
        sys.exit(1)


def get_all_news(i):
    headers = {
        "User-Agent": USER_AGENT,
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


def fetch_tags(link):
    splits = link.split("/")
    tags = splits[3:-3]
    return tags, splits[-1].replace(".cms", "")

def add_news_article_to_dynamodb(client, link, headline, content, tags, article_number, date_of_pub):
    table = client.Table(TABLE_NAME)
    retries = 5
    for i in range(retries):
        try:
            item = {
                'id': str(uuid.uuid4()),  # Generate a UUID for the 'id' field
                'date': str(date_of_pub),  # Date as a string
                'article_number': str(article_number),
                'link': link,
                'headline': headline,
                'content': content,
                'tags': tags  # Array of strings
            }
            table.put_item(Item=item)
            break
        except ClientError as e:
            if e.response['Error']['Code'] == 'ProvisionedThroughputExceededException':
                print("Throttled! Retrying...")
                time.sleep(2 ** i)  # Exponential backoff
            else:
                print(f"Error inserting item: {e}")
                break
        except Exception as e:
            print(f"Error inserting item to DB with error: {e}")
            sys.exit(1)
            break

async def fetch(url, headline, session, client=None, df=None):
    headers = {
        "User-Agent": USER_AGENT,
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }
    try:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                response.encoding = 'utf-8'  # Example of setting a different encoding
                content = await response.text()
                soup = BeautifulSoup(content, 'html.parser')
                div_content = soup.find('div', class_='_s30J clearfix')
                date_time = soup.find('div', class_="xf8Pm byline").text
                date_time = date_time.split('/')[-1]
                if div_content:
                    content = div_content
                    content = content.text
                    tags, article_number = fetch_tags(url)
                    try:
                        if client is not None:
                            add_news_article_to_dynamodb(client, url, headline, content, tags, article_number, date_time)
                        if df is not None:
                            df.loc[len(df)] = [headline, url, content, date_time, tags, article_number]
                        return True
                    except Exception as e:
                        print(f"Unable to add data to Dynamo DB for date: {date} with error: {e}")
                        sys.exit(1)
                else:
                    print("Div with the specified class not found.")
            elif response.status == 410 or response.status == 404:
                return None
            else:
                print(f"Failed to fetch {url}. Status code: {response.status}")
                sys.exit(1)
                return None
            
    except Exception as e:
        print(f"An error occurred for {url}: {e}")
        return None
    
async def fetch_all(link_headlines_tuples, client=None, df=None):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for (link, headline) in link_headlines_tuples:
            tasks.append(fetch(link, headline, session, client,  df))
        # Gather all the tasks and wait for them to finish
        responses = await asyncio.gather(*tasks)
        return responses
    
def scrap_news(page_suffix, client=None, df=None):
    for i in range(page_suffix, page_suffix-1, -1):
        start_time  = time.time()
        print(f"Starting scraping for suffix: {i}")
        try:
            link_headlines_tuples = get_all_news(i)
        except Exception as e:
            print(f"Exception caught while calling get_all_news with error: {e}")
            
        asyncio.run(fetch_all(link_headlines_tuples, client, df))

        
        print("Done!")
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Time taken to run the function: {elapsed_time:.4f} seconds")
        print("\n\n")


def main():
    dynamodb = None
    # dynamodb = boto3.client('dynamodb', region_name='us-east-1')  # e.g., 'us-east-1'
    # create_table(dynamodb)

    # dynamodb = boto3.resource('dynamodb')

    news_articles_for_day = pd.DataFrame(columns=["headline", "url", "content", "date_time", "tags", "article_number"])
    cms_number = 45594
    scrap_news(cms_number, dynamodb, news_articles_for_day)
    news_articles_for_day.to_csv("./fetched-data/news_articles_for_today.csv", index=False)

if __name__=="__main__":
    main()