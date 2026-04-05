import os, pandas as pd, scipy.sparse as sp, numpy as np, json

from tqdm.auto import tqdm
from typing import Optional

from xcai.misc import BEIR_DATASETS
from sugar.core import *


def load_data(data_dir:str):
    lbl_concept = sp.load_npz(f"{data_dir}/concept_lbl_X_Y.npz")
    concept_ids, concept_txt = load_raw_file(f"{data_dir}/raw_data/label_concept.raw.csv")

    return lbl_concept, concept_txt


def get_examples(lbl_file:str, data_dir:str, n_samples:Optional[int]=None):
    lbl_ids, lbl_txt = load_raw_file(lbl_file)
    lbl_concept, concept_txt = load_data(data_dir)

    lbl_idxs = np.where(lbl_concept.getnnz(axis=1) > 0)[0]
    if n_samples is not None:
        lbl_idxs = np.random.permutation(lbl_idxs)[:n_samples]

    examples = []
    for idx in lbl_idxs:
        lbl_concepts = [concept_txt[c] for c in lbl_concept[idx].indices]
        example = {
            "Identifier": lbl_ids[idx],
            "Document": lbl_txt[idx],
            "Concepts": lbl_concepts.__str__(),
        }
        examples.append(example)

    return examples


def main(data_dir:str, n_samples:Optional[int]=None):
    examples = []
    for dataset in tqdm(BEIR_DATASETS):
        lbl_file = f"{data_dir}/{dataset}/XC/raw_data/label.raw.csv"
        meta_dir = f"{data_dir}/{dataset}/XC/document_concept_and_summary/"
        
        print(dataset)

        if os.path.exists(meta_dir):
            examples.extend(get_examples(lbl_file, meta_dir, n_samples=n_samples))
        else:
            print(f"Directory not found: {meta_dir}")
    return examples


def save_raw_txt(fname, raw, sep:Optional[str]='->', encoding:Optional[str]='utf-8'):
    with open(fname, 'w', encoding=encoding) as file:
        for r in zip(*raw):
            l = sep.join([str(i).replace("\n", "").replace("\t", "").replace(sep, "") for i in r])
            file.write(f'{l}\n')


if __name__ == "__main__":
    # data_dir = "/home/yprabhu/suchith/datasets/beir/"
    # save_file = "/data/desaini/Research/OAK/v1/MOGIC/Paper/09-beir_queries/samples/samples.raw.txt"

    data_dir = "/home/sasokan/b-sprabhu/datasets/beir/"
    # save_file = "/home/sasokan/b-sprabhu/datasets/processed/papyrus/09-beir_queries/samples/samples.raw.txt"
    save_file = "/home/sasokan/b-sprabhu/datasets/processed/papyrus/09-beir_queries/labels.raw.txt"

    os.makedirs(os.path.dirname(save_file), exist_ok=True)

    examples = main(data_dir)

    df = pd.DataFrame(examples)
    raw = [df["Identifier"].tolist(), df["Document"].tolist(), df["Concepts"].tolist()]
    save_raw_txt(save_file, raw, sep="\t")

