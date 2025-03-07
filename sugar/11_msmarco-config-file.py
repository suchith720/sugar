# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/11_msmarco_config_file.ipynb.

# %% auto 0
__all__ = ['get_msmarco_config', 'parse_args']

# %% ../nbs/11_msmarco_config_file.ipynb 2
import json, os, argparse
from xcai.config import PARAM

# %% ../nbs/11_msmarco_config_file.ipynb 4
def get_msmarco_config(data_dir, model, entity_type, suffix=''):
    mat_suffix = f'_{suffix}' if len(suffix) else ''
    raw_suffix = f'.{suffix}' if len(suffix) else ''
    return {
        f"data_{entity_type}-{model}{mat_suffix}": {
            "path": {
                "train": {
                    "data_lbl": f"{data_dir}/trn_X_Y{mat_suffix}.npz",
                    "data_info": f"{data_dir}/raw_data/train.raw.txt",
                    "lbl_info": f"{data_dir}/raw_data/label{raw_suffix}.raw.txt",
                    "ent_meta": {
                        "prefix": "ent",
                        "data_meta": f"{data_dir}/{entity_type}_{model}_trn_X_Y.npz",
                        "lbl_meta": f"{data_dir}/{entity_type}_{model}_lbl_X_Y{mat_suffix}.npz",
                        "meta_info": f"{data_dir}/raw_data/{model}_{entity_type}.raw.txt"
                    }
                },
                "test": {
                    "data_lbl": f"{data_dir}/tst_X_Y{mat_suffix}.npz",
                    "data_info": f"{data_dir}/XC/raw_data/test.raw.txt",
                    "lbl_info": f"{data_dir}/raw_data/label{raw_suffix}.raw.txt",
                    "ent_meta": {
                        "prefix": "ent",
                        "data_meta": f"{data_dir}/{entity_type}_{model}_tst_X_Y.npz",
                        "lbl_meta": f"{data_dir}/{entity_type}_{model}_lbl_X_Y{mat_suffix}.npz",
                        "meta_info": f"{data_dir}/raw_data/{entity_type}_{model}.raw.txt"
                    }
                }
            },
            "parameters": PARAM,
        }
    }

# %% ../nbs/11_msmarco_config_file.ipynb 5
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', type=str, required=True)
    parser.add_argument('--model', type=str, required=True)
    parser.add_argument('--entity_type', type=str, required=None)
    parser.add_argument('--suffix', type=str, default='')
    return parser.parse_args()
    

# %% ../nbs/11_msmarco_config_file.ipynb 7
if __name__ == '__main__':
    args = parse_args()
    
    config = get_msmarco_config(args.data_dir, args.model, args.entity_type, args.suffix)
    os.makedirs(f'{args.data_dir}/configs/', exist_ok=True)

    mat_suffix = f'_{args.suffix}' if len(args.suffix) else ''
    with open(f'{args.data_dir}/configs/{args.entity_type}_{args.model}{mat_suffix}.json', 'w') as file:
        json.dump(config, file, indent=4)
        
