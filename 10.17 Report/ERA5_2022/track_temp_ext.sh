# Path to TempestExtremes binaries on YS
UQSTR=ERA5_jlgf
TEMPESTEXTREMESDIR=/home/skompella/tempestextremes/
FILELISTNAME=ERA5_filelist.txt
DATESTRING='202201'
DCU_PSLFOMAG=200.0
DCU_PSLFODIST=5.5
DCU_WCFOMAG=-6.0   # Z300Z500 -6.0, T400 -0.4
DCU_WCFODIST=6.5
DCU_WCMAXOFFSET=1.0
DCU_WCVAR="_DIFF(H(300hPa),H(500hPa))"   #DCU_WCVAR generally _DIFF(Z300,Z500) or T400

starttime=$(date -u +"%s")
DATESTRING=`date +"%s%N"`
echo $DATESTRING
echo $starttime

PATHTOFILES=/home/cl4460/ERA5_2022/
DCU_MERGEDIST=6.0
SN_TRAJRANGE=8.0
SN_TRAJMINLENGTH=10
SN_TRAJMAXGAP=3
SN_MAXTOPO=150.0
SN_MAXLAT=50.0
SN_MINWIND=10.0
SN_MINLEN=10
sLP="SLP"
u10="U10M"
v10="V10M"
Zs="PHIS"
TRAJFILENAME=trajectories.txt.${UQSTR}
MONTHSTRARR=`seq 01 02`
for zz in ${MONTHSTRARR}
do
  echo 0$zz
#  find ${PATHTOFILES} -name "*19800${zz}*.nc" | sort -n >> $FILELISTNAME
done

STRDETECT="--out cyclones_tempest.${DATESTRING} --timestride 1 --closedcontourcmd $sLP,${DCU_PSLFOMAG},${DCU_PSLFODIST},0;${DCU_WCVAR},${DCU_WCFOMAG},${DCU_WCFODIST},${DCU_WCMAXOFFSET} --mergedist ${DCU_MERGEDIST} --searchbymin $sLP --outputcmd $sLP,min,0;_VECMAG($u10,$v10),max,2;$Zs,min,0"



TOPOFILE=/home/cl4460/ERA5_2022/ERA5.topo.nc
#TOPOFILE=ERA5.topo_tempest.nc

#sed -e 's?$?;'"${TOPOFILE}"'?' -i $FILELISTNAME

echo $STRDETECT
echo ${TEMPESTEXTREMESDIR}bin/DetectNodes --in_data_list "${FILELISTNAME}" ${STRDETECT} </dev/null
${TEMPESTEXTREMESDIR}bin/DetectNodes --in_data_list "${FILELISTNAME}" ${STRDETECT} </dev/null

cat cyclones_tempest.${DATESTRING}* >> cyclones.${DATESTRING}
#rm cyclones_tempest.${DATESTRING}*

${TEMPESTEXTREMESDIR}bin/StitchNodes --in cyclones.${DATESTRING} --out "ERA5_second_trail.dat" --in_fmt "lon,lat,slp,wind,PHIS" --range ${SN_TRAJRANGE} --mintime "54h" --maxgap "24h" --threshold "wind,>=,10.0,10;lat,<=,50.0,10;lat,>=,-50.0,10;PHIS,<=,${SN_MAXTOPO},${SN_MINLEN}" </dev/null
