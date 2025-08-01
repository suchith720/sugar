# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/19_map-amazon-meta-from-gpt-generations.ipynb.

# %% auto 0
__all__ = ['extract_text_between_tags', 'extract_generations', 'get_file_key', 'collate_generations', 'collate_metadata',
           'map_generation_to_data', 'extract_and_save_generations', 'parse_args']

# %% ../nbs/19_map-amazon-meta-from-gpt-generations.ipynb 2
import pandas as pd, re, numpy as np, os, scipy.sparse as sp
from tqdm.auto import tqdm

# %% ../nbs/19_map-amazon-meta-from-gpt-generations.ipynb 3
from .core import *

# %% ../nbs/19_map-amazon-meta-from-gpt-generations.ipynb 5
def extract_text_between_tags(text, tag='Label'):
    pattern = fr"<{tag}>(.*?)</{tag}>"
    match = re.search(pattern, text)
    return match.group(1).strip() if match else ''
    

# %% ../nbs/19_map-amazon-meta-from-gpt-generations.ipynb 6
def extract_generations(df, tag='Label'):
    generations = []
    for i in range(df.shape[0]):
        text = df['raw_model_response'].iloc[i]
        text = extract_text_between_tags(text, tag=tag)
        generations.append(text)
    title = df['title'].tolist()
    return title, generations
    

# %% ../nbs/19_map-amazon-meta-from-gpt-generations.ipynb 7
def get_file_key(fname):
    key = re.match(r'[a-z]*([0-9]+).tsv', fname)
    return int(key.group(1))
    

# %% ../nbs/19_map-amazon-meta-from-gpt-generations.ipynb 8
def collate_generations(data_dir, tag='Label'):
    title, generations = [], []

    for fname in tqdm(sorted(os.listdir(data_dir), key=get_file_key)):
        df = pd.read_table(f'{data_dir}/{fname}')
        df.fillna('', inplace=True)
        t, g = extract_generations(df, tag=tag)
        title.extend(t)
        generations.extend(g)

    return title, generations
    

# %% ../nbs/19_map-amazon-meta-from-gpt-generations.ipynb 9
def collate_metadata(data_dir, tag, sep=None):
    title, generation = collate_generations(data_dir, tag=tag)
    metadata = [[text] if sep is None else [o.strip(sep) for o in text.split(sep)] for text in generation]
    return title, metadata
    

# %% ../nbs/19_map-amazon-meta-from-gpt-generations.ipynb 23
def map_generation_to_data(data_dir, gen_title, gen_meta_text, data_type='test', prepend_title=True):
    fname = f'{data_dir}/test.raw.txt' if data_type == 'test' else f'{data_dir}/train.raw.txt'
    ids, text = load_raw_file(fname)
    
    mapping = {k:v for k,v in zip(gen_title, gen_meta_text)}
    if prepend_title: meta_text = [f'{o} :: {mapping[o]}' if o in mapping else o for o in text]
    else: meta_text = [mapping.get(o, '') for o in text]

    return ids, text, meta_text


# %% ../nbs/19_map-amazon-meta-from-gpt-generations.ipynb 33
def extract_and_save_generations(generation_dir, data_dir, data_type, tag, save_tag, prepend_title):
    gen_title, gen_text = collate_generations(generation_dir, tag=tag)

    ids, text, meta_text = map_generation_to_data(data_dir, gen_title, gen_text, data_type, prepend_title)
    
    fname = f'{data_dir}/test_{save_tag}.raw.txt' if data_type == 'test' else f'{data_dir}/train_{save_tag}.raw.txt'
    save_raw_file(fname, ids, meta_text) 
    

# %% ../nbs/19_map-amazon-meta-from-gpt-generations.ipynb 65
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--generation_dir', type=str, required=True)
    parser.add_argument('--data_dir', type=str, required=True)
    parser.add_argument('--tag', type=str, default='Label')
    parser.add_argument('--data_type', type=str, default=None)
    parser.add_argument('--save_tag', type=str, default='entity')
    return parser.parse_args()
    

# %% ../nbs/19_map-amazon-meta-from-gpt-generations.ipynb 66
if __name__ == '__main__':
    start_time = timer()

    args = parse_args()
    extract_and_save_generations(args.generation_dir, args.data_dir, args.data_type, args.tag, args.save_tag)
    
    end_time = timer()
    print(f'Time elapsed: {end_time-start_time:.2f} seconds.')
    
