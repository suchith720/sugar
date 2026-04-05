import pandas as pd, scipy.sparse as sp, os, numpy as np, json
from sugar.core import *


if __name__ == "__main__":
    data_dir = "/home/sasokan/suchith/datasets/trecdl20/XC"

    qry_lbl = sp.load_npz(f"{data_dir}/tst_X_Y.npz")
    qry_ids, qry_txt = load_raw_file(f"{data_dir}/raw_data/test.raw.csv")
    lbl_ids, lbl_txt = load_raw_file(f"{data_dir}/raw_data/label.raw.csv")

    examples = []
    idx = np.random.permutation(len(qry_ids))[:5]
    for i in idx:
        example = {
            "query": qry_txt[i],
            "labels": [lbl_txt[l] for l in qry_lbl[i].indices],
        }
        examples.append(example)

    save_dir = f"{os.path.dirname(data_dir)}/examples"
    os.makedirs(save_dir, exist_ok=True)
    with open(f"{save_dir}/examples.json", "w") as file:
        json.dump(examples, file, indent=4)

