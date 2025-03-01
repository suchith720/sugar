# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/09_msmarco-dataset.ipynb.

# %% auto 0
__all__ = ['download_msmarco', 'load_queries', 'load_passages', 'load_qrels', 'construct_matrix', 'load_qrel_matrix',
           'save_raw_txt', 'save_query_info', 'PassageInfo', 'QueryInfo', 'load_msmarco', 'save_msmarco',
           'sample_msmarco', 'construct_msmarco', 'parse_args']

# %% ../nbs/09_msmarco-dataset.ipynb 2
from tqdm.auto import tqdm
from dataclasses import dataclass
import os, json, pandas as pd, scipy.sparse as sp, numpy as np, argparse
from huggingface_hub import snapshot_download

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
    

# %% ../nbs/09_msmarco-dataset.ipynb 13
def construct_matrix(query_to_passage, pid_to_idx):
    query_id = []

    data, indices, indptr = [], [], [0]
    for qid, pid in tqdm(query_to_passage.items()):
        query_id.append(qid)
        data.extend([1] * len(pid))
        indices.extend([pid_to_idx[o] for o in pid])
        indptr.append(len(indices))
        
    mat = sp.csr_matrix((data, indices, indptr), shape=(len(query_id), len(pid_to_idx)), dtype=np.int64)
    return mat, query_id


# %% ../nbs/09_msmarco-dataset.ipynb 16
def load_qrel_matrix(fname, pid_to_idx):
    query_to_passage = load_qrels(fname)
    return construct_matrix(query_to_passage, pid_to_idx)
    

# %% ../nbs/09_msmarco-dataset.ipynb 17
def save_raw_txt(fname, ids, texts):
    with open(fname, 'w') as file:
        for k,v in tqdm(zip(ids, texts), total=len(ids)):
            file.write(f'{k}->{v}\n')
        

# %% ../nbs/09_msmarco-dataset.ipynb 18
def save_query_info(mat_file, raw_file, mat, ids, texts):
    sp.save_npz(mat_file, mat)
    save_raw_txt(raw_file, ids, texts)
    

# %% ../nbs/09_msmarco-dataset.ipynb 19
@dataclass
class PassageInfo:
    ids: list
    txt: list

    def sample(self, valid_idx:list):
        self.ids = [self.ids[i] for i in valid_idx]
        self.txt = [self.txt[i] for i in valid_idx]

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

    @property
    def stats(self):
        n_data, n_lbl = self.mat.shape
        
        lbl_p_dat = self.mat.getnnz(axis=1).mean()
        dat_p_lbl = self.mat.getnnz(axis=0).mean()
        
        dat_no_lbl = np.sum(self.mat.getnnz(axis=1) == 0)
        lbl_no_dat = np.sum(self.mat.getnnz(axis=0) == 0)
        
        stats = pd.DataFrame([{
            'Number of queries': n_data, 
            'Number of labels': n_lbl, 
            'Number of queries per label': dat_p_lbl, 
            'Number of labels per query': dat_p_lbl, 
            'Number of queries without label': dat_no_lbl, 
            'Number of labels without query': lbl_no_dat
        }], index=['MSMARCO'])
        
        return stats
    

# %% ../nbs/09_msmarco-dataset.ipynb 20
def load_msmarco(query_fname:str, passage_fname:str, train_qrel_fname:str, test_qrel_fname:str):
    queries = load_queries(query_fname)
    
    passage_txt, pid_to_idx = load_passages(passage_fname)
    passage_ids = sorted(pid_to_idx, key=lambda x: pid_to_idx[x])

    trn_mat, trn_ids = load_qrel_matrix(train_qrel_fname, pid_to_idx)
    trn_txt = [queries[o] for o in trn_ids]
    
    tst_mat, tst_ids = load_qrel_matrix(test_qrel_fname, pid_to_idx)
    tst_txt = [queries[o] for o in tst_ids]
    
    return PassageInfo(passage_ids, passage_txt), QueryInfo(trn_mat, trn_ids, trn_txt), QueryInfo(tst_mat, tst_ids, tst_txt)
    

