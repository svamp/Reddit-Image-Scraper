#!/usr/bin/python
# -*- coding: utf-8 -*-

"""

	Downloads images from a subreddit

"""

from imgurpython import ImgurClient
from imgurpython.helpers.error import ImgurClientError
from settings import IMGUR_CLIENT_ID, IMGUR_SECRET_KEY, REDDIT_CLIENT_ID, REDDIT_SECRET_KEY
from urllib.parse import urlparse
from urllib.request import urlopen, urlretrieve
import argparse, praw, shutil, sys, os

imgur_client = ImgurClient(IMGUR_CLIENT_ID, IMGUR_SECRET_KEY)

def direct_url(url, subreddit, custom_path):
	
	file_name = url.split('/')[-1]
	if '?' in file_name:
		file_name = file_name.split('?')[0]
	folder_path = os.path.join(os.path.abspath(custom_path), subreddit)

	if not os.path.isdir(folder_path):
		os.makedirs(folder_path)

	if not os.path.isfile(os.path.join(folder_path, file_name)):
		with urlopen(url) as response, open(os.path.join(folder_path, file_name), 'wb') as out_file:
			shutil.copyfileobj(response, out_file)


def handle_albums(imgur_id, subreddit, custom_path):

	album = imgur_client.get_album(imgur_id)
	if album.title:
		# Replaces charactes Windows doesn't like
		folder_name = album.title.replace(' ', '_').replace(':','-').replace('/', '-')
	else:
		folder_name = imgur_id

	folder_path = os.path.join(os.path.abspath(custom_path), subreddit, folder_name)

	if not os.path.isdir(folder_path):
		os.makedirs(folder_path)

	images = imgur_client.get_album_images(imgur_id)
	i = 0
	for image in images:

		image_name = str(i) + '.' + image.type.split('/')[-1]
		i += 1

		if not os.path.isfile(os.path.join(folder_path, image_name)):
			with urlopen(image.link) as response, open(os.path.join(folder_path, image_name), 'wb') as out_file:
				shutil.copyfileobj(response, out_file)
	
def main():
	
	# Arguments
	parser = argparse.ArgumentParser()
	parser.add_argument('subreddit', help='Download images from the provided subreddit.')
	parser.add_argument('-p', '--path', help='A path to where to save the downloaded images. Default is the current directory.')
	parser.add_argument('-s', '--section', help='Defines the section of the subreddit. Default is [hot]', choices=['hot', 'new', 'rising', 'controversial', 'top'], default='hot')
	parser.add_argument('-l', '--limit', help='Limits the amounts of request. 1-100 default is 25', type=int, choices=range(0,101), default=25, metavar='[0-100]')
	args = parser.parse_args()

	subreddit = args.subreddit
	custom_path = args.path
	if not custom_path:
		custom_path = '.'
	section = args.section
	limit = args.limit


	user_agent = sys.platform+':image_scraper:v0.1.0 (by /u/Svamp)'
	reddit_client = praw.Reddit(client_id=REDDIT_CLIENT_ID, client_secret=REDDIT_SECRET_KEY, user_agent=user_agent)

	section_select = {
		'hot': reddit_client.subreddit(subreddit).hot(limit=limit),
		'new': reddit_client.subreddit(subreddit).new(limit=limit),
		'rising': reddit_client.subreddit(subreddit).rising(limit=limit),
		'controversial': reddit_client.subreddit(subreddit).controversial(limit=limit),
		'top': reddit_client.subreddit(subreddit).top(limit=limit)
	}

	posts = section_select[section]

	for post in posts:
		
		url = urlparse(post.url)
		if url.netloc == 'i.imgur.com':
			
			direct_url(post.url, subreddit, custom_path)

		elif url.netloc == 'imgur.com':
			imgur_id = url.path.split('/')
			
			if imgur_id[1] == 'a':
				handle_albums(imgur_id[-1], subreddit, custom_path)

			elif imgur_id[1] == 'gallery':
				
				try:
					gallery = imgur_client.gallery(imgur_id[-1])
				except KeyError:
					try:
						handle_albums(imgur_id[-1], subreddit, custom_path)
					except ImgurClientError:
						# In some cases this will cause an additional ImgurClientError
						image = imgur_client.get_image(imgur_id[-1])
						direct_url(image.link, subreddit, custom_path)
				except Exception as e:
					print(e)

			else:
				image = imgur_client.get_image(imgur_id[-1])
				direct_url(image.link, subreddit, custom_path)
			

		
main()