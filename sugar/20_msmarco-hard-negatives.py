# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/20_msmarco-hard-negatives.ipynb.

# %% auto 0
__all__ = ['load_msmarco_ce_scores', 'parse_args']

# %% ../nbs/20_msmarco-hard-negatives.ipynb 2
import pickle, scipy.sparse as sp, numpy as np, argparse, os
from tqdm.auto import tqdm
from typing import Optional, List

from xcai.main import *
from .core import *

# %% ../nbs/20_msmarco-hard-negatives.ipynb 4
def load_msmarco_ce_scores(fname:str, data_ids:Optional[List]=None):
    with open(fname, 'rb') as file:
        negatives = pickle.load(file)

    data_ids = list(negatives) if data_ids is None else data_ids

    lbl_id2idx = dict()
    data, indices, indptr = [], [], [0]
    for idx in tqdm(data_ids):
        if idx in negatives:
            data.extend(list(negatives[idx].values()))
            for i in negatives[idx]:
                index = lbl_id2idx.setdefault(i, len(lbl_id2idx))
                indices.append(index)
        indptr.append(len(data))

    lbl_ids = sorted(lbl_id2idx, key=lambda x: lbl_id2idx[x])
    return data_ids, lbl_ids, sp.csr_matrix((data, indices, indptr), dtype=np.float32)
    

# %% ../nbs/20_msmarco-hard-negatives.ipynb 26
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pkl_dir', type=str, required=True)
    parser.add_argument('--data_dir', type=str, required=True)
    return parser.parse_args()
    

# %% ../nbs/20_msmarco-hard-negatives.ipynb 27
if __name__ == '__main__':
    args = parse_args()
    
    config_file = f'{args.data_dir}/XC/configs/data_exact.json'
    config_key = 'data_exact'
    
    use_sxc_sampler = True
    pkl_file = f'{args.pkl_dir}/mogicX/msmarco_data_distilbert-base-uncased_sxc_exact.joblib'
    os.makedirs(os.path.dirname(pkl_file), exist_ok=True)
    block = build_block(pkl_file, config_file, use_sxc_sampler, config_key, do_build=False, only_test=False)

    ce_file = f"{args.data_dir}/ce_scores/cross-encoder-ms-marco-MiniLM-L-6-v2-scores.pkl"

    # save ce score information
    trn_ids = [int(i) for i in block.train.dset.data.data_info['identifier']]
    data_ids, ce_ids, data_ce = load_msmarco_ce_scores(ce_file, trn_ids)
    lbl_ce = sp.csr_matrix((block.n_lbl, data_ce.shape[1]), dtype=np.float32)
    
    sp.save_npz(f'{args.data_dir}/XC/ce-scores_trn_X_Y.npz', data_ce)
    sp.save_npz(f'{args.data_dir}/XC/ce-scores_lbl_X_Y_exact.npz', lbl_ce)

    all_lbl_ids, all_lbl_txt = load_raw_file(f'{args.data_dir}/XC/raw_data/label.raw.txt')
    all_lbl_map = {k:v for k,v in zip(all_lbl_ids, all_lbl_txt)}

    ce_txt = [all_lbl_map[str(i)] for i in ce_ids]
    save_raw_file(f'{args.data_dir}/XC/raw_data/ce-scores.raw.txt', ce_ids, ce_txt)

    # save ce scores for positives
    data_lbl = block.train.dset.data.data_lbl.copy().astype(np.float32)
    data_lbl.sort_indices()
    lbl_ids = block.train.dset.data.lbl_info['identifier']

    def align_with_matrix_labels(inp_data_lbl, inp_lbl_ids, targ_lbl_id2idx, targ_shape, use_data=False):
        indices = [targ_lbl_id2idx[str(inp_lbl_ids[i])] for i in inp_data_lbl.indices]
        indptr = inp_data_lbl.indptr
        data = inp_data_lbl.data if use_data else np.ones(len(indices))
        return sp.csr_matrix((data, indices, indptr), dtype=np.float32, shape=targ_shape)

    ce_id2idx = {str(id): idx for idx,id in enumerate(ce_ids)}
    data_lbl_ce_align = align_with_matrix_labels(data_lbl, lbl_ids, ce_id2idx, data_ce.shape)
    data_lbl_ce_align.sort_indices()

    data_lbl_ce_align = data_lbl_ce_align.multiply(data_ce)
    data_lbl_ce_align.eliminate_zeros()

    lbl_id2idx = {str(id): idx for idx,id in enumerate(lbl_ids)}
    data_lbl = align_with_matrix_labels(data_lbl_ce_align, ce_ids, lbl_id2idx, data_lbl.shape, use_data=True)
    data_lbl.sort_indices()
    
    sp.save_npz(f'{args.data_dir}/XC/trn_X_Y_ce-exact.npz', data_lbl)

    # save ce scores for negatives
    x_idx, y_idx = data_lbl_ce_align.nonzero()
    data_ce[x_idx, y_idx] = 0
    data_ce.eliminate_zeros()

    sp.save_npz(f'{args.data_dir}/XC/ce-negatives_trn_X_Y.npz', data_ce)
    sp.save_npz(f'{args.data_dir}/XC/ce-negatives_lbl_X_Y_exact.npz', lbl_ce)
    
