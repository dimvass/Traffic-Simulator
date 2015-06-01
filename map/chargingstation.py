import os, sys
import optparse
import subprocess
from chargingunit import ChargingUnit

try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', "tools")) # tutorial in tests
    sys.path.append(os.path.join(os.environ.get("SUMO_HOME", os.path.join(os.path.dirname(__file__), "..", "..", "..")), "tools")) # tutorial in docs
    from sumolib import checkBinary
except ImportError:
        sys.exit("please declare environment variable 'SUMO_HOME' as the root directory of your sumo installation (it should contain folders 'bin', 'tools' and 'docs')\nexport SUMO_HOME=/home/dimvas/Downloads/sumo-0.22.0/")
import traci

charging_time = 10

#this class represents a charging station
#attributes: an id, the edge and position of the station, the number of charging units,  the price of charging, and the parameters for cost calculation
class ChargingStation:
    def __init__(self,id,edge,pos,unit_count,price,time_posib):
        self.id = id
        self.edge = edge
        self.pos = pos
        self.time = charging_time
        self.price = price
        self.unit_count = unit_count
        self.time_posib = time_posib
        self.units = []
        for u in range(self.unit_count):
            self.units.append(ChargingUnit(u))
        self.cost = []
        (self.x,self.y) = traci.simulation.convert2D(self.edge,self.pos,0,False)
    #created the units of the station and calculates their costs
    def calculateCost(self):    
        self.cost = self.calculateUnitCost(self.price,self.time_posib)
        #return self.units
    #calculates the cost of one unit for 24 hours
    #cost = P[unit to be occupied based on number of units] * P[unit to be occupied based on time of day]
    def calculateUnitCost(self,price,time_posib):
        cost_per_hour = []
        for t in range(24):
             cost_per_hour.append(price*time_posib[t])
        return cost_per_hour
    def findAvailableUnit(self):
        for u in self.units:
            if not u.occupied:
                return u
        return None