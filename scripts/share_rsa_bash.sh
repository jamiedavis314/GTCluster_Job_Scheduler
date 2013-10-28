#!/bin/bash

#Which host are we on?
HOST=$(hostname)
#echo $HOST

#figure out which hosts aren't us!
POSSIBLE_HOSTS=( hydrogen lithium beryllium nitrogen sodium magnesium aluminium silicon )
i=0
while true; do
	#if it's not the current host, add it to the host list
#	echo ${POSSIBLE_HOSTS[$i]}
	if [ "$HOST" != "${POSSIBLE_HOSTS[$i]}" ]
	then
#		echo ${POSSIBLE_HOSTS[$i]}
		HOST_LIST[$i]=${POSSIBLE_HOSTS[$i]}
	else
		echo "Not equal"
	fi

	#check if we're done
	if [ ${POSSIBLE_HOSTS[$i]} == "silicon" ]
	then
		break
	fi

	i=$((i+1))

done

#print out hosts we got
for host in "${HOST_LIST[@]}"
do
	echo "Trying $host"
	./share_rsa_expect.sh nodepassword $host
done
