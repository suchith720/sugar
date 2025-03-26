# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/17_map-amazon-reviews-from-dump.ipynb.

# %% auto 0
__all__ = ['REVIEW_PROCS', 'title_proc', 'text_proc', 'title_text_proc', 'get_review_proc', 'extract_review_info',
           'create_vocab_and_item2idx', 'get_vocabulary', 'get_matrix_from_item2idx', 'get_matrix', 'get_metadata',
           'parse_args']

# %% ../nbs/17_map-amazon-reviews-from-dump.ipynb 2
import scipy.sparse as sp, argparse, numpy as np

from tqdm.auto import tqdm
from pathlib import Path
from timeit import default_timer as timer

from sugar.map_amazon_dump import *

# %% ../nbs/17_map-amazon-reviews-from-dump.ipynb 7
def title_proc(o):
    return (o['title'], o['rating'])

def text_proc(o):
    return (o['text'], o['rating'])

def title_text_proc(o):
    return (o['title'] + ' ' + o['text'], o['rating'])


# %% ../nbs/17_map-amazon-reviews-from-dump.ipynb 8
REVIEW_PROCS = {
    'title': title_proc,
    'text': text_proc,
    'title_text': title_text_proc,
}

# %% ../nbs/17_map-amazon-reviews-from-dump.ipynb 9
def get_review_proc(dtype):
    assert dtype in REVIEW_PROCS, f'Invalid review processing function: {dtype}.'
    return REVIEW_PROCS[dtype]

def extract_review_info(items, dtype, key):
    func = get_review_proc(dtype)
    reviews = dict()
    for o in tqdm(items, total=len(items)): reviews.setdefault(o[key], []).append(func(o))
    return reviews


# %% ../nbs/17_map-amazon-reviews-from-dump.ipynb 12
def create_vocab_and_item2idx(mapping):
    mapping_item2idx, vocab = dict(), dict()
    for k,v in tqdm(mapping.items()):
        for o in v:
            idx = vocab.setdefault(o[0], len(vocab))
            l = mapping_item2idx.setdefault(k, [])
            l.append((idx,o[1]))
    return vocab, mapping_item2idx


# %% ../nbs/17_map-amazon-reviews-from-dump.ipynb 13
def get_vocabulary(mapping):
    vocab, mapping_item2idx = create_vocab_and_item2idx(mapping)

    vocab_txt = sorted(vocab, key=lambda x: vocab[x])
    vocab_ids = list(range(len(vocab_txt)))

    return vocab_ids, vocab_txt, mapping_item2idx


# %% ../nbs/17_map-amazon-reviews-from-dump.ipynb 17
def get_matrix_from_item2idx(mapping, vocab_size, ids=None):
    data, indices, indptr = [], [], [0]
    ids = list(mapping) if ids is None else ids
    for i in tqdm(ids):
        if i in mapping:
            item_idx, item_val = list(zip(*mapping[i]))
            data.extend(item_val)
            indices.extend(item_idx)
        indptr.append(len(data))
    mat = sp.csr_matrix((data, indices, indptr), shape=(len(ids), vocab_size), dtype=np.float32)
    mat.sort_indices()
    mat.sum_duplicates()
    return mat, ids


# %% ../nbs/17_map-amazon-reviews-from-dump.ipynb 18
def get_matrix(mapping_item2idx, vocab_size, trn_ids, tst_ids, lbl_ids):
    trn_mat, trn_ids = get_matrix_from_item2idx(mapping_item2idx, vocab_size, trn_ids)
    tst_mat, tst_ids = get_matrix_from_item2idx(mapping_item2idx, vocab_size, tst_ids)
    lbl_mat, lbl_ids = get_matrix_from_item2idx(mapping_item2idx, vocab_size, lbl_ids)
    return trn_mat, tst_mat, lbl_mat


# %% ../nbs/17_map-amazon-reviews-from-dump.ipynb 19
def get_metadata(cache_dir, data_dir, meta_type, key, condition_type, do_filter=True):
    items = load_items(cache_dir, data_dir, key, condition_type, Path(data_dir).stem)

    review_mapping = extract_review_info(items, meta_type, key)

    metadata_ids, metadata_txt, mapping_item2idx = get_vocabulary(review_mapping)
    trn_ids, tst_ids, lbl_ids = get_ids(data_dir)
    trn_mat, tst_mat, lbl_mat = get_matrix(mapping_item2idx, len(metadata_ids), trn_ids, tst_ids, lbl_ids)

    if do_filter:
        metadata_ids, metadata_txt, trn_mat, tst_mat, lbl_mat = filter_vocab(metadata_ids, metadata_txt, trn_mat, tst_mat, lbl_mat)

    return trn_mat, tst_mat, lbl_mat, metadata_ids, metadata_txt


# %% ../nbs/17_map-amazon-reviews-from-dump.ipynb 21
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cache_dir', type=str, required=True)
    parser.add_argument('--data_dir', type=str, required=True)
    parser.add_argument('--key', type=str, default='parent_asin')
    parser.add_argument('--condition_type', type=str, default=None)
    parser.add_argument('--review_type', type=str, required=True)
    parser.add_argument('--no_filter', action='store_false')
    return parser.parse_args()


# %% ../nbs/17_map-amazon-reviews-from-dump.ipynb 22
if __name__ == '__main__':
    start_time = timer()

    args = parse_args()

    trn_mat, tst_mat, lbl_mat, metadata_ids, metadata_txt = get_metadata(args.cache_dir, args.data_dir, meta_type=args.review_type,
                                                                         key=args.key, condition_type=args.condition_type,
                                                                         do_filter=args.no_filter)
    save_metadata(args.data_dir, trn_mat, tst_mat, lbl_mat, metadata_ids, metadata_txt, f'review_{args.review_type}')

    end_time = timer()
    print(f'Time elapsed: {end_time-start_time:.2f} seconds.')

