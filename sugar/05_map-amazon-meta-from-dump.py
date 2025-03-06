# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/05_map-amazon-meta-from-dump.ipynb.

# %% auto 0
__all__ = ['METADATA_PROCS', 'default_condition', 'condition_a23', 'get_condition', 'read_jsongz', 'read_jsonl', 'read_file',
           'get_items', 'load_items', 'title_proc', 'description_proc', 'details_proc', 'image_proc', 'video_proc',
           'get_meta_proc', 'extract_meta_info', 'get_vocabulary', 'get_ids', 'get_matrix', 'filter_vocab',
           'get_downloaded_image_filename', 'download_image', 'download_images', 'verify_image', 'verify_images',
           'remove_images', 'filter_images', 'process_images', 'get_downloaded_video_filename', 'download_video',
           'download_videos', 'process_videos', 'get_metadata', 'save_metadata', 'parse_args']

# %% ../nbs/05_map-amazon-meta-from-dump.ipynb 2
import json, gzip, argparse, os, pickle, numpy as np, uuid, ssl, scipy.sparse as sp, requests, mimetypes
from timeit import default_timer as timer
from fastdownload import download_url
from multiprocessing import Pool
from functools import partial
from tqdm.auto import tqdm
from pathlib import Path
from PIL import Image

from .core import *

ssl._create_default_https_context = ssl._create_unverified_context

# %% ../nbs/05_map-amazon-meta-from-dump.ipynb 4
def default_condition(o): 
    return True

def condition_a23(o, ids, key):
    return o[key] in ids

def get_condition(data_dir, dtype, key):
    all_ids = get_all_ids(f'{data_dir}/raw_data', encoding='latin-1')
    
    if dtype == 'a23': 
        return partial(condition_a23, ids=all_ids, key=key)
    elif dtype is None:
        return default_condition
    else: 
        raise ValueError(f'Invalid condition: {dtype}')
        

# %% ../nbs/05_map-amazon-meta-from-dump.ipynb 5
def read_jsongz(fname, condition=default_condition):
    with gzip.open(fname, 'rt', encoding='utf-8') as file:
        return [json.loads(o) for o in file if condition(json.loads(o))]

def read_jsonl(fname, condition=default_condition):
    with open(fname, 'r') as file:
        return [json.loads(o) for o in file if condition(json.loads(o))]
        

# %% ../nbs/05_map-amazon-meta-from-dump.ipynb 6
def read_file(fname, condition=default_condition):
    if fname.endswith('.jsonl'):
        return read_jsonl(fname, condition)
    elif fname.endswith('.json.gz'):
        return read_jsongz(fname, condition)
    else:
        raise ValueError(f'Invalid file: {fname}')
        

# %% ../nbs/05_map-amazon-meta-from-dump.ipynb 9
def get_items(cache_dir, condition=default_condition):
    items = []
    files = [f'{cache_dir}/{fname}' for fname in os.listdir(cache_dir) if fname.endswith('.jsonl') or fname.endswith('.json.gz')]
    for file in tqdm(files): items.extend(read_file(file, condition))
    return items
    

# %% ../nbs/05_map-amazon-meta-from-dump.ipynb 12
def load_items(cache_dir:str, data_dir:str, key:str, condition_type=None, suffix=''):
    if len(suffix): suffix = f'_{suffix}'
    cache_file = f'{cache_dir}/products{suffix}.pkl' if condition_type is None else f'{cache_dir}/products_{condition_type}{suffix}.pkl'

    try:
        with open(cache_file, 'rb') as file:
            items = pickle.load(file)
    except:
        is_valid = get_condition(data_dir, condition_type, key)
        items = get_items(cache_dir, condition=is_valid)
        
        with open(cache_file, 'wb') as file:
            pickle.dump(items, file)

    return items
    

# %% ../nbs/05_map-amazon-meta-from-dump.ipynb 21
def title_proc(o): 
    return [o['title']]
    
def description_proc(o): 
    return o['description']
    
def details_proc(o): 
    return [o['details'].__str__()]

