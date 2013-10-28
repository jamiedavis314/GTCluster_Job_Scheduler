#!/bin/bash
fname='share_rsa_bash.sh'
fname2='share_rsa_expect.sh'
#for node in 'hydrogen' 'helium' 'lithium' 'beryllium' 'sodium' 'magnesium' 'aluminium' 'silicon' ; do
for node in 'hydrogen' 'lithium' 'beryllium' 'nitrogen' 'sodium' 'magnesium' 'aluminium' 'silicon' ; do
	echo "Copying files to "
	echo $node
	scp $fname node@$node:/home/node/
	scp $fname2 node@$node:/home/node/
#	ssh node@$node tar -zxvf $fname 
done

exit
