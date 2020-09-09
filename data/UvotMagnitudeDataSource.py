import glob
from astropy.table import Table
from data.MagnitudeDataSource import *
from utility import timing as tm

class UvotMagnitudeDataSource(MagnitudeDataSource):
    """
    Read and parse Photometry Data files from UVOTA instrument in the for of fits files
    which have been produced by tht uvotsource command.
    """

    def _ingest(self, source: str) -> DataFrame:
        """
        Ingest the data from the specified source and return it as a pandas DataFrame
        Implements the abstract method in DataSource which is used to set up this instance's state.
        """
        fits_field_names = ["MET", "MAG", "MAG_ERR", "FILTER", "SYS_ERR", "EXPOSURE", "SATURATED",
                            "AB_MAG", "AB_MAG_ERR", "FLUX_HZ", "FLUX_HZ_ERR"]
        output_col_names = ["jd", "mag", "mag_err", "band", "observer_code", "is_null_obs", "is_saturated_obs",
                            "ab_mag", "ab_mag_err", "flux_hz", "flux_hz_err"]
        rows = []

        source = self.__class__._canonicalize_filename(source)
        fits_file_names = Path(source.parent).glob(source.name)
        for fits_file_name in sorted(fits_file_names):
            print(f"\tParsing {fits_file_name.name}.")
            t = Table.read(fits_file_name, "MAGHIST")

            # Check the keywords to make sure this is the right instrument
            if (t.meta["EXTNAME"] != "MAGHIST") | (t.meta['TELESCOP'] != "SWIFT") | (t.meta['INSTRUME'] != "UVOTA"):
                print(f"Unrecognized FITS keywords for table MAHIST in fits file '{source}.  Ignoring.")
                print(t.meta)
            else:
                for fits_row in t.iterrows(*fits_field_names):
                    jd = UvotMagnitudeDataSource._met_to_jd(fits_row[0])
                    rows.append({
                        output_col_names[0]: jd,                    # jd : MET -> JD
                        output_col_names[1]: fits_row[1],           # mag : MAG
                        output_col_names[2]: fits_row[2],           # mag_err : MAG_ERR
                        output_col_names[3]: fits_row[3].strip(),   # band : FILTER
                        output_col_names[4]: "",                    # observer_code :
                        output_col_names[5]: fits_row[4],           # is_null_obs : SYS_ERR
                        output_col_names[6]: fits_row[6],           # is_saturated_obs : SATURATED
                        output_col_names[7]: fits_row[7],           # ab_mag : AB_MAG
                        output_col_names[8]: fits_row[8],           # ab_mag_err : AB_MAG_ERR
                        output_col_names[9]: fits_row[9],           # flux_hz : FLUX_HZ
                        output_col_names[10]: fits_row[10]          # flux_hz_err : FLUX_HZ_ERR
                    })

        return DataFrame.from_records(rows, columns=output_col_names)

    @classmethod
    def _met_to_jd(cls, met: float) -> float:
        # The issue here is that uvotmaghist/uvotsource don't copy over the UTCFINT & MJDREF fields either
        # in the HDU headers or in fields (FFS why not?).  There's also no easy way to tie an observation
        # back to the source file.  However, MJDREFI doesn't change and the change in UTCFINT amounts to 6 seconds
        # over the course of the observations, so for now I'll use a median value for this and if time I'll revisit.
        # Reference values from the first and last observations;
        # sw00011558001uw1_sk.img.gz: UTCFINIT = -23.57402
        # sw00011558033uw2_sk.img.gz: UTCFINIT = -23.62186
        # sw00045788001uw2_sk.img.gz: UTCFINIT = -17.07584
        # sw00045788105um2_sk.img.gz: UTCFINIT = -24.88188
        MJDREFI = 51910
        UTCFINT = -20.97886
        return tm.jd_from_mjd(MJDREFI + ((met + UTCFINT) / 86400))