def image_proc(o):
    images = list()
    for image in o['images']:
        for dtype in ['large', 'hi_res', 'thumb']:
            if dtype in image and image[dtype] is not None:
                images.append(image[dtype]); break
    assert len(images) == len(o['images']), f"Image not found: {o['title']}"
    return images

def video_proc(o):
    return [video['url'] for video in o['videos'] if video['url'] is not None]
    

# %% ../nbs/05_map-amazon-meta-from-dump.ipynb 24
METADATA_PROCS = {
    'title': title_proc, 
    'details': details_proc, 
    'images': image_proc,
    'videos': video_proc,
    'description': description_proc, 
}

# %% ../nbs/05_map-amazon-meta-from-dump.ipynb 25
def get_meta_proc(dtype):
    assert dtype in METADATA_PROCS, f'Invalid metadata processing function: {dtype}.'
    return METADATA_PROCS[dtype]

def extract_meta_info(items, dtype, key):
    func = get_meta_proc(dtype)
    return {o[key]: func(o) for o in items}
    

# %% ../nbs/05_map-amazon-meta-from-dump.ipynb 28
def get_vocabulary(mapping):
    vocab, mapping_item2idx = create_vocab_and_item2idx(mapping)

    vocab_txt = sorted(vocab, key=lambda x: vocab[x])
    vocab_ids = list(range(len(vocab_txt)))

    return vocab_ids, vocab_txt, mapping_item2idx
    

# %% ../nbs/05_map-amazon-meta-from-dump.ipynb 29
def get_ids(data_dir):
    trn_ids, _ = load_raw_txt(f'{data_dir}/raw_data/train.raw.txt', encoding='latin-1')
    tst_ids, _ = load_raw_txt(f'{data_dir}/raw_data/test.raw.txt', encoding='latin-1')
    lbl_ids, _ = load_raw_txt(f'{data_dir}/raw_data/label.raw.txt', encoding='latin-1')
    return trn_ids, tst_ids, lbl_ids
    

# %% ../nbs/05_map-amazon-meta-from-dump.ipynb 30
def get_matrix(mapping_item2idx, vocab_size, trn_ids, tst_ids, lbl_ids):
    trn_mat, trn_ids = get_matrix_from_item2idx(mapping_item2idx, vocab_size, trn_ids)
    tst_mat, tst_ids = get_matrix_from_item2idx(mapping_item2idx, vocab_size, tst_ids)
    lbl_mat, lbl_ids = get_matrix_from_item2idx(mapping_item2idx, vocab_size, lbl_ids)
    return trn_mat, tst_mat, lbl_mat
    

# %% ../nbs/05_map-amazon-meta-from-dump.ipynb 31
def filter_vocab(vocab_ids, vocab_txt, trn_mat, tst_mat, lbl_mat=None):
    valid_idx = np.where(trn_mat.getnnz(axis=0) > 0)[0]
    if lbl_mat is not None:
        lbl_idx = np.where(lbl_mat.getnnz(axis=0) > 0)[0]
        valid_idx = np.union1d(valid_idx, lbl_idx)

    trn_mat = trn_mat[:, valid_idx]
    tst_mat = tst_mat[:, valid_idx]
    if lbl_mat is not None: 
        lbl_mat = lbl_mat[:, valid_idx]
    
    vocab_ids, vocab_txt = [vocab_ids[i] for i in valid_idx], [vocab_txt[i] for i in valid_idx]

    return vocab_ids, vocab_txt, trn_mat, tst_mat, lbl_mat
    

# %% ../nbs/05_map-amazon-meta-from-dump.ipynb 35
def get_downloaded_image_filename(dest, name, suffix):
    start_index = 1
    candidate_name = name

    while (dest/f"{candidate_name}{suffix}").is_file():
        candidate_name = f"{candidate_name}{start_index}"
        start_index += 1

    return candidate_name
    

