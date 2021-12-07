#!/bin/bash

while getopts s:d flag
do
    case "${flag}" in
        s) source=${OPTARG};;
    esac
done
echo "Source: $source";
cd $source
pwd

animal_list=$(find $source -type d -name G71)
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
            if [ -f *Trial-01-ROI*.ti* ]; then
                if [ -f *Trial-01-ROI*.xls ]; then
                    continue 
                fi
            fi

            file_list=$(find $session -type f -name \*Trial-\[0-9\]\*)
            for file in $file_list
            do
                #readarray -d - -t arr <<< "$file" 

                #echo $file

                delimiter="-"
                concat_str="$file"$delimiter 

                arr=()
                while [[ $concat_str ]]; do
                    arr+=( "${concat_str%%"$delimiter"*}" )
                    concat_str=${concat_str#*"$delimiter"}
                done


                #for (( n=0; n < ${#arr[*]}; n++))
                #do
                    #echo "${arr[n]}"
                #done
                temp_str="${arr[1]}"

                old_file_num="${temp_str#"${temp_str%%[!0]*}"}"
                new_file_num=$(expr $old_file_num - 1)

                arr_len=${#arr[@]}

                new_file_name=${arr[0]}"_renamed-"


                if [ $new_file_num -lt 10 ] 
                then
                    new_file_name+="0"$new_file_num
                else
                    new_file_name+="$new_file_num"
                fi


                for (( i=2; i<$arr_len; i++ ))
                do
                    new_file_name+="-"${arr[$i]}
                done
                echo $old_file_num $new_file_num 

                if [ -f $new_file_name ]
                then
                    echo "ERROR : $new_file_name exists"
                else
                    mv $file $new_file_name
                fi
            done
            mmv \*_Trial_renamed-\* \#1_renamed_Trial-\#2
        done
    done
done

