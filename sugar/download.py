import requests, os, gzip, json, scipy.sparse as sp, numpy as np, argparse
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from tqdm.auto import tqdm

def get_urls(url):
    response = requests.get(url)
    assert response.status_code == 200, f'Invalid url: {url}'
    soup = BeautifulSoup(response.text, 'html.parser')
    return [link.get('href') for link in soup.find_all('a') if link.get('href').endswith('.gz')]

def download(url, fname):
    file_response = requests.get(url, stream=True)
    with open(fname, 'wb') as f:
        for chunk in file_response.iter_content(chunk_size=1024):
            f.write(chunk)

def download_amazon_dataset(url, data_dir):
    os.makedirs(data_dir, exist_ok=True)
    file_links = get_urls(url)
    for link in tqdm(file_links):
        furl, fname = urljoin(url, link), os.path.join(data_dir, link)
        print(f'- Processing url: {furl}')
        download(furl, fname)
        print(f'+ Save data to: {fname}')

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_url', type=str, required=True)
    parser.add_argument('--cache_dir', type=str, required=True)
    return parser.parse_args()


if __name__ == '__main__':
    # Command to download amazon reviews:
    # python sugar/download.py --data_url https://datarepo.eng.ucsd.edu/mcauley_group/data/amazon_v2/categoryFiles/ --cache_dir /scratch/scai/phd/aiz218323/Projects/sugar/data/amazon_review_2018/cache/reviews

    from timeit import default_timer as timer
    start_time = timer()

    args = parse_args()
    print(args.data_url, args.cache_dir)

    download_amazon_dataset(args.data_url, args.cache_dir)

    end_time = timer()
    print(f'Time elapsed: {end_time-start_time:.2f} seconds.')