# %% ../nbs/05_map-amazon-meta-from-dump.ipynb 36
def download_image(dest, inp, timeout=4, preserve_filename=False):
    i,url = inp
    url = url.split("?")[0]
    url_path = Path(url)
    suffix = url_path.suffix if url_path.suffix else '.jpg'
    name = get_downloaded_image_filename(dest, url_path.stem, suffix) if preserve_filename else str(uuid.uuid4())
    try: 
        dest = dest/f"{name}{suffix}"
        download_url(url, dest, show_progress=False, timeout=timeout)
        return dest
    except Exception as e: 
        f"Couldn't download {url}."
        return None
        

# %% ../nbs/05_map-amazon-meta-from-dump.ipynb 37
def download_images(dest, urls=None, n_workers=8, timeout=4, preserve_filename=False):
    dest = Path(dest)
    dest.mkdir(exist_ok=True)
    with Pool(processes=n_workers) as pool:
        fnames = list(tqdm(pool.imap(partial(download_image, dest, timeout=timeout, preserve_filename=preserve_filename), list(enumerate(urls))), total=len(urls)))
    return fnames
    

# %% ../nbs/05_map-amazon-meta-from-dump.ipynb 38
def verify_image(fn):
    try:
        im = Image.open(fn)
        im.draft(im.mode, (32,32))
        im.load()
        return True
    except: return False
        

# %% ../nbs/05_map-amazon-meta-from-dump.ipynb 39
def verify_images(fns, n_workers=8):
    with Pool(processes=n_workers) as pool:
        return list(tqdm(pool.imap(verify_image, fns), total=len(fns)))
        

# %% ../nbs/05_map-amazon-meta-from-dump.ipynb 40
def remove_images(fnames, is_valid):
    for fname,v in zip(fnames, is_valid):
        if not v and fname is not None: fname.unlink()
    

# %% ../nbs/05_map-amazon-meta-from-dump.ipynb 41
def filter_images(image_ids, image_txt, trn_mat, tst_mat, lbl_mat, valid_idx):
    trn_mat = trn_mat[:, valid_idx]
    tst_mat = tst_mat[:, valid_idx]
    lbl_mat = lbl_mat[:, valid_idx]
    
    image_ids, image_txt = [image_ids[i] for i in valid_idx], [image_txt[i] for i in valid_idx]

    return image_ids, image_txt, trn_mat, tst_mat, lbl_mat
    

# %% ../nbs/05_map-amazon-meta-from-dump.ipynb 42
def process_images(save_dir, metadata_ids, metadata_txt, trn_mat, tst_mat, lbl_mat):
    fnames = download_images(save_dir, urls=metadata_txt)
    
    is_valid = verify_images(fnames)
    remove_images(fnames, is_valid)

    metadata_txt = [o if o is None else o.name for o in fnames]
    return filter_images(metadata_ids, metadata_txt, trn_mat, tst_mat, lbl_mat, np.where(is_valid)[0])


# %% ../nbs/05_map-amazon-meta-from-dump.ipynb 48
def get_downloaded_video_filename(dest, name, suffix):
    start_index = 1
    candidate_name = name

    while (dest/f"{candidate_name}{suffix}").is_file():
        candidate_name = f"{candidate_name}{start_index}"
        start_index += 1

    return candidate_name
    

