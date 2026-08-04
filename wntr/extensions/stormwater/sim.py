"""
The wntr.stormwater.sim module includes methods to simulate 
hydraulics.
"""
import os
import pandas as pd

try:
    from openswmm.engine import Solver, EngineState
    has_swmm = True
except ModuleNotFoundError:
    has_swmm = False

from wntr.sim import SimulationResults
from wntr.extensions.stormwater.io import write_inpfile, read_outfile, read_rptfile, _extract_summary

class SWMMSimulator(object):
    """
    SWMM simulator class.
    """
    def __init__(self, swn):
        self._swn = swn

    def run_sim(self, file_prefix='temp', full_results=True):
        """
        Run a SWMM simulation
        
        Parameters
        ----------
        file_prefix : str
            Default prefix is "temp". Output files (.out and .rpt) use this prefix
        full_results: bool (optional)
            If full_results is True, the binary output file and report summary
            file are used to extract results.  If False, results are only 
            extracted from report summary file. Default = True.
        
        Returns
        -------
        Simulation results from the binary .out file (default) or summary .rpt file
        """
        if not has_swmm:
            raise ModuleNotFoundError('openswmm.engine is required')

        temp_inpfile = file_prefix + '.inp'
        if os.path.isfile(temp_inpfile):
            os.remove(temp_inpfile)
        
        temp_outfile = file_prefix + '.out'
        if os.path.isfile(temp_outfile):
            os.remove(temp_outfile)
        
        temp_rptfile = file_prefix + '.rpt'
        if os.path.isfile(temp_rptfile):
            os.remove(temp_rptfile)

        write_inpfile(self._swn, temp_inpfile)

        with Solver(temp_inpfile, temp_rptfile, temp_outfile) as s:
            while s.state == EngineState.RUNNING:
                for _ in s.steps():
                    pass
            stats_report = _extract_summary(s)
        
        if full_results:
            results = read_outfile(temp_outfile)
        else:
            results = SimulationResults()
        
        #results.report = read_rptfile(temp_rptfile)
        results.report = stats_report
        
        return results
