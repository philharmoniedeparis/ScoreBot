#!/bin/sh

### Check the capability to merge with protected branch :  build docker image with an up to date code ###
### Author : Dany Rafina <danyrafina@gmail.com> ###
### Version : 1.0 ###
### Last update : 2021-03-11 ###
if git merge-base --is-ancestor $1 @
then
  echo "Your branch is up to date."
  exit 0
else
  echo "You need to merge / rebase."
  exit 1
fi
