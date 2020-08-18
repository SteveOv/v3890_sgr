# Code generated by generate_spectra_lookup_module.py
from typing import Dict
from utility import timing as tm


def get_spectra_epochs(eruption_jd: float) -> Dict[str, float]:
    """
    Gets the timing of the LT Spectra for the 2019 eruption as an epochs dictionary.
    """
    return {
        "b_e_20190828_11": tm.delta_t_from_jd(2458724.408415, eruption_jd),
        "b_e_20190828_3": tm.delta_t_from_jd(2458724.358298, eruption_jd),
        "b_e_20190830_5": tm.delta_t_from_jd(2458726.358392, eruption_jd),
        "b_e_20190831_11": tm.delta_t_from_jd(2458727.433088, eruption_jd),
        "b_e_20190831_5": tm.delta_t_from_jd(2458727.354917, eruption_jd),
        "b_e_20190901_11": tm.delta_t_from_jd(2458728.430003, eruption_jd),
        "b_e_20190901_5": tm.delta_t_from_jd(2458728.356852, eruption_jd),
        "b_e_20190902_5": tm.delta_t_from_jd(2458729.353593, eruption_jd),
        "b_e_20190902_7": tm.delta_t_from_jd(2458729.419832, eruption_jd),
        "b_e_20190903_5": tm.delta_t_from_jd(2458730.363364, eruption_jd),
        "b_e_20190903_7": tm.delta_t_from_jd(2458730.42483, eruption_jd),
        "b_e_20190904_4": tm.delta_t_from_jd(2458731.363214, eruption_jd),
        "b_e_20190905_5": tm.delta_t_from_jd(2458732.351202, eruption_jd),
        "b_e_20190905_7": tm.delta_t_from_jd(2458732.431063, eruption_jd),
        "b_e_20190910_1": tm.delta_t_from_jd(2458737.355612, eruption_jd),
        "b_e_20190911_5": tm.delta_t_from_jd(2458738.346323, eruption_jd),
        "b_e_20190911_7": tm.delta_t_from_jd(2458738.410921, eruption_jd),
        "b_e_20190913_5": tm.delta_t_from_jd(2458740.345966, eruption_jd),
        "b_e_20190913_7": tm.delta_t_from_jd(2458740.406875, eruption_jd),
        "b_e_20190915_5": tm.delta_t_from_jd(2458742.344409, eruption_jd),
        "r_e_20190828_11": tm.delta_t_from_jd(2458724.408344, eruption_jd),
        "r_e_20190828_3": tm.delta_t_from_jd(2458724.358227, eruption_jd),
        "r_e_20190830_5": tm.delta_t_from_jd(2458726.358327, eruption_jd),
        "r_e_20190831_11": tm.delta_t_from_jd(2458727.433159, eruption_jd),
        "r_e_20190831_5": tm.delta_t_from_jd(2458727.354847, eruption_jd),
        "r_e_20190901_11": tm.delta_t_from_jd(2458728.430132, eruption_jd),
        "r_e_20190901_5": tm.delta_t_from_jd(2458728.356769, eruption_jd),
        "r_e_20190902_5": tm.delta_t_from_jd(2458729.353522, eruption_jd),
        "r_e_20190902_7": tm.delta_t_from_jd(2458729.419905, eruption_jd),
        "r_e_20190903_5": tm.delta_t_from_jd(2458730.363294, eruption_jd),
        "r_e_20190903_7": tm.delta_t_from_jd(2458730.42476, eruption_jd),
        "r_e_20190904_4": tm.delta_t_from_jd(2458731.363149, eruption_jd),
        "r_e_20190905_5": tm.delta_t_from_jd(2458732.351137, eruption_jd),
        "r_e_20190905_7": tm.delta_t_from_jd(2458732.431134, eruption_jd),
        "r_e_20190910_1": tm.delta_t_from_jd(2458737.355542, eruption_jd),
        "r_e_20190911_5": tm.delta_t_from_jd(2458738.346253, eruption_jd),
        "r_e_20190911_7": tm.delta_t_from_jd(2458738.410851, eruption_jd),
        "r_e_20190913_5": tm.delta_t_from_jd(2458740.345901, eruption_jd),
        "r_e_20190913_7": tm.delta_t_from_jd(2458740.406804, eruption_jd),
        "r_e_20190915_5": tm.delta_t_from_jd(2458742.344338, eruption_jd),
    }
