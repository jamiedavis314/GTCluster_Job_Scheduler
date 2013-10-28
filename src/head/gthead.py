#!/usr/bin/python

#TODO tar -ztvf test.tar.gz  | awk 'NR < 2 {print $6}'
#TODO shut down cleanly in case of sigint. To do this, add a data structure 
#    keeping track of all of the sockets that are open (union of the sockets
#    holding open the freeNodeList and the busyNodeDict IPs)
#TODO style this like datetime
import cfg #constants

import os
import sys
import socket
from threading import Lock, Thread, Event
import select
from datetime import datetime
from string import strip
import time
import pwd
import comm

#print cfg.NODEIPORT

lock = Lock()
freeNodeList = [] # list of IPs
busyNodeDict = dict() # [ip] -> ( JobID, taskID )
jobProgressDict = dict() #  [JobID] -> nTasksCompleted
freeNodeListEvent = Event();

def main():
#    global lock
#    global freeNodeList
#    global busyNodeDict
        
          #paranoia
    freeNodeListEvent.clear();
    
    # start a thread that listens to node statuses and modifies the available nodes
    listenNodeStatuses = Thread( target=listen_statuses, args=() )
    listenNodeStatuses.start()

    listenJobRequests = Thread( target=listen_jobs, args=() )
    listenJobRequests.start()
    # start a thread that listens for user input

    listenNodeStatuses.join()
    listenJobRequests.join()

def listen_jobs():
    jobServSock = comm.open_serv_sock( cfg.USERIPORT )
    jobNum = -1
    while True:
        jobNum += 1
        #print "waiting for user conn"
        job_sock, job_ip = jobServSock.accept()

        print "Job connection made from user IP {0}".format(job_ip[0])
        jobDir = "{0}/{1}{2}".format(os.getcwd(), "jobDir", jobNum )
        os.mkdir(jobDir)
        listenJobStatusThread = Thread( target=listen_job, args=(job_sock, job_ip, jobNum, jobDir) )
#	print "listening for a job thread STARTING"
        listenJobStatusThread.start()

#sock, ip are the user's socket and ip
#jobDir is the full path of the temporary directory 
#created for this user's job
def listen_job(sock, ip, jobID, jobDir):
    global lock
    global freeNodeList
    global busyNodeDict
    ip = ip[0]

#    print "listening for a job from ip",ip
    istream = sock.makefile()

    #read msg 
    #msg has form /path/to/tgz \n port \n
    msg = []
    for i in range(0,2):
        msg.append( strip(istream.readline()) )# TODO deal with the situation where they connect and don't send anything (look in docs for timeout...)

    tarballName = msg[0].split("/")[-1]
    untarredName = tarballName.split(".")[:-2][0]

    #print "message read for the job, it was", msg

    #copy the specified file to the temp directory and untar
    os.system("scp {0}:{1} {2}".format(ip, msg[0], jobDir))

    print "Job received from IP {0}".format(ip)

#    print "untarring: from {0}/{1} to {0}/".format(jobDir, tarballName)
    os.system("tar xzf {0}/{1} -C {0}/".format(jobDir, tarballName))

    #TODO error checking
    
    #parse the user's job request file
    #print "{0}/{1}/{2}".format(jobDir, untarredName, "job.txt")
    jobFile = open("{0}/{1}/{2}".format(jobDir, untarredName, "job.txt"), 'r')
    jobList = jobFile.readlines()

    #pull off the uname@IP:/path/to/result/directory.tar.gz
    userPath = jobList[0].strip()
    jobList = jobList[1:]
    index = 0
    for task in jobList:
        jobList[index] = task.strip().split("|")
        index += 1        
    
    #now that we have the list of job requests, we need
    #to divvy them up to the nodes which are playing with us
    #print "job thread: ready to assign tasks"

    jobsAssigned = 0
    firstTimeThrough = True
    
    #we have made no progress on the job thus far
    lock.acquire()
    jobProgressDict[ jobID ] = 0
    lock.release()

    #if we have any jobs left, sleep/wakeup cycle
    while jobsAssigned < len(jobList):
        if not firstTimeThrough:
            freeNodeListEvent.wait() # block for free node
        else:
            firstTimeThrough = False
        lock.acquire()

        limitingFactor = min(len(jobList)-jobsAssigned,len(freeNodeList))
        for i in range(0,limitingFactor):
