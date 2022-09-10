import requests
import json
from bs4 import BeautifulSoup
import os
import time
from urllib.parse import urlparse
from os.path import isfile, split, normpath
import re

def writeFile(filename, path, binary, overwrite=False):
	if overwrite:
		print(f"writing {filename}")
		with open(path+filename, "wb") as f:
			f.write(binary)
		return
	elif not isfile(path+filename):
		print(f"writing {filename}")
		with open(path+filename, "wb") as f:
			f.write(binary)
		return
	else: return ZeroDivisionError

def get_specdl_file(session, download_id):
	#reset cookies
	session.cookies = requests.cookies.RequestsCookieJar()
	
	download_body = {
		"_method": "POST",
		"spec_code": download_id,
	}
	
	logindownload_body = {
		"_method": "POST",
		"spec_code": download_id,
		"catalog": "0",
		"demo": "0",
		"webdemo": "0",
		"mitsumori": "0",
		"message": "",
		"download": "agree and download",
	}
	
	download = session.post("https://www.noritake-itron.jp/spec/download/", data=download_body, allow_redirects=False)
	
	if download.status_code == 200:
		filename = re.search(r"filename=\"([a-zA-Z0-9\-_\.]+)\"", download.headers["Content-Disposition"])[1]
		return {"binary": download.content, "filename": filename}
	elif download.status_code == 302:
		print(f"{download_id} tried to redirect")
		
		# might have to clear headers after this to do more of these loginwalled downloads? (make new sessions?)
		logindownload = session.post("https://www.noritake-itron.jp/spec/download/", data=logindownload_body, allow_redirects=False)
		
		file = session.get("https://www.noritake-itron.jp/spec/spec_dl_func")
		try:
			filename = re.search(r"filename=\"([a-zA-Z0-9\-_\.\(\)]+)\"", file.headers["Content-Disposition"])[1]
		except:
			print(file.headers)
			print(file.status_code)
			exit()
		
		return {"binary": file.content, "filename": filename}
	else:
		print(download.content)
		print(download.headers)
		print(download.status_code)
		exit()

def main():
	
	output_dir = "." # no trailing slash
	request_delay = 0.5
	request_delay = 1
	overwrite_old_files=True
	product_list_offset = 0

	# user agent to use for requests
	headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36 RuxitSynthetic/1.0 v2238161363 t3111481328944777029 athfa3c3975 altpub cvcv=2 smf=0"}
	baseurl="https://www.noritake-itron.jp"
	input_products = "./search/products.json"
	with open(input_products, "r+") as f:
		products = json.loads(f.read())
		products=products[product_list_offset:]
	
	session = requests.Session()
	session.headers.update(headers) # set headers for this session
	for product_category in products:
		
		# create product directory
		try:
			os.makedirs(output_dir+product_category)
		except FileExistsError:
			pass
		
		# get product index
		product_url = baseurl+product_category
		product_cat_short = normpath(urlparse(product_url)[2]).split(os.sep)[-1:][0]
		print("downloading product line", product_cat_short)
		webpage = session.get(product_url, allow_redirects=False)
		tstart=time.time()
		if webpage.status_code == 200: pass
		elif webpage.status_code == 302:
			print(f"product {product_cat_short} tried to redirect, skipping...")
			continue
		else:
			print("unknown request status code")
			print(webpage.status_code)
			exit()
		soup = BeautifulSoup(webpage.text, "html.parser")
		
		models = soup.find_all(class_="detail-lineup-box-c")
		
		downloadforms={}
		for form in soup.find_all("form"):
			href = form.get("action")
			post_id = form.get("name")
			downloadform={"href": href}
			
			for input in form.find_all("input"):
				key = input.get("name")
				value = input.get("value")
				downloadform[key]=value
			
			downloadforms[post_id] = downloadform
		
		displaymodels=[]
		for model in models:
			downloads=[]
			images=[]
			
			modelname=model.find(class_="detail-lineup-name").text
			
			for box in model.find_all(class_="detail-lineup-box-l"):
				for image in box.find_all("img"):
					images.append({"href": image.get("src"), "name": image.get("alt")})
			
			for box in model.find_all(class_="detail-lineup-box-l"):
				for download in box.find_all("a"):
					if download.get("class") == None: continue
					post_id = re.search(r"\.([_a-z0-9]+)\.", download.get("onclick"))[1]
					name = download.get("title")
					spec_download = {"post_id": post_id, "name": name}
					downloads.append(spec_download)
			
			displaymodel = {"name": modelname, "spec_downloads": downloads, "images": images}
			displaymodels.append(displaymodel)
		
		# write webpage file to disk if it doesn't exist
		writeFile("index.html", output_dir+product_category, webpage.content, overwrite=overwrite_old_files)
		
		displays_info = {"displays": displaymodels, "downloads": downloadforms}
		writeFile("displays.json", output_dir+product_category, json.dumps(displays_info).encode("utf-8"), overwrite=overwrite_old_files)
		
		# download images and downloads?
		for display in displaymodels:
			for image in display["images"]:
				print(image["href"])
				filename = image["name"]
				if filename=="": filename=normpath(urlparse(image["href"])[2]).split(os.sep)[-1:][0]
				if not overwrite_old_files:
					if isfile(output_dir+product_category+filename):
						print(f"file {filename} exists, skipping...")
						continue # skip display if file exists and we overwrites disabled
				data = session.get(baseurl+image["href"])
				if data.status_code==404: continue
				writeFile(filename, output_dir+product_category, data.content, overwrite=overwrite_old_files)
				time.sleep(request_delay) # wait between requests
				
		
		# get downloads here
		# can't skip duplicate downloads because you don't get filename until you make the post request
		# (well I could but I'd have to keep a separate dict or name the files differently, etc..)
		print(f"{len(downloadforms)} download forms found")
		unique_downloads=[]
		for download in downloadforms:
			download=downloadforms[download]
			unique_downloads.append(download["spec_code"])
		unique_downloads=list(dict.fromkeys(unique_downloads))
		print(f"{len(unique_downloads)} unique downloads found")
		
		for spec_code in unique_downloads:
			file = get_specdl_file(session, spec_code)
			writeFile(file["filename"], output_dir+product_category, file["binary"], overwrite=overwrite_old_files)
			time.sleep(request_delay) # wait between "requests" (lol the getspecdlfile func makes 1-3 rq/"request")
		
		time.sleep(request_delay) # wait between requests

if __name__ == "__main__":
	main()
