#!/bin/bash
#This script is run from *@cosiwulf[.cslabs.clarkson.edu]
#It assumes that gtcluster is running on the element cluster
#This script can be run as follows:
# $> ./execute_cluster_code.sh head_node file_to_execute email_address
#where 
#head_node is the gtcluster head node
#file_to_execute is the local path to the file we wish to execute
#email_address is the email address to which you wish "completion" notices sent
head_node=$1
file=$2
email=$3

#copy file to beryllium
scp $file node@beryllium:/home/node/
#execute gtclustersubmit on beryllium; background here and there
ssh node@beryllium "./gtcluster/src/user/gtclustersubmit.sh $head_node /home/node/$file $email &"
#NOTE the file is not copied back or cleaned up because it isn't on beryllium;
#the user is responsible for modifying the first line of $file/job.txt to direct it where 
#he wishes (possibly to node@[an element], possibly to *@cosiwulf, etc.)
