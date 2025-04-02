# Download wikipedia dataset
python sugar/04_download-wikipedia-dataset.py --project enwiki --date 20250123 --cache_dir /home/scai/phd/aiz218323/scratch/datasets/wikipedia/20250123/dumps/
python sugar/04_download-wikipedia-dataset.py --project enwiki --date 20241120 --cache_dir /home/scai/phd/aiz218323/scratch/datasets/wikipedia/20241120/dumps/

# Download amazon dataset
python sugar/03_download-amazon-dataset.py --dfrom hf --dtype meta --cache_dir /home/scai/phd/aiz218323/scratch/datasets/amazon/dumps/

# Parse wikipedia dump
python sugar/06_parse-wikipedia-dump.py --index_source /home/scai/phd/aiz218323/scratch/datasets/wikipedia/20250123/dumps/enwiki-20250123-pages-articles-multistream-index.txt.bz2 --articles_source /home/scai/phd/aiz218323/scratch/datasets/wikipedia/20250123/dumps/enwiki-20250123-pages-articles-multistream.xml.bz2 --cache_dir /home/scai/phd/aiz218323/scratch/datasets/wikipedia/20250123/info/

python sugar/06_parse-wikipedia-dump.py --index_source /home/scai/phd/aiz218323/scratch/datasets/wikipedia/20241120/dumps/enwiki-20241120-pages-articles-multistream-index.txt.bz2 --articles_source /home/scai/phd/aiz218323/scratch/datasets/wikipedia/20241120/dumps/enwiki-20241120-pages-articles-multistream.xml.bz2 --cache_dir /home/scai/phd/aiz218323/scratch/datasets/wikipedia/20241120/info

# Extract metadata from wikipedia dump
python sugar/08_map-wikipedia-metadata.py --info_dir /home/scai/phd/aiz218323/scratch/datasets/wikipedia/20250123/info/ --data_dir /home/scai/phd/aiz218323/scratch/datasets/benchmarks/\(mapped\)LF-WikiSeeAlsoTitles-320K/ --save_dir /home/scai/phd/aiz218323/scratch/datasets/wikipedia/20250123/LF-WikiSeeAlsoTitles-320K/ --label_key see_also --metadata_key category --combine

python sugar/08_map-wikipedia-metadata.py --info_dir /home/scai/phd/aiz218323/scratch/datasets/wikipedia/20241120/info/ --data_dir /home/scai/phd/aiz218323/scratch/datasets/benchmarks/\(mapped\)LF-WikiSeeAlsoTitles-320K/ --save_dir /home/scai/phd/aiz218323/scratch/datasets/wikipedia/20241120/LF-WikiSeeAlsoTitles-320K/ --label_key see_also --metadata_key category --combine

python sugar/08_map-wikipedia-metadata.py --info_dir /home/scai/phd/aiz218323/scratch/datasets/wikipedia/20250123/info/ --data_dir /home/scai/phd/aiz218323/scratch/datasets/benchmarks/\(mapped\)LF-WikiTitles-500K/ --save_dir /home/scai/phd/aiz218323/scratch/datasets/wikipedia/20250123/LF-WikiTitles-500K/ --label_key category --metadata_key hyper_link --combine

# Extract metadata from amazon dump
python sugar/05_map-amazon-meta-from-dump.py --cache_dir /home/scai/phd/aiz218323/scratch/datasets/amazon/dumps/raw/meta_categories/ --data_dir /home/scai/phd/aiz218323/scratch/datasets/benchmarks/LF-Amazon-131K/ --key parent_asin --condition_type a23 --metadata_type videos

# Download MSMARCO dump
python sugar/09_msmarco-dataset.py --data_dir /home/scai/phd/aiz218323/scratch/datasets/msmarco/ --download

# Create MSMARCO dataset
python sugar/09_msmarco-dataset.py --data_dir /home/scai/phd/aiz218323/scratch/datasets/msmarco/ --save_dir /home/scai/phd/aiz218323/scratch/datasets/msmarco/XC

# Extract entities for MSMARCO
python sugar/10_msmarco-generated-entities.py --data_dir /home/scai/phd/aiz218323/scratch/datasets/msmarco/XC/ --entity_dir /home/scai/phd/aiz218323/scratch/datasets/msmarco/entities/gpt/ --entity_type entity --model gpt

python sugar/10_msmarco-generated-entities.py --data_dir /home/scai/phd/aiz218323/scratch/datasets/msmarco/XC/ --entity_dir /home/scai/phd/aiz218323/scratch/datasets/msmarco/entities/llama/ --entity_type entity --model llama

# Config for MSMARCO
python sugar/11_msmarco-config-file.py --data_dir /home/scai/phd/aiz218323/scratch/datasets/msmarco/XC/ --model gpt --entity_type entity
python sugar/11_msmarco-config-file.py --data_dir /home/scai/phd/aiz218323/scratch/datasets/msmarco/XC/ --model llama --entity_type entity

python sugar/15_wikipedia-config-file.py --data_dir /home/scai/phd/aiz218323/scratch/datasets/wikipedia/20250123/LF-WikiSeeAlsoTitles-320K/ --metadata_type category --x_prefix old --y_prefix new --z_prefix combined --raw_ext csv

python sugar/17_map-amazon-reviews-from-dump.py --cache_dir /home/scai/phd/aiz218323/scratch/datasets/amazon/dumps/raw/review_categories/ --data_dir /home/scai/phd/aiz218323/scratch/datasets/benchmarks/\(mapped\)LF-AmazonTitles-1.3M/ --key parent_asin --condition_type a23 --review_type title_text

python sugar/18_map-amazon-meta-from-dump.py --cache_dir /home/scai/phd/aiz218323/scratch/datasets/amazon/dumps/raw/meta_categories/ --data_dir /home/scai/phd/aiz218323/scratch/datasets/benchmarks/\(mapped\)LF-AmazonTitles-1.3M/ --key parent_asin --condition_type a23 --metadata_type description

python sugar/18_map-amazon-meta-from-dump.py --cache_dir /home/scai/phd/aiz218323/scratch/datasets/amazon/dumps/raw/meta_categories/ --data_dir /home/scai/phd/aiz218323/scratch/datasets/benchmarks/\(mapped\)LF-AmazonTitles-1.3M/ --key parent_asin --condition_type a23 --metadata_type description --no_filter
