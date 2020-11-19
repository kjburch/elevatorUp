#!/usr/bin/env python3.8

# Kyle J Burch
# Computer Simulations
# 10/9/20

import math
import sys
import numpy as np

# Setup -------------------------------------------------------------------------------------------------
# Number of people on each floor
people = 100
# Maximum elevator capacity
elevatorCapacity = 10

# Outputs
maxQ = 0
stops = 0
avgDelay = 0
stdDelay = 0

# Get the arguments
arguments = sys.argv
# Get the num of floors in the building
floors = int(arguments[1])
# Get the num of elevators in the building
elevators = int(arguments[2])
# Get the random nums
try:
    rand = open(arguments[3], "r")
except:
    sys.exit(1)
# Get the num of days to run the sim
days = int(arguments[4])

# Classes  -------------------------------------------------------------------------------------------------
# Creates an elevator rider
class Person:
    completionTime = -1

    def __init__(self, destinationFloor, arrivalTime):
        self.destinationFloor = destinationFloor
        self.arrivalTime = arrivalTime

    # Prints the passenger
    def __str__(self):
        if self.completionTime != -1:
            return "Destination floor: "+str(self.destinationFloor)+" - Total Travel Time: "+str(
                self.completionTime-self.arrivalTime)+" - Arrival Time: "+str(
                self.arrivalTime)+" - Completion Time: "+str(self.completionTime)+" - Normalized Delay: "+str(
                self.normalizedDelay())
        return "Person has not completed their travel yet"

    # Calculates the total travel time
    def totalTravelTime(self):
        return self.completionTime-self.arrivalTime

    # Calculates the normalized delay for the passenger
    def normalizedDelay(self):
        optimalTime = travelTime(self.destinationFloor)+boardingTime(1)+boardingTime(1)
        return (self.totalTravelTime()-optimalTime) / optimalTime


# Creates an elevator
class Elevator:
    def __init__(self):
        self.currentFloor = 0
        self.passengers = []
        self.time = 0
        self.totalStops = 0

    def __str__(self):
        temp = "Elevator Time: "+str(self.time)+" - Current Floor: "+str(self.currentFloor)+" - Passengers: [ "
        for p in self.passengers:
            temp += str(p.destinationFloor)+" "
        return temp+"]"

    # Determine the next destination floor then update time and move to floor
    def nextFloor(self):
        self.totalStops += 1
        # Return to floor zero if there are no passengers
        if len(self.passengers) == 0:
            # print("Back to floor 0")
            self.time += travelTime(self.currentFloor)
            self.currentFloor = 0
        else:
            # print("Going up")
            # Determine the next floor
            f = floors
            for p in self.passengers:
                if p.destinationFloor < f:
                    f = p.destinationFloor
            # Increment Travel Time
            self.time += travelTime(f-self.currentFloor)
            self.currentFloor = f

    def loadAndGo(self, globalTime):
        self.time = globalTime+boardingTime(len(self.passengers))
        self.nextFloor()

    def unloadAndGo(self, globalTime):
        ul = []
        for p in self.passengers:
            if p.destinationFloor == self.currentFloor:
                ul.append(self.passengers.pop(self.passengers.index(p)))
        self.time = globalTime+boardingTime(len(self.passengers))
        self.nextFloor()
        return ul


# Creates a building to run everything
class Building:
    def __init__(self):
        self.maxWaiting = 0
        self.floors = []
        for i in range(0, floors):
            self.floors.append([])
        self.elevators = []
        for i in range(0, elevators):
            self.elevators.append(Elevator())
        self.globalTime = 0
        self.waitingPeople = []

    # Load passengers that are waiting
    def loadPassengers(self):
        # Determine which elevators are eligible for loading
        waitingElevators = []
        for e in self.elevators:
            # Elevators need to have passenger room left, there needs to be waiting passengers, and the elevator needs
            # to be not in transit
            if e.currentFloor == 0 and len(e.passengers) < elevatorCapacity and len(
                    self.waitingPeople) > 0 and e.time <= self.globalTime:
                waitingElevators.append(self.elevators.index(e))

        # Load passengers onto elevators until there are either no passengers or no elevators left
        wait = True
        while wait:
            wait = False
            for i in waitingElevators:
                if len(self.elevators[i].passengers) < elevatorCapacity and len(self.waitingPeople) > 0:
                    wait = True
                    self.elevators[i].passengers.append(self.waitingPeople.pop(0))

        # Change Elevator Time and send elevators to their next floor
        for i in waitingElevators:
            if len(self.elevators[i].passengers) > 0:
                self.elevators[i].loadAndGo(self.globalTime)

    # Unload passengers that have reached their floors
    def unloadPassengers(self):
        # Determine which elevators are eligible for unloading
        waitingElevators = []
        for e in self.elevators:
            # Elevators need to be at a nonzero floor, and be at global time
            if e.currentFloor != 0 and e.time == self.globalTime:
                waitingElevators.append(self.elevators.index(e))

        for i in waitingElevators:
            temp = self.elevators[i].unloadAndGo(self.globalTime)
            for p in temp:
                p.completionTime = self.globalTime+boardingTime(len(temp))
                self.floors[p.destinationFloor-1].append(p)

    # Moves time forward and makes the necessary calls
    def proceed(self):
        if len(self.waitingPeople) > self.maxWaiting:
            self.maxWaiting = len(self.waitingPeople)
        self.loadPassengers()
        self.unloadPassengers()
        self.globalTime += 1

    def getDelay(self):
        d = []
        for floor in self.floors:
            for p in floor:
                d.append(p.normalizedDelay())
        return d

    def getStops(self):
        e = []
        for elevator in self.elevators:
            e.append(elevator.totalStops)
        return e


