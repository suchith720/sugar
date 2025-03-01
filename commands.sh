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

python sugar/08_map-wikipedia-metadata.py --info_dir /home/scai/phd/aiz218323/scratch/datasets/wikipedia/20250123/info/ --data_dir /home/scai/phd/aiz218323/scratch/datasets/benchmarks/\(mapped\)LF-WikiTitles-500K/ --save_dir /home/scai/phd/aiz218323/scratch/datasets/wikipedia/20250123/LF-WikiTitles-500K/ --label_key category --metadata_key hyper_link --combine

