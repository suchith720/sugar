import os, pandas as pd, scipy.sparse as sp, numpy as np, json
from typing import Optional
from tqdm.auto import tqdm

from xcai.misc import BEIR_DATASETS

def load_data(data_dir:str, dtype:str):
    short_hand = {"simple-query": "sq", "multihop-query": "mq"}

    assert dtype in short_hand, f"Invalid data-type: {dtype}."

    data_info = pd.read_csv(f"{data_dir}/raw_data/{dtype}.raw.csv")
    sub_info = pd.read_csv(f"{data_dir}/raw_data/{short_hand[dtype]}-substring.raw.csv")
    
    der_info = pd.read_csv(f"{data_dir}/raw_data/{short_hand[dtype]}-derived-queries.raw.csv")

    data_sub = sp.load_npz(f"{data_dir}/{dtype}_{short_hand[dtype]}-substring.npz")
    data_der = sp.load_npz(f"{data_dir}/{dtype}_{short_hand[dtype]}-derived-queries.npz")

    lbl_sub = sp.load_npz(f"{data_dir}/lbl_{short_hand[dtype]}-substring.npz")
    sub_phs = sp.load_npz(f"{data_dir}/{short_hand[dtype]}-substring_{short_hand[dtype]}-derived-phrases.npz")

    phs_info = pd.read_csv(f"{data_dir}/raw_data/{short_hand[dtype]}-substring_{short_hand[dtype]}-derived-phrases.raw.csv")

    return data_sub, data_info, sub_info, lbl_sub, sub_phs, phs_info, data_der, der_info


def get_lbl_examples(labels:pd.DataFrame, lbl_sub:sp.csr_matrix, sub_info:pd.DataFrame, sub_phs:sp.csr_matrix, phs_info:pd.DataFrame, save_file:str):
    lbl_examples = []
    for idx in np.random.permutation(labels.shape[0])[:10]:
        substrings = [sub_info["text"].iloc[i] for i in lbl_sub[idx].indices]
        phrases = [[phs_info["text"].iloc[j] for j in sub_phs[i].indices] for i in lbl_sub[idx].indices]

        example = {
            "Document": labels["text"].iloc[idx],
            "Substring": [{"original":k, "phrases":v} for k,v in zip(substrings, phrases)],
        }
        lbl_examples.append(example)
    
    with open(save_file, "w") as file:
        json.dump(lbl_examples, file, indent=4)

    return lbl_examples


def get_qry_examples(data_sub:sp.csr_matrix, data_info:pd.DataFrame, sub_info:pd.DataFrame, data_der:sp.csr_matrix, der_info:pd.DataFrame, save_file:str):
    qry_examples = []
    for idx in np.random.permutation(data_sub.shape[0])[:10]:
        substrings = [sub_info["text"].iloc[i] for i in data_sub[idx].indices]
        derived = [der_info["text"].iloc[i] for i in data_der[idx].indices]

        example = {
            "Document": data_info["text"].iloc[idx],
            "Substring": substrings,
            "Derived": derived,
        }
        qry_examples.append(example)

    with open(save_file, "w") as file:
        json.dump(qry_examples, file, indent=4)

    return qry_examples


def save_examples(lbl_file:str, save_dir:str, dtype:str, example_dir:str, seed:Optional[int]=100):
    np.random.seed(seed)

    labels = pd.read_csv(lbl_file)
    data_sub, data_info, sub_info, lbl_sub, sub_phs, phs_info, data_der, der_info = load_data(save_dir, dtype)

    os.makedirs(example_dir, exist_ok=True)

    # label examples
    save_file = f"{example_dir}/01_document-substring_{dtype}.json"
    lbl_examples = get_lbl_examples(labels, lbl_sub, sub_info, sub_phs, phs_info, save_file)

    # query examples
    save_file = f"{example_dir}/02_query-substring_{dtype}.json"
    qry_examples = get_qry_examples(data_sub, data_info, sub_info, data_der, der_info, save_file)

    return lbl_examples, qry_examples


if __name__ == "__main__":
    data_dir = "/data/datasets/beir/"

    beir_examples = []
    for dataset in tqdm(BEIR_DATASETS):
        for dtype in ["simple-query", "multihop-query"]:
            lbl_file = f"{data_dir}/{dataset}/XC/raw_data/label.raw.csv"
            save_dir = f"{data_dir}/{dataset}/XC/document_substring/"

            example_dir = f"{data_dir}/{dataset}/XC/examples/"
            lbl_examples, qry_examples = save_examples(lbl_file, save_dir, dtype, example_dir, seed=100)

            beir_examples.append({
                "dataset":dataset, 
                "type": dtype,
                "document":np.random.choice(lbl_examples), 
                "query":np.random.choice(qry_examples)
            })

    save_file = "/home/aiscuser/scratch1/examples/01-beir_substring_examples.json"
    os.makedirs("/home/aiscuser/scratch1/examples/", exist_ok=True)
    with open(save_file, "w") as file:
        json.dump(beir_examples, file, indent=4)




