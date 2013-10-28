#!/usr/bin/python
import socket

def open_serv_sock(port):
	statusServSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	statusServSock.bind(('', port))
	statusServSock.listen(5)
	return statusServSock

