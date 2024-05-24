### This ia an adpative randomized rounding process to identify a feasible solution satisfying minimum demand and maximum risk requirements. 
import networkx as nx
import pandas as pd
import copy
import myDictionaryGRB20240220 as mdg
#from gurobipy import *
import random
import myDictionary20240220 as md
import math
import time
import datetime
import numpy as np
import socket

machineName = socket.gethostname()

print(datetime.datetime.now())
timeLimit = 3600 * 4

# size = 30 # IEEE-30
# size = 118
# size = 300
size = 500
instance = 1

lines = pd.read_csv('data/lines_%s_inst%s.csv'%(size,instance))
nodes = pd.read_csv('data/nodes_%s.csv'%size)

bestSolutions = pd.read_csv('bestSwitchPhase2_%s_inst%s_pareto.csv'%(size,instance))

paretoArray = []
for t in bestSolutions['Trial']:
    pareto = True
    [percentD_t] = bestSolutions.loc[bestSolutions['Trial']==t,'percentD']
    [percentR_t] = bestSolutions.loc[bestSolutions['Trial']==t,'percentR']
    for tt in bestSolutions['Trial']:
        if t != tt:
            [percentD_tt] = bestSolutions.loc[bestSolutions['Trial']==tt,'percentD']
            [percentR_tt] = bestSolutions.loc[bestSolutions['Trial']==tt,'percentR']
            
            if percentD_tt >= percentD_t and percentR_tt <= percentR_t:
                pareto = False
                break
    paretoArray += [pareto]

bestSolutions['Pareto'] = paretoArray

bestSolutions.to_csv('bestSwitchPhase2_%s_inst%s_pareto.csv'%(size,instance), index=False)
    
            
    
    
    
    
    
    
    
    
    
    
    
    
    