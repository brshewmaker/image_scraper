#!/usr/bin/python
from bs4 import BeautifulSoup
import httplib
import urllib
import urllib2
import re
import urlparse
from urlparse import urljoin
import time
import os
import collections
from collections import deque

#|-----------------------------------------------------------
#|         Global Variables / Initial setup
#|-----------------------------------------------------------

# Get and parse the URL
scrape_url = raw_input("Input the URL (include http): ")
o = urlparse.urlparse(scrape_url)
domain = o.netloc
if 'www.' in domain:
    domain = o.netloc[4:]

# Scraper mode --> entire domain, or subdir?
mode = int(raw_input('Which mode for given url? 0: Entire Domain | 1: Given subdirectory: '))
optional_search_path = ''
if mode:
    domain = domain + o.path
    optional_search_path = str(raw_input('(optional) Give a custom subdir search string: '))

# Global Variables
counter = int(raw_input("Iteration count (enter 0 to run until no more links): "))
limit = 1
if counter == 0:
    limit = 0
minimum_image_size = int(raw_input("Minimum image size (in KB): "))
timeout = 4  #how long to wait before urllib2.open() gives up?, in seconds

# Data structures
urls_to_visit= deque([scrape_url])
visited_urls = set()
images_grabbed = set()


#|-----------------------------------------------------------
#|         Functions
#|-----------------------------------------------------------
# Function from http://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python
def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError:
        print '     --> mkdir_p error on path: ' + path

# Try to create a beautiful soup object from the url.  Returns 0 on failure
def get_soup(url):
    # First, build the Request object
    try:
        opener = urllib2.build_opener()
        request = urllib2.Request(url)
        request.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1')
        # Next, send and process the request
        try:
            data = opener.open(request, None, timeout).read()
        # For some reason, if you don't except on the right error, it was failing.  using this except clause fixed incompleteread bug
        except httplib.IncompleteRead:
            return 0
    except:
        print '   !Error in grabbing url: ' + url
        return 0
    return BeautifulSoup(data)

# Given a link to an image and a base directory to save to,
# try to Download and save the image.  Then after saving, delete the
# image if it is under the global minimum image size
def get_image(url):
    # Split apart the given url to get directory and filename information
    o = urlparse.urlparse(url)
    split = o.path.split('/')
    save_location = ''
    for i in range(len(split) - 1):
        save_location += split[i] + '/'
    save_location = domain + save_location[0:-1]
    full_location = save_location + '/' + split[-1]

    print 'Saving ' + url + ' to ' + full_location
    # Create the path(s) if they aren't already there
    if not os.path.exists(save_location):
        mkdir_p(save_location)

    # Grab and save the file
    try:
        urllib.urlretrieve(url, full_location)
        size_kb = os.path.getsize(full_location) / 1024 #returns size in bytes, so adjust to get kb
        if size_kb < minimum_image_size:
            os.remove(full_location)
            print '    --> File size: ' + str(size_kb) + ' too small, deleting file: ' + full_location
    except IOError as e:
        print "I/O error({0}): {1}".format(e.errno, e.strerror)

# Given a regular href link from an <a> tag, see if it actually a link to an image
def is_image_link(url):
    image_types = ['.jpg', '.png', '.gif', '.tiff']
    o = urlparse.urlparse(url)
    split = o.path.split('/')
    test_value_3 = split[-1][-4:]  # if it has one, this will grab the file extension
    test_value_4 = split[-1][-5:]  # for file extensions 4 long, like tiff
    if test_value_3 in image_types or test_value_4 in image_types:
        return 1
    else:
        return 0


# Given a url, grab that url, find all images and links,
# grab the images on this page, and add new links to the queue
def scrape_url(url):
    print 'scrape_url on: ' + url
    soup = get_soup(url)
    if not soup:
        return 0

    #First, get all <img> tags for this url and grab them
    for img in soup.find_all('img'):
        if img.get('src') is not None:
            imgsrc = urlparse.urljoin(url, img['src'])
            if imgsrc not in images_grabbed:
                get_image(imgsrc)
                images_grabbed.add(imgsrc)

    #next, get all links for this page
    for link in soup.find_all('a'):
        if link.get('href') is not None:
            linkhref = urlparse.urljoin(url, link['href'])
            # Is this link an image link?
            if is_image_link(linkhref) and linkhref not in images_grabbed:
                get_image(linkhref)
                images_grabbed.add(linkhref)
                continue
            elif linkhref not in visited_urls:
                if (len(optional_search_path) > 0) and (domain in linkhref or optional_search_path in linkhref):
                    urls_to_visit.append(linkhref)
                elif domain in linkhref:
                    urls_to_visit.append(linkhref)

#|-----------------------------------------------------------
#|         Run the Image Scraper
#|-----------------------------------------------------------

while urls_to_visit:
    if limit and not counter:
        break
    if limit:
        counter -= 1
    current_url = urls_to_visit.popleft()
    if current_url not in visited_urls:
        visited_urls.add(current_url)
        scrape_url(current_url)
