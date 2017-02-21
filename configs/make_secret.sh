#!/bin/bash
tar -czvf ~/secret.tgz ~/secret/*
gpg -c ~/secret.tgz
mv ~/secret.tgz.gpg .
