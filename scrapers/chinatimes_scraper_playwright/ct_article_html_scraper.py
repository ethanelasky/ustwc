"""
Scrapes text from articles on the China Times' online newspaper website. 
See the docstring of scrape_text_from_page for more info. 

Usage: python ct_article_scraper.py [path_to_urls] [output_file_name]

Ex: python ct_article_scraper.py ct_2013_links.json 
                                    ct_2013_article_contents.csv
"""

import asyncio
import glob
import os
import pandas as pd
from playwright_stealth import stealth_async
from playwright.async_api import async_playwright
import re
import sys
from scipy import stats
import zipfile

async def scrape_html(index_url_pairs):
    """ 
    Scrapes article HTML from webpages given a list of URLs.
    
    Inputs: 
    - A list of URLs (as strings)

    Outputs:
    - HTML files that each represent one article. 
    """

    path_to_extension = "./uBlock"
    user_data_dir = "/tmp/test-user-data-dir"
    ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'

    async with async_playwright() as p:

        async def new_context():
            context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            user_agent=ua,
            args=[
                f"--disable-extensions-except={path_to_extension}",
                f"--load-extension={path_to_extension}",
            ],
            )
            return context
        async def new_page(context): 
            page = await context.new_page()
            await stealth_async(page)
            return page

        context = await new_context()
        page = await new_page(context)
        forbidden_count = 0

        for i in range(len(index_url_pairs)):
            if i % 50 == 49:
                await page.close()
                await context.close()
                context = await new_context()
                page = await new_page(context)
                print("Created new page and context as scheduled")
            pair = index_url_pairs[i]
            index = pair[0]
            url = pair[1]
            j = 0
            while True:
                try:
                    resp = await page.goto(url)      
                except:
                    sleep_duration = stats.beta.rvs(5, 1) + 15
                    await asyncio.sleep(sleep_duration)
                    print("waiting for page to load", sleep_duration)
                    j += 1
                    if j == 10:
                        j = 0
                        await page.close()
                        await context.close()
                        context = await new_context()
                        page = await new_page(context)
                        print("Created new page and context from error state")
                    continue
                break
                
            if resp.status == 403 or resp.status == 502:
                forbidden_count += 1
                print(f"Received {resp.status}. Skipping page {index}.")
                if forbidden_count > 10:
                    print("Too many denials. Halting crawl.")
                    break

            else: 
                contents = await page.content()
                with open(str(index) + ".html", 'w', encoding="utf-8") as f:
                    f.write(contents)
                    print(f"Wrote {index} to file.")

            sleep_duration = stats.beta.rvs(1, 5) + 9
            print("Between pages. Wait time: ", sleep_duration)
            await asyncio.sleep(sleep_duration)

        await context.close()

        if i == len(index_url_pairs):
            html_files = glob.glob('*.html')
            zip_file_name = re.search("[^\.]+", sys.argv[1])[0] + ".zip"
            
            with zipfile.ZipFile(zip_file_name, 'w') as zipf:
                for file in html_files:
                    zipf.write(file)

            for file in html_files:
                os.remove(file)
            
            print("Scrape complete. All HTML files have been zipped into ", zip_file_name, " and deleted.")

        

if sys.argv[1][:-3] == ".csv":
    df = pd.read_csv(sys.argv[1], index_col=0)
    if len(sys.argv) == 3:
        df = df.loc[int(sys.argv[2]):, :]
    indices = df.index
    links = df['link'].values
    index_url_pairs = list(zip(indices, links))
else:
    df = pd.read_parquet(sys.argv[1])
    if len(sys.argv) == 3:
        df = df.loc[int(sys.argv[2]):, :]
    indices = df.index
    links = df['link'].values
    index_url_pairs = list(zip(indices, links))
print(df)

asyncio.run(scrape_html(index_url_pairs))