#	    print "job thread: assigning task number",jobList[jobsAssigned+i]
            assign_job( jobList[jobsAssigned+i], "{0}/{1}".format(jobDir, untarredName), freeNodeList[0], jobDir, jobID )
        jobsAssigned += limitingFactor

        #if there are no free nodes left, 
        #threads should wait on the event
        if len(freeNodeList) == 0:
            freeNodeListEvent.clear()

        lock.release() 

    print "Job thread ID {0}: All tasks assigned. Waiting for completion...".format(jobID)

    #now we have assigned all of our jobs
    #wait for all the jobs to be done
    while True:
        #TODO use a different lock
        #(this doesn't have aything to do with the free/busy lists)
        lock.acquire()
        #if all of our jobs are done, we're done!
	#(if jobID not yet in the progress dictionary, we're definitely not done)
	print "Job thread ID: {0}, # tasks completed = {1}. Total # tasks = {2}".format(jobID, jobProgressDict[jobID], len(jobList) )
#print "waiting for # to be {0}".format(len(jobList))
        if jobID in jobProgressDict and jobProgressDict[jobID] == len(jobList):
            lock.release()
#  	    print "job thread: all the tasks are done!"
            break        
        lock.release()
#        print "job thread: tasks not done yet. sleeping for 5 seconds..."
        time.sleep(5) #sleep for five seconds...
        
    print "Job thread ID {0}: All tasks done. Copying results back to user with IP {1}".format(jobID, ip)
    #all the jobs are done. 
    #tar up the directory, copy it back to U, and clean up
    #print "running the tar command:"
    #print "tar czf {0} -C {1} {2}".format(tarballName, jobDir, untarredName)
    os.system("tar czf {0} -C {1} {2}".format(tarballName, jobDir, untarredName))
    #print "running the following scp command:\n"
    #print "scp {0} {1}".format(tarballName, userPath)
    os.system("scp {0} {1}".format(tarballName, userPath))
    os.system("rm {0} -rf".format(jobDir))
    os.system("rm {0}".format(tarballName))

    #print "sending user: DONE"
    msg = bytearray("DONE\n")

    userSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    userSock.connect((ip, cfg.USEROPORT))
    userSock.send(msg)
    userSock.close()
    print "Job thread ID {0}: Done handling this job request.".format(jobID)

    return
        
#Task is a list (task_id, script.sh, tarballname)
def assign_job( task, taskPath, node_ip, jobDir, jobID ):
    global freeNodeList
    global busyNodeList
    
    #copy file to node, send message to node
    
    # TODO: Generalize to any username
#    print "running scp: ","scp {0}/{1} node@{2}:{3}".format(taskPath, task[2],node_ip,"/home/node/")
    os.system("scp {0}/{1} node@{2}:{3}".format(taskPath, task[2],node_ip,"/home/node/"))
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((node_ip, cfg.NODEOPORT))
    
    #TODO get the IP address instead of saying "@hydrogen"

    untarredFName = taskPath.rpartition('/')[2]

#    print "sending message"
#    print "{0}|{1}|{2}@hydrogen:{3}/{6}/{4}{5}.tar.gz \n".format(task[1],task[2],getuname(),jobDir,task[2],task[0], untarredFName)
    msg = bytearray("{0}|{1}|{2}@hydrogen:{3}/{6}/{4}{5}.tar.gz \n".format(task[1],task[2],getuname(),jobDir,task[2],task[0], untarredFName))
    s.send(msg)
    s.close()
    
    #modify data structures
    freeNodeList.remove(node_ip)
    busyNodeDict[node_ip] = [jobID, task[0]]
    

def listen_statuses():
#    global lock
#    global freeNodeList
#    global busyNodeDict

    statusServSock = comm.open_serv_sock( cfg.NODEIPORT )

    while True:
#        print "waiting for status conn"
        node_sock, node_ip = statusServSock.accept()
#        print "Status connection accepted"
        listenNodeStatusThread = Thread( target=listen_status, args=(node_sock, node_ip) )
        listenNodeStatusThread.start()

