#!/usr/bin/env python

import requests, mimetypes, json, time, os
from pathlib import Path

def load_feed():
	
	page_size = 100
	page = load_page(0)
	
	total_results = int(page['total_results'])
	total_pages = number_of_pages(total_results, page_size)
	
	print('feed: total_results={}, page_size={}, pages={}'.format(total_results, page_size, total_pages))
	
	load_images(page['images'])
	
	for page_num in range(1, total_pages + 1):
		page = load_page(page_num. page_size)
		load_images(page['images'])
		time.sleep(1)

def load_page(page, page_size):
	mars_api = 'https://mars.nasa.gov/rss/api/'
	
	# Could use condition_2=<MINIMUM-NUM>:sol:gte for minimum and condition_3=<MAXIMUM-NUM>:sol:lte for maxiumum sol here
	params = {'feed': 'raw_images', 'category': 'mars2020', 'feedtype': 'json', 'num': page_size, 'page': page, 'order': 'sol desc', 'extended': 'sample_type::full'}
	
	r = requests.get(mars_api, params=params)
	
	print('request: status={}, url="{}"'.format(r.status_code, r.url))
	
	return r.json()

def load_images(images):
	root_dir = Path(Path.home(), 'mars2020/')
	
	for image in images:
		print('image: id="{}", title="{}"'.format(image['imageid'], image['title']))
		
		image_url = image['image_files']['full_res']
		image_sol = str(image['sol'])
		image_dir = Path(root_dir, image_sol)
		image_path = Path(image_dir, image_url.split("/")[-1])
		
		if image_path.is_file():
			print('image: exists="{}"'.format(image_path))
		else:	
			r = requests.get(image_url)
		
			print('request: status={}, url="{}"'.format(r.status_code, r.url))
		
			if r.status_code == 200:
				save_image(image_dir, image_path, r.content)
		
		time.sleep(1)
		
def save_image(image_dir, image_path, image_bytes):

	try:
		os.mkdir(image_dir)
		print('directory: created="{}"'.format(image_dir))
	except FileExistsError:
		print('directory: exists="{}"'.format(image_dir))
		pass

	with open(image_path, 'wb') as outfile:
		outfile.write(image_bytes)
		print('image: created="{}"'.format(image_path))

def round_up_by_num(number, multiple):
    num = number + (multiple - 1)
    return num - (num % multiple)
    
def number_of_pages(total, page_size):
	return int(round_up_by_num(total, page_size) / page_size)

if __name__ == '__main__':

	OUTPUT_DIR = 

	try:
		os.mkdir(OUTPUT_DIR)
		print('directory: created="{}"'.format(OUTPUT_DIR))
	except FileExistsError:
		print('directory: exists="{}"'.format(OUTPUT_DIR))

	load_feed()