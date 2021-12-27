#!/bin/sh

case $1 in
    send)
         PYTHONPATH=./ python ./send_health_probes.py
	 ;;
    check)
         PYTHONPATH=./ python ./check_health_probes.py
	 ;;
    *)
	 echo "Usage: $1 <send|check>"
	 ;;
esac
