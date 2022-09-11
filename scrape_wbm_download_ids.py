import requests
from download_datasheets import get_specdl_file, writeFile
from urllib.parse import urlparse
from os import listdir
from os.path import isfile, isdir, splitext, split, join
from bs4 import BeautifulSoup
import time
import sys
import asyncio
import aiohttp

def writemsg(msg):
	sys.stdout.write(msg)
	sys.stdout.flush()

def find_files(fdir, fext):
	directories = [fdir]
	files = []
	# traverse directories looking for files
	for directory in directories:
		for f in listdir(directory):
			if isfile(directory+"/"+f): files.append(directory+"/"+f)
			elif isdir(directory+"/"+f): directories.append(directory+"/"+f)
			else: print("you shouldn't be seeing this", directory, f)
	
	files2=[]
	# remove non fext files
	for file in files:
		x, extension = splitext(file)
		if extension.lower() == fext:
			files2.append(file)
	# print("found {} {} files in {}".format(len(files2), fext, fdir))
	return files2

async def download_page(session, url, retries, headers):
	await asyncio.sleep(0.5) # be nice to IA ^-^
	response_c = 600
	for attempt in range(0, retries+1):
		async with session.get(url, headers=headers) as response:
			response_c=response.status
			if response_c==200:
				writemsg('.')
				return {"page": await response.text(), "url": url}
			else: continue

async def fast_downloader(urls, retries, headers, timeout, max_concurr_downloads):
	tasks=[]
	connector = aiohttp.TCPConnector(limit=max_concurr_downloads)
	async with aiohttp.ClientSession(trust_env=True, timeout=timeout, connector=connector) as session:
		for url in urls:
			task = download_page(session, url["url"], retries, headers)
			tasks.append(task)
		tasks = await asyncio.gather(*tasks, return_exceptions=True)
	return tasks

def main():
	output_dir = "./wbm_datasheet_ids"
	normal_downloads_dir = "./products" # search this dir for downloads to skip
	cdx_url = "https://web.archive.org/cdx/search/cdx?url=noritake-itron.jp/eng/products/module*"
	wbm_url = "https://web.archive.org/web/{}/{}" # timestamp - url
	max_concurr_downloads = 10
	timeout = aiohttp.ClientTimeout(sock_connect=1.5, sock_read=30, total=1200)
	retries = 10
	
	headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36 RuxitSynthetic/1.0 v2238161363 t3111481328944777029 athfa3c3975 altpub cvcv=2 smf=0"}
	session = requests.Session()
	session.headers.update(headers)
	
	print("getting wayback machine index")
	cdx = requests.get(cdx_url, headers=headers)
	urls=[]
	for line in cdx.text.split("\n"):
		line = line.split()
		if not line: continue
		timestamp=line[1]
		url=line[2]
		status_code=line[4]
		
		parsed_url=urlparse(url)
		url_ext=splitext(parsed_url[2])[1]
		
		if url_ext: continue
		if status_code != "200": continue
		
		urls.append({"url": url, "timestamp": timestamp})
	
	print(f"grabbing {len(urls)} noritake product pages from the wayback machine")
	spec_codes=[]
	loop = asyncio.new_event_loop()
	asyncio.set_event_loop(loop)
	pages = loop.run_until_complete(fast_downloader(urls, retries, headers, timeout, max_concurr_downloads))
	
	for page in pages:
		soup = BeautifulSoup(page["page"], "html.parser")
		
		for form in soup.find_all("form"):
			spec_code = form.find_all("input")
			for input1 in spec_code:
				if input1.get("name")=="spec_code":
					spec_codes.append({input1.get("value"): page["url"]}) # dict so we don't get dupes
		time.sleep(0.5) # be nice to the IA ^-^
	writemsg('\n')
	
	print("downloading files from noritake's servers (bypass login >.>)")
	for spec_code in spec_codes:
		for key in spec_code.keys():
			spec_dl = get_specdl_file(session, key)
		spec_ext = splitext(spec_dl["filename"])
		existing_files = find_files(normal_downloads_dir, spec_ext[1])
		
		isDuplicate=False
		for file in existing_files:
			filename = split(file)[1]
			if filename==spec_dl["filename"]: # find if our file is a duplicate of one already on disk
				isDuplicate=True
				break
		if isDuplicate:
			print(f"file {spec_dl['filename']} is a duplicate, skipping...")
			continue
		else:
			print(f"writing file {spec_dl['filename']} to disk...")
			writeFile(spec_dl['filename'],
			output_dir+urlparse(spec_code[key])[2],
			spec_dl['binary'])
		time.sleep(0.5) # be nice to noritake ^-^

if __name__ == "__main__":
	try:
		main()
	except KeyboardInterrupt:
		print("interrupted!")
