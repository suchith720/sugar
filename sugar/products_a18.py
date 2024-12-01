from sugar.amazon_helper import save_dataset, construct_dataset
import os, gzip, json, numpy as np, argparse
from timeit import default_timer as timer
from tqdm.auto import tqdm

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cache_dir', type=str, required=True)
    parser.add_argument('--output_dir', type=str, required=True)
    return parser.parse_args()

if __name__ == '__main__':
    start_time = timer()

    args = parse_args()

    files = [f'{args.cache_dir}/{file}' for file in os.listdir(args.cache_dir) if file.endswith('.gz')]
    item_info, item2row, item2col, matrix = construct_dataset(files)

    with open(f'{args.cache_dir}/item_info.json', 'w') as f:
        json.dump(item_info, f)

    items = set(list(item2row.keys()) + list(item2col.keys()))
    info = {o:item_info[o] for o in items}
    save_dataset(args.output_dir, matrix, item2row, item2col, info)

    end_time = timer()
    print(f'Time elapsed: {end_time-start_time:.2f} seconds.')

