import json
import requests
import time
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse

request_delay=0.5
outputdir="./search/"
searchlimit=100
# https://www.noritake-itron.jp/cs/dl_spec/
base_url="https://www.noritake-itron.jp/search?page={}&limit={}" # limit 100, 50, 20

# user agent to use for requests
headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36 RuxitSynthetic/1.0 v2238161363 t3111481328944777029 athfa3c3975 altpub cvcv=2 smf=0"}

results={} # and save the results to a json file
pages={} # save the pages
session=requests.Session()

# grab search pages
page=1
print(f"grabbing page {page}...")
x = session.get(base_url.format(page, searchlimit), headers=headers)
pages[page] = x.content
y = BeautifulSoup(x.text, "html.parser")
rangestr = y.find(class_="search-result-total").text.strip()
rangestr = re.search(r"全(\d+) 件中(\d+)～(\d+)", rangestr)

rangetotal = int(rangestr[1])
rangest = int(rangestr[2])
rangeend = int(rangestr[3])

while True:
	currentrange=range((searchlimit*page)+1, (searchlimit*(page+1))+1)
	page+=1
	
	print(f"grabbing page {page}...")
	x = session.get(base_url.format(page, searchlimit), headers=headers)
	pages[page] = x.content
	
	print("current range is", currentrange)
	
	if rangetotal in currentrange:
		print("finished searching!")
		break

# extract info from search pages
product_pages=[]
for html in pages.keys():
	x = pages[html]
	y = BeautifulSoup(x, "html.parser")
	for link in y.find_all(class_="c-link"):
		x = link.get("href")
		y = urlparse(x)
		z = y[0]+y[1]+y[2]
		product_pages.append(z)
product_pages = list(dict.fromkeys(product_pages))

with open(outputdir+"products.json", "wb") as f:
	f.write(json.dumps(product_pages).encode("utf-8"))

# save html pages to disk
for html in pages.keys():
	x = pages[html]
	y = BeautifulSoup(x, "html.parser")
	z = y.find(class_="search-result-total").text.strip()
	z = re.search(r"全(\d+) 件中(\d+)～(\d+)", z)
	rangest=z[2]
	rangeend=z[3]
	
	filename = "results_{}-{}.html".format(rangest, rangeend)
	
	with open(outputdir+filename, "wb") as f:
		f.write(x)

print("done")
exit()
