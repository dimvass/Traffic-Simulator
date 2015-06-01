import os, sys
import optparse
import subprocess
import chargingstation
from center import Center

try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', "tools")) # tutorial in tests
    sys.path.append(os.path.join(os.environ.get("SUMO_HOME", os.path.join(os.path.dirname(__file__), "..", "..", "..")), "tools")) # tutorial in docs
    from sumolib import checkBinary
except ImportError:
    sys.exit("please declare environment variable 'SUMO_HOME' as the root directory of your sumo installation (it should contain folders 'bin', 'tools' and 'docs')\nexport SUMO_HOME=/home/dimvas/Downloads/sumo-0.22.0/")
import traci


#this class represents an electric vehicle
#attributes: an id (count), the source and destination of the journey, the vehicle type, and a parameter for the charging value calculation
class Electric_Vehicle:
    def __init__ (self,count,src,dest,typ,val_max,temp):
        self.id = str(count)
        self.src = src
        self.dest = dest
        self.val_max = val_max
        self.typ = typ
        #TODO
        self.state = 0      #0  not yet inserted
                            #1  inserted, heading to charging station
                            #2  arrived to charging station, waiting for available unit
                            #3  parked, charging
                            #4  charged, heading to final destination                            
        self.with_stop_travel_times = []
        self.toDel = False
        self.reported = False
        self.assinged = False
        self.stop = None
        self.unit = None
        #there is no predefined route for the new vehicle - we need to create one
        #add temporary vehicle, change destination, and get route
        traci.route.add(self.id+'tmp',[self.src.edge])
        traci.vehicle.add(self.id+'tmp',self.id+'tmp',self.src.time,self.src.pos,0,0,self.typ)
        traci.vehicle.changeTarget(self.id+'tmp',self.dest.edge)
        traci.route.add(self.id+'vroute',traci.vehicle.getRoute(self.id+'tmp'))

        #now we need to delete the temporary vehicle
        #change target to the closest edge, and add to delete list
        #TODO search for more efficient way to do it
        traci.vehicle.changeTarget(self.id+'tmp',self.src.edge)        
        temp.append((self.id+'tmp',self.src.time))
        
        #add the vehicle to the simulation
        traci.vehicle.addFull(self.id, self.id+'vroute', self.typ, str(self.src.time), '0', str(self.src.pos), '0', '0', str(self.dest.pos))
    
    #reroute vehicle to assigned stop
    #actually reroute to an edge following the station's edge - if the destination is the station's edge the vehicle is deleted in the beggining of the edge
    #if we are at the (final) destination edge (and need to cyrcle the block) - wait to get to the next, then charnge the target
    def stopToCharge(self):
        (L,x,y,z)  = traci.lane.getLinks(self.stop.edge+'_0')[0]
        edge = traci.lane.getEdgeID(L)
        if traci.vehicle.getRoadID(self.id) == edge:
            return False
        traci.vehicle.changeTarget(self.id,edge)
        return True

    #check if the vehile has been inserted to the simulation, and change it's state
    def checkInserted(self):
        for v in traci.simulation.getDepartedIDList():
            if v == self.id:
                print '[LOG] ', self.id, 'inserted @', traci.simulation.getCurrentTime()/1000
                self.state = 1

    #check if the vehicle has reached the charing station and change it's state
    def park(self):        
        if traci.vehicle.getRoadID(self.id) == self.stop.edge:
            if abs(traci.vehicle.getLanePosition(self.id) - self.stop.pos) < 10:
                print '[LOG] ', self.id, 'trying to park @', traci.simulation.getCurrentTime()/1000
                traci.vehicle.setSpeed(self.id,0)
                self.state = 2

    #try to find an available unit to charge - wait until there is one                
    def charge(self):
        if traci.vehicle.getSpeed(self.id) == 0:
                self.unit = self.stop.findAvailableUnit()
                if self.unit != None:
                    print '[LOG] ', self.id, 'parked @', traci.simulation.getCurrentTime()/1000
                    traci.vehicle.setStop(self.id,traci.vehicle.getRoadID(self.id),traci.vehicle.getLanePosition(self.id)+self.unit.id*+5,0,100000000,1)
                    traci.vehicle.setSpeed(self.id,100)
                    self.unit.occupied = True
                    self.state = 3
                    self.timeparked = 0

    #when the vehicle is fully charged reroute to final destination, change it's state, and free the charging unit
    def fullyCharged(self):
        traci.vehicle.resume(self.id)
        traci.vehicle.changeTarget(self.id,self.dest.edge)
        traci.vehicle.setStop(self.id,self.dest.edge,self.dest.pos,0,1000000000,1)
        print '[LOG] ', self.id, 'charged @', traci.simulation.getCurrentTime()/1000
        self.state = 4
        self.unit.occupied = False

    #check if the vehicle has arrived at it's destination, remove from simulation, and delete from structures
    def checkArrived(self):
        if traci.vehicle.getRoadID(self.id) == self.dest.edge and abs(traci.vehicle.getLanePosition(self.id) - self.dest.pos) < 5:
                print '[LOG] ', self.id, 'arrived @', traci.simulation.getCurrentTime()/1000
                traci.vehicle.remove(self.id,1)
                self.toDel = True

    #update and manage the vehicle's state using the above functions
    def updateState(self,dest):
        if self.state == 0:
            self.checkInserted()
        elif self.state == 1:
            self.park()
        elif self.state == 2:
            self.charge()
        elif self.state == 3:
            self.timeparked += 1
            if (self.timeparked == chargingstation.charging_time):
                self.fullyCharged()
        elif self.state == 4:
            self.checkArrived()        
        else:
            print 'invalid state'
        return self.state

    #caclulate the vehicle's value array
    def calculateValues(self,stops,current_hour,temp):
        #the estimated travel time to the destination without a stop
        self.init_travel_time = self.estimateTravelTime(self.id)

        #for each charging station
        for s in stops:
            #change the target to the station
            traci.vehicle.changeTarget(self.id,s.edge)
            #and calculate the estimated travel time from source to station
            with_stop_time = self.estimateTravelTime(self.id) + chargingstation.charging_time

            #add a temporary vehicle - from the station to the final destination
            traci.route.add(self.id+str(s.id)+"vroute",[s.edge])
            traci.vehicle.add(self.id+str(s.id),self.id+str(s.id)+"vroute",traci.simulation.getCurrentTime()/1000,s.pos,0,0,self.typ)
            traci.vehicle.changeTarget(self.id+str(s.id),self.dest.edge)
            
            #and calculate the estimated travel time from station to destination
            from_stop_time = self.estimateTravelTime(self.id+str(s.id))

            #then delete it
            traci.vehicle.changeTarget(self.id+str(s.id),s.edge)
            temp.append((self.id+str(s.id),traci.simulation.getCurrentTime()/1000))

            #and calculate the values using the formula
            self.with_stop_travel_times.append(with_stop_time+chargingstation.charging_time+from_stop_time)
        values = []
        for s in stops:
            values.append(self.calculateSingleValue(s,current_hour))
    
        return values

    #calculate the value of charging the vehicle each our in a charging station
    #formula: u_max - a*(t_actual_arr - t_depart) - c*(t_prefer_arr - t_depart)
    #for all hours before the current value = 0 - current value from formula - value halved every hour
    def calculateSingleValue(self,stop,current_hour):
        a = 1
        c = 0.5
#        print '[DEBUG] ',self.id,'station',stop.id,'no stop',self.init_travel_time,'with stop',self.with_stop_travel_times[stop.id]
        val = []        
        for i in range(24):
            val.append(0)
        val[current_hour] = self.val_max - a*(self.with_stop_travel_times[stop.id]+chargingstation.charging_time) - c*(self.init_travel_time - self.with_stop_travel_times[stop.id]+chargingstation.charging_time)
#        print '[DEBUG] ',self.id, 'value', val[current_hour]
        for i in range(0,current_hour):
            val[i] = 0
        temp = val[current_hour]
        for i in range(current_hour,24):
            val[i] = temp
            temp = temp / 2
        return val

    #calculates the time a vehicle needs to reach it's destination
    #by traversing the edges on the route and adding the travelTime in each of them
    #TODO: not accurate for first and last edge (partial)
    def estimateTravelTime(self,vid):
        route = traci.vehicle.getRoute(vid)
        estimatedTravelTime = 0
        for r in route:
            estimatedTravelTime += traci.edge.getTraveltime(r)
#        print '[DEBUG] ', vid, 'route', route, 'tt', estimatedTravelTime
        return estimatedTravelTime