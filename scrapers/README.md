This readme elaborates on my thesis paper's Appendix A with regards to data scraping and processing.

## Data collection and processing

The pipeline follows three general steps, regardless of newspaper. First, I collected links to all articles from within the given timeframe (Feb 2021-Jan 2024, three complete years). Then, I collected page HTMLs, and then scraped their contents.

Attached to this project are open-source versions of links to all articles and data scraping tools with my configurations (unfortunately, uploading the article contents themselves would breach fair use).

## General tools and rationale for use

### Scrapy

I started using Scrapy after finding BeautifulSoup insufficient for my web scraping needs. Built into Scrapy are customizable request delays that make your website traffic look more realistic (i.e. less like a robot, which Cloudflare will ban at the first chance). I used it for the Liberty Times website, although I switched to Playwright because Scrapy is unable to pass JavaScript challenges.

### Playwright

[Playwright](https://playwright.dev) is Microsoft's webapp testing software. It makes for a great scraping tool. I used the asynchronous version to time request delays better. I used headful mode (i.e. `headless=False`), meaning the actually browser loaded every link whose HTML I grabbed. I implemented request delays for each site I scraped, whose time in seconds followed a $\text{Gamma}(5,1) + C$ distribution ($C_{CT} = 9; C_{UD} = 4$). I used Chromium with the uBlock Origin extension as my Playwright browser to avoid frequent ad-related timeouts. I also created a new browser instance every 25-50 requests (depending on the power of my computer). Finally, I used `playwright-stealth`. Automated browsers (e.g. ones used in Playwright) will sometimes send a website a message that they are being "driven" by a program. `playwright-stealth` masks this WebDriver message.

These measures ensured that websites saw my computers as humans and not as automated traffic (which would warrant a ban). Each of these is necessary and only in combination is sufficient to scrape high volumes of bot-unfriendly pages. 

### Wayback Machine
Internet Archive's Wayback Machine was unreasonably helpful for speeding up scrapes. They allow for 1 request/second, far faster than the websites I was scraping, and they always a majority of the articles I wanted. I used the [wayback API](https://wayback.readthedocs.io/en/stable/) to access these articles. `wayback_retriever` contains my work for this section.


### Avoiding rate-limiting

Rate limiting happens when a computer sends too many requests within a given span of time. This often results in a temporary ban of a few hours to days and is either enforced by the website (e.g. The Liberty Times' NGINX server instance) or a DNS provider (e.g. The China Times). Aside from everything I detailed above with respect to browser and scraper choice, there were a few other choices I made to avoid a ban. First, I spread out requests -- I bought two Raspberry Pi's and borrowed compute and network resources from friends and family to avoid sending too many requests from a single IP. I used RustDesk, an open-source remote desktop control software, to supervise my six computers. Second, I did not use data centers to send requests -- this would have been a feasible alternative had the websites I was scraping been friendly to scraping, but because they weren't, they would have been flagged by Cloudflare for having insufficient IP reputation.


## Process by website

### The Liberty Times
- Links: Scraped the website's article search page available at [search.ltn.com.tw](search.ltn.com.tw) using the search query ‘的' (the most frequent word in Chinese; more frequent than "the", the most frequent word in English). My work for this is contained in the `ltn_link_scraper` folder within `scrapers`. It is a Scrapy spider that iteratively searches for '的' one day at a time, going through  all pages of search results and grabbing all article links served. The LTN search has a limit of 10,000 articles, but searching by day resolves this as only a small number of (usually <750) articles were published each day.

- HTMLs: Scrapy. Refer to `ltn_html_getter`.
- Article contents: BeautifulSoup.


### The China Times
- Links: I scraped the website's sitemaps with Playwright. I scraped the AMP sitemap, available at [https://chinatimes.com/sitemaps/sitemap_article_all_index_amp_0.xml](https://chinatimes.com/sitemaps/sitemap_article_all_index_amp_0.xml). I scraped the AMP sitemap because of its less storage-intensive and more consistent format.
- HTMLs: Playwright and Wayback Machine. The China Times website had the strictest rate limit by far, at 9 seconds/request, so I used the Wayback Machine to get a plurality of the articles first and then used Playwright for the rest.
- Article contents: BeautifulSoup. 

### The United Daily
- Links: Scraped the website's sitemap (available at [https://udn.com/sitemapxml/news/mapindex.xml](https://udn.com/sitemapxml/news/mapindex.xml)) with Playwright. 
Articles: Playwright (headless) or Wayback Machine, depending on year. As of the time of writing, the United Daily 404’s links to articles older than one year (e.g. before Feburary 2023). For this newspaper, I have access to all non-erroring news articles on the United Daily website (which currently go back to 2023) as well as Wayback Machine HTMLs for all available archived articles.
- HTMLs: Playwright
- Article contents: BeautifulSoup

### Processing

After I had my zipped files (stored in `tar.xz` (preferred), `zip`, and `7z`), I transferred the files to my advisor's server and then to my computer to process. I unzipped the files, processed them into the directory/HTML structure if necessary (CT and UD data were already like this from how I set up their scrapers in Playwright, although I wrote `de_csv_ltn.py` for LT articles), and then used the respective `parse_<newspaper>.py` to convert a directory of HTMLs to a CSV file containing the processed contents. I then manually cut out a few straggling articles violating my corpus period (i.e. before Feb 1, 2020 or after Jan 31, 2024). Then, I used `drop_duplicates` within each paper's corpus to remove redundant articles, which cut my corpus down significantly (e.g. many China Times articles are duplicated with different referring URLs).

### Edge cases
The print media outlets I followed sometimes published multimedia articles. If an article was not accompanied by text (above and beyond photo captions, e.g. [this](https://udn.com/news/story/7328/7448580)) and solely consisted of a title and one or more photos or videos, I removed it from the dataset.

Occasionally, I would encounter 502 or 403 errors. These were signs that I had just hit a rate-limit, so when this happened I halted the crawl and manually recrawled the erroring articles. Sometimes, however, I would encounter "random" 502s in the middle of a successful crawl, and recrawling would produce the same error. I removed these errant 502s from the dataset.

I also excluded all 404 error pages (and similar Page Not Found errors, e.g. "抱歉，目前無法找到任何頁面"), links that redirect to the title page, and pages which had nonsensical dates ([example](https://ec.ltn.com.tw/article/breakingnews/4175363) article that has date 1970/01/01). Finally, I excluded pages whose metadata nor content listed a publication date. These were few in number (<100 for the entire corpus). 


