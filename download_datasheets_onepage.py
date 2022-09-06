import requests
from bs4 import BeautifulSoup
import time
import re

output_dir = "./datasheets/"
request_delay = 1
request_delay = 0
overwrite_old_files=True

url = "https://www.noritake-itron.jp/cs/dl_spec/"
# user agent to use for requests
headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36 RuxitSynthetic/1.0 v2238161363 t3111481328944777029 athfa3c3975 altpub cvcv=2 smf=0"}

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


session = requests.Session()
session.headers.update(headers) # set headers for this session
main_page = session.get(url)
writeFile("index.html", output_dir, main_page.content, overwrite=overwrite_old_files)

soup = BeautifulSoup(main_page.text, "html.parser")

download_ids = []
for form in soup.find_all("form"):
	dform={}
	for input in form.find_all("input"):
		dform[input.get("name")] = input.get("value")
	download_ids.append(dform["spec_code"])

print(f"found {len(download_ids)} download forms")
unique_downloads=list(dict.fromkeys(download_ids))
print(f"found {len(unique_downloads)} unique downloads")

for download in download_ids:
	data = get_specdl_file(session, download)
	writeFile(data["filename"], output_dir, data["binary"], overwrite=overwrite_old_files)
	time.sleep(request_delay)

exit()
