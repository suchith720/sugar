#!/bin/bash

# datasets="arguana climate-fever dbpedia fever fiqa hotpotqa msmarco nfcorpus nq quora raw_data scidocs scifact touche2020 trec-covid \
# 	cqadupstack/android cqadupstack/english cqadupstack/gaming cqadupstack/gis cqadupstack/mathematica cqadupstack/physics cqadupstack/programmers \
# 	cqadupstack/stats cqadupstack/tex cqadupstack/unix cqadupstack/webmasters cqadupstack/wordpress"

datasets="arguana climate-fever dbpedia fever fiqa hotpotqa nfcorpus nq quora scidocs scifact touche2020 trec-covid cqadupstack/android \
	cqadupstack/english cqadupstack/gaming cqadupstack/gis cqadupstack/mathematica cqadupstack/physics cqadupstack/programmers cqadupstack/stats \
	cqadupstack/tex cqadupstack/unix cqadupstack/webmasters cqadupstack/wordpress"

for dset in $datasets
do
	echo $dset
	python sugar/22_beir-config-file.py --data_dir /data/datasets/beir/$dset/XC 
done
