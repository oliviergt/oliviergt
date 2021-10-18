#!/bin/bash
sudo apt-get install git tmux
git clone https://github.com/oliviergt/oliviergt.git
tmux new oliviergt/configs/setup.py
