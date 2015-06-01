#this class represents the departure of a vehicle
#attributes: the edge, the position, and the time of departure
#depart lane and speed can be added - currenintly considered 0
class Source:
    def __init__(self,edge,pos,time):
        self.edge = edge
        self.pos = pos
        self.time = time