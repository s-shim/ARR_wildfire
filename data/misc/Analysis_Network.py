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


size = 500

lines = pd.read_csv('lines_%s.csv'%size)
nodes = pd.read_csv('nodes_%s.csv'%size)

G = nx.MultiGraph()

source = {}
target = {}
key = {}
for l in lines['Line']:
    [source_l] = lines.loc[lines['Line']==l,'Source']
    [target_l] = lines.loc[lines['Line']==l,'Target']
    source[l] = source_l
    target[l] = target_l
    key[l] = G.add_edge(source_l,target_l)

theVulnerable = []
for l in lines['Line']:
    copyG= copy.deepcopy(G)
    copyG.remove_edge(source[l],target[l],key[l])
    if nx.has_path(copyG,source[l],target[l]) == True:
        theVulnerable += [1]
    else:
        theVulnerable += [0]

lines['Vulnerable'] = theVulnerable
lines.to_csv('lines_%s.csv'%size, index=False)




















