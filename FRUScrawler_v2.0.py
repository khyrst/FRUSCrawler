# ---------- Dependencies ----------
import os
import requests
import re
import logging
import time
from lxml import html
from urllib.parse import urljoin
from tqdm import tqdm
from random import randint

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# ---------- Definitions ----------
# Time
start_year = 1945
end_year = 1985

# Replace with the hub URL you intend to crawl.
hub_url = 'https://history.state.gov/historicaldocuments/carter'

# Replace with the desired destination folder
destination_folder = 'C:/Users/tomc9/Dropbox/0.Research/AggregationProblem/FRUS_files'

# DEBUG
debug_mode = False

# User-Agent string, listing github and institution mail
# For ethical crawling, I've added random delays between each host call to avoid overloading
headers = {
    'User-Agent': 'Mozilla/5.0 (compatible; FRUSCrawler/2.0; +https://github.com/khyrst; khyrst@korea.ac.kr)'
}

# ---------- Functions ----------


def download_file(url, destination, destination_folder_path):
    full_path = os.path.join(destination_folder_path, destination)
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Ensures we notice bad responses
    with open(full_path, 'wb') as file:
        file.write(response.content)


def get_links_from_hub(url):
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    tree = html.fromstring(response.content)
    links = tree.xpath('//a[@data-template="app:parse-params"]/@href')
    return [link for link in links if isinstance(link, str)]  # Ensures only strings (URLs) are returned.


def get_download_link(url):
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    tree = html.fromstring(response.content)
    download_links = tree.xpath('//a[@data-template="frus:epub-href-attribute"]/@href')
    return download_links[0] if download_links else None


def get_document_title(url):
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    tree = html.fromstring(response.content)
    title_elements = tree.xpath('/html/body/div[1]/section/div/main/div/div[2]/div[1]/div/h1/text()') # Tailored for FRUS
    if not title_elements:
        return None
    # Join elements, replace multiple spaces with a single space
    title = ''.join(title_elements).strip()
    title = re.sub(r'\W\s+', ' ', title)

    # Replaces specific string with "FRUS"
    title = title.replace("Foreign Relations of the United States", "FRUS")

    # Replaces any non-alphanumeric and non-dash characters (excluding underscore and space) with a single dash
    title = re.sub(r'[^a-zA-Z0-9_ \-]', '-', title)

    # Replaces 3 or more dashes (---) with single dash
    title = re.sub(r'-{3,}', '-', title)

    # Replaces spaces with underscores
    title_with_underscores = title.replace(' ', '_')

    # Truncates underscored title to manageable length
    if len(title_with_underscores) > 80:
        front_part = title_with_underscores[:50]
        # Finds the next underscore to cut off at the next word
        next_underscore = front_part.rfind('_')
        if next_underscore != -1:
            front_part = front_part[:next_underscore]
        end_underscore = title_with_underscores[:-30].rfind('_')
        back_part = title_with_underscores[end_underscore + 1:]
        title_with_underscores = f"{front_part}...{back_part}"

    # Extracts the first occurrence of four consecutive digits
    year_match = re.search(r'\d{4}', title)
    year = year_match.group(0) if year_match else ''

    # Prepends year to the title, if found
    formatted_title = f'{year}_{title_with_underscores}' if year else title_with_underscores
    return formatted_title


def get_downloaded_files(destination_fp):
    return {file for file in os.listdir(destination_fp) if
            os.path.isfile(os.path.join(destination_fp, file))}


def main(url, destination_fp, file_extension, start_year, end_year, test_mode=False):
    downloaded_files = get_downloaded_files(destination_fp)
    document_links = get_links_from_hub(url)
    if test_mode:  # if test mode, limits functionality
        document_links = document_links[:3]
    if debug_mode:
        logging.debug("NOTE: Debug mode is turned on.\nThe console will be cluttered.")

    # Initializes progress bar (tqdm)
    with tqdm(total=len(document_links), desc="Downloading", unit="file") as pbar:
        for link in document_links:
            document_link = urljoin(url, link)
            document_title = get_document_title(document_link)
            if not document_title:
                logging.warning(f"Could not retrieve title for document: {document_link}")
                pbar.update(1)
                continue
            if debug_mode:
                logging.debug(f"Document title: {document_title}")
            # Flag to determine if the document should be downloaded
            should_download = True
            # Extract the year and check if it falls within the specified range
            year_match = re.search(r'\d{4}', document_title)
            if year_match:
                year = int(year_match.group(0))
                if year < start_year or year > end_year:
                    should_download = False  # Skips this document
                    if debug_mode:
                        logging.debug(f"Found year: {year}, skipping...")
            if should_download:
                download_link = get_download_link(document_link)
                if download_link and document_title:
                    absolute_download_link = urljoin(document_link, download_link)
                    file_name = f'{document_title}.{file_extension}'
                    # Skip download if file already exists
                    if file_name in downloaded_files:
                        # Update progress bar
                        pbar.update(1)
                        if debug_mode:
                            logging.debug(f"File already downloaded: {file_name}")
                        continue
                    if debug_mode:
                        logging.debug(f"Downloading...")
                    download_file(absolute_download_link, file_name, destination_fp)
                    # Add delay to avoid overloading the server
                    time.sleep(randint(1, 5))
            # Update progress bar
            pbar.update(1)
            # Add delay to avoid overloading the server
            time.sleep(randint(1, 5))


def test_crawler():
    main(hub_url,
         destination_folder,
         'epub',
         start_year,
         end_year,
         test_mode=True)


def true_crawler():
    main(hub_url,
         destination_folder,
         'epub',
         start_year,
         end_year,
         test_mode=False)


if __name__ == "__main__":
    true_crawler()