# Helper functions --------------------------------------------------------------------------
# Calculates the amount of time in seconds is required to travel h floors
def travelTime(h):
    if h == 1:
        return 8
    elif h > 1:
        return 2 * 8+5 * (h-2)
    elif h == 0:
        return 0
    else:
        print("Invalid floor num")
        return -1


# Calculates how long it will take for n num of passengers to board
def boardingTime(n):
    if n == 10:
        return 22
    else:
        return 1+(n * 2)

# Get next random num from file
def nextRandom():
    try:
        r = rand.readline().strip()
        return float(r)
    except:
        exit(1)

# Welford Equations --------------------------------------------------------------------------
def welfordMean(lst):
    k = 0
    M = 0
    S = 0

    for x in lst:
        if x is None:
            return
        k += 1
        newM = M+(x-M) * 1. / k
        newS = S+(x-M) * (x-newM)
        M, S = newM, newS

    return M


def welfordStd(lst):
    k = 0
    M = 0
    S = 0

    for x in lst:
        if x is None:
            return
        k += 1
        newM = M+(x-M) * 1. / k
        newS = S+(x-M) * (x-newM)
        M, S = newM, newS

    return (S / (k-1)) ** 0.5


# Random distribution functions ----------------------------------------------------------------
def geometricCDF(x):
    return 1-(1-0.65) ** (x+1)


def truncatedGeometricCdf(x):
    return (geometricCDF(x)-geometricCDF(1)) / (geometricCDF(8)-geometricCDF(1))


# Calculates a cdf truncated variable
def cdfModRandom():
    # Get next rand from file
    u = nextRandom()
    randomVariate = 4
    # Find a random variate from truncate cdf
    if truncatedGeometricCdf(randomVariate) <= u:
        while truncatedGeometricCdf(randomVariate) <= u:
            randomVariate += 1
    elif truncatedGeometricCdf(2) <= u:
        while truncatedGeometricCdf(randomVariate-1) > u:
            randomVariate -= 1
    else:
        randomVariate = 2
        # return random variate
    return randomVariate


def exponentialFunction(x):
    return 1-math.e ** (-x / 10)


def invertedExponentialCDF(u):
    return -10 * math.log(1-u)


# Calculates the random variate using TCI
def exponentialTCI():
    r = nextRandom()
    alpha = exponentialFunction(2)
    beta = 1.0-exponentialFunction(90)
    u = (((1-beta)-alpha) * r)+alpha
    randomVariate = invertedExponentialCDF(u)
    return randomVariate


#  Main ----------------------------------------------------------------------------------------------
def main():
    global maxQ
    tempDelay = []
    tempStops = []
    for d in range(0, days):
        building = Building()

        remainingFloorCapacity = [people] * floors

        timeOfPriorGroup = 0
        full = False
        lock = True
        timeOfNextGroup = 0

        # Run sim while there are still floors that are not full
        while not full:
            # Get arrival time of next group
            if lock:
                timeOfNextGroup = int(exponentialTCI())
                lock = False

            # If the group has arrived, generate new people
            if building.globalTime-timeOfPriorGroup >= timeOfNextGroup:
                timeOfPriorGroup = building.globalTime
                # Allow a new group arrival time to be generated
                lock = True

                # Determine group size
                groupSize = int(cdfModRandom())

                # Generate num Group Size new people
                for i in range(groupSize):
                    openFloors = []
                    for j in range(0, len(remainingFloorCapacity)):
                        if remainingFloorCapacity[j] > 0:
                            openFloors.append(j)

                    # If there is no remaining space, do nothing
                    if len(openFloors) > 0:
                        # Randomly choose a destination floor from open floors
                        # Change for linux
                        randomFloor = math.floor(nextRandom())
                        remainingFloorCapacity[openFloors[randomFloor]] -= 1
                        # add new waiting person with random destination floor
                        building.waitingPeople.append(
                            Person(arrivalTime=building.globalTime, destinationFloor=openFloors[randomFloor]+1))

            # Determine if sim is done
            full = True
            for rfc in building.floors:
                if len(rfc) < people:
                    full = False

            # Continue to the next second if the building is not full
            if not full:
                building.proceed()

        # Create a list of all of the delays on all of the floors on all of the days
        tempDelay.append(building.getDelay())
        tempStops.append(building.getStops())

        # Determine the maximum wait across all days
        if maxQ < building.maxWaiting:
            maxQ = building.maxWaiting

    s = []
    for stop in tempStops:
        for st in stop:
            s.append(st)
    print("OUTPUT stops ", round(welfordMean(s),5))
    print("OUTPUT max qsize  ", maxQ)
    dly = []
    for di in tempDelay:
        for j in di:
            dly.append(j)
    print("OUTPUT average delay ", round(welfordMean(dly),5))
    print("OUTPUT stddev delay ", round(welfordStd(dly),5))


if __name__ == '__main__':
    main()
