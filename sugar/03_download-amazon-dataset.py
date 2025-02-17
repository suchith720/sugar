# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/03_download-amazon-dataset.ipynb.

# %% auto 0
__all__ = ['OLD_AMAZON_URL', 'HF_CATEGORIES_URL', 'get_urls_in_page', 'download_url', 'download_amazon_dataset_from_url',
           'get_hf_categories', 'download_amazon_dataset_from_hf', 'parse_args']

# %% ../nbs/03_download-amazon-dataset.ipynb 2
import requests, os, gzip, json, scipy.sparse as sp, numpy as np, argparse
from huggingface_hub import hf_hub_download
from timeit import default_timer as timer
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from tqdm.auto import tqdm

# %% ../nbs/03_download-amazon-dataset.ipynb 3
OLD_AMAZON_URL = 'https://datarepo.eng.ucsd.edu/mcauley_group/data/amazon_v2/'
HF_CATEGORIES_URL = 'https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023/raw/main/all_categories.txt'

# %% ../nbs/03_download-amazon-dataset.ipynb 4
def get_urls_in_page(url):
    response = requests.get(url)
    assert response.status_code == 200, f'Invalid url: {url}'
    soup = BeautifulSoup(response.text, 'html.parser')
    return [link.get('href') for link in soup.find_all('a') if link.get('href').endswith('.gz')]

# %% ../nbs/03_download-amazon-dataset.ipynb 5
def download_url(url, fname):
    file_response = requests.get(url, stream=True)
    with open(fname, 'wb') as f:
        for chunk in file_response.iter_content(chunk_size=1024):
            f.write(chunk)

# %% ../nbs/03_download-amazon-dataset.ipynb 6
def download_amazon_dataset_from_url(data_dir, dtype='meta'):
    folder = 'product' if dtype == 'meta' else 'review'
    data_dir = f'{data_dir}/{folder}'
    os.makedirs(data_dir, exist_ok=True)
    url = f'{OLD_AMAZON_URL}/metaFiles2' if dtype == 'meta' else f'{OLD_AMAZON_URL}/categoryFiles'
    file_links = get_urls_in_page(url)
    for link in tqdm(file_links):
        furl, fname = urljoin(url, link), os.path.join(data_dir, link)
        download_url(furl, fname)
        

# %% ../nbs/03_download-amazon-dataset.ipynb 7
def get_hf_categories(data_dir):
    fname = os.path.join(data_dir, 'all_categories.txt')
    if not os.path.exists(fname): download_url(HF_CATEGORIES_URL, fname)
    with open(fname, 'r') as f:
        categories = f.read().split('\n')[:-1]
    return categories
    

# %% ../nbs/03_download-amazon-dataset.ipynb 8
def download_amazon_dataset_from_hf(data_dir, dtype='meta'):
    os.makedirs(data_dir, exist_ok=True)
    categories = get_hf_categories(data_dir)
    fprefix = 'raw/meta_categories/meta_' if dtype == 'meta' else 'raw/review_categories/'
    for category in tqdm(categories):
        hf_hub_download(repo_id='McAuley-Lab/Amazon-Reviews-2023', filename=f'{fprefix}{category}.jsonl',
                        repo_type="dataset", local_dir=data_dir)
        

# %% ../nbs/03_download-amazon-dataset.ipynb 9
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dfrom', type=str, required=True)
    parser.add_argument('--dtype', type=str, required=True)
    parser.add_argument('--cache_dir', type=str, required=True)
    return parser.parse_args()

if __name__ == '__main__':
    start_time = timer()

    args = parse_args()

    if args.dfrom == 'url':
        download_amazon_dataset_from_url(args.cache_dir, dtype=args.dtype)
    elif args.dfrom == 'hf':
        download_amazon_dataset_from_hf(args.cache_dir, dtype=args.dtype)
    else:
        raise ValueError(f'Invalid source of dataset: {args.dfrom}')

    end_time = timer()
    print(f'Time elapsed: {end_time-start_time:.2f} seconds.')
