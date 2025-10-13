#!/bin/bash

TASK="verify"

if [ $TASK == "download" ]
then
	datasets="arguana climate-fever dbpedia-entity fever fiqa hotpotqa nfcorpus nq quora scidocs scifact webis-touche2020 trec-covid cqadupstack"
	for dset in $datasets
	do
		read -p "Do you want to download $dset? (Y/n) : " choice
		if [[ $choice == "y" || $choice == "Y" ]]
		then
			python sugar/21_beir-dataset.py --download --dataset $dset --data_dir /data/datasets/beir/$dset/
		fi
	done

elif [ $TASK == "verify" ]
then
	datasets="arguana climate-fever dbpedia-entity fever fiqa hotpotqa nfcorpus nq quora scidocs scifact webis-touche2020 trec-covid \
		cqadupstack/android cqadupstack/english cqadupstack/gaming cqadupstack/gis cqadupstack/mathematica cqadupstack/physics \
		cqadupstack/programmers cqadupstack/stats cqadupstack/tex cqadupstack/unix cqadupstack/webmasters cqadupstack/wordpress"
	
	for dset in $datasets
	do
		echo $dset
		echo ---------------

		data_dir=/data/datasets/beir/$dset

		files="$data_dir/corpus.jsonl $data_dir/queries.jsonl $data_dir/generated-queries/train.jsonl $data_dir/qrels/train.tsv \
			$data_dir/qrels/dev.tsv $data_dir/qrels/test.tsv"
		for file in $files
		do
			if [ ! -f $file ]
			then
				echo $file
			fi
		done
		echo
	done
fi

