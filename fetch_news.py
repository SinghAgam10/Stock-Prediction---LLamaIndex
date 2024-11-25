import xmltodict
import requests
import json
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, firestore
from bs4 import BeautifulSoup

# response = requests.get("https://timesofindia.indiatimes.com/archivelist/starttime-45533.cms")
# soup = BeautifulSoup(response.text, 'html.parser')
# soup = soup.find_all('td')
# soup = soup[4:6]
# for td in soup:
#     a_tags = td.find_all('a')
#     for a in a_tags:
#         print(f"Link: {a['href']} - Text: {a.text}")

url = "https://timesofindia.indiatimes.com/astrology/horoscope/horoscope-today-august-29-2024-read-your-todays-astrological-predictions/articleshow/112839194.cms"  # Replace with your target URL
response = requests.get(url)

# Step 2: Parse the HTML content
soup = BeautifulSoup(response.text, 'html.parser')

# Step 3: Find the <div> tag with the specific class
div_content = soup.find('div', class_='_s30J clearfix')

# Step 4: Print the content inside the <div>
if div_content:
    print(div_content.text)
else:
    print("Div with the specified class not found.")

# cred = credentials.Certificate("./key.json")
# firebase_admin.initialize_app(cred)

# start_date = datetime(2024, 6, 30)
# days_back = 300
# flag = False

# def get_news(date, offset = 0, country="in", language = "en"):
#     url = (
#         "http://api.mediastack.com/v1/news?access_key=ca5a1394ece07fec634c4def67371ef7&"
#         f"countries={country}&limit=100&languages={language}&date={date}&sort=published_desc&offset={offset}"
#     )
#     response = requests.get(url)
#     response_json = json.dumps(response.json(), indent=4)
#     response_json = json.loads(response_json)
#     print(f"Fetching done for date={date}, total articles fetched is={len(response_json['data'])}")
#     return response_json

# def delete_document(collection, document):
#     db = firestore.client()
#     doc_ref = db.collection(collection).document(document)
#     doc_ref.delete()
#     print(f"Document '{document}' deleted from collection '{collection}'.")

# def store_in_db(collection, document, data):
#     db = firestore.client()

#     doc_ref = db.collection(collection).document(document)
#     doc = doc_ref.get()
#     if doc.exists:
#         existing_data = doc.to_dict().get("articles", [])  # Get the list if it exists, otherwise use an empty list
#         if isinstance(existing_data, list):
#             existing_data.extend(data)  # Append new data to the existing list
#         else:
#             existing_data = data  # If the field isn't a list, replace it with the new data
#         doc_ref.update({"articles": existing_data})
#         print(f"Data appended to articles in {document} within {collection}.")
#     else:
#         # Document doesn't exist, create it with the new data
#         doc_ref.set({"articles": data})
#         print(f"Document created with data in articles in {document} within {collection}.")

# for i in range(days_back + 1):
#     country = "in"
#     language = "en"
#     current_date = start_date - timedelta(days=i)
#     fetch_news_for_date = current_date.strftime("%Y-%m-%d")
#     offset = 0
#     while(True):
#         try:
#             print(f"Starting fetching for date={fetch_news_for_date} with offset={offset}")
#             result = get_news(fetch_news_for_date, offset, country, language)
#             result = json.dumps(result, indent=4)
#             result = json.loads(result)
#             store_in_db("raw_news", f"date_{fetch_news_for_date}", result.get("data"))

#             pagination = result.get("pagination")
#             if offset == 1000 or (pagination["count"] + pagination['offset']) >= pagination["total"]:
#                 break
#             offset = offset + 100

#         except Exception as e:
#             print(f"Exception received is: {e}")
#             flag = True
#             break
#     if flag:
#         print(f"Exception received for date: {fetch_news_for_date} with offset: {offset}")
#         break
#     print(f"Done for date: {fetch_news_for_date}")
#     print("\n\n\n")