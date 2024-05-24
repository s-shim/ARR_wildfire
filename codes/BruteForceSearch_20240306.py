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
from itertools import product

weightDemand = 0.5

size = 30 # IEEE-30
#size = 118 # IEEE-118

print(datetime.datetime.now())
#timeLimit = 600

lines = pd.read_csv('data/lines_%s.csv'%size)
nodes = pd.read_csv('data/nodes_%s.csv'%size)

rNode = sorted(list(nodes['Bus']))[0]
slackBus = sorted(list(nodes['Bus']))[0]
print('rNode=',rNode)
print('slackBus=',slackBus)
riskFunction, source, target, susceptance, typeFunction, flowLimit, lineFunction, key, nodeArray, lineArray, theContingent, theMonitored, theSwitchable, G = md.profile(lines,nodes)    

zeroSwitch = {}
for l in theSwitchable:
    zeroSwitch[l] = 0

noSlackNodeArray = copy.deepcopy(nodeArray)
if slackBus != -1:
    noSlackNodeArray.remove(slackBus)
        
gMax = {}
dMax = {}
nodeArray = list(nodes['Bus'])    
for b in nodeArray:
    [gLimit] = nodes.loc[nodes['Bus']==b, 'Capacity (MW)']
    [dLimit] = nodes.loc[nodes['Bus']==b, 'Load (MW)']
    gMax[b] = gLimit
    dMax[b] = dLimit

len_listProduct = 2 ** len(theSwitchable)
print('len_listProduct =', len_listProduct)

countSecuredArray = []
timeArray = []
weightDemandArray = []
phase2Array = []
demandArray = []
riskArray = []
intSwitchableArray = {}
for l in theSwitchable:
    intSwitchableArray[l] = []

tic = time.time()
countSecured = 0
count = 0
intSwitchable = {}
for switchOnOff in product([0,1],repeat=len(theSwitchable)):
   
    #print('count =',count)
    for ind in range(len(theSwitchable)):
        intSwitchable[theSwitchable[ind]] = 1 - switchOnOff[ind]
        
    copyG = copy.deepcopy(G)
    for l in theSwitchable:        
        if intSwitchable[l] == 0:
            copyG.remove_edge(source[l],target[l],key[l])
        
    subNodeArray = list(nx.node_connected_component(copyG,rNode))    
    subG = copyG.subgraph(subNodeArray)
    subLineArray = []
    subContingent = []
    subMonitored = []
    subSwitch = []
    intSwitch = copy.deepcopy(zeroSwitch)
    for (source_e,target_e,key_e) in subG.edges(keys=True):
        [source_e,target_e] = sorted([source_e,target_e])
        subLineArray += [ lineFunction[source_e,target_e,key_e] ]
        if typeFunction[lineFunction[source_e,target_e,key_e]] == 'Contingency':
            subContingent += [lineFunction[source_e,target_e,key_e]]
        if typeFunction[lineFunction[source_e,target_e,key_e]] == 'Monitored':
            subMonitored += [lineFunction[source_e,target_e,key_e]]
        if typeFunction[lineFunction[source_e,target_e,key_e]] == 'Switchable':
            intSwitch[lineFunction[source_e,target_e,key_e]] = 1
            subSwitch += [lineFunction[source_e,target_e,key_e]]

    secured = True
    for l in subContingent:
        subGCopy = nx.MultiGraph(subG)
        subGCopy.remove_edge(source[l],target[l],key[l])
        if nx.has_path(subGCopy,source[l],target[l]) == False:
            secured = False
            break

    if secured == True:  
        countSecured += 1

        noSlackSubNodeArray = copy.deepcopy(subNodeArray)
        if slackBus in subNodeArray:
            noSlackSubNodeArray.remove(slackBus)    
        Delta, indexOfLine, indexOfNode = md.isf(slackBus, noSlackSubNodeArray, susceptance, subLineArray, source, target)
    
        DeltaC = {}
        indexOfLineC = {}
        indexOfNodeC = {}
        lineArrayC = {}
        for l_c in subContingent:
            lineArrayC[l_c] = copy.deepcopy(subLineArray)
            lineArrayC[l_c].remove(l_c)
            DeltaC[l_c], indexOfLineC[l_c], indexOfNodeC[l_c] = md.isf(slackBus, noSlackSubNodeArray, susceptance, lineArrayC[l_c], source, target)
        
        model = mdg.subproblem(Delta, indexOfLine, indexOfNode, DeltaC, indexOfLineC, indexOfNodeC, lineArrayC, slackBus, subNodeArray, subLineArray, source, target, flowLimit, dMax, gMax,subContingent,subMonitored)


        # read totalDemand and risk
        totalDemand = 0.0
        for v in model.getVars():
            if v.varname[0] == 'd':
                totalDemand += v.x
        
        totalRisk = 0.0
        for l in subLineArray:
            totalRisk += riskFunction[l]

        print()          
        print('count =',count,'/',len_listProduct)
        print('countSecured =',countSecured)
        print('Phase II: totalDemand - totalRisk=',weightDemand * totalDemand - (1- weightDemand) * totalRisk)
        print('totalDemand =',totalDemand)
        print('totalRisk =',totalRisk)

        countSecuredArray += [countSecured]
        toc = time.time()
        timeArray += [toc-tic]
        weightDemandArray += [weightDemand]
        phase2Array += [weightDemand * totalDemand - (1- weightDemand) * totalRisk]
        demandArray += [totalDemand]
        riskArray += [totalRisk]

        list_of_tuples = list(zip(countSecuredArray, timeArray, weightDemandArray, phase2Array, demandArray, riskArray))
        df = pd.DataFrame(list_of_tuples, columns=['countSecured', 'Time', 'Demand Weight To Risk', 'Phase2', 'Demand', 'Risk'])

        for l in theSwitchable:
            intSwitchableArray[l] += [intSwitch[l]]
            df['%s'%l] = intSwitchableArray[l]

        df.to_csv('switch_%s.csv'%len(G.nodes()), index=False)
        
    count += 1

print()
print('FINISH')
print('count =',count,'/',len_listProduct)
print('countSecured =',countSecured)

