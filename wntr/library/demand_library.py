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

    def __init__(self, filename_or_data=None):
        
        self.library = {}
        if isinstance(filename_or_data, NoneType):
            filename = join(libdir, 'DemandPatternLibrary.json')
            with open(filename, "r") as fin:
                data = json.load(fin)
        elif isinstance(filename_or_data, str):
            filename = filename_or_data
            with open(filename, "r") as fin:
                data = json.load(fin)
        elif isinstance(filename_or_data, list):
            data = filename_or_data
        
        for entry in data:
            name = entry['name']
            self.add_pattern(name, entry)
    
    @property
    def pattern_name_list(self):
        """
        Return a list of demand pattern entry names
        """
        return list(self.library.keys())
    
    def get_pattern(self, name):
        """
        Return a pattern entry from the demand pattern library
        """
        return self.library[name]
    
    def remove_pattern(self, name):
        """
        Remove a pattern from the demand pattern library
        """
        del self.library[name]
    
    def copy_pattern(self, name, new_name):
        """
        Add a copy of an existing pattern to the library
        """
        assert isinstance(name, str)
        assert isinstance(new_name, str)
        assert name != new_name

        entry = self.get_pattern(name).copy()
        entry['name'] = new_name
        self.add_pattern(new_name, entry)

    def filter_by_category(self, category):
        """
        Filter library by category
        """
        assert isinstance(category, (str, NoneType))

        subset = []
        for name in self.pattern_name_list:
            entry = self.get_pattern(name)
            if entry['category'] == category:
                subset.append(entry)

        return subset

    def normalize_pattern(self, name, inplace=True):
        """
        Normalize values in a pattern so the mean equals 1
        """
        assert isinstance(name, str)

        series = self.to_Series(name, duration=None)
        series = series/series.mean()
        
        if inplace:
            self.library[name]['multipliers'] = list(series)
        
        return series
    
    def apply_noise(self, name, std, normalize=False, seed=None, inplace=True):
        """
        Apply gaussian random noise to a pattern
        """
        assert isinstance(name, str)
        assert isinstance(std, (int, float))
        assert isinstance(normalize, bool)
        
        np.random.seed(seed)
        
        series = self.to_Series(name, duration=None)
        
        noise = np.random.normal(0, std, len(series))
        series = series + noise

        if normalize:
            series = series/series.mean()

        if inplace:
            self.library[name]['multipliers'] = list(series)
        
        return series
        
    def resample_multipliers(self, name, duration=86400, 
                             pattern_timestep=3600, start_clocktime=0,
                             wrap=True, inplace=True):
        """
        Resample multipliers, which can change if the start_clocktime, 
        pattern_timestep, or wrap status changes
        """
        # Pattern defined using the current time parameters
        entry = self.get_pattern(name)
        entry_start_clocktime = entry['start_clocktime']

        pattern = self.to_Pattern(name)
        
        # index uses new time parameters
        index = np.arange(start_clocktime, duration, pattern_timestep)
        multipliers = []
        for i in index:
            multipliers.append(pattern.at(i-entry_start_clocktime))
        
        if inplace:
            self.library[name]['start_clocktime'] = start_clocktime
            self.library[name]['pattern_timestep'] = pattern_timestep
            self.library[name]['wrap'] = wrap
            self.library[name]['multipliers'] = list(multipliers)
        
        return pd.Series(index=index, data=multipliers)
    
    def add_pattern(self, name, entry):
        """
        Add a pattern to the library
        """
        assert isinstance(name, str)
        assert isinstance(entry, dict)
        required_keys = ['name', 
                         'start_clocktime', 
                         'pattern_timestep', 
                         'wrap', 
                         'multipliers']
        assert set(required_keys) <= set(entry.keys())

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

        entry = {'name': name,
                 'category': None,
                 'description': None,
                 'citation': None,
                 'start_clocktime': start_clocktime,
                 'pattern_timestep': pattern_timestep,
                 'wrap': wrap,
                 'multipliers': list(multipliers)}

        self.add_pattern(name, entry)

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

        entry = {'name': name,
                 'category': None,
                 'description': None,
                 'citation': None,
                 'start_clocktime': start_clocktime,
                 'pattern_timestep': pattern_timestep,
                 'wrap': wrap,
                 'multipliers': list(multipliers)}

        self.add_pattern(name, entry)

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

        entry = {'name': name, 
                 'category': None,
                 'description': None,
                 'citation': None,
                 'start_clocktime': start_clocktime,
                 'pattern_timestep': pattern_timestep,
                 'wrap': wrap,
                 'multipliers': list(multipliers)}

        self.add_pattern(name, entry)

    def add_combined_pattern(self, names, duration=86400, 
                             pattern_timestep=3600, start_clocktime=0,
                             wrap=True, normalize=False, name='Combined'):
        """
        Combine patterns to create a new pattern
        """
        series = {}
        for n in names: 
            entry = self.get_pattern(n)
            entry_start_clocktime = entry['start_clocktime']
            
            pattern = self.to_Pattern(n)
    
            index = np.arange(start_clocktime, duration, pattern_timestep)
            multipliers = []
            for i in index:
                multipliers.append(pattern.at(i-start_clocktime))
    
            series[n] = pd.Series(index=index, data=multipliers)
            
        df = pd.DataFrame(index=index, data=series)
        multipliers = df.sum(axis=1)
    
        if normalize:
            multipliers = multipliers/multipliers.mean()
    
        entry = {'name': name, 
                 'category': None,
                 'description': None,
                 'citation': None,
                 'start_clocktime': start_clocktime,
                 'pattern_timestep': pattern_timestep,
                 'wrap': wrap,
                 'multipliers': list(multipliers)}
    
        self.add_pattern(name, entry)

    def to_Pattern(self, name, pattern_start=0):
        """
        Convert the pattern library entry to a WNTR Pattern
        """

        entry = self.get_pattern(name)

        # Note pattern_start is only used by the EpanetSimulator or WNTRSimulator
        pattern_timestep = entry['pattern_timestep']
        pattern_interpolation=True
        multipliers = entry['multipliers']
        wrap = entry['wrap']
        pattern = Pattern(name=name,
                          multipliers=multipliers,
                          time_options=(pattern_start, 
                                        pattern_timestep, 
                                        pattern_interpolation),
                          wrap=wrap)

        return pattern

    def to_Series(self, name, duration=None):
        """
        Convert the pattern library entry to a Pandas Series
        """

        entry = self.get_pattern(name)

        start_clocktime = entry['start_clocktime']
        pattern_timestep = entry['pattern_timestep']
        if duration is None:
            multipliers = entry['multipliers']
            duration = start_clocktime + len(multipliers)*pattern_timestep

        pattern = self.to_Pattern(name)

        # Get values at a particular time, can be used to resample
        index = np.arange(start_clocktime, duration, pattern_timestep)
        data = []
        for i in index:
            data.append(pattern.at(i-start_clocktime))
        series = pd.Series(index=index, data=data)

        return series

    def write_json(self, filename):
        """
        Write the library to a JSON file
        """
        data = []
        for name, entry in self.library.items():
            data.append(entry)
            
        if isinstance(filename, str):
            with open(filename, "w") as fout:
                json.dump(data, fout)

    def plot_patterns(self, names=None, duration=None, linewidth=1.5, ax=None):
        """
        Plot patterns
        """

        if names is None:
            names = self.pattern_name_list

        if ax is None:
            fig, ax = plt.subplots()

        for name in names:
            series = self.to_Series(name, duration=duration)
            series.plot(ax=ax, linewidth=linewidth, label=name)

        ax.legend()

        return ax
