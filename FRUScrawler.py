#!/usr/bin/env python
# coding: utf-8

# In[382]:


### Dependencies

import os
import requests
import re
from lxml import html
from urllib.parse import urljoin
from tqdm import tqdm


# In[429]:


### Definitions

## Time
start_year = 1940
end_year = 1990

## Replace with the actual hub URL
hub_url = 'https://history.state.gov/tags/russia'

## Replace with the actual XPath for document links
# The author of this code (Hyunbin Choi @ Korea Univ) used Google Chrome's HTML source code funcationality (cf. F12)
links_xpath = '/html/body/div/section/div/main/div[2]/div/div/div/div/ul/li/a/@href'

## Replace with the actual XPath for download button/link
download_link_xpath = '/html/body/div/section/div/main/div[2]/aside/div[1]/ul/li[1]/ul/li[1]/a/@href' 

## Replace with the actual XPath for the document title
title_xpath = '/html/body/div/section/div/main/div[2]/div/div/div[1]/div/div[1]/h1/span/text()'

## Replace with the desired destination folder
destination_folder = '' #do not fill; used as failsafe
destination_folder = 'C:/Users/tomc9/Dropbox/9.Programming/tech_var_2023/FRUS EPUB/Tag_Country_Russia/'


## DEBUG
debug_mode = False


# In[402]:


def download_file(url, destination, destination_folder):
    full_path = os.path.join(destination_folder, destination)
    response = requests.get(url)
    with open(full_path, 'wb') as file:
        file.write(response.content)


# In[403]:


def get_links_from_hub(hub_url, links_xpath):
    response = requests.get(hub_url)
    tree = html.fromstring(response.content)
    links = tree.xpath(links_xpath)
    return [link for link in links if isinstance(link, str)]  # Ensure only strings (URLs) are returned


# In[404]:


def get_download_link(document_url, download_link_xpath):
    response = requests.get(document_url)
    tree = html.fromstring(response.content)
    download_links = tree.xpath(download_link_xpath)
    return download_links[0] if download_links else None


# In[405]:


def get_document_title(document_url, title_xpath):
    response = requests.get(document_url)
    tree = html.fromstring(response.content)
    title_elements = tree.xpath(title_xpath)
    if not title_elements:
        return None
    
    # Join elements, replace multiple spaces with a single space
    title = ''.join(title_elements).strip()
    title = re.sub(r'\W\s+', ' ', title)

    # Replace specific string with "FRUS"
    title = title.replace("Foreign Relations of the United States", "FRUS")

    # Replace any non-alphanumeric and non-dash characters (excluding underscore and space) with a single dash
    title = re.sub(r'[^a-zA-Z0-9_ \-]', '-', title)
    
    # Replace 3 or more dashes (---) with single dash
    title = re.sub(r'-{3,}', '-', title)

    # Replace spaces with underscores
    title_with_underscores = title.replace(' ', '_')

    # Truncate underscored title to manageable length
    if len(title_with_underscores) > 80:
        front_part = title_with_underscores[:50]
        # Find the next underscore to cut off at the next word
        next_underscore = front_part.rfind('_')
        if next_underscore != -1:
            front_part = front_part[:next_underscore]
        end_underscore = title_with_underscores[:-30].rfind('_')
        back_part = title_with_underscores[end_underscore+1:]
        title_with_underscores = f"{front_part}...{back_part}"
    
    # Extract the first occurrence of four consecutive digits
    year_match = re.search(r'\d{4}', title)
    year = year_match.group(0) if year_match else ''

    # Prepend year to the title, if found
    formatted_title = f'{year}_{title_with_underscores}' if year else title_with_underscores
    
    return formatted_title


# In[406]:


def get_downloaded_files(destination_folder):
    return {file for file in os.listdir(destination_folder) if os.path.isfile(os.path.join(destination_folder, file))}


# In[425]:


def main(hub_url, links_xpath, download_link_xpath, title_xpath, destination_folder, file_extension, start_year, end_year, test_mode=False):
    downloaded_files = get_downloaded_files(destination_folder)
    document_links = get_links_from_hub(hub_url, links_xpath)

    if test_mode:
        document_links = document_links[:3]
        
    if debug_mode:
        print("NOTE: Debug mode is turned on.\nThe console will be cluttered.")

    # Initialize progress bar (tqdm)
    with tqdm(total=len(document_links), desc="Downloading", unit="file") as pbar:
        for link in document_links:
            document_link = urljoin(hub_url, link)
            document_title = get_document_title(document_link, title_xpath)
            if debug_mode: print(f"Document title: {document_title}")  # Debugging

            # Flag to determine if the document should be downloaded
            should_download = True
        
            # Extract the year and check if it falls within the specified range
            year_match = re.search(r'\d{4}', document_title)
            if year_match:
                year = int(year_match.group(0))
                if year < start_year or year > end_year:
                    should_download = False  # Skip this document
                    if debug_mode: print(f"Found year: {year}, skipping...")  # Debugging

            if should_download:
                download_link = get_download_link(document_link, download_link_xpath)
                if download_link and document_title:
                    absolute_download_link = urljoin(document_link, download_link)
                    file_name = f'{document_title}.{file_extension}'
                
                    # Skip download if file already exists
                    if file_name in downloaded_files:
                        # Update progress bar
                        pbar.update(1)
                        if debug_mode: print(f"File already downloaded: {file_name}")  # Debugging
                        continue
                    
                    if debug_mode: print(f"Downloading...")  # Debugging
                    download_file(absolute_download_link, file_name, destination_folder)

            # Update progress bar
            pbar.update(1)


# In[426]:


def test_crawler():
    main(hub_url,
         links_xpath,
         download_link_xpath,
         title_xpath,
         destination_folder,
         'epub',
         start_year,
         end_year,
         test_mode=True)


# In[427]:


def true_crawler():
     main(hub_url,
         links_xpath,
         download_link_xpath,
         title_xpath,
         destination_folder,
         'epub',
          start_year,
          end_year,
          test_mode=False)


# In[428]:


true_crawler()


# In[431]:





# In[ ]:




