### This ia an adpative randomized rounding process to identify a feasible solution satisfying minimum demand and maximum risk requirements. 
import networkx as nx
import pandas as pd
import copy
import myDictionaryGRB as mdg
#from gurobipy import *
import random
import myDictionary as md
import math
import time
import datetime
import numpy as np
import socket

machineName = socket.gethostname()

# weightDemand = 0.5

# size , demandRequired, riskLimit = 30, 0, 999 # IEEE-30
size , demandRequired, riskLimit = 500, 0, 9999 # SC-500

print(datetime.datetime.now())
timeLimit = 10

instance = 1
#for instance in range(1,11):

lines = pd.read_csv('data/lines_%s_inst%s.csv'%(size,instance))
nodes = pd.read_csv('data/nodes_%s.csv'%size)

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
totalDemand = 0.0
for v in model.getVars():
    if v.varname[0] == 'd':
        totalDemand += v.x

totalRisk = 0
for l in lineArray:
    totalRisk += riskFunction[l]

weightDemand = 1 / (1 + totalDemand / totalRisk)

allSwitch = {}
halfSwitch = {}
zeroSwitch = {}
for l in theSwitchable:
    allSwitch[l] = 1
    halfSwitch[l] = 0.5
    zeroSwitch[l] = 0
    
bestSwitch = copy.deepcopy(allSwitch)
bestInfeasible = min(0, totalDemand - demandRequired) + min(0, - totalRisk + riskLimit) 
bestDemand = totalDemand
bestRisk = totalRisk

print('Trial =',0,'; Time =',0.0,'; infeasibility =',bestInfeasible)
print('Demand=',bestDemand)
print('Risk=',bestRisk)

relaxSwitch = copy.deepcopy(halfSwitch)
tic = time.time()
toc = time.time()
trial = 0
nLocal = 0
feasibleSolution = False

if bestInfeasible > 0.0 - 0.0001:
    print('### FEASIBLE SOLUTION FOUND')
    feasibleSolution = True

if feasibleSolution == False:
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
                
                totalRisk = 0.0
                for l in subLineArray:
                    totalRisk += riskFunction[l]
                                
                infeasibility = min(0, totalDemand - demandRequired) + min(0, - totalRisk + riskLimit) 
    
                if bestInfeasible < infeasibility:
                    bestInfeasible = infeasibility
                    bestSwitch = copy.deepcopy(intSwitch)
                    bestDemand = totalDemand
                    bestRisk = totalRisk
                    toc = time.time()
                    print()
                    print('Trial =',trial,'; Time =',toc-tic,'; infeasibility =',bestInfeasible)
                    print('Demand=',bestDemand)
                    print('Risk=',bestRisk)
                    if bestInfeasible > 0.0 - 0.0001:
                        print('### FEASIBLE SOLUTION FOUND')
                        feasibleSolution = True
                        
                        break
    
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
    
if feasibleSolution == True:
    machineNameArray = [machineName]
    sizeArray = [size]
    demandRequiredArray = [demandRequired]
    riskLimitArray = [riskLimit]
    trialArray = [0]
    timeArray = [toc - tic]
    weightDemandArray = [weightDemand]
    phase2Array = [weightDemand * bestDemand - (1 - weightDemand) * bestRisk]
    demandArray = [bestDemand]
    riskArray = [bestRisk]

    list_of_tuples = list(zip(machineNameArray, sizeArray, demandRequiredArray, riskLimitArray, trialArray, timeArray, weightDemandArray, phase2Array, demandArray, riskArray))
    df = pd.DataFrame(list_of_tuples, columns=['Machine', 'Size', 'demandRequired', 'riskLimit', 'Trial', 'Time', 'weightDemand', 'Phase2', 'Demand', 'Risk'])

    for l in theSwitchable:
        df['%s'%l] = [bestSwitch[l]]

    df.to_csv('bestSwitchPhase0_%s_inst%s.csv'%(len(G.nodes()),instance), index=False)
    







