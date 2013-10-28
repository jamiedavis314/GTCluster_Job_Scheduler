#!/bin/bash
HEAD='hydrogen'
SLAVES=( hydrogen lithium beryllium nitrogen sodium magnesium aluminium silicon )

headID=`ssh node@$HEAD 'ps -ef' | grep gtcluster/src/head/gthead.py | awk '{ print $2}'`
ssh node@$HEAD "kill -9 $headID"
ssh node@$HEAD "rm -rf /home/node/jobDir*"

for slave in "${SLAVES[@]}"
do
	slaveID=`ssh node@$slave 'ps -ef' | grep gtcluster/src/node/gtnode.rb | awk '{ print $2}'`
	ssh node@$slave "kill -9 $slaveID"
done
