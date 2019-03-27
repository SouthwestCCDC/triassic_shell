#!/bin/bash

cd /mnt/nfs/pcc/triassic_shell
source virtenv/bin/activate

TEAMNO=$1

python triassic_shell.py -f ../data/team$TEAMNO.pcc telnet -a 192.168.199.2 -p 23 &

sleep 3

python triassic_scoring.py -f ../data/team$TEAMNO.pcc -a 10.138.0.10$TEAMNO -p 80 &

while true; do
    python degrade_step.py -f ../data/team$TEAMNO.pcc
    sleep 60
done
