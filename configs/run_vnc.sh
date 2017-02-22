#!/bin/bash
Xvfb :0 -ac -screen 0 1024x768x24
x11vnc -ncache 10 -ncache_cr -display :0 -forever -shared  -bg -noipv6 -rfbauth ~/.vnc/passwd
