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
		self.num_stations = len(stations)
		self.num_vehicles = len(vehicles)
		self.sellers = self.num_stations*[None]
		self.buyers = self.num_vehicles*[None]
	def assign(self,vehicle,stops):
		#TODO: allow only allocations with positive value-cost
		max = -1000000000000
		alloc = None
		for t in range(24):
			for s in stops:
				if (self.buyers[int(vehicle.id)][s.id][t] - self.sellers[s.id][t] > max):
					max = self.buyers[int(vehicle.id)][s.id][t] - self.sellers[s.id][t]
					alloc = s
		print '[ALLOC]','veh', vehicle.id, 'station', alloc.id
		vehicle.stop = alloc
	#called when a vehicle enters the simulation - buyer reports its value
	def buyer_report(self,vehicle,stations,current_hour,temp):
		self.buyers[int(vehicle.id)] = vehicle.calculateValues(stations,current_hour,temp)
		print '[REPORT]','vehicle',vehicle.id,'charging units value ', self.buyers[int(vehicle.id)]
	#called before the start of the simulation - all sellers report their cost arrays
	def seller_report(self,station):
		self.sellers[station.id] = station.calculateCost()
		print '[REPORT]','charging station', station.id, 'cost', self.sellers[station.id]