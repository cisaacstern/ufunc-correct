
import numpy as np
import pandas as pd
from pysolar import solar

import config as c

class Correction():
    '''
    '''
    def __init__(attribute_grids):
        self.attribute_grids = attribute_grids

    @staticmethod
    def _add_sun_position(df):
        '''
        solar altitude + azimuth to dataframe, makes a second pass as dropping 
        non-sunlit timepoints by removing rows for which solar altitude is < 0.
        '''
        lat, lon = c.LAT_LON
        alt_list = [90 - solar.get_altitude(lat, lon, utc_time) 
                    for utc_time in df['utc_datetime']]
        azi_list = [solar.get_azimuth(lat, lon, utc_time) 
                    for utc_time in df['utc_datetime']]

        df.insert(5, 'solar_altitude', alt_list)
        df.insert(6, 'solar_azimuth', azi_list)

        return df[df['solar_altitude'] < 90] 
            #dropping non-sunlit rows from top and bottom (second pass)

    def calculate_correction(self, time):
        '''
        Parameters
        ==========
        grids : tuple of len == 2
            grids[0] is a slope array in radians
            grids[1] is an aspect array in degrees,
                with south = 0, and east positive.
        '''
        alt = self.df['solar_altitude'].iloc[time]
        azi = self.df['solar_azimuth'].iloc[time]
    
        slope, aspect = self.attribute_grids

        T0 = np.deg2rad(alt)
        P0 = np.deg2rad(180 - azi)

        S = np.deg2rad(slope) 
        A = np.deg2rad(aspect)

        cosT0 = np.cos(T0)
        cosS = np.cos(S)
        sinT0 = np.sin(T0)
        sinS = np.sin(S)
        cosP0A = np.cos(P0 - A)

        cosT = (cosT0*cosS) + (sinT0*sinS*cosP0A)

        return cosT/cosT0

    