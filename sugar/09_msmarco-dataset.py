# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/09_msmarco-dataset.ipynb.

# %% auto 0
__all__ = ['download_msmarco', 'load_queries', 'load_passages', 'load_qrels', 'construct_matrix', 'load_qrel_matrix',
           'save_raw_txt', 'save_qrel_matrix', 'construct_msmarco', 'parse_args']

# %% ../nbs/09_msmarco-dataset.ipynb 2
from tqdm.auto import tqdm
import json, pandas as pd, scipy.sparse as sp, numpy as np, argparse
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
        idx = 0
        for line in file:
            data = json.loads(line)
            pid_to_idx[int(data['_id'])] = idx
            passages.append((data['title'], data['text']))
            idx += 1
    return passages, pid_to_idx
        

# %% ../nbs/09_msmarco-dataset.ipynb 8
def load_qrels(fname):
    qrels = pd.read_table(fname)
    assert (qrels['score'] == 1).all(), 'Score should contain all 1s'

    query_to_passage = dict()
    for qid, pid in tqdm(zip(qrels['query-id'], qrels['corpus-id']), total=qrels.shape[0]):
        query_to_passage.setdefault(qid, []).append(pid)

    return query_to_passage
    

# %% ../nbs/09_msmarco-dataset.ipynb 9
def construct_matrix(query_to_passage, pid_to_idx):
    query_id = []

    data, indices, indptr = [], [], [0]
    for qid, pid in tqdm(query_to_passage.items()):
        query_id.append(qid)
        data.extend([1] * len(pid))
        indices.extend([pid_to_idx[o] for o in pid])
        indptr.append(len(indices))
        
    mat = sp.csr_matrix((data, indices, indptr), shape=(len(query_id), len(passages)), dtype=np.int64)
    return mat, query_id


# %% ../nbs/09_msmarco-dataset.ipynb 10
def load_qrel_matrix(fname, pid_to_idx):
    query_to_passage = load_qrels(fname)
    return construct_matrix(query_to_passage, pid_to_idx)
    

# %% ../nbs/09_msmarco-dataset.ipynb 11
def save_raw_txt(fname, ids, texts):
    with open(fname, 'w') as file:
        for k,v in tqdm(zip(ids, texts), total=len(ids)):
            file.write(f'{k}->{v}\n')
        

# %% ../nbs/09_msmarco-dataset.ipynb 12
def save_qrel_matrix(qrel_fname, queries, pid_to_idx, save_dir, data_type='train'):
    mat, query_ids = load_qrel_matrix(qrel_fname, pid_to_idx)
    if data_type == 'train': mat_file, raw_file = f'{save_dir}/trn_X_Y.npz', f'{save_dir}/raw_data/train.raw.txt'
    elif data_type == 'test': mat_file, raw_file = f'{save_dir}/tst_X_Y.npz', f'{save_dir}/raw_data/test.raw.txt'
    else: raise ValueError(f'Invalid data type: {data_type}')
    sp.save_npz(mat_file, mat)
    save_raw_txt(raw_file, query_ids, [queries[o] for o in query_ids])
    

# %% ../nbs/09_msmarco-dataset.ipynb 13
def construct_msmarco(data_dir:str, save_dir:str, query_fname:str, passage_fname:str, 
                      train_qrel_fname:str, test_qrel_fname:str, is_download:bool):
    if is_download: download_msmarco(data_dir)
    
    if not os.path.exists(save_dir): os.makedirs(save_dir, exist_ok=True)
    if not os.path.exists(f'{save_dir}/raw_data'): os.makedirs(f'{save_dir}/raw_data', exist_ok=True)

    queries = load_queries(query_fname)
    passages, pid_to_idx = load_passages(passage_fname)

    passage_ids = sorted(pid_to_idx, key=lambda x: pid_to_idx[x])
    save_raw_txt(f'{save_dir}/raw_data/titles.raw.txt', passage_ids, [o[0] for o in passages])
    save_raw_txt(f'{save_dir}/raw_data/passages.raw.txt', passage_ids, [o[1] for o in passages])

    save_qrel_matrix(trn_qrel_fname, queries, pid_to_idx, save_dir=save_dir, data_type='train')
    save_qrel_matrix(tst_qrel_fname, queries, pid_to_idx, save_dir=save_dir, data_type='test')
    

# %% ../nbs/09_msmarco-dataset.ipynb 14
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--download', action='store_true')
    
    parser.add_argument('--data_dir', type=str, required=True)
    parser.add_argument('--save_dir', type=str, required=True)
    
    parser.add_argument('--query_filename', type=str, required=True)
    parser.add_argument('--passage_filename', type=str, required=True)

    parser.add_argument('--train_qrel_filename', type=str, required=True)
    parser.add_argument('--test_qrel_filename', type=str, required=True)
    return parser.parse_args()
    

# %% ../nbs/09_msmarco-dataset.ipynb 15
if __name__ == '__main__':
    args = parse_args()
    construct_msmarco(args.data_dir, args.save_dir, args.query_filename, args.passage_filename, 
                      args.train_qrel_filename, args.test_qrel_filename, is_download=args.download)
    
