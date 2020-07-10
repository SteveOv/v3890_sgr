shopt -s globstar
SCRIPT=${BASHSOURCE[0]}
echo "Running script: ${SCRIPT}"
SCRIPTDIR="$( cd "$( dirname "${SCRIPT}" )" >/dev/null 2>&1 && pwd )"

# Move over to the staging folder to run the analysis so we don't get temp files left in the final location
# Make sure we have copies of the aperture/region files for V3890 Sgr and the background regions there
STAGINGDIR="/Users/steveo/Documents/V3890_Sgr_Data/Swift_UVOT/"
echo "Will run analysis from: ${STAGINGDIR}"
cp -f ./ref/V3890Sgr*.reg $STAGINGDIR 
cd $STAGINGDIR

LOGFILE="maghist_all.log"
echo "LOGFILE: ${LOGFILE}"

rm -f $LOGFILE 
rm -f ./*maghist_*.fits

FILESPEC="./reproc/*/uvot/image/sw*_sk.img.gz"
echo "Parsing files matching; ${FILESPEC}"
for INFILE in $(ls -U ${FILESPEC});
do  
    #INFILE="${INFILE##*/}"
    OUTFILE="${INFILE##*/}"
    OUTFILE="maghist_${OUTFILE%%.*}.fits"
    echo "INFILE: ${INFILE}"
    echo "OUTFILE: ${OUTFILE}"
    
    # clobber=no, so that the photometry magnitude data from all of the source files is appended to a single output fits file (make sure its deleted first)
    echo "INFILE: ${INFILE}" >> $LOGFILE
    echo "OUTFILE: ${OUTFILE}" >> $LOGFILE
     
    # Using UVOTMAGHIST as this drives UVOTSOURCE and is smart enough to check the HDUs in advance (so handles files with multiple HDUs and those HDUs that are not compatible)
    # Downside is that I can't get it to append to a single output fits file, so I end up with a fits per input file (which is much slower to parse in Python)
    uvotmaghist infile=$INFILE outfile=$OUTFILE srcreg=V3890Sgr.reg bkgreg=V3890Sgr_bkg.reg plotfile=None zerofile=CALDB coinfile=CALDB lssfile=CALDB psffile=CALDB clobber=no cleanup=yes chatter=5 >> $LOGFILE
    echo "--------------------------------" >> $LOGFILE
done

# Copy the output and log file to local folder (overwriting existing)
#echo "Copying the output and log to ${SCRIPTDIR}"
#cp -f ./swift_uvot_maghist_*.fits "${SCRIPTDIR}"
#cp -f $LOGFILE "${SCRIPTDIR}"

cd "${SCRIPTDIR}"
