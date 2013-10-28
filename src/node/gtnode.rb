#!/usr/bin/ruby1.9.1
# This is the node program for gtcluster
# Usage: $./gtnode.rb IP.ADDRESS.OF.HEAD
#TODO error checking

require 'socket'

#This is what is executed when this script gets executed
def main
$status = 1
$homedir = "/home/node/"

hIP = ARGV[0]
inputPort = 16180
outputPort = 27182

#TODO this is awful
#open client connection to H
outputSock = TCPSocket.open(hIP, outputPort)

#ensure connections get established properly
statusThread = Thread.new{sendStatusMessage(outputSock)}

#open server; first client is the head node
inputServer = TCPServer.open(inputPort)

jobThread = Thread.new{receiveJobMessage(inputServer)}

jobThread.join
statusThread.join

end

#This function sends status message to the outputSock argument it received
#Observe that the status may get written incorrectly because we are not
#synchronizing; however, within 1 second the problem should fix itself. No biggie.
def sendStatusMessage(outputSock)
  while true
    sleep 3
    outputSock.puts $status
#    outputSock.write $status
#    outputSock.write "\n"
  end
end

#This function waits on the input port for messages of jobs to run.
#It parses the message -- of the form "cmd|tarballname|user@host:/place/to/put/it/and/filename".

#If the message is formatted incorrectly, it ignores the message.
#Else, it unzips the tarball and runs the job.
#It then rezips the directory, copies it back to the host, and sends an alert message.
#Upon completion, it deletes the directory.
#TODO error checking.
def receiveJobMessage(inputServer)
  while true	
puts "Node waiting for job"
    inputSock = inputServer.accept 
puts "Job received"
    msg = inputSock.readline.chomp
puts "Msg received, it was:"+msg
    $status = 2 #now we're running a job
    sleep 5 #Forces node to send at least one busy message before finishing a task
    msg = msg.split "|" 
    next unless msg.length == 3 #ensure it's the right form
    #split up msg
    cmd = msg[0]
    tarball = msg[1]
    dir = msg[1][0..-8]
    end_loc = msg[2]

    #navigate to the home directory, untar the file, delete the tarball
    Dir.chdir $homedir 
    `tar xfz #{tarball}`
    `rm #{tarball}` 

    #enter the file, execute the command
    Dir.chdir "#{$homedir + dir}" 
    `./#{cmd}` 
puts "Done executing command"

    #tar up the result, send it back to the specified end location,and clean up
    Dir.chdir $homedir 
    `tar cfz #{tarball} #{dir}` 

    `scp #{tarball} #{end_loc}`
    `rm #{tarball}` 
    `rm #{dir} -rf ` 

    #change our status; we're done running a job
    $status=1
    inputSock.close
#puts "Ending -- back to top of loop!"
  end
end

#run main
main

