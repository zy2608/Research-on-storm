# Path to TempestExtremes binaries on YS
UQSTR=NeuralGCM_jlgf
TEMPESTEXTREMESDIR=/home/skompella/tempestextremes/
FILELISTNAME=NeuralGCM.txt
DATESTRING='202007'  # Detection Control Unit
DCU_PSLFOMAG=200.0  # SLP increase of at least 0.6 hPa (60 Pa)
DCU_PSLFODIST=5.5  # GCD radius for SLP increase
DCU_WCFOMAG=-6.0  # Geopotential height difference decrease of at least 58.8 m²/s²   
DCU_WCFODIST=6.5  # GCD radius for geopotential height difference
DCU_WCMAXOFFSET=1.0  # Max offset for candidate geopotential
DCU_WCVAR="_DIFF(H(300hPa),H(500hPa))"   # Variable for geopotential height difference
# DCU_WCVAR="_DIFF(H300,H500)"



starttime=$(date -u +"%s")
DATESTRING=`date +"%s%N"`
echo $DATESTRING
echo $starttime

PATHTOFILES=/home/cl4460/NeuralGCM/  # Storm Tracking
DCU_MERGEDIST=6.0  # Merge distance
SN_TRAJRANGE=8.0  # Max allowable distance between consecutive candidates
SN_TRAJMINLENGTH=10  # Minimum trajectory length (in time steps)
SN_TRAJMAXGAP=3  # Maximum allowable gap size (number of time steps)
SN_MAXTOPO=150.0  # Increased maximum topography height to match data units
SN_MAXLAT=50.0  # Maximum latitude for storm formation   
SN_MINWIND=10.0  # Minimum wind speed
SN_MINLEN=10  # Reduced minimum number of time steps for thresholds
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



TOPOFILE=/home/cl4460/NeuralGCM/topo.nc
#TOPOFILE=ERA5.topo_tempest.nc

#sed -e 's?$?;'"${TOPOFILE}"'?' -i $FILELISTNAME

echo $STRDETECT
echo ${TEMPESTEXTREMESDIR}bin/DetectNodes --in_data_list "${FILELISTNAME}" ${STRDETECT} </dev/null
${TEMPESTEXTREMESDIR}bin/DetectNodes --in_data_list "${FILELISTNAME}" ${STRDETECT} </dev/null

cat cyclones_tempest.${DATESTRING}* >> cyclones.${DATESTRING}
#rm cyclones_tempest.${DATESTRING}*

${TEMPESTEXTREMESDIR}bin/StitchNodes --in cyclones.${DATESTRING} --out "NeuralGCM_onemonth.dat" --in_fmt "lon,lat,slp,wind,PHIS" --range ${SN_TRAJRANGE} --mintime "54h" --maxgap "24h" --threshold "wind,>=,10.0,10;lat,<=,50.0,10;lat,>=,-50.0,10;PHIS,<=,${SN_MAXTOPO},${SN_MINLEN}" </dev/null
