#!/usr/bin/env python
import os, sys
import optparse
import subprocess

from chargingstation import ChargingStation
from source import Source
from destination import Destination
from electricvehicle import Electric_Vehicle
from center import Center

# we need to import python modules from the $SUMO_HOME/tools directory
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', "tools")) # tutorial in tests
    sys.path.append(os.path.join(os.environ.get("SUMO_HOME", os.path.join(os.path.dirname(__file__), "..", "..", "..")), "tools")) # tutorial in docs
    from sumolib import checkBinary
except ImportError:
    sys.exit("please declare environment variable 'SUMO_HOME' as the root directory of your sumo installation (it should contain folders 'bin', 'tools' and 'docs')\nexport SUMO_HOME=/home/dimvas/Downloads/sumo-0.22.0/")

import traci
# the port used for communicating with your sumo instance
PORT = 8873

def run():
    global current_hour
    """execute the TraCI control loop"""
    traci.init(PORT)

    src = [
        Source("D2",100,1),
        Source("D2",100,2),
        Source("D2",100,3),
        Source("L16",100,51),
        Source("L14",50,25),
        Source("V4",0,30)
        ]
    dest = [
            Destination("V4",150),
            Destination("V4",100),
            Destination("D8",5),
            Destination("V4",150),
            Destination("D1",10),
            Destination("D1",20)
            ]
    stops = [
            ChargingStation(0,"D6",50,2,10,[0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5])
            ,
            ChargingStation(1,"V2",50,2,8,[0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5])
            ]            
    types = ["CarA", "CarA", "CarD", "CarB", "CarC", "CarC"]

    #number of elechtric vehicle insterted
    veh_count = 0
    vehicles = []
    temp_vehs = []
    for i in range(6):
        vehicles.append(Electric_Vehicle(veh_count,src[i],dest[i],types[i],1000,temp_vehs))
        veh_count+=1

    center = Center(stops,vehicles)
    for s in stops:
        center.seller_report(s)

    temp_toDel = False
    while vehicles != []:
        traci.simulationStep()
        if traci.simulation.getCurrentTime()/1000 % 1000 == 0 and traci.simulation.getCurrentTime()>0:
            current_hour += 1
            print '[HOUR]', current_hour
        deleteTempVehicles(temp_vehs)        
        for v in vehicles:
            if (v.updateState(dest) == 1 and not v.reported):
                center.buyer_report(v,stops,current_hour,temp_vehs)
                center.assign(v,stops)
                v.assinged = v.stopToCharge()
                v.reported = True
            if (v.toDel):
                vehicles.remove(v)
            if v.reported and not v.assinged:
                v.assinged = v.stopToCharge()
        
    traci.close()
    sys.stdout.flush()

def deleteTempVehicles(temp):
    for (v,t) in temp:
        for i in traci.simulation.getDepartedIDList():
            if i == v:
                lane = traci.vehicle.getLaneID(v)
                leng = traci.lane.getLength(lane)
                traci.vehicle.moveTo(v,lane,leng-1)
                temp.remove((v,t))

def get_options():
    optParser = optparse.OptionParser()
    optParser.add_option("--nogui", action="store_true", default=False, help="run the commandline version of sumo")
    options, args = optParser.parse_args()
    return options

# this is the main entry point of this script
if __name__ == "__main__":
    current_hour = 0
    options = get_options()
    # this script has been called from the command line. It will start sumo as a
    # server, then connect and run
    if options.nogui:
        sumoBinary = checkBinary('sumo')
    else:
        sumoBinary = checkBinary('sumo-gui')
    # first, generate the route file for this simulation
    
    netconvertBinary = checkBinary('netconvert')
    # build/check network

    retcode = subprocess.call([netconvertBinary, "-c", "data/quickstart.netccfg"], stdout=sys.stdout, stderr=sys.stderr)
    try: shutil.copy("data/quickstart.net.xml", "net.net.xml")
    except: print "Missing 'quickstart.net.xml'"
    print ">> Netbuilding closed with status %s" % retcode
    sys.stdout.flush()
    # this is the normal way of using traci. sumo is started as a
    # subprocess and then the python script connects and runs
    sumoProcess = subprocess.Popen([sumoBinary, "-c", "data/quickstart.sumocfg", "--tripinfo-output", "tripinfo.xml", "--remote-port", str(PORT)], stdout=sys.stdout, stderr=sys.stderr)
    run()
    sumoProcess.wait()