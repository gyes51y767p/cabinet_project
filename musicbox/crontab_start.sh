#!/bin/bash
PATH=$PATH:/home/admin/projects/cabinet_project/musicbox/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/local/games:/usr/games

cd /home/admin/projects/cabinet_project/musicbox
echo "Waiting 30 seconds for system to settle..."
sleep 15
echo "starting musicbox now..."
#/home/admin/projects/cabinet_project/musicbox/venv/bin/python musicbox.py > /home/admin/projects/cabinet_project/musicbox/log/musicbox.log 2>&1
/home/admin/projects/cabinet_project/musicbox/venv/bin/python musicbox.py 
echo "musicbox exited early"
#/home/admin/projects/cabinet_project/musicbox/venv/bin/python helloworld.py > /home/admin/projects/cabinet_project/musicbox/log/hello.log 2>&1


