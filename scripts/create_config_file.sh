#!/bin/bash
datasets="nq hotpotqa fever dbpedia quora"
for dset in $datasets
do
	echo $dset
	python sugar/22_beir-config-file.py --data_dir /data/datasets/$dset/XC --add_trn_cfg 1 --add_linker_cfg 0
done

datasets="fiqa trec-covid climate-fever scifact scidocs arguana nfcorpus"
for dset in $datasets
do
	echo $dset
	python sugar/22_beir-config-file.py --data_dir /data/datasets/$dset/XC --add_trn_cfg 1 --add_linker_cfg 0 --main_max_lbl_sequence_length 512
done
