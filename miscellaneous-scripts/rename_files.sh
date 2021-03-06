#!/bin/bash

while getopts s:d flag
do
  case "${flag}" in
    s) source=${OPTARG};;
    #d) dest=${OPTARG};;
  esac
done
echo "Source: $source";
cd $source
pwd

animal_list=$(find $source -type d -name [Gg]\*)
for animal in $animal_list
do
  cd $animal
  pwd
  day_list=$(find $animal -type d -name 20\*)
  for day in $day_list
  do
    cd $day
    pwd
    session_num_list=$(find $day -type d -name \[0-9])
    for session in $session_num_list
    do
      cd $session
      pwd
      if [[ $animal =~ .*G[0-9].* ]]; then 
        echo $(ls G*.tif | wc -l)
        mmv \*_Trial-\[0-9]-\*.tif \#1_Trial-0\#2-\#3.tif
        mmv \*_Trial-\[0-9]-\*.xls \#1_Trial-0\#2-\#3.xls
        echo $(ls G*.tif | wc -l)
      fi
      if [[ $animal =~ .*g[0-9].* ]]; then 
        echo $(ls *.tif* | wc -l)
        mmv Trial\[0-9]-\*.tif Trial-0\#1-\#2.tif
        mmv Trial\[0-9]-\*.xls Trial-0\#1-\#2.xls
        mmv Trial\[0-9]\[0-9]-\*.tif Trial-\#1\#2-\#3.tif
        mmv Trial\[0-9]\[0-9]-\*.xls Trial-\#1\#2-\#3.xls
        echo $(ls *.tif* | wc -l)
      fi
    done
  done
done

