from sugar.amazon_helper import *
import os, gzip, json, numpy as np, argparse, scipy.sparse as sp, pandas as pd, pickle, multiprocessing as mp
from timeit import default_timer as timer
from tqdm.auto import tqdm

def read_file(fname, item_info):
    reviews = {}
    with gzip.open(fname, 'rt', encoding='utf-8') as f:
        records = [json.loads(d) for d in f]

    for record in records:
        user_id, item_id = record['reviewerID'], record['asin']

        review_text = record['reviewText'] if 'reviewText' in record else ''
        if 'summary' in record: review_text += record['summary']

        if item_id and len(item_id) > 0 and item_id in item_info:
            if user_id and len(user_id) > 0 and review_text and len(review_text) > 0:
                users = reviews.setdefault(item_id, {})
                o = users.setdefault(user_id, [])
                o.append(review_text)

    return reviews


def collate_reviews(files, item_info, output_dir):
    reviews = {}
    for file_idx,fname in tqdm(enumerate(files)):
        freviews = read_file(fname, item_info)

        for item_id, item_reviews in freviews.items():
            for user_id, user_reviews in item_reviews.items():
                o = reviews.setdefault(item_id, {})
                l = o.setdefault(user_id, [])
                l.extend(user_reviews)

    with open(f'{output_dir}/reviews.pkl', 'wb') as f:
        pickle.dump(reviews, f)


def fast_read_file(o):
    fname, item_info = o
    return read_file(fname, item_info)

def fast_collate_reviews(files, item_info, output_dir):
    nprocs = 2 #max(1, os.cpu_count()//2)
    with mp.Pool(nprocs) as pool:

        func_input = [(o, item_info) for o in files]

        file_idx = 1
        for reviews in tqdm(pool.imap(fast_read_file, func_input, chunksize=5), total=len(files)):
            with open(f'{output_dir}/reviews_{file_idx:02d}.pkl', 'wb') as f:
                pickle.dump(reviews, f)
            file_idx += 1

def fast_combine_reviews(files, output_dir):
    reviews = {}
    for file_idx in tqdm(range(len(files))):

        with open(f'{output_dir}/reviews_{file_idx+1:02d}.pkl', 'rb') as f:
            freviews = pickle.load(f)

        for item_id, item_reviews in freviews.items():
            for user_id, user_reviews in item_reviews.items():
                o = reviews.setdefault(item_id, {})
                l = o.setdefault(user_id, [])
                l.extend(user_reviews)

    with open(f'{output_dir}/reviews.pkl', 'wb') as f:
        pickle.dump(reviews, f)


def construct_pairs(review_file, output_dir):
    with open(review_file, 'r') as file:
        reviews = json.load(file)

    with open(f'{output_dir}/user-item_pairs.txt', 'w') as file:
        for item_id,rs in reviews.items():
            for user_id, texts in rs.items():
                for i in range(len(texts)):
                    file.write(f'{user_id}\t{item_id}\n')


def construct_matrix(review_file, output_dir):
    with open(review_file, 'r') as file:
        reviews = json.load(file)

    item2row, user2col = {}, {}

    data, indices, indptr = [], [], [0]
    for i,(item_id,rs) in tqdm(enumerate(reviews.items()), total=len(reviews)):
        assert item_id not in item2row, f"Duplicate item `{item_id}`."
        item2row[item_id] = i

        for user_id,texts in rs.items():
            c = user2col.setdefault(user_id, len(user2col))
            data.append(len(texts))
            indices.append(c)
        indptr.append(len(indices))

    matrix = sp.csr_matrix((data, indices, indptr), dtype=np.int32)
    sp.save_npz(f"{output_dir}/data_lbl.npz", matrix)

    data_info = pd.DataFrame({'identifier':list(item2row), 'id': list(item2row.values())})
    data_info.to_csv(f'{output_dir}/data_info.csv', index=False)

    lbl_info = pd.DataFrame({'identifier':list(user2col), 'id': list(user2col.values())})
    lbl_info.to_csv(f'{output_dir}/lbl_info.csv', index=False)


if __name__ == '__main__':
    start_time = timer()

    parser = argparse.ArgumentParser()
    parser.add_argument('--proc_type', type=str, required=True)

    parser.add_argument('--cache_dir', type=str)
    parser.add_argument('--item_info', type=str)

    parser.add_argument('--review_file', type=str)

    parser.add_argument('--output_dir', type=str, required=True)

    args = parser.parse_args()

    if args.proc_type == "reviews":
        # python sugar/reviews_a18.py --proc_type reviews --cache_dir data/amazon_review_2018/cache/reviews/
        # --item_info data/amazon_review_2018/products/all_item_ids.npy --output_dir data/amazon_review_2018/reviews/

        files = [f'{args.cache_dir}/{file}' for file in os.listdir(args.cache_dir) if file.endswith('.gz')]
        item_info = set(np.load(args.item_info, allow_pickle=True))

        # collate_reviews(files, item_info, args.output_dir)

        fast_collate_reviews(files, item_info, args.output_dir)

        # fast_combine_reviews(files, args.output_dir)

    elif args.proc_type == "pairs":
        construct_pairs(args.review_file, args.output_dir)

    elif args.proc_type == "matrix":
        # python sugar/reviews_a18.py --review_file data/amazon_review_2018/reviews_5-core/reviews.json
        # --output_file data/amazon_review_2018/reviews_5-core/

        construct_matrix(args.review_file, args.output_dir)


    end_time = timer()
    print(f'Time elapsed: {end_time-start_time:.2f} seconds.')

