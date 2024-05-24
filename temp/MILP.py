### This ia an adpative randomized rounding process to identify a feasible solution satisfying minimum demand and maximum risk requirements. 
import networkx as nx
import pandas as pd
import copy
import myDictionaryGRB20240220 as mdg
from gurobipy import *
import random
import myDictionary20240220 as md
import math
import time
import datetime
import numpy as np
import socket

machineName = socket.gethostname()

weightDemandMILP = 0.5

# size , demandRequired, riskLimit = 30, 300, 650 # IEEE-30
size , demandRequired, riskLimit = 118, 1140, 8900 # 1158, 9080 # IEEE-118

print(datetime.datetime.now())

lines = pd.read_csv('data/lines_%s.csv'%size)
nodes = pd.read_csv('data/nodes_%s.csv'%size)

rNode = 1
slackBus = 1
riskFunction, source, target, susceptance, typeFunction, flowLimit, lineFunction, key, nodeArray, lineArray, theContingent, theMonitored, theSwitchable, G = md.profile(lines,nodes)    

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



model = Model('wild fire')

d_vars = []
d_names = []
for i in nodeArray:
    d_vars += [(i)]
    d_names += ['d[%s]'%i]
d = model.addVars(d_vars, vtype = GRB.CONTINUOUS, name = d_names)

g_vars = []
g_names = []
for i in nodeArray:
    g_vars += [(i)]
    g_names += ['g[%s]'%i]
g = model.addVars(g_vars, vtype = GRB.CONTINUOUS, name = g_names)

x_vars = []
x_names = []
for i in nodeArray:
    x_vars += [(i)]
    x_names += ['x[%s]'%i]
x = model.addVars(x_vars, vtype = GRB.BINARY, name = x_names)

z_vars = []
z_names = []
for l in lineArray:
    z_vars += [(l)]
    z_names += ['z[%s]'%l]
z = model.addVars(z_vars, vtype = GRB.BINARY, name = z_names)

f_vars = []
f_names = []
for l in lineArray:
    f_vars += [(source[l],target[l],l)]
    f_names += ['F[%s,%s,%s]'%(source[l],target[l],l)]
    f_vars += [(target[l],source[l],l)]
    f_names += ['F[%s,%s,%s]'%(target[l],source[l],l)]
F = model.addVars(f_vars, vtype = GRB.CONTINUOUS, name = f_names)

fc_vars = []
fc_names = []
for c in theContingent:
    for l in lineArray:
        fc_vars += [(source[l],target[l],l,c)]
        fc_names += ['FC[%s,%s,%s,%s]'%(source[l],target[l],l,c)]
        fc_vars += [(target[l],source[l],l,c)]
        fc_names += ['FC[%s,%s,%s,%s]'%(target[l],source[l],l,c)]
FC = model.addVars(fc_vars, vtype = GRB.CONTINUOUS, name = fc_names)



# add constraints
## demand required

LHS_Demand = []
LHS_Risk = []
for i in nodeArray:
    LHS_Demand += [(1,d[i])]
for l in lineArray:
    LHS_Risk += [(riskFunction[l],z[l])]
model.addConstr(LinExpr(LHS_Demand)>=demandRequired, name='Eq.demandRequired')
model.addConstr(LinExpr(LHS_Risk)<=riskLimit, name='Eq.riskLimit')

## total balance = 0
LHS = []
for b in nodeArray:
    LHS += [(1,d[b]),(-1,g[b])] 
model.addConstr(LinExpr(LHS)==0, name='Eq.total balance = 0')

## dMax, gMax
for b in nodeArray:
    dLHS = [(1,d[b]),(-dMax[b],x[b])]
    gLHS = [(1,g[b]),(-gMax[b],x[b])]
    model.addConstr(LinExpr(dLHS)<=0, name='Eq.dMax[%s]'%b)
    model.addConstr(LinExpr(gLHS)<=0, name='Eq.gMax[%s]'%b)

LHS = [(1,x[rNode])]
model.addConstr(LinExpr(LHS)==1, name='Eq.x[rNode] = 1')

## node-line relation
for l in lineArray:
    LHS1 = [(1,x[source[l]]),(-1,z[l])]
    LHS2 = [(1,x[target[l]]),(-1,z[l])]
    model.addConstr(LinExpr(LHS1)>=0, name='Eq.nodeEdge1(%s)'%(l))
    model.addConstr(LinExpr(LHS2)>=0, name='Eq.nodeEdge2(%s)'%(l))

## edge constraint
for l in lineArray:
    if l not in theSwitchable:
        LHS = [(1,x[source[l]]),(1,x[target[l]]),(-1,z[l])]
        model.addConstr(LinExpr(LHS)<=1, name='Eq.edgeConstraint(%s)'%(l))

for l in lineArray:
    LHS = [(1,F[source[l],target[l],l]),(1,F[target[l],source[l],l]),(-len(nodeArray),z[l])]
    model.addConstr(LinExpr(LHS)<=0, name='Eq.flowCapacity(%s)'%(l))

LHS = []
for l in lineArray:
    if source[l] == rNode:
        LHS += [(1,F[target[l],source[l],l])]
    if target[l] == rNode:
        LHS += [(1,F[source[l],target[l],l])]
model.addConstr(LinExpr(LHS)==0, name='Eq.infow=0')

LHS = []
for l in lineArray:
    if target[l] == rNode:
        LHS += [(1,F[target[l],source[l],l])]
    if source[l] == rNode:
        LHS += [(1,F[source[l],target[l],l])]
