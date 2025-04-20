import pandas as pd
import json
import re
from ws_connect import WebScraperConnector
from datetime import datetime, timezone
import uuid
from io import StringIO
import os
from pymongo import MongoClient

# Suppress specific deprecation warnings
import warnings
from cryptography.utils import CryptographyDeprecationWarning

warnings.filterwarnings("ignore", category=CryptographyDeprecationWarning)

from dotenv import load_dotenv
from scrapfinderlabutils.aws_client.secret_manager_client import secret_manager

load_dotenv()

#connecting to webscraper api
api_token = os.getenv("WS_API_TOKEN")
ws = WebScraperConnector(api_token=api_token)

#mogodb connection
mongo_uri = secret_manager.get_secret("MONGO_URI")
mongo_name = "crawlab"
client = MongoClient(mongo_uri)
db = client[mongo_name]
# output folder for data
output_folder = "load_data"
os.makedirs(output_folder, exist_ok=True)

BASE_DIR = os.path.dirname(os.path.realpath(__file__))

#"1257746" - easypara FR, "1257745" - dosfarma ES, "1257744" - atida ES, 1263557 - farmavazquez ES,
#  1264856 - cloud10-listings
sitemap_ids = ["1257746", "1257745", "1257744",  '1263557', '1264856']
# Sitemap to collection mapping
sitemap_to_collection = {
    "easypara_price_track_final": "bayer_price_tracking",
    "dosfarma_price_check_final": "bayer_es_price_tracking",
    "atida_price_check_final": "bayer_es_price_tracking",
    "farmavazquez_price_check_final": "bayer_es_price_tracking"
    "cloud10beauty-listings": "first_aid_beauty_listing"
    
}


for sitemap_id in sitemap_ids:
    sitemap_name = ws.get_sitemap(sitemap_id)['data']['name']

    # Collection in MongoDB
    mongo_collection = sitemap_to_collection.get(sitemap_name, "test") # save to test in case no collection is found
    collection = db[mongo_collection]

    dog = f"""
                                  .-.
     (___________________________()' `-, HAU HAU
     (   ______________________   /''"`
     //\\                      //\\
     "" ""                     "" ""
           PROCESSING {sitemap_name.upper()}
"""
    print(dog)


    #mapping file
    df_map = pd.read_excel(rf"{BASE_DIR}\mapping_files\{sitemap_name}_map.xlsx")
    #latest job for a sitemap
    jobs = ws.get_scraping_jobs_by_sitemap(sitemap_id)
    latest_job = sorted(jobs['data'], key=lambda x: x['time_created'], reverse=True)[0]
    print('Latest job:', datetime.fromtimestamp(latest_job['time_created'], tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S'))
    
    #Check if the latest job is from today
    if datetime.fromtimestamp(latest_job['time_created'], tz=timezone.utc).strftime('%Y-%m-%d') != datetime.today().strftime('%Y-%m-%d'):
        print(f'Skipping {sitemap_name} as the latest job is not from today')
        continue

    latest_job_id = latest_job['id']
    #zescrapowane dane dla ostatniego job'a
    scrapped_data_json = json.dumps(ws.get_scraped_data(latest_job_id))
    df_scrapped_data = pd.read_json(StringIO(scrapped_data_json))
    
    #PROCESSING
    df_scrapped_data.rename(columns={"web-scraper-start-url":"product_link"}, inplace=True)
    df_scrapped_data.drop(columns=["web-scraper-order"], inplace=True, errors='ignore')

    # Handle optional columns
    if 'availability' in df_scrapped_data.columns:
        df_scrapped_data['availability'] = df_scrapped_data['availability'].notnull()

    if 'check_pdp_live' in df_scrapped_data.columns:
        df_scrapped_data['check_pdp_live'] = df_scrapped_data['check_pdp_live'].notnull()

    if 'old_price' in df_scrapped_data.columns:
        df_scrapped_data['old_price'] = df_scrapped_data['price'].astype(str).str.replace(r"[^\d,.]", "", regex=True).replace(",",".")

    if 'price' in df_scrapped_data.columns:    
        df_scrapped_data['price'] = df_scrapped_data['price'].astype(str).str.replace(r"[^\d,.]", "", regex=True).replace(",",".")

    df_scrapped_data['task_id'] = str(uuid.uuid4())
    
    if not "time-scraped" in df_scrapped_data.columns:
        df_scrapped_data["date"] = datetime.today().strftime('%Y-%m-%d')
    else:
        df_scrapped_data.rename(columns={'time-scraped':'date'}, inplace=True)

    df_load = pd.merge(df_scrapped_data, df_map, on='product_link', how='left')

    # Save the export file to the load_data folder
    export_file_path = os.path.join(output_folder, f"{sitemap_name}_load_{datetime.today().strftime('%Y-%m-%d')}.json")
    df_load.to_json(export_file_path, index=False, force_ascii=False, orient='records')
    print('Exported', sitemap_name,
         '\n', 'Data shape:', df_load.shape)
    # Save to MongoDB
    records = df_load.to_dict(orient='records')
    collection.insert_many(records)
    print('SAVED TO MONGO:',
          '\n', 'database:', mongo_name,
           '\n','collection:', mongo_collection,
           '\n', 'task_id:',f"'{df_load.task_id.unique()[0]}'")
    print('______________________________________________')

# Close the MongoDB connection
client.close()