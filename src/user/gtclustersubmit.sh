#!/bin/bash
#gtclustersubmit.sh allows a user to submit job requests to the
#gtcluster head. 
#
#Usage: 
#$./gtclustersubmit head_ip /abs/path/to/jobs.tar.gz email_for_results
#e.g.
#$./gtclustersubmit hydrogen /home/node/... davisjc@clarkson.edu
#
#TODO error checking (on num_inputs and for the echoing and nc and whatnot

local_port=14142
head_ip=$1
head_port=31415
job_path=$2
email=$3

#send information to head
echo -e $job_path "\n" $local_port "\n" | nc $head_ip $head_port 

#listen for "DONE"
nc -l $local_port > isDone
echo "All done!" | mail -s "Data has been gathered" $email
