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
    def _format_plt(fig, ax, title, 
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
    def _set_title(fn, opt='input'):
        '''
        '''
        date = fn[:4] + '-' + fn[4:6] + '-' + fn[6:8]

        if opt == 'input':
            return date + ': Interpolation'
        if opt == 'slope':
            return date + ': Slope (radians)'

    @param.depends('date')
    def input(self):
        '''
        '''
        fig, ax = plt.subplots(1)

        self.filename = self.filelist[self.date]
        self.array = np.load(f'{self.datapath}/{self.filename}')

        ax.imshow(self.array, origin='lower')

        title = self._set_title(fn=self.filename)
        self._format_plt(fig=fig, ax=ax, title=title)

        plt.close('all')
        return fig

    def output(self):
        '''
        '''
        self.attributes = Attributes(self.array, resolution=300)
        print('UPDATE resolution to param')
        self.slope, self.aspect = self.attributes.calc_attributes()
        
        return pn.Row('output')

    def export(self):
        '''
        '''
        return pn.Row('export')

    
    def plot_slope(self):

        fig, ax = plt.subplots(1)

        ax.imshow(self.slope, origin='lower', cmap='YlOrBr')

        title = self._set_title(fn=self.filename)
        self._format_plt(fig=fig, ax=ax, title=title)

        plt.close('all')
        return fig


    def plot_aspect(self):
        pass

    def plot_sun(self):
        pass

interact = Interact()

input_params = [interact.param.date,]
output_params = []

tmpl.add_panel('A', pn.Column(interact.input, *input_params))
tmpl.add_panel('B', pn.Column(interact.output, *output_params))
tmpl.add_panel('C', interact.export)
tmpl.add_panel('D', interact.plot_slope)
tmpl.add_panel('E', pn.Row('aspect plot'))
tmpl.add_panel('F', pn.Row('sun plot'))

tmpl.servable()
