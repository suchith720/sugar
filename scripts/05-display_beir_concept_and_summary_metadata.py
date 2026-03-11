import os, pandas as pd, scipy.sparse as sp, numpy as np, json

from tqdm.auto import tqdm
from typing import Optional

from xcai.misc import BEIR_DATASETS
from sugar.core import *

def load_data(data_dir:str):
    lbl_concept = sp.load_npz(f"{data_dir}/concept_lbl_X_Y.npz")
    concept_ids, concept_txt = load_raw_file(f"{data_dir}/raw_data/label_concept.raw.csv")

    concept_var = sp.load_npz(f"{data_dir}/variations_concept_X_Y.npz")
    var_ids, var_txt = load_raw_file(f"{data_dir}/raw_data/concept_variations.raw.csv")
    
    concept_type = sp.load_npz(f"{data_dir}/type_concept_X_Y.npz")
    type_ids, type_txt = load_raw_file(f"{data_dir}/raw_data/concept_type.raw.csv")

    concept_summ = sp.load_npz(f"{data_dir}/summary_concept_X_Y.npz")
    summ_ids, summ_txt = load_raw_file(f"{data_dir}/raw_data/concept_summary.raw.csv")

    return lbl_concept, concept_txt, concept_var, var_txt, concept_type, type_txt, concept_summ, summ_txt 


def save_examples(lbl_file:str, save_dir:str, example_file:str, seed:Optional[int]=100):
    np.random.seed(seed)

    lbl_ids, lbl_txt = load_raw_file(lbl_file)
    lbl_concept, concept_txt, concept_var, var_txt, concept_type, type_txt, concept_summ, summ_txt = load_data(save_dir)

    os.makedirs(example_dir, exist_ok=True)

    lbl_idxs = np.where(lbl_concept.getnnz(axis=1) > 0)[0]

    # label examples
    lbl_examples = []
    for idx in np.random.permutation(lbl_idxs)[:10]:

        lbl_concepts = []
        for c in lbl_concept[idx].indices:
            concepts = {
                "Concept": concept_txt[c],
                "Type": [type_txt[i] for i in concept_type[c].indices],
                "Summary": [summ_txt[i] for i in concept_summ[c].indices],
                "Variations": [var_txt[i] for i in concept_var[c].indices],
            }
            lbl_concepts.append(concepts)
        
        example = {
            "Document": lbl_txt[idx],
            "Concepts": lbl_concepts,
        }
        lbl_examples.append(example)
    
    with open(example_file, "w") as file:
        json.dump(lbl_examples, file, indent=4)

    return lbl_examples


if __name__ == "__main__":
    data_dir = "/home/sasokan/b-sprabhu/datasets/beir/"
    example_dir = f"{data_dir}/examples/01_document-concept-and-summary/"

    os.makedirs(example_dir, exist_ok=True)

    beir_examples = []
    for dataset in tqdm(BEIR_DATASETS):
        lbl_file = f"{data_dir}/{dataset}/XC/raw_data/label.raw.csv"
        save_dir = f"{data_dir}/{dataset}/XC/document_concept_and_summary/"
        
        print(dataset)

        if os.path.exists(save_dir):
            example_file = f"{example_dir}/{dataset.replace('/', '-')}.json"
            lbl_examples = save_examples(lbl_file, save_dir, example_file, seed=100)
        else:
            print(f"Directory not found: {save_dir}")

