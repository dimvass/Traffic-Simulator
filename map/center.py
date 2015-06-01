import os, sys
import optparse
from chargingstation import ChargingStation
from chargingunit import ChargingUnit

try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', "tools")) # tutorial in tests
    sys.path.append(os.path.join(os.environ.get("SUMO_HOME", os.path.join(os.path.dirname(__file__), "..", "..", "..")), "tools")) # tutorial in docs
    from sumolib import checkBinary
except ImportError:
    sys.exit("please declare environment variable 'SUMO_HOME' as the root directory of your sumo installation (it should contain folders 'bin', 'tools' and 'docs')\nexport SUMO_HOME=/home/dimvas/Downloads/sumo-0.22.0/")
import traci

#this class represents the center where the buyers and sellers report their costs and values
#the centers assigns the vehicles to charging stations
#attributes: the simulation's charging stations and electric vehicles
class Center:
	def __init__(self,stations,vehicles):
		self.stations = stations
		self.vehicles = vehicles
		self.num_stations = len(stations)
		self.num_vehicles = len(vehicles)
		self.sellers = self.num_stations*[None]
		self.buyers = self.num_vehicles*[None]
	def assign(self,vehicle,stops):
		max = -1000000000000
		alloc = None
		for t in range(24):
			for s in stops:
					#print '[DEBUG]','vehicle',vehicle.id,'value ', self.buyers[int(vehicle.id)][i][t],'charging station', self.stations[i].id,'unit', u.id, 'cost', u.cost[t], self.buyers[int(vehicle.id)][i][t] - u.cost[t]
					if (self.buyers[int(vehicle.id)][s.id][t] - s.cost[t] > max):
						max = self.buyers[int(vehicle.id)][s.id][t] - s.cost[t]
						alloc = s
		print '[DEBUG]','veh', vehicle.id, 'alloc station', alloc.id
		vehicle.stop = alloc
		return alloc
	#called when a vehicle enters the simulation - buyer reports its value
	def buyer_report(self,vehicle,stations,current_hour,temp):
		self.buyers[int(vehicle.id)] = vehicle.calculateValues(stations,current_hour,temp)
		print '[REPORT]','vehicle',vehicle.id,'charging units value ', self.buyers[int(vehicle.id)]
	#called before the start of the simulation - all sellers report their cost arrays
	def sellers_report(self,stations):
		i = 0
		for s in stations:
			s.calculateCost()
			i += 1
		for s in stations:
				print '[REPORT]','charging station', s.id, 'cost', s.cost