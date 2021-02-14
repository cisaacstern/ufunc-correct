from tempfile import TemporaryFile

import numpy as np
import richdem as rd

import config as c

class Attributes():

    def __init__(self, grid, resolution):
        self.grid = grid
        self.resolution = resolution

    def _numpy2richdem(self, in_array, no_data=-9999):
        '''
        slope and aspect calculations are performed by richdem, which
        requires data in rdarray format. this function converts numpy
        arrays into rdarrays.
        '''
        out_array = rd.rdarray(in_array, no_data=no_data)
        out_array.projection = c.PROJECTION
        cell_scale = np.around(a=c.SIDE_LEN/self.resolution, decimals=5)
        out_array.geotransform = [0, cell_scale, 0, 0, 0, cell_scale]
        return out_array

    @staticmethod
    def _richdem2numpy(rda, attribute):
        '''
        Parameters
        ==========
        in_array : richdem array

        attribute : str
            One of 'slope
        '''
        outfile = TemporaryFile()
        np.save(outfile, rd.TerrainAttribute(rda, attrib=attribute))
        _ = outfile.seek(0)
        out_array = np.load(outfile)

        if attribute == 'aspect':
            out_array[out_array>180] = out_array[out_array>180]-360
            return out_array
        else:
            return out_array

    def calc_attributes(self):
        '''
        given input grid, returns slope and aspect grids
        '''
        rda = self._numpy2richdem(np.asarray(self.grid), -9999)

        slope = self._richdem2numpy(rda=rda, attribute='slope_radians')
        aspect = self._richdem2numpy(rda=rda, attribute='aspect')

        return slope, aspect
