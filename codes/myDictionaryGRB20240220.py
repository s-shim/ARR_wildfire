import networkx as nx
import pandas as pd
import copy
from gurobipy import *
import random
import myDictionary20240220 as md
import math
import time
import datetime
import numpy as np

def subproblem(Delta, indexOfLine, indexOfNode, DeltaC, indexOfLineC, indexOfNodeC, lineArrayC, slackBus, nodeArray, lineArray, source, target, flowLimit, dMax, gMax,theContingent,theMonitored):    
    model = Model('Subproblem')
    model.setParam('OutputFlag', 0) 
           
    d_vars = []
    d_names = []
    for u in nodeArray:
        d_vars += [(u)]
        d_names += ['d[%s]'%u]
    d = model.addVars(d_vars, vtype = GRB.CONTINUOUS, name = d_names)
        
    g_vars = []
    g_names = []
    for u in nodeArray:
        g_vars += [(u)]
        g_names += ['g[%s]'%u]
    g = model.addVars(g_vars, vtype = GRB.CONTINUOUS, name = g_names)
    
    # add constraints
    ## dMax, gMax
    for b in nodeArray:
        dLHS = [(1,d[b])]
        gLHS = [(1,g[b])]
        model.addConstr(LinExpr(dLHS)<=dMax[b], name='Eq.dMax[%s]'%b)
        model.addConstr(LinExpr(gLHS)<=gMax[b], name='Eq.gMax[%s]'%b)
    
    ## total balance = 0
    LHS = []
    for b in nodeArray:
        LHS += [(1,d[b]),(-1,g[b])] 
    model.addConstr(LinExpr(LHS)==0, name='Eq.total balance = 0')
    
    
    ## power flow constraint
    pf_vars = []
    pf_names = []
    for l in lineArray:
        pf_vars += [(l)]
        pf_names += ['PF[%s]'%(l)]
    PF = model.addVars(pf_vars, vtype = GRB.CONTINUOUS, lb = -GRB.INFINITY, name = pf_names)
    
    for l in lineArray:
        LHS = [(-1,PF[l])]
        for b in nodeArray:
            if b != slackBus:
                #print(l,indexOfLine[l],b)
                #print(indexOfNode[b])
                LHS += [(Delta[indexOfLine[l],indexOfNode[b]],d[b])]
                LHS += [(-Delta[indexOfLine[l],indexOfNode[b]],g[b])]
        model.addConstr(LinExpr(LHS)==0, name='Eq.power flow (%s)'%(l))
    
    for l in theMonitored:
        LHS = [(1,PF[l])]
        model.addConstr(LinExpr(LHS) >= - flowLimit[l], name='Eq.flow lower bound (%s)'%(l))
        model.addConstr(LinExpr(LHS) <=   flowLimit[l], name='Eq.flow upper bound (%s)'%(l))
    
    
    ### power flow constraint C
    for l_c in theContingent:
        pfc_vars = []
        pfc_names = []
        for l in lineArrayC[l_c]:
            pfc_vars += [(l,l_c)]
            pfc_names += ['PFC[%s,%s]'%(l,l_c)]
        PFC = model.addVars(pfc_vars, vtype = GRB.CONTINUOUS, lb = -GRB.INFINITY, name = pfc_names)
        
        for l in lineArrayC[l_c]:
            LHS = [(-1,PFC[l,l_c])]
            for b in nodeArray:
                if b != slackBus:
                    LHS += [(DeltaC[l_c][indexOfLineC[l_c][l],indexOfNodeC[l_c][b]],d[b])]
                    LHS += [(-DeltaC[l_c][indexOfLineC[l_c][l],indexOfNodeC[l_c][b]],g[b])]
            model.addConstr(LinExpr(LHS)==0, name='Eq.power flowC (%s,%s)'%(l,l_c))
        
        for l in theMonitored:
            LHS = [(1,PFC[l,l_c])]
            model.addConstr(LinExpr(LHS) >= - flowLimit[l], name='Eq.flow lower bound C (%s,%s)'%(l,l_c))
            model.addConstr(LinExpr(LHS) <=   flowLimit[l], name='Eq.flow upper bound C (%s,%s)'%(l,l_c))
    
    
    # set objective
    objTerms = []
    for b in nodeArray:
        objTerms += [(1,d[b])]
    model.setObjective(LinExpr(objTerms), GRB.MAXIMIZE)
    
    
    model.update()
    model.optimize()

    return model


