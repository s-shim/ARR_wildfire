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

bestSolutions = pd.read_csv('bestSwitchPhase0_%s_inst%s.csv'%(size,instance))
[demandRequired] = bestSolutions.loc[bestSolutions['Trial']==0,'demandRequired']
[riskLimit] = bestSolutions.loc[bestSolutions['Trial']==0,'riskLimit']
[timePhase1] = bestSolutions.loc[bestSolutions['Trial']==0,'Time']

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
totalDemand = 0
for v in model.getVars():
    if v.varname[0] == 'd':
        totalDemand += v.x
print('totalDemand =',totalDemand)

totalRisk = 0
for l in lineArray:
    totalRisk += riskFunction[l]
print('totalRisk =',totalRisk)

allSwitch = {}
halfSwitch = {}
zeroSwitch = {}
bestSwitch = {}
for l in theSwitchable:
    allSwitch[l] = 1
    halfSwitch[l] = 0.5
    zeroSwitch[l] = 0
    [switch_l] = bestSolutions.loc[bestSolutions['Trial']==0,'%s'%l]
    bestSwitch[l] = switch_l

[bestDemand] = bestSolutions.loc[bestSolutions['Trial']==0,'Demand']
[bestRisk] = bestSolutions.loc[bestSolutions['Trial']==0,'Risk']
[bestPhase2] = bestSolutions.loc[bestSolutions['Trial']==0,'Phase2']
[weightDemand] = bestSolutions.loc[bestSolutions['Trial']==0,'weightDemand']

machineNameArray = list(bestSolutions['Machine'])
sizeArray = list(bestSolutions['Size'])
demandRequiredArray = list(bestSolutions['demandRequired'])
riskLimitArray = list(bestSolutions['riskLimit'])
trialArray = list(bestSolutions['Trial'])
timeArray = list(bestSolutions['Time'])
weightDemandArray = list(bestSolutions['weightDemand'])
phase2Array = list(bestSolutions['Phase2'])
demandArray = list(bestSolutions['Demand'])
riskArray = list(bestSolutions['Risk'])

soldf = {}
for l in theSwitchable:
    soldf[l] = list(bestSolutions['%s'%l])
    
# =============================================================================
# bestSwitch = copy.deepcopy(allSwitch)
# bestInfeasible = min(0, totalDemand - demandRequired) + min(0, - totalRisk + riskLimit) 
# =============================================================================

relaxSwitch = copy.deepcopy(halfSwitch)
tic = time.time()
toc = time.time()
print(0,toc-tic,'bestPhase2 =',bestPhase2)
trial = 0
nLocal = 0
feasibleSolution = False
while toc - tic < timeLimit:
    trial += 1
    move = True
    
    copyG = copy.deepcopy(G)
    for l in theSwitchable:        
        ptbSwitchOpen  = relaxSwitch[l] * random.random() 
        ptbSwitchClose = relaxSwitch[l] + (1 - relaxSwitch[l]) * random.random() 
    
        if ptbSwitchOpen - 0 < 1 - ptbSwitchClose:
            copyG.remove_edge(source[l],target[l],key[l])
            
    subNodeArray = list(nx.node_connected_component(copyG,rNode))    
    subG = copyG.subgraph(subNodeArray)
    subLineArray = []
    subContingent = []
    subMonitored = []
    intSwitch = copy.deepcopy(zeroSwitch)
    same = True
    for (source_e,target_e,key_e) in subG.edges(keys=True):
        [source_e,target_e] = sorted([source_e,target_e])
        subLineArray += [ lineFunction[source_e,target_e,key_e] ]
        if typeFunction[lineFunction[source_e,target_e,key_e]] == 'Contingency':
            subContingent += [lineFunction[source_e,target_e,key_e]]
        if typeFunction[lineFunction[source_e,target_e,key_e]] == 'Monitored':
            subMonitored += [lineFunction[source_e,target_e,key_e]]
        if typeFunction[lineFunction[source_e,target_e,key_e]] == 'Switchable':
            intSwitch[lineFunction[source_e,target_e,key_e]] = 1
            if bestSwitch[lineFunction[source_e,target_e,key_e]] == 0:
                same = False
    if same == True:
        for l in theSwitchable:
            if intSwitch[l] != bestSwitch[l]:
                same = False
                break

    if same == True:    
        nLocal += 1
        
        RMSD = 0.0
        for l in theSwitchable:
            RMSD += (relaxSwitch[l] - 0.5) ** 2
        RMSD = RMSD / len(theSwitchable)
        RMSD = math.sqrt(RMSD)
        
        if random.random() < RMSD * min(1, nLocal / 20):
            relaxSwitch = copy.deepcopy(halfSwitch)
            move = False
        
    else:
        nLocal = 0

        totalRisk = 0.0
        for l in subLineArray:
            totalRisk += riskFunction[l]

        if totalRisk <= riskLimit:
        
            secured = True
            for l in subContingent:
                subGCopy = nx.MultiGraph(subG)
                subGCopy.remove_edge(source[l],target[l],key[l])
                if nx.has_path(subGCopy,source[l],target[l]) == False:
                    secured = False
                    break
        
            if secured == True:  
                
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

                if totalDemand >= demandRequired and bestPhase2 < weightDemand * totalDemand - (1 - weightDemand) * totalRisk:    
                    bestPhase2 = weightDemand * totalDemand - (1 - weightDemand) * totalRisk
                    bestSwitch = copy.deepcopy(intSwitch)
                    bestDemand = totalDemand
                    bestRisk = totalRisk
                    toc = time.time()
                    print(trial,toc-tic,'bestPhase2 =',bestPhase2)

                    machineNameArray += [machineName]
                    sizeArray += [size]
                    demandRequiredArray += [demandRequired]
                    riskLimitArray += [riskLimit]
                    trialArray += [trial]
                    timeArray += [toc - tic + timePhase1]
                    weightDemandArray += [weightDemand]
                    phase2Array += [bestPhase2]
                    demandArray += [bestDemand]
                    riskArray += [bestRisk]
                
                    list_of_tuples = list(zip(machineNameArray, sizeArray, demandRequiredArray, riskLimitArray, trialArray, timeArray, weightDemandArray, phase2Array, demandArray, riskArray))
                    df = pd.DataFrame(list_of_tuples, columns=['Machine', 'Size', 'demandRequired', 'riskLimit', 'Trial', 'Time', 'weightDemand', 'Phase2', 'Demand', 'Risk'])
                
                    for l in theSwitchable:
                        soldf[l] += [bestSwitch[l]]
                        df['%s'%l] = soldf[l]
                
                    df.to_csv('bestSwitchPhase2_%s_inst%s.csv'%(size,instance), index=False)

    if move == True:
        RMSD = 0.0
        for l in theSwitchable:
            RMSD += (relaxSwitch[l] - 0.5) ** 2
        RMSD = RMSD / len(theSwitchable)
        RMSD = math.sqrt(RMSD)

        alpha = 1 / (1 + math.exp(4 * RMSD))

        for l in theSwitchable:
            relaxSwitch[l] = (1 - alpha) * relaxSwitch[l]
            if bestSwitch[l] == 1:
                relaxSwitch[l] += alpha

    toc = time.time()
 









