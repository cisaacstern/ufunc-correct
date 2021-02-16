import os
from tempfile import TemporaryFile

import param
import panel as pn
import numpy as np
import matplotlib.pyplot as plt

from templates.template import template
from static.css import css
from static.description import description
from static.blockquote import blockquote
from static.extras import extras
from static.returns import returns
from static.js import js
from attributes import Attributes
from correction import Correction
import config as c

pn.config.raw_css = [css,]

name = 'ufunc-correct'
tmpl = pn.Template(template)
tmpl.add_variable('app_title', name)
tmpl.add_variable('description', description)
tmpl.add_variable('blockquote', blockquote)
tmpl.add_variable('extras', extras)
tmpl.add_variable('returns', returns)
tmpl.add_variable('js', js)

class Interact(param.Parameterized):
    '''

    '''
    def __init__(self):
        super(Interact, self).__init__()
        self.datapath = name + '/data'
        self.filelist = os.listdir(self.datapath)
        self.filelist.sort()
    
    # TODO: improve default setting
    DEM = param.Selector(default='20190623_NNR300S20.npy')
    time = param.Integer(0, bounds=(0,100))

    @staticmethod
    def _format_imshow(fig, ax, title, 
                        m=0.02, bgc='#292929', axc='#eee', lblc='#fff'):
        ax.margins(m)
        ax.set_aspect(aspect=1)
        ax.set_xlabel('Easting')
        ax.set_ylabel('Northing')
        ax.set_title(title, color=axc, loc='left', pad=20)
        ax.xaxis.label.set_color(lblc)
        ax.yaxis.label.set_color(lblc)
        ax.tick_params(axis='x', colors=lblc)
        ax.tick_params(axis='y', colors=lblc)
        ax.spines['bottom'].set_color(axc)
        ax.spines['top'].set_color(axc) 
        ax.spines['right'].set_color(axc)
        ax.spines['left'].set_color(axc)
        ax.set_facecolor(bgc)
        fig.patch.set_facecolor(bgc)

    @staticmethod
    def _format_polar(fig, ax, bgc='#292929', axc='#eee', lblc='#fff'):
        tks = [np.deg2rad(a) for a in np.linspace(0,360,8,endpoint=False)]
        xlbls = np.array(['N','45','E','135','S','225','W','315'])
        ax.set_theta_zero_location('N')
        ax.set_xticks((tks))
        ax.set_xticklabels(xlbls, rotation="vertical", size=12)
        ax.tick_params(axis='x', pad = 0.5)
        ax.set_theta_direction(-1)
        ax.set_rmin(0)
        ax.set_rmax(90)
        ax.set_rlabel_position(90)
        ax.set_facecolor(bgc)
        ax.spines['polar'].set_color(axc)
        ax.xaxis.label.set_color(lblc)
        ax.yaxis.label.set_color(lblc)
        ax.tick_params(axis='x', colors=axc)
        ax.tick_params(axis='y', colors=axc)
        fig.patch.set_facecolor(bgc)

    @staticmethod
    def _set_title(fn, opt):
        '''Assigns titles for self._imshow().
        '''
        date = f'{fn[:4]}-{fn[4:6]}-{fn[6:8]}'

        if opt == 'elevation':
            addendum = ': Interpolation'
        elif opt == 'slope':
            addendum = ': Slope (radians)'
        elif opt == 'aspect':
            addendum = ': Aspect (degrees)'
        elif opt == 'correction':
            addendum = ': Terrain Correction'

        return date + addendum

    def _imshow(self, array, cmap, opt):
        '''Generalized method for calling plt.imshow()
        '''
        fig, ax = plt.subplots(1)
        ax.imshow(array, origin='lower', cmap=cmap, )
        title = self._set_title(fn=self.DEM, opt=opt)
        self._format_imshow(fig=fig, ax=ax, title=title)
        plt.close('all')
        return fig

    def _looped_correction(self):
        '''
        '''
        for i in range(self.correct.sunposition_df.shape[0]):
            if i == 0:
                correct_stack = self.correct.calc_correction_onetime(i)
            else:
                correct_stack = np.dstack(
                    (correct_stack, self.correct.calc_correction_onetime(i))
                )
        return correct_stack
    
    def _ufunc_correction(self):
        '''
        '''
        correct_stack = self.correct.calc_correction_fullday()

        return correct_stack

    @param.depends('DEM')
    def input(self):
        '''Assigns the self.filename and self.elevation_array
        instance variables. Returns as plot of self.elevation_array.
        '''
        self.param.DEM.default = self.filelist[0]
        self.param.DEM.objects = self.filelist
        self.elevation_array = np.load(f'{self.datapath}/{self.DEM}')
        
        return self._imshow(array=self.elevation_array, cmap='viridis', 
                            opt='elevation')

    @param.depends('time')
    def output(self):
        '''Instantiates the Attributes and Correction classes,
        assigns associated instance variables, and returns a plot
        of the terrain correction array.
        '''
        self.attributes = Attributes(
                self.elevation_array,
                resolution=self.elevation_array.shape[0],
                projection=c.PROJECTION,
                side_len=c.SIDE_LEN
        )
        self.slope, self.aspect = self.attributes.calc_attributes()

        self.correct = Correction(
                attribute_grids=(self.slope, self.aspect),
                local_timezone=c.TIMEZONE,
                date_str=self.DEM[:8],
                lat_lon=c.LAT_LON
        )
        self.param.time.bounds = (0,self.correct.sunposition_df.shape[0]-1)
        print(self.param.time.bounds)
        self.correct_array = self.correct.calc_correction_onetime(self.time)

        return self._imshow(array=self.correct_array, cmap='magma', 
                            opt='correction')

    def export(self):
        '''
        '''
        correct_stack = self._looped_correction()

        outfile = TemporaryFile()
        np.savez(outfile,
                    elevation=self.elevation_array,
                    slope=self.slope,
                    aspect=self.aspect,
                    sunposition=self.correct.sunposition_df.to_numpy(),
                    correction_stack=correct_stack,
        )
        _ = outfile.seek(0)

        name = f'{self.DEM[:-4]}_correction.npz'
        return pn.widgets.FileDownload(file=outfile, filename=name)
    
    def plot_slope(self):
        '''Return a plot of the self.slope array
        '''        
        return self._imshow(array=self.slope, cmap='YlOrBr', opt='slope')

    def plot_aspect(self):
        '''Return a plot of the self.aspect array
        '''
        return self._imshow(array=self.aspect, cmap='hsv', opt='aspect')

    def plot_sun(self):
        '''Return a plot of sun position
        '''
        xs = np.deg2rad(self.correct.sunposition_df['azimuth'])
        ys = self.correct.sunposition_df['altitude']
        
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='polar')
        ax.scatter(xs,ys, s=10, c='orange',alpha=0.5)
        self._format_polar(fig=fig, ax=ax)
        plt.close('all')
        return fig


interact = Interact()

input_params = [interact.param.DEM,]
output_params = [interact.param.time,]

tmpl.add_panel('A', pn.Column(interact.input, *input_params))
tmpl.add_panel('B', pn.Column(interact.output, *output_params))
tmpl.add_panel('C', interact.export)
tmpl.add_panel('D', interact.plot_slope)
tmpl.add_panel('E', interact.plot_aspect)
tmpl.add_panel('F', interact.plot_sun)

tmpl.servable()
