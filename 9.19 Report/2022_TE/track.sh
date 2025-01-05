UQSTR=MERRA2_jlgf
TEMPESTEXTREMESDIR=/home/skompella/tempestextremes/

FILELISTNAME=tracktext.txt
DATESTRING='20220101'
DCU_PSLFOMAG=200.0
DCU_PSLFODIST=5.5
DCU_WCFOMAG=-6.0
DCU_WCFODIST=6.5
DCU_WCMAXOFFSET=1.0
DCU_WCVAR="_DIFF(H(lev=300),H(lev=500h))"

starttime=$(date -u +"%s")
DATESTRING=`date +"%s%N"`
echo $DATESTRING
echo $starttime

PATHTOFILES=/home/cl4460/2022_Data/
DCU_MERGEDIST=6.0
SN_TRAJRANGE=8.0
SN_TRAJMINLENGTH=10
SN_TRAJMAXGAP=3
SN_MAXTOPO=150.0
SN_MAXLAT=50.0
SN_MINWIND=10.0
SN_MINLEN=10

sLP="T(lev=500)"     
# u10="0"       
# v10="0"        
Zs="H"           # Topographic variable


TRAJFILENAME=trajectories.txt.${UQSTR}
MONTHSTRARR=`seq 01 02`
for zz in ${MONTHSTRARR}
do
  echo 0$zz
  find ${PATHTOFILES} -name "*2022010${zz}*.nc" | sort -n >> $FILELISTNAME
done

STRDETECT="--out cyclones_tempest.${DATESTRING} --timestride 1 --closedcontourcmd $sLP,${DCU_PSLFOMAG},${DCU_PSLFODIST},0;${DCU_WCVAR},${DCU_WCFOMAG},${DCU_WCFODIST},${DCU_WCMAXOFFSET} --mergedist ${DCU_MERGEDIST} --searchbymin $sLP --outputcmd $sLP,min,0;$Zs,min,0"


TOPOFILE=/home/cl4460/2022_Data/MERRA2.topo.nc

echo $STRDETECT
echo ${TEMPESTEXTREMESDIR}bin/DetectNodes --in_data_list "${FILELISTNAME}" ${STRDETECT} </dev/null
${TEMPESTEXTREMESDIR}bin/DetectNodes --in_data_list "${FILELISTNAME}" ${STRDETECT} </dev/null
cat cyclones_tempest.${DATESTRING}* >> cyclones.${DATESTRING}
${TEMPESTEXTREMESDIR}bin/StitchNodes --in cyclones.${DATESTRING} --out "MERRA2_second_trail.dat" --in_fmt "time,lev,lat,lon,T,wind,H" --range ${SN_TRAJRANGE} --mintime "54h" --maxgap "24h" --threshold "wind,>=,10.0,10;lat,<=,50.0,10;lat,>=,-50.0,10;H,<=,${SN_MAXTOPO},${SN_MINLEN}" </dev/null



