#!/bin/bash
pushd ~
tar -czvf secret.tgz secret/*
gpg -c ~/secret.tgz
popd
mv ~/secret.tgz.gpg .
