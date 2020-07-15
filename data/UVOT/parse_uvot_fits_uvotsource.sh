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

# Clear any existing output files
rm -f ./*maghist_*.fits

# We've found two ids for V3890 Sgr in the Swift data.  Process them separately as it'll make diagnostics easier
declare -a IDS=("00011558" "00045788") 
for ID in "${IDS[@]}"
do
    LOGFILE="maghist_${ID}.log"
    echo "LOGFILE: ${LOGFILE}"
    
    OUTFILE="maghist_${ID}.fits"
    echo "OUTFILE: ${OUTFILE}"

    # Make sure any existing output file is deleted, otherwise we will append to it
    rm -f $LOGFILE 

    FILESPEC="./reproc/*/uvot/image/sw${ID}*_sk.img.gz"
    echo "Parsing files matching; ${FILESPEC}"
    for INFILE in $(ls -U ${FILESPEC});
    do  
        #INFILE="${INFILE##*/}"
        echo "INFILE:" $INFILE;

        # clobber=no, so that the photometry magnitude data from all of the source files is appended to a single output fits file (make sure its deleted first)
        echo "INFILE: ${INFILE}" >> $LOGFILE
        echo "OUTFILE: ${OUTFILE}" >> $LOGFILE

        # Using UVOTSOURCE directly means I can drive it to append rows to the same output fits file (makes later processing in Python much quicker!!)
        # The downside is that I can't easily check the presence/suitability of additional HDUs in the source files (like UVOTMAGHIST does).
        # Easiest solution is a brute force approach of trying to access all HDUs and reviewing the errors (I know no source has >4 data HDUs).
        uvotsource image="${INFILE}+1" outfile=$OUTFILE srcreg=V3890Sgr.reg bkgreg=V3890Sgr_bkg.reg sigma=3 apercorr=CURVEOFGROWTH zerofile=CALDB coinfile=CALDB lssfile=CALDB psffile=CALDB sensfile=CALDB syserr=no frametime=DEFAULT centroid=no fwhmsig=-1 subpixel=8 deadtimecorr=yes extprec=0 expfile=None output=mag chatter=2 clobber=no cleanup=yes >> $LOGFILE        
        uvotsource image="${INFILE}+2" outfile=$OUTFILE srcreg=V3890Sgr.reg bkgreg=V3890Sgr_bkg.reg sigma=3 apercorr=CURVEOFGROWTH zerofile=CALDB coinfile=CALDB lssfile=CALDB psffile=CALDB sensfile=CALDB syserr=no frametime=DEFAULT centroid=no fwhmsig=-1 subpixel=8 deadtimecorr=yes extprec=0 expfile=None output=mag chatter=2 clobber=no cleanup=yes >> $LOGFILE        
        uvotsource image="${INFILE}+3" outfile=$OUTFILE srcreg=V3890Sgr.reg bkgreg=V3890Sgr_bkg.reg sigma=3 apercorr=CURVEOFGROWTH zerofile=CALDB coinfile=CALDB lssfile=CALDB psffile=CALDB sensfile=CALDB syserr=no frametime=DEFAULT centroid=no fwhmsig=-1 subpixel=8 deadtimecorr=yes extprec=0 expfile=None output=mag chatter=2 clobber=no cleanup=yes >> $LOGFILE        
        uvotsource image="${INFILE}+4" outfile=$OUTFILE srcreg=V3890Sgr.reg bkgreg=V3890Sgr_bkg.reg sigma=3 apercorr=CURVEOFGROWTH zerofile=CALDB coinfile=CALDB lssfile=CALDB psffile=CALDB sensfile=CALDB syserr=no frametime=DEFAULT centroid=no fwhmsig=-1 subpixel=8 deadtimecorr=yes extprec=0 expfile=None output=mag chatter=2 clobber=no cleanup=yes >> $LOGFILE        
        echo "--------------------------------" >> $LOGFILE
    done

    # Copy the output and log file to local folder (overwriting existing)
    echo "Copying the output and log to ${SCRIPTDIR}"
    cp -f $OUTFILE "${SCRIPTDIR}"
    cp -f $LOGFILE "${SCRIPTDIR}"
done

cd "${SCRIPTDIR}"
