#!/bin/bash

UQSTR=ERA5_2020
TEMPESTEXTREMESDIR=/home/cl4460/NeuralGCM_1.4/tempestextremes/
DCU_PSLFOMAG=60.0 
DCU_PSLFODIST=5.5
DCU_WCFOMAG=-2.6327   
DCU_WCFODIST=6.5
DCU_WCMAXOFFSET=1.0
DCU_WCVAR="_DIFF(H(300hPa),H(500hPa))"   
TOPOFILE=/home/cl4460/NeuralGCM_1.4/ERA5.topo.nc
DATA_PATH=/home/ar4639/te_ready_1_4/  


OUTPUT_PATH=/home/cl4460/NeuralGCM_1.4/1.4_resolution_output_files/
mkdir -p "$OUTPUT_PATH"
MAX_JOBS=8

# Define processing function
run_te_model() {
  local FILEPATH="$1"
  local FILENAME
  FILENAME=$(basename "$FILEPATH")
  local DATESTRING
  DATESTRING=$(date +"%s%N")_$RANDOM  
  local FILELISTNAME="ERA5_filelist_${DATESTRING}.txt"
  local OUTPUT_FILE="${OUTPUT_PATH}NeuralGCM_${FILENAME%.nc}.dat"  

  # Create a list of files without the quotes
  echo "${FILEPATH};${TOPOFILE};${TOPOFILE}" > "$FILELISTNAME"

  local STRDETECT="--out cyclones_tempest.${DATESTRING} --timestride 1 --closedcontourcmd SLP,${DCU_PSLFOMAG},${DCU_PSLFODIST},0;${DCU_WCVAR},${DCU_WCFOMAG},${DCU_WCFODIST},${DCU_WCMAXOFFSET} --mergedist 6.0 --searchbymin SLP --outputcmd SLP,min,0;_VECMAG(U10M,V10M),max,2;PHIS,min,0"

  # Do DetectNodes and make a log
  "${TEMPESTEXTREMESDIR}bin/DetectNodes" --in_data_list "${FILELISTNAME}" ${STRDETECT} </dev/null
  if [ $? -ne 0 ]; then
    echo "Error: DetectNodes failed for \"$FILENAME\"" >&2
    rm -f "$FILELISTNAME"
    return 1
  fi

  # Execute StitchNodes and log
  "${TEMPESTEXTREMESDIR}bin/StitchNodes" --in "cyclones_tempest.${DATESTRING}" --out "$OUTPUT_FILE" \
    --in_fmt "lon,lat,slp,wind,PHIS" --range 8.0 --mintime "54h" --maxgap "24h" \
    --threshold "wind,>=,10.0,10;lat,<=,50.0,10;lat,>=,-50.0,10;PHIS,<=,150.0,10" </dev/null
  if [ $? -ne 0 ]; then
    echo "Error: StitchNodes failed for \"$FILENAME\"" >&2
    rm -f "$FILELISTNAME" cyclones_tempest.${DATESTRING}*
    return 1
  fi
  rm -f "$FILELISTNAME" cyclones_tempest.${DATESTRING}*
}

# Export necessary variables and functions for use by child processes
export TEMPESTEXTREMESDIR DATA_PATH TOPOFILE DCU_PSLFOMAG DCU_PSLFODIST \
       DCU_WCFOMAG DCU_WCFODIST DCU_WCMAXOFFSET DCU_WCVAR OUTPUT_PATH
export -f run_te_model

# Use find and xargs to handle filenames that contain Spaces and control the number of parallel tasks
find "$DATA_PATH" -type f -name '*.nc' -print0 | xargs -0 -I {} -P "$MAX_JOBS" bash -c 'run_te_model "$@"' _ "{}"
wait

echo "Processing of all.nc files is complete."
