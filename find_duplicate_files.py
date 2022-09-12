from os import listdir
from os.path import isfile, isdir, splitext, split, join
import sys
import hashlib

def find_files(fdir, fext=None):
	directories = [fdir]
	files = []
	# traverse directories looking for files
	for directory in directories:
		for f in listdir(directory):
			if isfile(directory+"/"+f): files.append(directory+"/"+f)
			elif isdir(directory+"/"+f): directories.append(directory+"/"+f)
			else: print("you shouldn't be seeing this", directory, f)
	
	# remove non fext files
	if fext:
		files2=[]
		for file in files:
			x, extension = splitext(file)
			if extension.lower() == fext:
				files2.append(file)
		files=files2
	
	# print("found {} {} files in {}".format(len(files2), fext, fdir))
	return files

def main():
	input_dirs = [
		"G:/2022.09.01 noritake datasheet downloads/download-noritake-jp-datasheets/products",
		"G:/2022.09.01 noritake datasheet downloads/download-noritake-jp-datasheets/wbm_datasheet_ids"
	]
	
	# find files in the directories
	all_files=[]
	for fdir in input_dirs:
		all_files+=find_files(fdir)
	print(f"{len(all_files)} files")
	
	# hash all the files
	i=0
	hashes={}
	for file in all_files:
		print(f"hashing file {i}")
		with open(file, "rb") as f:
			fhash = hashlib.md5(f.read()).hexdigest()
			if fhash in hashes:
				hashes[fhash].append(file)
			else:
				hashes[fhash]=[file]
		i+=1
	
	# print duplicate files
	# for fhash in hashes:
		# if len(hashes[fhash])>1:
			# print(hashes[fhash])
	
	# print unique files
	for fhash in hashes:
		if len(hashes[fhash])==1:
			print(hashes[fhash])
	
	#damn none of the wbm ones are actually unique
	
if __name__ == "__main__":
	main()

