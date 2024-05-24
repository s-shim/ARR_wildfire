### This ia an adpative randomized rounding process to identify a feasible solution satisfying minimum demand and maximum risk requirements. 
import networkx as nx
import pandas as pd
import copy
#import myDictionaryGRB20240220 as mdg
#from gurobipy import *
import random
#import myDictionary20240220 as md
import math
import time
import datetime
import numpy as np
import socket

machineName = socket.gethostname()

weightDemand = 0.5

# size , demandRequired, riskLimit = 30, 300, 650 # IEEE-30
# size , demandRequired, riskLimit = 118, 1140, 8900 # 1158, 9080 # IEEE-118
# size , demandRequired, riskLimit = 1354, 1140, 8900 # 1158, 9080 # IEEE-118
# size , demandRequired, riskLimit = 300, 10000, 10000
size = 500

print(datetime.datetime.now())

lines = pd.read_csv('lines_%s.csv'%size)
nodes = pd.read_csv('nodes_%s.csv'%size)
generators = pd.read_csv('generators_%s.csv'%size)

buses = []
powerCaps = []
for b in nodes['Bus']:
    genCap = 0.0
    for g in generators['Bus']:
        if b == g:
            [pmax] = generators.loc[generators['Bus']==g,'Pmax']
            genCap += pmax
    buses += [b]
    powerCaps += [genCap]
nodes['Capacity (MW)'] = powerCaps
nodes.to_csv('nodes_%s.csv'%size, index=False)









