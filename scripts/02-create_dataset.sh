#!/bin/bash

datasets="arguana climate-fever dbpedia-entity fever fiqa hotpotqa nfcorpus nq quora scidocs scifact webis-touche2020 trec-covid \
	cqadupstack/android cqadupstack/english cqadupstack/gaming cqadupstack/gis cqadupstack/mathematica cqadupstack/physics \
	cqadupstack/programmers cqadupstack/stats cqadupstack/tex cqadupstack/unix cqadupstack/webmasters cqadupstack/wordpress"

for dset in $datasets
do
	python sugar/21_beir-dataset.py --data_dir /data/datasets/beir/$dset/ --save_dir /data/datasets/beir/$dset/XC/

	echo $dset
	echo ---------------

	data_dir="/data/datasets/beir"
	files="$data_dir/$dset/XC/trn_X_Y.npz $data_dir/$dset/XC/tst_X_Y.npz $data_dir/$dset/XC/raw_data/train.raw.csv \
		$data_dir/$dset/XC/raw_data/test.raw.csv $data_dir/$dset/XC/raw_data/label.raw.csv"
	for file in $files
	do
		if [ ! -f $file ]
		then
			echo $file
		fi
	done
	echo
done
