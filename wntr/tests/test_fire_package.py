# -*- coding: utf-8 -*-
"""
Created on Tue Feb 26 15:45:18 2019

@author: PHassett
"""

#from nose.tools import *
import unittest
from os.path import abspath, dirname, join
import wntr


testdir = dirname(abspath(str(__file__)))
datadir = join(testdir, 'networks_for_testing')
netdir = join(testdir, '..','..','examples','networks')

class TestFireMethods(unittest.TestCase):

        inp_file = join(netdir, 'net3.inp')
        wn = wntr.network.WaterNetworkModel(inp_file)

     
    