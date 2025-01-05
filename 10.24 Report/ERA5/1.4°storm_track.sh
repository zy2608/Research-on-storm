# Path to TempestExtremes binaries
UQSTR=ERA5_jlgf
TEMPESTEXTREMESDIR=/home/skompella/tempestextremes/
FILELISTNAME=ERA5_filelist.txt
DATESTRING=$(date +"%Y%m%d%H%M%S")
echo $DATESTRING

PATHTOFILES=/home/cl4460/NeuralGCM/

# Adjusted parameters for 1.4° resolution
DCU_PSLFOMAG=60.0    # SLP increase of at least 0.6 hPa (60 Pa)
DCU_PSLFODIST=5.5    # GCD radius for SLP increase
DCU_WCFOMAG=-25.8    # Geopotential height difference decrease of at least 25.8 m²/s²
DCU_WCFODIST=6.5     # GCD radius for geopotential height difference
DCU_WCMAXOFFSET=1.0  # Max offset for candidate geopotential
DCU_WCVAR="_DIFF(H(300hPa),H(500hPa))"   # Variable for geopotential height difference

DCU_MERGEDIST=6.0    # Merge distance
SN_TRAJRANGE=8.0     # Max allowable distance between consecutive candidates
SN_TRAJMINLENGTH=1  # Minimum trajectory length (in time steps)
SN_TRAJMAXGAP=3      # Maximum allowable gap size (number of time steps)
SN_MAXTOPO=150.0   # Increased maximum topography height to match data units
SN_MAXLAT=50.0       # Maximum latitude for storm formation
SN_MINLEN=1          # Reduced minimum number of time steps for thresholds

sLP="SLP"
Zs="PHIS"  # Surface geopotential height
TRAJFILENAME=trajectories.txt.${UQSTR}

# Generate file list (update this section based on your data files)
MONTHSTRARR=$(seq -w 1 12)
for zz in ${MONTHSTRARR}
do
  echo 0$zz
#  find ${PATHTOFILES} -name "*2022${zz}*.nc" | sort -n >> $FILELISTNAME
done


STRDETECT="--out cyclones_tempest.${DATESTRING} --timestride 1 --closedcontourcmd $sLP,${DCU_PSLFOMAG},${DCU_PSLFODIST},0;${DCU_WCVAR},${DCU_WCFOMAG},${DCU_WCFODIST},${DCU_WCMAXOFFSET} --mergedist ${DCU_MERGEDIST} --searchbymin $sLP --outputcmd $sLP,min,0;$Zs,min,0"


# Path to topography file
TOPOFILE=/home/cl4460/NeuralGCM/ERA5.topo.nc

# Uncomment and modify the following line if you need to append the topography file to your file list
# sed -e 's?$?;'"${TOPOFILE}"'?' -i $FILELISTNAME

echo $STRDETECT
echo ${TEMPESTEXTREMESDIR}bin/DetectNodes --in_data_list "${FILELISTNAME}" ${STRDETECT} </dev/null
${TEMPESTEXTREMESDIR}bin/DetectNodes --in_data_list "${FILELISTNAME}" ${STRDETECT} </dev/null

# Combine the output files
cat cyclones_tempest.${DATESTRING}* >> cyclones.${DATESTRING}
# rm cyclones_tempest.${DATESTRING}*


${TEMPESTEXTREMESDIR}bin/StitchNodes --in cyclones.${DATESTRING} --out "wholeyear__NeuralGCM.dat" --in_fmt "lon,lat,slp,PHIS" --range ${SN_TRAJRANGE} --mintime "54h" --maxgap "24h" --threshold "lat,<=,50.0,10;lat,>=,-50.0,10;PHIS,<=,${SN_MAXTOPO},${SN_MINLEN}" </dev/null