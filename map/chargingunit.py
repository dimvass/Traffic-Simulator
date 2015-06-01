#this class represents a charging unit of a charging station
#attributes: an id, and if it currently occupied
class ChargingUnit:
    def __init__(self,id):
        self.id = id
        self.occupied = False