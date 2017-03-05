#!/bin/bash
killall startxfce4
x11vnc -R stop
killall Xvfb
