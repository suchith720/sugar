"""https://amazon-reviews-2023.github.io/"""

# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/00_amazon-review-2023.ipynb.

# %% auto 0
__all__ = ['get_categories', 'construct_dataset', 'download_amazon_dataset', 'parse_args']

# %% ../nbs/00_amazon-review-2023.ipynb 4
import requests, os, gzip, json, scipy.sparse as sp, numpy as np, argparse, pandas as pd, multiprocessing as mp
from tqdm.auto import tqdm
from huggingface_hub import hf_hub_download

# %% ../nbs/00_amazon-review-2023.ipynb 5
def get_categories(data_dir):
    fname = os.path.join(data_dir, 'all_categories.txt')
    with open(fname, 'r') as f:
        categories = f.read().split('\n')[:-1]
    return categories
    

# %% ../nbs/00_amazon-review-2023.ipynb 16
def construct_dataset(files):
    item_info, item2row, item2col = {}, {}, {}
    data, indices, indptr = [], [], [0]

    for file_idx,fname in enumerate(files):
        with open(fname, 'r', encoding='utf-8') as f:
            items = [json.loads(d) for d in f]

        progress_bar = None
        for item in items:
            if progress_bar is None:
                progress_bar = tqdm(total=len(items), unit='items', desc=f'File {file_idx+1}')
            progress_bar.update(1)
            
            identifier = item['parent_asin'] 
            short_text = item['title'] if 'title' in item else None
            full_text = ''
            if ('description' in item) and (item['description'] is not None):
                full_text += ''.join(item['description'])
            elif ('features' in item) and (item['features'] is not None):
                full_text += ''.join(item['features'])

            category = item['categories'] if 'categories' in item else None
            store = item['store'] if 'store' in item else None
            details = item['details'] if 'details' in item else None
            
            if identifier and len(identifier) > 0 and short_text and len(short_text) > 0:
                item_info[identifier] = {'short_text': short_text, 'full_text': full_text, 'category': category, 
                                         'store': store, 'details': details}
                
                if ('bought_together' in item) and (item['bought_together'] is not None) and (identifier not in item2row):
                    item2row.setdefault(identifier, len(item2row))
                    data.extend([1] * len(item['bought_together']))
                    indices.extend([item2col.setdefault(o, len(item2col)) for o in item['bought_together']])
                    indptr.append(len(indices))
                    
    r,c = len(item2row), len(item2col)
    matrix = sp.csr_matrix((data, indices, indptr), shape=(r,c), dtype=np.float16)
    return item_info, item2row, item2col, matrix
    

# %% ../nbs/00_amazon-review-2023.ipynb 17
def download_amazon_dataset(data_dir):
    categories = get_categories(args.cache_dir)
    for category in tqdm(categories):
        hf_hub_download(repo_id='McAuley-Lab/Amazon-Reviews-2023', filename=f'raw/meta_categories/meta_{category}.jsonl', 
                        repo_type="dataset", local_dir=data_dir)
        

# %% ../nbs/00_amazon-review-2023.ipynb 18
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cache_dir', type=str, required=True)
    parser.add_argument('--output_dir', type=str, required=True)
    return parser.parse_args()
    

# %% ../nbs/00_amazon-review-2023.ipynb 20
from .amazon_review_2018 import clean_dataset, save_dataset

# %% ../nbs/00_amazon-review-2023.ipynb 21
if __name__ == '__main__':
    from timeit import default_timer as timer
    start_time = timer()
    
    args = parse_args()

    files = [f'{args.cache_dir}/raw/meta_categories/{file}' for file in os.listdir(f'{args.cache_dir}/raw/meta_categories') if file.endswith('.jsonl')]
    item_info, item2row, item2col, matrix = construct_dataset(files)

    valid_matrix, valid_item2row, valid_item2col = clean_dataset(matrix, item2row, item2col, item_info)

    save_dataset(args.output_dir, valid_matrix, valid_item2row, valid_item2col, item_info)

    end_time = timer()
    print(f'Time elapsed: {end_time-start_time:.2f} seconds.')
        