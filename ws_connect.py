import requests
import json
import os
from dotenv import load_dotenv

"""
By default, each user has a limit of 200 API calls per 15 minutes.
"""

load_dotenv()


class WebScraperConnector:
    def __init__(self, api_token=None):
        if api_token is not None:
            self.api_token = api_token
        else:
            self.api_token = os.getenv("API_TOKEN")
        if self.api_token is None:
            raise ValueError("API token not found")

    def get_sitemap(self, sitemap_id):
        # ws.get_sitemap("1165658")
        url = f"https://api.webscraper.io/api/v1/sitemap/{sitemap_id}?api_token={self.api_token}"
        response = requests.get(url)
        return response.json()
    
    def get_sitemaps(self):
        url = f"https://api.webscraper.io/api/v1/sitemaps?api_token={self.api_token}"
        response = requests.get(url)
        return response.json()
    
    def update_sitemap(self, sitemap_id, data: dict):
        """
        {
            "_id": "webscraper-io-landing",
            "startUrl": [
                "http://webscraper.io/"
            ],
            "selectors": [
                {
                    "parentSelectors": [
                        "_root"
                    ],
                    "type": "SelectorText",
                    "multiple": false,
                    "id": "title",
                    "selector": "h1",
                    "regex": "",
                    "delay": ""
                }
            ]
        }
        """
        url = f"https://api.webscraper.io/api/v1/sitemap/{sitemap_id}?api_token={self.api_token}"
        response = requests.put(url, json=data)
        return response.json()
    
    def delete_sitemap(self, sitemap_id):
        url = f"https://api.webscraper.io/api/v1/sitemap/{sitemap_id}?api_token={self.api_token}"
        response = requests.delete(url)
        return response.json()
    
    def create_sitemap(self, data: dict):
        """
        {
            "_id": "webscraper-io-landing",
            "startUrl": [
                "http://webscraper.io/"
            ],
            "selectors": [
                {
                    "parentSelectors": [
                        "_root"
                    ],
                    "type": "SelectorText",
                    "multiple": false,
                    "id": "title",
                    "selector": "h1",
                    "regex": "",
                    "delay": ""
                }
            ]
        }
        """
        url = f"https://api.webscraper.io/api/v1/sitemap?api_token={self.api_token}"
        response = requests.post(url, json=data)
        return response.json()
    
    def create_scraping_job(self, data: dict):
        """
        {
            "sitemap_id": 123,
            "driver": "fast", // "fast" or "fulljs"
            "page_load_delay": 2000,
            "request_interval": 2000,
            "proxy": 0, // 0: No proxy, 1: Use proxy, 123: Custom proxy id, 'residential-*': Use residential proxy, replace * with country code, for example, 'residential-us'
            "start_urls": [		// optional, if set, will overwrite sitemap start URLs
                "https://www.webscraper.io/test-sites/e-commerce/allinone/computers",
                "https://www.webscraper.io/test-sites/e-commerce/allinone/phones"
            ],
            "custom_id": "custom-scraping-job-12" // optional, will be included in webhook notification
        }
        """
        url = f"https://api.webscraper.io/api/v1/scraping-job?api_token={self.api_token}"
        response = requests.post(url, json=data)
        return response.json()
    
    def get_scraping_jobs_by_sitemap(self, sitemap_id):
        url = f"https://api.webscraper.io/api/v1/scraping-jobs?sitemap_id={sitemap_id}&api_token={self.api_token}"
        response = requests.get(url)
        return response.json()
    
    def get_scraping_job(self, job_id):
        url = f"https://api.webscraper.io/api/v1/scraping-job/{job_id}?api_token={self.api_token}"
        response = requests.get(url)
        return response.json()
    
    def get_scraped_data(self, job_id):
        url = f"https://api.webscraper.io/api/v1/scraping-job/{job_id}/json?api_token={self.api_token}"
        response = requests.get(url)
        return json.loads(
            "["+",".join([row for row in response.content.decode("utf-8").split("\n") if row])+"]"
        )
    
    def create_split_scraping_job(self, data: dict, urls: list, batch_size=10):
        """
        {
            "sitemap_id": 123,
            "driver": "fast", // "fast" or "fulljs"
            "page_load_delay": 2000,
            "request_interval": 2000,
            "proxy": 0, // 0: No proxy, 1: Use proxy, 123: Custom proxy id, 'residential-*': Use residential proxy, replace * with country code, for example, 'residential-us'
            "start_urls": [		// optional, if set, will overwrite sitemap start URLs
                "https://www.webscraper.io/test-sites/e-commerce/allinone/computers",
                "https://www.webscraper.io/test-sites/e-commerce/allinone/phones"
            ],
            "custom_id": "custom-scraping-job-12" // optional, will be included in webhook notification
        }
        """

        batches = [urls[i:i+batch_size] for i in range(0, len(urls), batch_size)]

        response_jsons = []

        for batch in batches:
            data["start_urls"] = batch
            response = self.create_scraping_job(data)
            response_jsons.append(response)

        return response_jsons


if __name__ == "__main__":
    ws = WebScraperConnector()
    with open("results.json", "w") as file:
        json.dump(ws.get_scraped_data("22966226"), file, indent=4)
    