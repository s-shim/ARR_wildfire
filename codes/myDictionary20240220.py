import networkx as nx
import pandas as pd
import copy
#import myDictionary_GRB as mdg
#from gurobipy import *
import random
#import myDictionary as md
import math
import time
import datetime
import numpy as np



def isf(slackBus, noSlackNodeArray, susceptance, lineArray, source, target):
    zeroM, zeroD, indexOfLine, indexOfNode = zeroMatrices(noSlackNodeArray, lineArray)
    
    M = copy.deepcopy(zeroM)
    D = copy.deepcopy(zeroD)
    
    for l in lineArray:
        if slackBus != source[l]:
            M[indexOfLine[l],indexOfNode[source[l]]] = -1
        if slackBus != target[l]:
            M[indexOfLine[l],indexOfNode[target[l]]] =  1        
        D[indexOfLine[l]][indexOfLine[l]] = susceptance[l]
    
    DM = np.dot(D,M)
    MTDM = np.dot(M.T,DM)
    invMTDM = np.linalg.inv(MTDM)
    Delta = np.dot(DM,invMTDM)
    
    # print(np.linalg.det(MTDM))
    
    return Delta, indexOfLine, indexOfNode



def profile(lines,nodes):
  
    source = {}
    target = {}
    susceptance = {}
    typeFunction = {}
    riskFunction = {}
    flowLimit = {}
    lineFunction = {}
    linePairArray = []
    lineArray = list(lines['Line'])
    key = {}
    
    nodeMultiSet = []
    theContingent = []
    theMonitored = []
    theSwitchable = []
    G = nx.MultiGraph()
    for l in lineArray:
        [risk_l] = lines.loc[lines['Line']==l,'Risk']
        riskFunction[l] = risk_l
        [source_l] = lines.loc[lines['Line']==l,'Source']
        [target_l] = lines.loc[lines['Line']==l,'Target']
        [type_l] = lines.loc[lines['Line']==l,'Type']
        [susceptance_l] = lines.loc[lines['Line']==l,'Susceptance']
        #[flowLimit_l] = lines.loc[lines['Line']==l,'Emergency Flow Limit (MW)']
        [flowLimit_l] = lines.loc[lines['Line']==l,'Flow Limit (MW)']        
        [source_l,target_l] = sorted([source_l,target_l])
        key[l] = G.add_edge(source_l,target_l)
        typeFunction[l] = type_l
        
        lineFunction[source_l,target_l,key[l]] = l 
        source[l] = source_l
        target[l] = target_l
        susceptance[l] = susceptance_l
        flowLimit[l] = flowLimit_l
    
        nodeMultiSet.append(source_l)
        nodeMultiSet.append(target_l)

        [type_l] = lines.loc[lines['Line']==l,'Type']
        if type_l == 'Contingency':
            theContingent += [l]
        if type_l == 'Monitored':
            theMonitored += [l]
        if type_l == 'Switchable':
            theSwitchable += [l]
    
    nodeArray = list(set(nodeMultiSet))    
    
    return riskFunction, source, target, susceptance, typeFunction, flowLimit, lineFunction, key, nodeArray, lineArray, theContingent, theMonitored, theSwitchable, G     



def zeroMatrices(nodeArray, lineArray):    
    indexOfNode = {}
    indexOfLine = {}
    zeroIncidenceArray = []
    zeroSusceptanceArray = []
    for i in range(len(nodeArray)):
        zeroIncidenceArray += [0]
        indexOfNode[nodeArray[i]] = i
    for j in range(len(lineArray)):
        zeroSusceptanceArray += [0]     
        l = lineArray[j]
        indexOfLine[l] = j

    zeroIncidence = []
    zeroSusceptance = []
    for l in lineArray:
        zeroIncidence   += [zeroIncidenceArray]
        zeroSusceptance += [zeroSusceptanceArray]
    
    zeroM = np.array(zeroIncidence)
    zerod = np.array(zeroSusceptance)
    zeroD = zerod.astype(float)
    
    return zeroM, zeroD, indexOfLine, indexOfNode








