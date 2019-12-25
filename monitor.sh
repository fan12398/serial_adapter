#!/bin/bash

# monitor script
# To monitor program running status, if not running, then start it

while [ true ]
do
    pro=$(ps -ef | grep "$1" | grep -v grep | grep -v "$0")
    # filter thread info, if pro is empty, means thread not running
    # inverse filter out prep thread and this thread, as these two thread contain dest name
    
    if [ -z "$pro" ]
    then 
        echo "Program not running, restart now"
		$1    # Restart program
	else
	    echo "Program is running..."
    fi
    sleep 30
done
