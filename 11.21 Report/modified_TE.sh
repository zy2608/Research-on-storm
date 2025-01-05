UQSTR=ERA5_2020
TEMPESTEXTREMESDIR=/home/zy2608/tempest_project/tempestextremes/
DATESTRING='202007'
DCU_PSLFOMAG=200.0 
DCU_PSLFODIST=5.5
DCU_WCFOMAG=-6.0   # Z300Z500 -6.0, T400 -0.4
DCU_WCFODIST=6.5
DCU_WCMAXOFFSET=1.0
DCU_WCVAR="_DIFF(H(300hPa),H(500hPa))"   #DCU_WCVAR generally _DIFF(Z300,Z500) or T400

TOPOFILE=/home/zy2608/tempest_project/ERA5.topo.nc
DATA_PATH=/home/ar4639/te_ready_merged/  # 数据文件目录
FILES=(
2020-07-01.nc 2020-07-02.nc 2020-07-03.nc 2020-07-04.nc
2020-07-05.nc 2020-07-06.nc 2020-07-07.nc 2020-07-08.nc
2020-07-09.nc 2020-07-10.nc 2020-07-11.nc 2020-07-12.nc
2020-07-13.nc 2020-07-14.nc 2020-07-15.nc 2020-07-16.nc
2020-07-17.nc 2020-07-18.nc 2020-07-19.nc 2020-07-20.nc
2020-07-21.nc 2020-07-22.nc 2020-07-23.nc 2020-07-24.nc
2020-07-25.nc 2020-07-26.nc 2020-07-27.nc 2020-07-28.nc
2020-07-29.nc 2020-07-30.nc 2020-07-31.nc
)

run_te_model() {
  FILENAME=$1
  DATESTRING=$(date +"%s%N")_$RANDOM  
  FILELISTNAME="ERA5_filelist_${DATESTRING}.txt"
  OUTPUT_FILE="NeuralGCM_${FILENAME}.dat"

  echo "${DATA_PATH}${FILENAME};${TOPOFILE};${TOPOFILE}" > $FILELISTNAME

  STRDETECT="--out cyclones_tempest.${DATESTRING} --timestride 1 --closedcontourcmd SLP,${DCU_PSLFOMAG},${DCU_PSLFODIST},0;${DCU_WCVAR},${DCU_WCFOMAG},${DCU_WCFODIST},${DCU_WCMAXOFFSET} --mergedist 6.0 --searchbymin SLP --outputcmd SLP,min,0;_VECMAG(U10M,V10M),max,2;PHIS,min,0"

  # DetectNodes
  ${TEMPESTEXTREMESDIR}bin/DetectNodes --in_data_list "${FILELISTNAME}" ${STRDETECT} </dev/null

  
  if [ $? -ne 0 ]; then
    echo "Error: DetectNodes failed for $FILENAME" >&2
    rm -f $FILELISTNAME
    return 1
  fi

  # StitchNodes
  ${TEMPESTEXTREMESDIR}bin/StitchNodes --in cyclones_tempest.${DATESTRING} --out "$OUTPUT_FILE" --in_fmt "lon,lat,slp,wind,PHIS" --range 8.0 --mintime "54h" --maxgap "24h" --threshold "wind,>=,10.0,10;lat,<=,50.0,10;lat,>=,-50.0,10;PHIS,<=,150.0,10" </dev/null

  
  if [ $? -ne 0 ]; then
    echo "Error: StitchNodes failed for $FILENAME" >&2
    rm -f $FILELISTNAME cyclones_tempest.${DATESTRING}*
    return 1
  fi

  # delete cyclones_tempest
  rm -f $FILELISTNAME cyclones_tempest.${DATESTRING}*
}

# max files running simultameously
MAX_JOBS=8
CURRENT_JOBS=0

for file in "${FILES[@]}"
do
  run_te_model "$file" &  
  CURRENT_JOBS=$((CURRENT_JOBS + 1))

  
  if [ "$CURRENT_JOBS" -ge "$MAX_JOBS" ]; then
    wait  
    CURRENT_JOBS=0  
  fi
done


wait

