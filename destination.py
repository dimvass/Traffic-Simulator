#this class represents the destination of a vehicle
#attributes: the edge abd the position of the destination
#arrival lane and speed can be added - currenintly considered 0
class Destination:
    def __init__(self,edge,pos):
        self.edge = edge
        self.pos = pos