# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/09_msmarco-dataset.ipynb.

# %% auto 0
__all__ = ['download_msmarco', 'load_queries', 'load_passages', 'load_qrels', 'get_matrix', 'QueryInfo', 'LabelInfo',
           'get_msmarco', 'save_msmarco', 'sample_msmarco', 'get_and_save_msmarco', 'parse_args']

# %% ../nbs/09_msmarco-dataset.ipynb 2
import os, json, pandas as pd, scipy.sparse as sp, numpy as np, argparse

from tqdm.auto import tqdm
from dataclasses import dataclass
from huggingface_hub import snapshot_download

from .core import *

# %% ../nbs/09_msmarco-dataset.ipynb 4
def download_msmarco(data_dir=None):
    if not os.path.exists(data_dir): os.makedirs(data_dir, exist_ok=True)
    snapshot_download(repo_id="mteb/msmarco", repo_type="dataset", local_dir=data_dir)
    

# %% ../nbs/09_msmarco-dataset.ipynb 6
def load_queries(fname):
    queries = dict()
    with open(fname, 'r') as file:
        for line in file:
            data = json.loads(line)
            queries[int(data['_id'])] = data['text']
    return queries
        

# %% ../nbs/09_msmarco-dataset.ipynb 7
def load_passages(fname):
    passages, pid_to_idx = [], dict()
    with open(fname, 'r') as file:
        for idx,line in enumerate(file):
            data = json.loads(line)
            pid_to_idx[int(data['_id'])] = idx
            passages.append(data['text'])
    return passages, pid_to_idx
        

# %% ../nbs/09_msmarco-dataset.ipynb 8
def load_qrels(fname):
    qrels = pd.read_table(fname)
    assert (qrels['score'] == 1).all(), 'Score should contain all 1s'

    query_to_passage = dict()
    for qid, pid in tqdm(zip(qrels['query-id'], qrels['corpus-id']), total=qrels.shape[0]):
        query_to_passage.setdefault(qid, []).append(pid)

    return query_to_passage
    

# %% ../nbs/09_msmarco-dataset.ipynb 17
def get_matrix(fname, vocab_size):
    mapping = load_qrels(fname)
    return get_matrix_from_item2idx(mapping, vocab_size)
    

# %% ../nbs/09_msmarco-dataset.ipynb 18
@dataclass
class QueryInfo:
    mat: sp.csr_matrix
    ids: list
    txt: list

    def sample_labels(self, lbl_idx:list):
        data_idx = np.where(self.mat.getnnz(axis=1) > 0)[0]
        
        self.mat = self.mat[:, lbl_idx][data_idx, :]
        self.ids = [self.ids[i] for i in data_idx]
        self.txt = [self.txt[i] for i in data_idx]

@dataclass
class LabelInfo:
    ids: list
    txt: list

    def sample(self, valid_idx:list):
        self.ids = [self.ids[i] for i in valid_idx]
        self.txt = [self.txt[i] for i in valid_idx]
    

# %% ../nbs/09_msmarco-dataset.ipynb 19
def get_msmarco(query_file:str, lbl_file:str, trn_file:str, tst_file:str):
    queries = load_queries(query_file)
    
    lbl_txt, lbl_id2idx = load_passages(lbl_file)
    lbl_ids = sorted(lbl_id2idx, key=lambda x: lbl_id2idx[x])

    trn_mat, trn_ids = get_matrix(trn_file, len(lbl_txt))
    trn_txt = [queries[o] for o in trn_ids]
    
    tst_mat, tst_ids = get_matrix(tst_file, len(lbl_txt))
    tst_txt = [queries[o] for o in tst_ids]
    
    return QueryInfo(trn_mat, trn_ids, trn_txt), QueryInfo(tst_mat, tst_ids, tst_txt), LabelInfo(lbl_ids, lbl_txt)
    

# %% ../nbs/09_msmarco-dataset.ipynb 20
def save_msmarco(save_dir, trn_info, tst_info, lbl_info, suffix=''):
    os.makedirs(save_dir, exist_ok=True)
    x_suffix = f'_{suffix}' if len(suffix) else ''
    sp.save_npz(f'{save_dir}/trn_X_Y{x_suffix}.npz', trn_info.mat)
    sp.save_npz(f'{save_dir}/tst_X_Y{x_suffix}.npz', tst_info.mat)
    
    os.makedirs(f'{save_dir}/raw_data', exist_ok=True)
    y_suffix = f'.{suffix}' if len(suffix) else ''
    save_raw_file(f'{save_dir}/raw_data/train.raw.txt', trn_info.ids, trn_info.txt)
    save_raw_file(f'{save_dir}/raw_data/test.raw.txt', tst_info.ids, tst_info.txt)
    save_raw_file(f'{save_dir}/raw_data/label{y_suffix}.raw.txt', lbl_info.ids, lbl_info.txt)
    

# %% ../nbs/09_msmarco-dataset.ipynb 21
def sample_msmarco(trn_info, tst_info, lbl_info, sampling_type=None):
    if sampling_type == 'exact':
        trn_valid_idx = np.where(trn_info.mat.getnnz(axis=0) > 0)[0]
        tst_valid_idx = np.where(tst_info.mat.getnnz(axis=0) > 0)[0]
        valid_idx = np.union1d(trn_valid_idx, tst_valid_idx)
    elif sampling_type == 'xc':
        valid_idx = np.where(trn_info.mat.getnnz(axis=0) > 0)[0]
    else:
        raise ValueError(f'Invalid sampling value: {sampling_type}.')
            
    trn_info.sample_labels(valid_idx)
    tst_info.sample_labels(valid_idx)
    lbl_info.sample(valid_idx)
    

# %% ../nbs/09_msmarco-dataset.ipynb 22
def get_and_save_msmarco(query_file:str, lbl_file:str, trn_file:str, tst_file:str, save_dir:str=None, sampling_type=None, suffix=''):
    trn_info, tst_info, lbl_info = get_msmarco(query_file, lbl_file, trn_file, tst_file)
    
    if sampling_type is not None: 
        sample_msmarco(trn_info, tst_info, lbl_info, sampling_type)
        
    if save_dir is not None: 
        save_msmarco(save_dir, trn_info, tst_info, lbl_info, suffix)
        
    return trn_info, tst_info, lbl_info
    

# %% ../nbs/09_msmarco-dataset.ipynb 23
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--download', action='store_true')
    
    parser.add_argument('--data_dir', type=str, required=True)
    parser.add_argument('--save_dir', type=str)
    
    return parser.parse_args()
    

# %% ../nbs/09_msmarco-dataset.ipynb 24
if __name__ == '__main__':
    args = parse_args()
    if args.download: 
        download_msmarco(args.data_dir)
    else:
        get_and_save_msmarco(f'{args.data_dir}/queries.jsonl', f'{args.data_dir}/corpus.jsonl', f'{args.data_dir}/qrels/train.tsv', 
                             f'{args.data_dir}/qrels/dev.tsv', args.save_dir, 'xc', 'xc')
        
        get_and_save_msmarco(f'{args.data_dir}/queries.jsonl', f'{args.data_dir}/corpus.jsonl', f'{args.data_dir}/qrels/train.tsv', 
                             f'{args.data_dir}/qrels/dev.tsv', args.save_dir, 'exact', 'exact')

        get_and_save_msmarco(f'{args.data_dir}/queries.jsonl', f'{args.data_dir}/corpus.jsonl', f'{args.data_dir}/qrels/train.tsv', 
                             f'{args.data_dir}/qrels/dev.tsv', args.save_dir)
                          
