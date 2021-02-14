import os

import param
import panel as pn
import numpy as np
import matplotlib.pyplot as plt

from templates.template import template
from static.css import css
from static.description import description
from static.blockquote import blockquote
from static.extras import extras
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
tmpl.add_variable('js', js)

class Interact(param.Parameterized):
    '''

    '''
    def __init__(self):
        super(Interact, self).__init__()
        self.datapath = name + '/data'
        self.filelist = os.listdir(self.datapath)
        self.filelist.sort()
    
    nums = [i for i in range(74)] #update this
    date = param.Selector(default=0, objects=nums)

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
    def _set_title(fn, opt='input'):
        '''
        '''
        date = fn[:4] + '-' + fn[4:6] + '-' + fn[6:8]

        if opt == 'input':
            addendum = ': Interpolation'
        elif opt == 'slope':
            addendum = ': Slope (radians)'
        elif opt == 'aspect':
            addendum = ': Aspect (degrees)'

        return date + addendum

    @param.depends('date')
    def input(self):
        '''
        '''
        fig, ax = plt.subplots(1)

        self.filename = self.filelist[self.date]
        self.array = np.load(f'{self.datapath}/{self.filename}')

        ax.imshow(self.array, origin='lower')

        title = self._set_title(fn=self.filename)
        self._format_imshow(fig=fig, ax=ax, title=title)

        plt.close('all')
        return fig

    def output(self):
        '''
        '''
        self.attributes = Attributes(
                self.array,
                resolution=300,
                projection=c.PROJECTION,
                side_len=c.SIDE_LEN
        )
        print('UPDATE resolution to param')
        self.slope, self.aspect = self.attributes.calc_attributes()

        self.correction = Correction(
                attribute_grids=(self.slope, self.aspect),
                local_timezone=c.TIMEZONE,
                date_str=self.filename[:8],
                lat_lon=c.LAT_LON
        )

        return pn.Row('output')

    def export(self):
        '''
        '''
        return pn.Row('export')
    
    def plot_slope(self):
        '''
        '''        
        fig, ax = plt.subplots(1)
        ax.imshow(self.slope, origin='lower', cmap='YlOrBr')

        title = self._set_title(fn=self.filename, opt='slope')
        self._format_imshow(fig=fig, ax=ax, title=title)

        plt.close('all')
        return fig

    def plot_aspect(self):
        '''
        '''
        fig, ax = plt.subplots(1)
        ax.imshow(self.aspect, origin='lower', cmap='hsv')

        title = self._set_title(fn=self.filename, opt='aspect')
        self._format_imshow(fig=fig, ax=ax, title=title)

        plt.close('all')
        return fig

    def plot_sun(self):
        '''
        '''
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='polar')

        xs = np.deg2rad(self.correction.sunposition_df['azimuth'])
        ys = self.correction.sunposition_df['altitude']
        
        ax.scatter(xs,ys, s=10, c='orange',alpha=0.5)
        
        self._format_polar(fig=fig, ax=ax)

        plt.close('all')
        return fig


interact = Interact()

input_params = [interact.param.date,]
output_params = []

tmpl.add_panel('A', pn.Column(interact.input, *input_params))
tmpl.add_panel('B', pn.Column(interact.output, *output_params))
tmpl.add_panel('C', interact.export)
tmpl.add_panel('D', interact.plot_slope)
tmpl.add_panel('E', interact.plot_aspect)
tmpl.add_panel('F', interact.plot_sun)

tmpl.servable()
