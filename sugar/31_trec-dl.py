import pandas as pd, os, json, numpy as np, scipy.sparse as sp, re

from tqdm.auto import tqdm
from typing import Optional, List, Dict

from sugar.core import *

def load_qrels(fname):
    with open(fname) as file:
        content = file.read()

    qrels = dict()
    for line in content.split("\n")[:-1]:
        l = line.split()
        if l[3] != "0":
            qrels.setdefault(int(l[0]), []).append((int(l[2]), int(l[3])))

    return qrels


def get_matrix(qry_ids, lbl_ids2idx, qrels):
    data, indices, indptr = [], [], [0]

    for i in qry_ids:
        for l in qrels.get(i, []):
            indices.append(lbl_ids2idx[l[0]])
            data.append(l[1])
        indptr.append(len(data))

    return sp.csr_matrix((data, indices, indptr), shape=(len(qry_ids), len(lbl_ids2idx)), dtype=np.float32)


if __name__ == "__main__":
    year = 2020

    if year == 2019:
        data_dir = "/home/sasokan/suchith/datasets/trecdl19/"
        qry_file, qrel_file = f"{data_dir}/msmarco-test2019-queries.tsv", f"{data_dir}/2019qrels-pass.txt"
    elif year == 2020:
        data_dir = "/home/sasokan/suchith/datasets/trecdl20/"
        qry_file, qrel_file = f"{data_dir}/msmarco-test2020-queries.tsv", f"{data_dir}/2020qrels-pass.txt"
    else:
        raise ValueError("Invalid year")

    lbl_file = "/home/sasokan/b-sprabhu/datasets/beir/msmarco/XC/raw_data/label.raw.csv"

    # load data

    qry_df = pd.read_table(qry_file, header=None)
    lbl_ids, lbl_txt = load_raw_file(lbl_file)

    lbl_ids2idx = {k:i for i,k in enumerate(lbl_ids)}

    qrels = load_qrels(qrel_file)

    # process data

    qry_ids, qry_txt = qry_df.iloc[:, 0], qry_df.iloc[:, 1]
    qry_lbl = get_matrix(qry_ids, lbl_ids2idx, qrels)

    valid_idxs = np.where(qry_lbl.getnnz(axis=1) > 0)[0]

    qry_ids, qry_txt = [qry_ids[i] for i in valid_idxs], [qry_txt[i] for i in valid_idxs]
    qry_lbl = qry_lbl[valid_idxs]

    # save data

    if year == 2019:
        save_dir = "/home/sasokan/suchith/datasets/trecdl19/XC/"
    elif year == 2020:
        save_dir = "/home/sasokan/suchith/datasets/trecdl20/XC/"
    else:
        raise ValueError("Invalid year")

    os.makedirs(save_dir, exist_ok=True)
    os.makedirs(f"{save_dir}/raw_data", exist_ok=True)

    sp.save_npz(f"{save_dir}/tst_X_Y.npz", qry_lbl)
    save_raw_file(f"{save_dir}/raw_data/test.raw.csv", qry_ids, qry_txt)
    save_raw_file(f"{save_dir}/raw_data/label.raw.csv", lbl_ids, lbl_txt)



