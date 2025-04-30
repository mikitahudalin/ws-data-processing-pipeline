# WebScraper Data Pipeline

This project is a mini ETL (Extract, Transform, Load) pipeline for collecting data using the [WebScraper.io](https://webscraper.io/) API, transforming it, and loading it into MongoDB for further analysis or storage.

## 📂 Project Structure

- `main.py` — Orchestrates the pipeline: fetches data from WebScraper API, applies transformations, saves JSON files, and inserts into MongoDB.
- `ws_connect.py` — API client for interacting with WebScraper.io (retrieving sitemaps, scraping jobs, and scraped data).
- `mapping_files/` — Excel mapping files used to enrich the scraped data (`*_map.xlsx`).
- `load_data/` — Output directory where cleaned data is saved as JSON.
- `.env` — Environment variables for API tokens.


### What It Does

1. Connects to the WebScraper API.
2. Retrieves the latest job data for each sitemap ID.
3. Validates that the job is from today.
4. Downloads the scraped JSON data and processes it:
   - Cleans price fields.
   - Fills missing flags (`availability`, `check_pdp_live`).
   - Enriches with mapping data.
5. Saves results to `load_data/<sitemap>_load_<date>.json`.
6. Inserts records into the appropriate MongoDB collection.

## 🔐 Secrets & Authentication

- MongoDB connection string is stored in AWS Secrets Manager under the name `MONGO_URI`. (could be changed)
- WebScraper API token is read from `.env`. (could be changed)


## 🛠️ Notes

- If no mapping file exists for a sitemap, the script will likely fail.
- Scraped data is only processed if the latest job was run **today**.
- Unmapped sitemap names default to the "test" collection in MongoDB.