# %% ../nbs/05_map-amazon-meta-from-dump.ipynb 49
def download_video(dest, url, preserve_filename=False):
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            url_path = Path(url.split('/')[-1].split('?')[0])
            if not url_path.suffix:
                content_type = response.headers.get('Content-Type')
                suffix = mimetypes.guess_extension(content_type) if content_type else '.mp4'
                if not suffix: suffix = '.mp4'
            
            name = get_downloaded_video_filename(dest, url_path.stem, suffix) if preserve_filename else str(uuid.uuid4())

            dest = dest/f"{name}{suffix}"
            with open(dest, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk: f.write(chunk)
            return dest
        else:
            print(f"Failed to download {url}. Status code: {response.status_code}")
    except Exception as e:
        print(f"An error occurred while downloading {url}: {e}")


# %% ../nbs/05_map-amazon-meta-from-dump.ipynb 52
def download_videos(dest, urls=None, n_workers=8, timeout=4, preserve_filename=False):
    dest = Path(dest)
    dest.mkdir(exist_ok=True)
    with Pool(processes=n_workers) as pool:
        fnames = list(tqdm(pool.imap(partial(download_video, dest, preserve_filename=preserve_filename), urls), total=len(urls)))
    return fnames
    

# %% ../nbs/05_map-amazon-meta-from-dump.ipynb 55
def process_videos(metadata_ids, metadata_txt, trn_mat, tst_mat, lbl_mat):
    #TODO    
    
    is_valid = verify_images(fnames)
    remove_images(fnames, is_valid)

    metadata_txt = [o if o is None else o.name for o in fnames]
    return filter_images(metadata_ids, metadata_txt, trn_mat, tst_mat, lbl_mat, np.where(is_valid)[0])


# %% ../nbs/05_map-amazon-meta-from-dump.ipynb 62
def get_metadata(cache_dir, data_dir, meta_type, key, condition_type, do_filter=True):
    items = load_items(cache_dir, data_dir, key, condition_type)
    
    meta_mapping = extract_meta_info(items, meta_type, key)

    metadata_ids, metadata_txt, mapping_item2idx = get_vocabulary(meta_mapping)
    trn_ids, tst_ids, lbl_ids = get_ids(data_dir)
    trn_mat, tst_mat, lbl_mat = get_matrix(mapping_item2idx, len(metadata_ids), trn_ids, tst_ids, lbl_ids)

    if key == 'images':
        process_images(f'{data_dir}/images', metadata_ids, metadata_txt, trn_mat, tst_mat, lbl_mat)
    elif key == 'videos':
        raise NotImplementedError('TODO')

    if do_filter:
        metadata_ids, metadata_txt, trn_mat, tst_mat, lbl_mat = filter_vocab(metadata_ids, metadata_txt, trn_mat, tst_mat, lbl_mat)
        
    return trn_mat, tst_mat, lbl_mat, metadata_ids, metadata_txt
    

# %% ../nbs/05_map-amazon-meta-from-dump.ipynb 64
def save_metadata(save_dir, trn_mat, tst_mat, lbl_mat, metadata_ids, metadata_txt, metadata_type):
    sp.save_npz(f'{save_dir}/{metadata_type}_trn_X_Y.npz', trn_mat)
    sp.save_npz(f'{save_dir}/{metadata_type}_tst_X_Y.npz', tst_mat)
    sp.save_npz(f'{save_dir}/{metadata_type}_lbl_X_Y.npz', lbl_mat)
    
    os.makedirs(f'{save_dir}/raw_data', exist_ok=True)
    save_raw_txt(f'{save_dir}/raw_data/{metadata_type}.raw.txt', metadata_ids, metadata_txt)
    

# %% ../nbs/05_map-amazon-meta-from-dump.ipynb 69
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cache_dir', type=str, required=True)
    parser.add_argument('--data_dir', type=str, required=True)
    parser.add_argument('--key', type=str, default='parent_asin')
    parser.add_argument('--condition_type', type=str, default=None)
    parser.add_argument('--metadata_type', type=str, required=True)
    parser.add_argument('--no_filter', action='store_false')
    return parser.parse_args()


# %% ../nbs/05_map-amazon-meta-from-dump.ipynb 70
if __name__ == '__main__':
    start_time = timer()

    args = parse_args()

    trn_mat, tst_mat, lbl_mat, metadata_ids, metadata_txt = get_metadata(args.cache_dir, args.data_dir, meta_type=args.metadata_type, 
                                                                         key=args.key, condition_type=args.condition_type, 
                                                                         do_filter=args.no_filter)
    save_metadata(args.data_dir, trn_mat, tst_mat, lbl_mat, metadata_ids, metadata_txt, args.metadata_type)
    
    end_time = timer()
    print(f'Time elapsed: {end_time-start_time:.2f} seconds.')
    
