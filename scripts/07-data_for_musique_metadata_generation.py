import os, pandas as pd, scipy.sparse as sp, numpy as np, json

from tqdm.auto import tqdm
from typing import Optional, List

from xcai.misc import BEIR_DATASETS
from sugar.core import *


def get_examples(qry_ids:List, qry_txt:List, lbl_txt:List, qry_lbl:sp.csr_matrix, n_samples:Optional[int]=None):
    idxs = np.where(qry_lbl.getnnz(axis=1) > 0)[0]
    if n_samples is not None: 
        idxs = np.random.permutation(idxs)[:n_samples]

    examples = []
    for idx in idxs:
        lbls = [lbl_txt[i] for i in qry_lbl[idx].indices]
        example = {
            "Identifier": qry_ids[idx],
            "Query": qry_txt[idx],
            "Documents": json.dumps(lbls, indent=4),
        }
        examples.append(example)

    return examples


def main(data_dir:str, n_samples:Optional[int]=None):
    lbl_ids, lbl_txt = load_raw_file(f"{data_dir}/raw_data/label.raw.csv")

    qry_ids, qry_txt = load_raw_file(f"{data_dir}/raw_data/train.raw.csv")
    qry_lbl = sp.load_npz(f"{data_dir}/trn_X_Y.npz")
    trn_examples = get_examples(qry_ids, qry_txt, lbl_txt, qry_lbl, n_samples)

    qry_ids, qry_txt = load_raw_file(f"{data_dir}/raw_data/test.raw.csv")
    qry_lbl = sp.load_npz(f"{data_dir}/tst_X_Y.npz")
    tst_examples = get_examples(qry_ids, qry_txt, lbl_txt, qry_lbl, n_samples)

    return trn_examples, tst_examples


def save_raw_txt(fname, raw, sep:Optional[str]='->', encoding:Optional[str]='utf-8'):
    with open(fname, 'w', encoding=encoding) as file:
        for r in zip(*raw):
            l = sep.join([str(i).replace("\n", "").replace("\t", "").replace(sep, "") for i in r])
            file.write(f'{l}\n')


if __name__ == "__main__":
    data_dir = "/data/datasets/multihop/musique/XC/"

    save_dir = "/data/datasets/processed/papyrus/10-musique_concepts_from_query_and_document/"
    os.makedirs(save_dir, exist_ok=True)

    trn_examples, tst_examples = main(data_dir)

    def save_examples(examples, save_file):
        df = pd.DataFrame(examples)
        df.to_csv(save_file, header=None, index=None, sep="\t")

    save_examples(trn_examples, f"{save_dir}/train_labels.tsv")
    save_examples(tst_examples, f"{save_dir}/test_labels.tsv")
    
    # raw = [df["Identifier"].tolist(), df["Document"].tolist(), df["Concepts"].tolist()]
    # save_raw_txt(save_file, raw, sep="\t")

