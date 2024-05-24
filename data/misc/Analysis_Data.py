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

weightDemand = 0.5

# size , demandRequired, riskLimit = 30, 300, 650 # IEEE-30
# size , demandRequired, riskLimit = 118, 1140, 8900 # 1158, 9080 # IEEE-118
# size , demandRequired, riskLimit = 1354, 1140, 8900 # 1158, 9080 # IEEE-118
# size , demandRequired, riskLimit = 300, 10000, 10000
size , demandRequired, riskLimit = 500, 5000, 10000

print(datetime.datetime.now())

lines = pd.read_csv('lines_%s.csv'%size)
nodes = pd.read_csv('nodes_%s.csv'%size)

rNode = sorted(list(nodes['Bus']))[0]
slackBus = sorted(list(nodes['Bus']))[0]
print('rNode=',rNode)
print('slackBus=',slackBus)
riskFunction, source, target, susceptance, typeFunction, flowLimit, lineFunction, key, nodeArray, lineArray, theContingent, theMonitored, theSwitchable, G = md.profile(lines,nodes)    

noSlackNodeArray = copy.deepcopy(nodeArray)
if slackBus != -1:
    noSlackNodeArray.remove(slackBus)

Delta, indexOfLine, indexOfNode = md.isf(slackBus, noSlackNodeArray, susceptance, lineArray, source, target)
    
DeltaC = {}
indexOfLineC = {}
indexOfNodeC = {}
lineArrayC = {}
for l_c in theContingent:   
    lineArrayC[l_c] = copy.deepcopy(lineArray)
    lineArrayC[l_c].remove(l_c)
    DeltaC[l_c], indexOfLineC[l_c], indexOfNodeC[l_c] = md.isf(slackBus, noSlackNodeArray, susceptance, lineArrayC[l_c], source, target)
    
gMax = {}
dMax = {}
nodeArray = list(nodes['Bus'])    
for b in nodeArray:
    [gLimit] = nodes.loc[nodes['Bus']==b, 'Capacity (MW)']
    [dLimit] = nodes.loc[nodes['Bus']==b, 'Load (MW)']
    gMax[b] = gLimit
    dMax[b] = dLimit

model = mdg.subproblem(Delta, indexOfLine, indexOfNode, DeltaC, indexOfLineC, indexOfNodeC, lineArrayC, slackBus, nodeArray, lineArray, source, target, flowLimit, dMax, gMax,theContingent,theMonitored)

# read totalDemand and risk
varNames = []
varValues = []
totalDemand = 0.0
for v in model.getVars():
    varNames += [v.varname]
    varValues += [v.x]
    if v.varname[0] == 'd':
        totalDemand += v.x

totalRisk = 0.0
for l in lineArray:
    totalRisk += riskFunction[l]
    
print(totalDemand,totalRisk)

list_of_tuples = list(zip(varNames,varValues))
df = pd.DataFrame(list_of_tuples, columns=['varName','varValue'])
df.to_csv('profile%s.csv'%len(G.nodes()), index=False)





















    
    
    