# %% ../nbs/09_msmarco-dataset.ipynb 21
def save_msmarco(label_info, trn_info, tst_info, save_dir, file_suffix=None):
    os.makedirs(save_dir, exist_ok=True)
    os.makedirs(f'{save_dir}/raw_data', exist_ok=True)

    lbl_file = f'{save_dir}/raw_data/label.raw.txt' if file_suffix is None else f'{save_dir}/raw_data/label_{file_suffix}.raw.txt'
    save_raw_txt(lbl_file, passage_info.ids, [o[0] for o in passage_info.txt])

    mat_file = f'{save_dir}/trn_X_Y.npz' if file_suffix is None else f'{save_dir}/trn_{file_suffix}_X_Y.npz'
    raw_file = f'{save_dir}/raw_data/train.raw.txt' if file_suffix is None else f'{save_dir}/raw_data/train_{file_suffix}.raw.txt'
    save_qrel_matrix(mat_file, raw_file, trn_info.mat, trn_info.ids, trn_info.txt)

    mat_file = f'{save_dir}/tst_X_Y.npz' if file_suffix is None else f'{save_dir}/tst_{file_suffix}_X_Y.npz'
    raw_file = f'{save_dir}/raw_data/test.raw.txt' if file_suffix is None else f'{save_dir}/raw_data/test_{file_suffix}.raw.txt'
    save_qrel_matrix(mat_file, raw_file, tst_info.mat, tst_info.ids, tst_info.txt)
    

# %% ../nbs/09_msmarco-dataset.ipynb 22
def sample_msmarco(lbl_info, trn_info, tst_info, sampling_type=None):
    if sampling_type == 'exact':
        trn_valid_idx = np.where(trn_info.mat.getnnz(axis=0) > 0)[0]
        tst_valid_idx = np.where(tst_info.mat.getnnz(axis=0) > 0)[0]
        valid_idx = np.union1d(trn_valid_idx, tst_valid_idx)
    elif sampling_type == 'xc':
        valid_idx = np.where(trn_info.mat.getnnz(axis=0) > 0)[0]
    else:
        raise ValueError(f'Invalid sampling value: {sampling_type}.')
            
    lbl_info.sample(valid_idx)
    trn_info.sample_labels(valid_idx)
    tst_info.sample_labels(valid_idx)
    

# %% ../nbs/09_msmarco-dataset.ipynb 23
def construct_msmarco(query_file:str, passage_file:str, train_qrel_file:str, test_qrel_file:str, 
                      save_dir:str=None, sampling_type=None, file_suffix=None):
    
    lbl_info, trn_info, tst_info = load_msmarco(query_file, passage_file, train_qrel_file, test_qrel_file)
    
    if sampling_type is not None: sample_msmarco(lbl_info, trn_info, tst_info, sampling_type)
        
    if save_dir is not None: save_msmarco(lbl_info, trn_info, tst_info, save_dir, file_suffix)
        
    return lbl_info, trn_info, tst_info
    

# %% ../nbs/09_msmarco-dataset.ipynb 24
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--download', action='store_true')
    
    parser.add_argument('--data_dir', type=str, required=True)
    parser.add_argument('--save_dir', type=str)

    parser.add_argument('--sampling_type', type=str)
    parser.add_argument('--fname_suffix', type=str)
    
    return parser.parse_args()
    

# %% ../nbs/09_msmarco-dataset.ipynb 25
if __name__ == '__main__':
    args = parse_args()
    if args.download: 
        download_msmarco(args.data_dir)
    else:
        construct_msmarco(f'{args.data_dir}/queries.jsonl', f'{args.data_dir}/corpus.jsonl', 
                          f'{args.data_dir}/qrels/train.tsv', f'{args.data_dir}/qrels/dev.tsv', 
                          args.save_dir, args.sampling_type, args.fname_suffix)
                          
