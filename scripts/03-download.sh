#!/bin/bash

TASK="download"

if [ $TASK == "download" ]
then
	datasets="arguana climate-fever dbpedia fever fiqa hotpotqa nfcorpus nq quora scidocs scifact touche2020 trec-covid cqadupstack"
	for dset in $datasets
	do
		read -p "Press Enter to download $dset ..."
		python sugar/21_beir-dataset.py --download --dataset $dset --data_dir /data/datasets/beir/$dset/
	done

elif [ $TASK == "format" ]
then
	datasets="arguana climate-fever dbpedia fever fiqa hotpotqa nfcorpus nq quora scidocs scifact touche2020 trec-covid cqadupstack/android \
		cqadupstack/english cqadupstack/gaming cqadupstack/gis cqadupstack/mathematica cqadupstack/physics cqadupstack/programmers \
		cqadupstack/stats cqadupstack/tex cqadupstack/unix cqadupstack/webmasters cqadupstack/wordpress"
fi
