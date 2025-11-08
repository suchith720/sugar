#!/bin/bash

datasets="msmarco arguana climate-fever dbpedia-entity fever fiqa hotpotqa nfcorpus nq quora scidocs scifact webis-touche2020 trec-covid \
	cqadupstack/android cqadupstack/english cqadupstack/gaming cqadupstack/gis cqadupstack/mathematica cqadupstack/physics \
	cqadupstack/programmers cqadupstack/stats cqadupstack/tex cqadupstack/unix cqadupstack/webmasters cqadupstack/wordpress"

for dset in $datasets
do
	data_dir="/data/datasets/beir"
	save_dir="/data/datasets/beir"

	python sugar/21_beir-dataset.py --data_dir $data_dir/$dset/ --save_dir $save_dir/$dset/XC/ 

	echo $dset
	echo ---------------

	files="$save_dir/$dset/XC/trn_X_Y.npz $save_dir/$dset/XC/tst_X_Y.npz $save_dir/$dset/XC/raw_data/train.raw.csv \
		$save_dir/$dset/XC/raw_data/test.raw.csv $save_dir/$dset/XC/raw_data/label.raw.csv"
	for file in $files
	do
		if [ ! -f $file ]
		then
			echo $file
		fi
	done
	echo
done
