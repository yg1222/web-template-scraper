'''
Author: Umm..
This script takes in a base url and fetches all the resource files to allow for local rendering.
'''
import os
import sys
import re
import requests
import random
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging
from proxies import get_working_proxies, get_proxy_list

logger = logging.getLogger("fetcher")
log_format = '[%(asctime)s] %(levelname)s [line %(lineno)d in %(module)s]: %(message)s'
log_datefmt='%Y-%m-%d %H:%M:%S'
logging.basicConfig(
    format=log_format,
    datefmt=log_datefmt,
    filename='logs.log',
    level=logging.DEBUG
)
# filename='logs.log',


save_path=""
relative_html_paths = []
visited_pages = []
use_proxies = False
working_proxies = None
proxy_list=None
def scrape_and_download_resources(base_url):
    print(f"Base url: {base_url}\nSave path: {save_path}\n")
    print("Running scraper...\n")
    
    if use_proxies:
        proxy_list = get_proxy_list()
        working_proxies = get_working_proxies(proxy_list=proxy_list, url=base_url)
        if len(working_proxies) == 0:
            logging.error("No working proxies")
            sys.exit("Exited. No working proxies")

    def random_proxy_dict():
        proxies=None
        if use_proxies:
            proxy = random.choice(working_proxies)
            proxies = {
                'http': proxy,
                'https': proxy,
            }
        return proxies
    
    os.makedirs(save_path, exist_ok=True)
    # This erases the rem_files. Back them up if you wish to keep them
    html_txt_path = os.path.join(save_path, "relative_html_paths.txt")
    resources_txt_path = os.path.join(save_path, 'resources.txt')
    rem_files = [html_txt_path, resources_txt_path]
    for file_path in rem_files:
        try:
            os.remove(file_path)
            logger.info(f"File '{file_path}' deleted successfully.")
        except FileNotFoundError:
            continue
        except PermissionError:
            sys.exit(f"Permission denied to delete file '{file_path}'.")


    def scrape_html_urls(url):
        if url in visited_pages:
            return
        visited_pages.append(url)
        with open('test\\visited_pages.txt', 'a') as v:
            v.write(url+'\n')
        is_dead_file = False
        global relative_html_paths

        proxies = random_proxy_dict()
        url_res = requests.get(url, proxies=proxies)
        if url_res.status_code != 200:
            is_dead_file=True

        # save
        current_html_path=None
        save_html_path=None
        parsed = urlparse(url)
        if parsed.path.endswith(".html"):
            current_html_path = parsed.path.lstrip('/')
            save_html_path = os.path.normpath(os.path.join(save_path, current_html_path))
            
        # save this file content
        try:
            if not is_dead_file:
                if os.path.dirname(save_html_path) != "":
                    os.makedirs(os.path.dirname(save_html_path), exist_ok=True)
                with open(save_html_path, 'wb') as file:
                    file.write(url_res.content)
                logger.info(f'Downloaded and saved content for {save_html_path}')
        except Exception as e:
            logger.error(f"Error making directory and saving file {save_html_path}: {e}")



        soup=None
        # if parsed.path not in captured_paths:
        soup = BeautifulSoup(url_res.text, 'html.parser')
        
        for anchor in soup.find_all('a', href=True):
            href = anchor['href']
            if href.endswith('.html') and not href.startswith('#'):
                # print(f"href in {parsed.path}, {href}")
                # Checking if href is relative or contains the base utl
                if not urlparse(href).netloc:  # relative url
                    relative_html_paths.append(href)
                    scrape_html_urls(urljoin(base_url, href))
                elif base_url in href:
                    relative_html_paths.append(href.path.lstrip('/'))
                    scrape_html_urls(href)
                else:
                    continue



        relative_html_paths = list(set(relative_html_paths))

    # Start
    scrape_html_urls(base_url)

    # -----------------Scrape htmls
    # just writing to file for the user's records
    with open(html_txt_path, 'a', encoding='utf-8') as file:
        for relative_html_path in relative_html_paths:
            file.write(relative_html_path + '\n')

    resources = []
    
    # creating resouces list
    for relative_html_path in relative_html_paths:
        saved_html = os.path.join(save_path, relative_html_path)
        if os.path.exists(saved_html):
            with open(saved_html, 'r', encoding='utf-8') as html:
                # print(f"{saved_html} exists")
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract urls
                for link in soup.find_all('link', href=True):
                    if not urlparse(link['href']).netloc:
                        resources.append(urljoin(base_url, link['href']))

                for script in soup.find_all('script', src=True):
                    resources.append(urljoin(base_url, script['src']))

                for img in soup.find_all('img', src=True):
                    resources.append(urljoin(base_url, img['src']))

                for style in soup.find_all(style=True):
                    # css_urls = re.findall(r'url\((.*?)\)', style['style'])
                    css_urls = re.findall(r'url\s*\(\s*["\']?(.*?)["\']?\s*\)', style['style'], re.IGNORECASE)
                    for css_url in css_urls:
                        css_url = css_url.strip('\'"')
                        resources.append(urljoin(base_url, css_url))

    resources = list(set(resources))

    # just writing resources to file for the user's records
    with open(resources_txt_path, 'a', encoding='utf-8') as file:
        for resource in resources:
            file.write(resource + '\n')

    # Downloading each resource
    for resource in resources:
        resource_url = urlparse(resource)
        relative_resource_path = resource_url.path.lstrip('/')
        save_resource_path = os.path.normpath(os.path.join(save_path, relative_resource_path))
        try:
            os.makedirs(os.path.dirname(save_resource_path), exist_ok=True)
            proxies= random_proxy_dict()
            response = requests.get(resource, proxies=proxies)
            if response.status_code == 200:
                with open(save_resource_path, 'wb') as file:
                    file.write(response.content)
                logger.info(f'Downloaded and saved content for {resource}')
        except Exception as e:
            logger.error(f"Error downloading and saving file {save_resource_path}: {e}")


base_url=""
url_pattern = r'^(http|https):\/\/(([\w.-]+)(\.[\w.-]+)*|localhost|127\.0\.0\.1)(:\d+)?([\/\w\.-]*)*\/?$'

while not bool(re.match(url_pattern, base_url)):
    base_url = input("What is the home url: ")
save_path = input("\nEnter a directory (absolute or relative), leave blank to pick the default directory.\nWarning: Selecting the same directory as a previous project would cause the files to be overwritten (beneficial if re-downloading or updating the same project): ")
if save_path.strip() == "":
    save_path = 'default-overwritable'
# save_path = "test2"
# base_url ="http://127.0.0.1:5502/"
up = input("Try proxies? (y/n): ")
up = up.strip()
if up in ['y', 'Y']:
    use_proxies = True

scrape_and_download_resources(base_url)
