from sugar.amazon_helper import *

if __name__ == '__main__':
    from timeit import default_timer as timer
    start_time = timer()

    args = parse_args()

    data_info = pd.read_csv(f'{args.output_dir}/data_info.csv')
    item2row = {identifier:i for identifier,i in enumerate(data_info['identifier'])}

    lbl_info = pd.read_csv(f'{args.output_dir}/lbl_info.csv')
    item2col = {identifier:i for identifier,i in enumerate(lbl_info['identifier'])}

    with open(f'{args.output_dir}/item_info.json', 'r') as f:
        item_info = json.load(f)

    item2category, data_category, lbl_category = construct_meta_dataset(item_info, item2row, item2col, 'category')
    save_category(args.output_dir, data_category, lbl_category, item2category, 'category')

    end_time = timer()
    print(f'Time elapsed: {end_time-start_time:.2f} seconds.')

