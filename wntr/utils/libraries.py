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

    def add_pattern(self, name, entry):
        """
        Add a pattern to the library
        """
        assert isinstance(name, str)
        assert isinstance(entry, dict)
        assert entry.keys() <= ['category',
                                'description',
                                'source',
                                'start_clocktime',
                                'pattern_timestep',
                                'multipliers']

        self.library[name] = entry

    def combine_patterns(self, names, pattern_timestep=3600,
                         pattern_duration=86400, start_clocktime=0,
                         normalize=False, name='Combined'):
        """
        Combine patterns to create a new pattern
        """
        series = {}
        for n in names:
            series[n] = self.to_Series(n,
                                       pattern_timestep=pattern_timestep,
                                       pattern_duration=pattern_duration,
                                       start_clocktime=start_clocktime)
        df = pd.DataFrame(series)
        multipliers = df.sum(axis=1)

        if normalize:
            multipliers = multipliers/multipliers.mean()

        entry = {
         'category': None,
         'description': None,
         'source': None,
         'start_clocktime': start_clocktime,
         'pattern_timestep': pattern_timestep,
         'multipliers': list(multipliers)}

        self.library[name] = entry

    def normalize_pattern(self, name):
        """
        Normalize values in a pattern so the mean equals 1
        """

        assert isinstance(name, str)

        multipliers = self.library[name]['multipliers']
        multipliers = multipliers/multipliers.mean()

        self.library[name]['multipliers'] = multipliers.values()

    def apply_noise(self, name, std, normalize=False):
        """
        Apply gaussian random noise to a pattern
        """

        assert isinstance(name, str)
        assert isinstance(std, (int, float))
        assert isinstance(normalize, bool)

        multipliers = self.library[name]['multipliers']
        noise = np.random.normal(0, std, len(multipliers))
        multipliers = multipliers + noise

        if normalize:
            multipliers = multipliers/multipliers.mean()

        self.library[name]['multipliers'] = list(multipliers)

    def add_pulse_pattern(self, on_off_sequence, pattern_timestep=3600,
                          pattern_duration=86400, start_clocktime=0,
                          invert=False, normalize=False, name='Pulse'):
        """
        Add a pulse pattern to the library using a sequence of on/off times
        """

        assert isinstance(on_off_sequence, list)
        assert np.all(np.diff(on_off_sequence) > 0) # is monotonically increasing

        index = np.arange(start_clocktime, pattern_duration, pattern_timestep)
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
         'source': None,
         'start_clocktime': start_clocktime,
         'pattern_timestep': pattern_timestep,
         'multipliers': list(multipliers)}

        self.library[name] = entry

    def add_gaussian_pattern(self, mean, std, pattern_timestep=3600,
                             pattern_duration=86400, start_clocktime=0,
                             invert=False, normalize=False, name='Gaussian'):
        """
        Add a Guassian pattern to the library defined by a mean and standard
        deviation
        """

        index = np.arange(start_clocktime, pattern_duration, pattern_timestep)
        multipliers = scipy.stats.norm.pdf(index, mean, std)

        if invert:
            multipliers = multipliers.max() - multipliers

        if normalize:
            multipliers = multipliers/multipliers.mean()

        entry = {
         'category': None,
         'description': None,
         'source': None,
         'start_clocktime': start_clocktime,
         'pattern_timestep': pattern_timestep,
         'multipliers': list(multipliers)}

        self.library[name] = entry

    def add_triangular_pattern(self, start, peak, end, pattern_timestep=3600,
                               pattern_duration=86400, start_clocktime=0,
                               invert=False, normalize=False, name='Triangular'):
        """
        Add a traingular pattern to the library defined by a start time,
        peak time, and end time
        """
        loc = start
        scale = end-start
        c = (peak-start)/(end-start)

        index = np.arange(start_clocktime, pattern_duration, pattern_timestep)
        multipliers = scipy.stats.triang.pdf(index, c, loc, scale)

        if invert:
            multipliers = multipliers.max() - multipliers

        if normalize:
            multipliers = multipliers/multipliers.mean()

        entry = {
         'category': None,
         'description': None,
         'source': None,
         'start_clocktime': start_clocktime,
         'pattern_timestep': pattern_timestep,
         'multipliers': list(multipliers)}

        self.library[name] = entry

    def to_Pattern(self, name):
        """
        Convert the pattern library entry to a WNTR Pattern
        """

        entry = self.library[name]
        start_clocktime = entry['start_clocktime']
        pattern_timestep = entry['pattern_timestep']
        multipliers = entry['multipliers']
        pattern = Pattern(name,
                          multipliers,
                          (start_clocktime, pattern_timestep),
                          True)

        return pattern

    def to_Series(self, name, pattern_timestep=3600, pattern_duration=86400,
                  start_clocktime=0):
        """
        Convert the pattern library entry to a Pandas Series
        """

        entry = self.library[name]

        if start_clocktime is None:
            start_clocktime = entry['start_clocktime']
        if pattern_timestep is None:
            pattern_timestep = entry['pattern_timestep']
        if pattern_duration is None:
            multipliers = entry['multipliers']
            pattern_duration = len(multipliers)*pattern_timestep

        pattern = self.to_Pattern(name)

        # Get values at a particular time, can be used to resample
        index = np.arange(start_clocktime, pattern_duration, pattern_timestep)
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

    def plot_patterns(self, names=None, pattern_timestep=3600,
                      pattern_duration=86400, start_clocktime=0,
                      linewidth=1.5, ax=None):
        """
        Plot patterns
        """

        if names is None:
            names = self.library.keys()

        if ax is None:
            fig, ax = plt.subplots()

        for name in names:
            series = self.to_Series(name,
                                    pattern_timestep=pattern_timestep,
                                    pattern_duration=pattern_duration,
                                    start_clocktime=start_clocktime)
            series.plot(ax=ax, linewidth=linewidth, label=name)

        ax.legend()

        return ax
