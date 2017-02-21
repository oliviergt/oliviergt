#!/bin/bash
pushd ~
chmod go-rwx ~/secret/*
tar -czvf secret.tgz secret/*
gpg -c ~/secret.tgz
rm ~/secret.tgz
popd
mv ~/secret.tgz.gpg .
