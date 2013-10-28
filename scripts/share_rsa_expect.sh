#!/usr/bin/expect -f
set pass [lindex $argv 0]
set host [lindex $argv 1]

spawn echo $pass
spawn echo $host

spawn ssh-copy-id node@$host
expect "*yes*" { send -- "yes\n" }
expect "*word*" { send -- "$pass\r" }
send -- "\r"
expect eof
