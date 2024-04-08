import matplotlib.pylab as plt
import pandas as pd
import numpy as np
import scipy.stats
import json
from os.path import abspath, dirname, join

from wntr.network.elements import Pattern

libdir = dirname(abspath(str(__file__)))
NoneType = type(None)

class DemandPatternLibrary(object):

    def __init__(self, filename=None):

        if isinstance(filename, NoneType):
            filename = join(libdir, 'DemandPatternLibrary.json')
        if isinstance(filename, str):
            with open(filename, "r") as fin:
                self.library = json.load(fin)

    def filter_by_category(self, category):
        """
        Filter library by category
        """

        assert isinstance(category, (str, NoneType))

        names = []
        for name in self.library.keys():
            if self.library[name]['category'] == category:
                names.append(name)

        return dict((k, self.library[k]) for k in names)

    def copy_pattern(self, name, new_name):
        """
        Add a copy of an existing pattern to the library
        """

        assert isinstance(name, str)
        assert isinstance(new_name, str)
        assert name != new_name

        entry = self.library[name].copy()
        self.library[new_name] = entry

    def normalize_pattern(self, name, inplace=True):
        """
        Normalize values in a pattern so the mean equals 1
        """

        assert isinstance(name, str)

        multipliers = self.library[name]['multipliers']
        multipliers = multipliers/multipliers.mean()
        
        if inplace:
            self.library[name]['multipliers'] = multipliers.values()
        
        return multipliers
    
    def apply_noise(self, name, std, normalize=False, inplace=True):
        """
        Apply gaussian random noise to a pattern
        """

        assert isinstance(name, str)
        assert isinstance(std, (int, float))
        assert isinstance(normalize, bool)
        
        entry = self.library[name]
        
        multipliers = entry['multipliers']
        noise = np.random.normal(0, std, len(multipliers))
        multipliers = multipliers + noise

        if normalize:
            multipliers = multipliers/multipliers.mean()

        if inplace:
            self.library[name]['multipliers'] = list(multipliers)
        
        return multipliers
        
    def resample_multipliers(self, name, duration, inplace=True):
        """
        Resample multipliers, which can change if the start_clocktime, 
        pattern_timestep, or wrap status changes
        """
        pattern = self.to_Pattern(name)
        
        entry = self.library[name]
        start_clocktime = entry['start_clocktime']
        pattern_timestep = entry['pattern_timestep']
        
        index = np.arange(start_clocktime, duration, pattern_timestep)
        multipliers = []
        for i in index:
            multipliers.append(pattern.at(i))
        
        if inplace:
            self.library[name]['multipliers'] = list(multipliers)
        
        return pd.Series(index=index, data=multipliers)
    
    def add_pattern(self, name, entry):
        """
        Add a pattern to the library
        """
        assert isinstance(name, str)
        assert isinstance(entry, dict)
        assert entry.keys() <= ['category',
                                'description',
                                'citation',
                                'start_clocktime',
                                'pattern_timestep',
                                'wrap',
                                'multipliers']

        self.library[name] = entry
        
    def add_pulse_pattern(self, on_off_sequence, duration=86400, 
                          pattern_timestep=3600, start_clocktime=0, 
                          wrap=True, invert=False, 
                          normalize=False, name='Pulse'):
        """
        Add a pulse pattern to the library using a sequence of on/off times
        """

        assert isinstance(on_off_sequence, list)
        assert np.all(np.diff(on_off_sequence) > 0) # is monotonically increasing

        index = np.arange(start_clocktime, duration, pattern_timestep)
        multipliers = pd.Series(index=index, data=0) # starts off
        switches = 0
        for time in on_off_sequence:
            switches = switches + 1
            position = np.mod(switches,2) # returns 0 or 1
            multipliers.loc[time::] = position

        if invert:
            multipliers = multipliers.max() - multipliers

        if normalize:
            multipliers = multipliers/multipliers.mean()

        entry = {
         'category': None,
         'description': None,
         'citation': None,
         'start_clocktime': start_clocktime,
         'pattern_timestep': pattern_timestep,
         'wrap': wrap,
         'multipliers': list(multipliers)}

        self.library[name] = entry

    def add_gaussian_pattern(self, mean, std, duration=86400, 
                             pattern_timestep=3600, start_clocktime=0, 
                             wrap=True, invert=False, normalize=False, 
                             name='Gaussian'):
        """
        Add a Guassian pattern to the library defined by a mean and standard
        deviation
        """

        index = np.arange(start_clocktime, duration, pattern_timestep)
        multipliers = scipy.stats.norm.pdf(index, mean, std)

        if invert:
            multipliers = multipliers.max() - multipliers

        if normalize:
            multipliers = multipliers/multipliers.mean()

        entry = {
         'category': None,
         'description': None,
         'citation': None,
         'start_clocktime': start_clocktime,
         'pattern_timestep': pattern_timestep,
         'wrap': wrap,
         'multipliers': list(multipliers)}

        self.library[name] = entry

    def add_triangular_pattern(self, start, peak, end, duration=86400, 
                               pattern_timestep=3600, start_clocktime=0,
                               wrap=True, invert=False, normalize=False, 
                               name='Triangular'):
        """
        Add a traingular pattern to the library defined by a start time,
        peak time, and end time
        """
        loc = start
        scale = end-start
        c = (peak-start)/(end-start)

        index = np.arange(start_clocktime, duration, pattern_timestep)
        multipliers = scipy.stats.triang.pdf(index, c, loc, scale)

        if invert:
            multipliers = multipliers.max() - multipliers

        if normalize:
            multipliers = multipliers/multipliers.mean()

        entry = {
         'category': None,
         'description': None,
         'citation': None,
         'start_clocktime': start_clocktime,
         'pattern_timestep': pattern_timestep,
         'wrap': wrap,
         'multipliers': list(multipliers)}

        self.library[name] = entry

    def add_combined_pattern(self, names, duration=86400, 
                             pattern_timestep=3600, start_clocktime=0,
                             wrap=True, normalize=False, name='Combined'):
        """
        Combine patterns to create a new pattern
        """
        series = {}
        for n in names: 
            entry = self.library[n]
            entry_start_clocktime = entry['start_clocktime']
            
            # For example, if the start_clocktime = 3:00 and the 
            # entry_start_clocktime = 1:00, then the adjusted_start_clocktime = -2:00
            adjusted_start_clocktime = entry_start_clocktime - start_clocktime
            pattern = self.to_Pattern(n, pattern_start = adjusted_start_clocktime)
    
            index = np.arange(start_clocktime, duration, pattern_timestep)
            multipliers = []
            for i in index:
                multipliers.append(pattern.at(i))
    
            series[n] = pd.Series(index=index, data=multipliers)
            
        df = pd.DataFrame(index=index, data=series)
        multipliers = df.sum(axis=1)
    
        if normalize:
            multipliers = multipliers/multipliers.mean()
    
        entry = {
         'category': None,
         'description': None,
         'citation': None,
         'start_clocktime': start_clocktime,
         'pattern_timestep': pattern_timestep,
         'wrap': wrap,
         'multipliers': list(multipliers)}
    
        self.library[name] = entry


    def to_Pattern(self, name, pattern_start=None):
        """
        Convert the pattern library entry to a WNTR Pattern
        """

        entry = self.library[name]
        if pattern_start is None:
            start_clocktime = entry['start_clocktime']
        else:
            start_clocktime = pattern_start
        pattern_timestep = entry['pattern_timestep']
        multipliers = entry['multipliers']
        wrap = entry['wrap']
        pattern = Pattern(name=name,
                          multipliers=multipliers,
                          time_options=(start_clocktime, pattern_timestep),
                          wrap=wrap)

        return pattern

    def to_Series(self, name, duration=86400):
        """
        Convert the pattern library entry to a Pandas Series
        """

        entry = self.library[name]

        start_clocktime = entry['start_clocktime']
        pattern_timestep = entry['pattern_timestep']
        if duration is None:
            multipliers = entry['multipliers']
            duration = len(multipliers)*pattern_timestep

        pattern = self.to_Pattern(name)

        # Get values at a particular time, can be used to resample
        index = np.arange(start_clocktime, duration, pattern_timestep)
        data = []
        for i in index:
            data.append(pattern.at(i))
        series = pd.Series(index=index, data=data)

        return series

    def write_json(self, filename):
        """
        Write the library to a JSON file
        """
        if isinstance(filename, str):
            with open(filename, "w") as fout:
                json.dump(self.library, fout)

    def plot_patterns(self, names=None, duration=None, linewidth=1.5, ax=None):
        """
        Plot patterns
        """

        if names is None:
            names = self.library.keys()

        if ax is None:
            fig, ax = plt.subplots()

        for name in names:
            if duration is None:
                entry = self.library[name]
                entry_duration = len(entry['multipliers'])*entry['pattern_timestep']
            else:
                entry_duration = duration
            series = self.to_Series(name, duration=entry_duration)
            series.plot(ax=ax, linewidth=linewidth, label=name)

        ax.legend()

        return ax
