import gurobipy as grb
from gurobipy import GRB
from math import ceil, floor
import pandas as pd    
   
def optimizeModel(modelName, weights, numTrucksT1, numTrucksT2, cap1, cap2, gap=0.001, timeLimit=150, threads=10):
    """optimizeModel solve a BLP model

    Parameters:
    modelNam: model name
    weights: weights of ralls
    numTrucksT1: number of trucks of type 1
    numTrucksT2: number of trucks of type 2
    cap1: capacity of tracks of type 1
    cap2: capacity of tracks of type 2
    gap: MIPGap attribute
    timeLimit: Timelimit attribute
    threads: Threads attribute
    
    Returns:
    model: BLP model
    x: x vriables
    y: y vriables 
    mintrucks: minimum number of track used in model
    """
    
    # indexes for variables
    rolls = range(len(weights))
    trucks = range(numTrucksT1 + numTrucksT2)
    
    # capacities of tracks
    capacities = [cap1 for truck in range(numTrucksT1)] + [cap2 for truck in range(numTrucksT2)]
    
    # construct model
    model = grb.Model(name=modelName)

    # add variables
    x, y = {}, {}
    for truck in trucks:
        y[truck] = model.addVar(name="y_%s"%(truck), vtype=GRB.BINARY)
        for roll in rolls:
            x[roll,truck] = model.addVar(name="x_%s,%s"%(roll,truck), vtype=GRB.BINARY)

    # add constraints (2)
    for roll in rolls:
        model.addConstr(sum(x[roll,truck] for truck in trucks) == 1)

    # add constraints (3)
    for truck in trucks:
        model.addConstr(sum(weights[roll] * x[roll,truck] for roll in rolls) <= capacities[truck] * y[truck])

    # define objective function    
    objective = grb.quicksum(capacities[truck] * y[truck] for truck in trucks)
    model.setObjective(objective, sense=GRB.MINIMIZE)
    
    # set Gap, Timelimit and number of Threads
    model.setParam('MIPGap', gap)   
    model.setParam('Timelimit', timeLimit)
    model.setParam('Threads', threads)
    
    # optimize the model
    model.optimize()

    # number or tracks used in the model
    numTraks = int(sum([1 for truck in trucks if abs(y[truck].X) > 1e-6]))
    
    return model, x, y, numTraks
    
def printSolution(model, x, y, weights, numTrucksT1, numTrucksT2, cap1, cap2):
    """printSolution prints solution

    Parameters:
    model: BLP model
    x: x vriables
    y: y vriables 
    weights: weights of ralls
    numTrucksT1: number of trucks of type 1
    numTrucksT2: number of trucks of type 2
    cap1: capacity of tracks of type 1
    cap2: capacity of tracks of type 2
    
    Returns:
    None
    """

    # indexes for variables
    rolls = range(len(weights))
    trucks = range(numTrucksT1 + numTrucksT2)
    
    # capacities of tracks
    capacities = [cap1 for truck in range(numTrucksT1)] + [cap2 for truck in range(numTrucksT2)]
    
    # print objective value
    print("\nThe optimal specific load (максимальная удельная загрузка): ", sum(weights)/model.objVal)
   
    # print load of each nonempty truck
    print("Load of trucks (распределение рулонов по машинам):")
    localIndex = 0
    for truck in trucks:
        if abs(y[truck].X > 1e-6):
            listRolls, listWeights = [], []
            localIndex += 1
            for roll in rolls:
                if abs(x[roll,truck].X > 1e-6):
                    listRolls.append(roll + 1)
                    listWeights.append(weights[roll])        
            print(f"Truck {localIndex} ({capacities[truck]}) is loaded with rolls: {listRolls} with weights: {listWeights}.")
 
    return None

if __name__ == "__main__":
    
    # read weights of rolls from file
    weights_df = pd.read_excel('weights.xlsx')
    weights = weights_df.weight.values.tolist()

    # capacities of tracks of type 1 and 2 
    cap1 = 22.2
    cap2 = 27.6

    # local minimum number of tracks of type 1 only or type2 only needed for the model
    locMinNumTrucksT1 = ceil(len(weights)/(floor(cap1/max(weights))))
    locMinNumTrucksT2 = ceil(len(weights)/(floor(cap2/max(weights))))
    
    # step 1
    # determine the minimum number of tracks needen in the model with only tracks of type 1 
    model1type, x1, y1, minNumTrucksT1 = optimizeModel("Model with trucks of type 1 only", 
                                                       weights, locMinNumTrucksT1, 0, cap1, cap2)
    # step 2
    # determine the minimum number of tracks needen in the model with only tracks of type 2 
    model2type, x2, y2, minNumTrucksT2 = optimizeModel("Model with trucks of type 2 only", 
                                                       weights, 0, locMinNumTrucksT2, cap1, cap2)
    # step 3
    # determine the optimal solution of the problem 
    modelbothtypes, x3, y3, minNumBothTrucks = optimizeModel("Model with trucks of both types", 
                                                     weights, minNumTrucksT1, minNumTrucksT2, cap1, cap2)
    
    #print solution
    printSolution(modelbothtypes, x3, y3, weights, minNumTrucksT1, minNumTrucksT2, cap1, cap2)