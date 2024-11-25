from firebase_admin import credentials, firestore
import firebase_admin
import json
import sys

cred = credentials.Certificate("./key.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

collection_ref = db.collection('toi_news_2024-10-22')

docs = collection_ref.stream()
doc_list = list(docs)

total_size_bytes = 0

for doc in doc_list:
    doc_dict = doc.to_dict()
    doc_json = json.dumps(doc_dict)
    doc_size = sys.getsizeof(doc_json)
    total_size_bytes += doc_size

    print(f'{doc.id} => {doc_size} bytes')

# Convert total size to KB and MB
total_size_kb = total_size_bytes / 1024
total_size_mb = total_size_kb / 1024

# Print total size
print(f'Total size of all documents: {total_size_bytes} bytes')
print(f'Total size in KB: {total_size_kb:.2f} KB')
print(f'Total size in MB: {total_size_mb:.2f} MB')