for i in nodeArray:
    if i != rNode:
        LHS += [(-1,x[i])]
model.addConstr(LinExpr(LHS)==0, name='Eq.flowValue=sumx')

for i in nodeArray:
    if i != rNode:
        LHS = [(-1,x[i])]
        for l in lineArray:
            if source[l] == i:
                LHS += [(1,F[target[l],source[l],l])]
                LHS += [(-1,F[source[l],target[l],l])]
            if target[l] == i:
                LHS += [(1,F[source[l],target[l],l])]
                LHS += [(-1,F[target[l],source[l],l])]
        model.addConstr(LinExpr(LHS)==0, name='Eq.flowBalance(%s)'%i)


for c in theContingent:
    LHS = [(1,FC[source[c],target[c],c,c]),(1,FC[target[c],source[c],c,c])]
    model.addConstr(LinExpr(LHS)==0, name='Eq.fcCap=0(%s)'%c)

for c in theContingent:
    for l in lineArray:
        LHS = [(1,FC[source[l],target[l],l,c]),(1,FC[target[l],source[l],l,c]),(-len(nodeArray),z[l])]
        model.addConstr(LinExpr(LHS)<=0, name='Eq.fcCapacity(%s,%s)'%(l,c))

for c in theContingent:
    LHS = []
    for l in lineArray:
        if source[l] == rNode:
            LHS += [(1,FC[target[l],source[l],l,c])]
        if target[l] == rNode:
            LHS += [(1,FC[source[l],target[l],l,c])]
    model.addConstr(LinExpr(LHS)==0, name='Eq.FCinfow=0(%s)'%c)

for c in theContingent:
    LHS = []
    for l in lineArray:
        if target[l] == rNode:
            LHS += [(1,FC[target[l],source[l],l,c])]
        if source[l] == rNode:
            LHS += [(1,FC[source[l],target[l],l,c])]
    for i in nodeArray:
        if i != rNode:
            LHS += [(-1,x[i])]
    model.addConstr(LinExpr(LHS)==0, name='Eq.flowValueC=sumx(%s)'%c)

for c in theContingent:
    for i in nodeArray:
        if i != rNode:
            LHS = [(-1,x[i])]
            for l in lineArray:
                if source[l] == i:
                    LHS += [(1,FC[target[l],source[l],l,c])]
                    LHS += [(-1,FC[source[l],target[l],l,c])]
                if target[l] == i:
                    LHS += [(1,FC[source[l],target[l],l,c])]
                    LHS += [(-1,FC[target[l],source[l],l,c])]
            model.addConstr(LinExpr(LHS)==0, name='Eq.flowCBalance(%s,%s)'%(i,c))



objTerms = []
for i in nodeArray:
    objTerms += [(weightDemandMILP,d[i])]
for l in lineArray:
    objTerms += [(-(1 - weightDemandMILP) * riskFunction[l], z[l])]

model.setObjective(LinExpr(objTerms), GRB.MAXIMIZE)

model.update()
model.optimize()

# read totalDemand and risk
totalDemand = 0.0
totalRisk = 0.0
referenceNodes = []
solutionSwitch = {}
subNodeArray = []
subLineArray = []
subContingent = []
subMonitored = []
for v in model.getVars():
    if v.varname[0] == 'd':
        #print(v.varname, v.x)
        totalDemand += v.x
    if v.varname[0] == 'z':
        # print(v.varname, v.varname[2:-1],v.x)
        l = int(v.varname[2:-1])
        totalRisk += riskFunction[l] * int(v.x + 0.0001)
        if l in theSwitchable:
            solutionSwitch[l] = int(v.x + 0.0001)
        if int(v.x + 0.0001) == 1:
            subLineArray += [l]
            if l in theContingent:
                subContingent+= [l]
            if l in theMonitored:
                subMonitored += [l]            
                
    if v.varname[0] == 'x':
        #print(v.varname, v.x)
        if int(v.x + 0.0001) == 1:
            referenceNodes += [int(v.varname[2:-1])]

print(len(referenceNodes),nx.is_connected(G.subgraph(referenceNodes)))            

print()
print('demandRequired =',demandRequired)
print('riskLimit =',riskLimit)

print()
print('MILP Demand =',totalDemand)
print('totalRisk =',totalRisk)
print('MILP objective (with lambda = %s) ='%weightDemandMILP,totalDemand * weightDemandMILP - (1 - weightDemandMILP) * totalRisk)


noSlackSubNodeArray = copy.deepcopy(referenceNodes)
if slackBus in referenceNodes:
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

demandModel = mdg.subproblem(Delta, indexOfLine, indexOfNode, DeltaC, indexOfLineC, indexOfNodeC, lineArrayC, slackBus, subNodeArray, subLineArray, source, target, flowLimit, dMax, gMax, subContingent, subMonitored)

trueDemand = 0.0
for v in demandModel.getVars():
    if v.varname[0] == 'd':
        trueDemand += v.x

print()
print('True Demand =',trueDemand)
print('totalRisk =',totalRisk)
print('True objective (with lambda = %s) ='%weightDemandMILP,trueDemand * weightDemandMILP - (1 - weightDemandMILP) * totalRisk)
if trueDemand >= demandRequired and totalRisk <= riskLimit:
    print('MILP Solution is FEASIBLE')
else:
    print('MILP Solution is INFEASIBLE')
    











