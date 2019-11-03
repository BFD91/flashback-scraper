# flashback-scraper
A simple webscraper to download the post histories from users of the Swedish online forum Flashback. 

Initialize by listing URLs for Flashback threads in the FB threads text file (separated by newlines), inserting your own login info in the python code, and then simply running the program. For each user posting in any of the listed threads, a csv file with that user's posts will by created. 

In accordance with the site's robots.txt, there is a 5 s delay between requests, which means the scraping is not fast. To improve the speed in future versions of the scraper, one could use the logged in account only to fetch post links, and use proxies to retrieve the posts. This would increase the speed by almost a factor of 50. 
