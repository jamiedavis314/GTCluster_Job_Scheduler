#!/bin/bash
HEAD='hydrogen'
SLAVES=( hydrogen lithium beryllium nitrogen sodium magnesium aluminium silicon )

ssh node@$HEAD './gtcluster/src/head/gthead.py &' &

#ensure head is ready
sleep 5

for slave in "${SLAVES[@]}"
do
	ssh node@$slave './gtcluster/src/node/gtnode.rb hydrogen &' &
done
