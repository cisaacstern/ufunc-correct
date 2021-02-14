import numpy as np
import pandas as pd
from pysolar import solar

class Correction():
    '''
    '''
    def __init__(self, attribute_grids, local_timezone, date_str, lat_lon):
        '''
        Parameters
        ==========
        attribute_grids : tuple, length == 2
            attribute_grids[0] is a slope array in radians
            attribute_grids[1] is an aspect array in degrees,
                with south = 0, and east positive.
        local_timezone : str

        date_str : str, length == 8
            YYYMMDD format
        lat_lon : tuple, length == 2

        '''
        self.attribute_grids = attribute_grids
        self.local_timezone = local_timezone
        self.date_str = f'{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}'
        self.lat, self.lon = lat_lon
        self.sunposition_df = self._init_dataframe()

    def _init_dataframe(self):
        df = pd.DataFrame()
        df = self._add_localtime_to_df(df=df)
        df = self._add_utctime_to_df(df=df)
        df = self._add_sunposition_to_df(df=df)
        df = self._drop_nonsunlit_rows(df=df)
        return df

    def _add_localtime_to_df(self, df):
        '''
        '''
        df['local_timestamps'] = pd.date_range(
            start=self.date_str + ' 00:00', 
            freq='15min', periods=96, tz=self.local_timezone
        )
        return df

    def _add_utctime_to_df(self, df):
        '''
        '''
        #df['utc_timestamps'] = df['local_timestamps'].tz_convert('UTC')
        df['utc_timestamps'] = pd.to_datetime(
            df['local_timestamps']).dt.tz_convert('UTC')
        return df

    def _add_sunposition_to_df(self, df):
        '''
        '''
        dts = pd.to_datetime(
            df['utc_timestamps'], infer_datetime_format=True,
        )
        df['altitude'] = [
            90 - solar.get_altitude(self.lat, self.lon, utc_dt) 
            for utc_dt in dts
        ]
        df['azimuth'] = [
            solar.get_azimuth(self.lat, self.lon, utc_dt) for utc_dt in dts
        ]
        return df

    @staticmethod
    def _drop_nonsunlit_rows(df):
        '''
        '''
        return df[df['altitude'] < 90]

    def calc_correction_single_timepoint(self, time):
        '''
        
        '''
        alt = self.sunposition_df['altitude'].iloc[time]
        azi = self.sunposition_df['azimuth'].iloc[time]
    
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
    
    def calc_correction_full_day(self):
        '''
        here's the ufunc magic
        '''
        alts = self.sunposition_df['altitude']
        azis = self.sunposition_df['azimuth']

        slope, aspect = self.attribute_grids

        T0s = np.deg2rad(alts)
        P0s = np.deg2rad(180 - azis)

        Ss = np.deg2rad(slope) # these need to be a full stack
        As = np.deg2rad(aspect) # " '  '" " "

        pass
    