def listen_status(sock, ip):
    global lock
    global freeNodeList
    global busyNodeDict

    ip = ip[0]

    print "Task node with IP {0} is attempting to make a connection.".format(ip)

    istream = sock.makefile()
#    print "made an istream"
    msg = strip(istream.readline()) # TODO deal with the situation where they connect and don't send anything (look in docs for timeout...)
#    print "message read!",msg
    #convert string to integer
    try:
        msg = int( msg )
    except:
        msg = -1 #msg was no good; -1 is not cfg value
#    print "msg received from ip",ip,"it was",msg
    if msg != cfg.FREEMSG:
        print "Error listening to IP {0}: msg not free msg. Closing this connection...".format(ip)
        sock.close()
        return
    if ip in freeNodeList or ip in busyNodeDict: # IPs must be unique
        print "Error listening to IP {0}: ip address already in use. Closing this connection...".format(ip)
        sock.close()
        return
          
#    print "new node. appending to freeNodeList"
    lock.acquire()
    freeNodeList.append(ip)
    #in the event that anyone is waiting for this
    #to get set, we set it
    freeNodeListEvent.set()
    lock.release()

    print "Node with ip {0} accepted to list of task nodes.".format(ip)

    while True:
        msg = "NO MESSAGE"
        is_r = [sock]
        is_w = []
        is_err = []
        #selecting 
#        print "selecting"
        r, w, e = select.select(is_r, is_w, is_err, cfg.TIMEOUT)
#        print "done selecting"
        if sock in r:
 	   # print "Trying to read a message"
            msg = strip(istream.readline())
#  	    print "message read: .{0}.".format(msg)
#	    print "unstripped: .{0}.".format(ms1)
            try:
                msg = int( msg )
            except:
                msg = -1 #msg was no good; -1 is not cfg value

            if msg == cfg.BUSYMSG:
                lock.acquire()
                if ip in busyNodeDict:
                    lock.release()
#                    print "node ",ip,"is busy"
                    continue
                else:
                    lock.release()
                    print "ERROR: node {0} says it is BUSY but our records show it is FREE".format(ip)
            elif msg == cfg.FREEMSG:
                lock.acquire()
                if ip in freeNodeList:
#                    print "node ",ip,"is free"
                    lock.release()
                    continue
                else:
		    #this setup assumes that the node will send at least one busy msg
		    #upon receipt of a job. to that end, node sleeps for 1 second
		    #before acting on a job
#                    print "Announcement: node", ip, "is no longer busy (has finished its task). Adjusting jobProgressDict and setting the freeNodeList event."
                    info = busyNodeDict[ip]    
		    #move node from busy list to free list
		    del busyNodeDict[ip]
	  	    freeNodeList.append(ip)
#		    print "changing jobProgressDict[{0}] from {1} to {2}".format(info[0], jobProgressDict[info[0]], jobProgressDict[info[0]]+1)
                    jobProgressDict[ info[0] ] += 1
                    freeNodeListEvent.set()
                    lock.release()
        
            else: #if msg no good, we break and stuff
                break 
        else:
            break

    print "ERROR. Node with ip {0} has timed out or submitted an invalid message.\nNode being removed from the list of task nodes.".format(ip)
    print "message was:",msg
    lock.acquire()
    if ip in freeNodeList:
        freeNodeList.remove(ip)
    if ip in busyNodeDict:
        #TODO give his job to someone else
        del busyNodeDict[ip]
    lock.release()

    sock.close()
    return
    
def getuname():
    return pwd.getpwuid(os.getuid())[0]



#os.system("scp " + sys.argv[1] + " node@hydrogen:~")
#servesock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#servesock.bind(('', IPORT))
#servesock.listen(1)
#conn, addr = servesock.accept()

#sendsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#while True:
#    try:
#        sendsock.connect(('128.153.145.201', OPORT))
#    except:
#        continue
#    break
#msg = bytearray(sys.argv[2] + '|' + sys.argv[1] + '|' + 'kopptr@cosiwulf:/home/kopptr/output.tar.gz' + '\n')
#sendsock.send(msg)
#
#while True:
#    x = 1
#sendsock.close()
#servesock.close()
#
if __name__ == '__main__':
    main()
