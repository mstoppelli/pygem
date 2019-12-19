import socket
import json
import random

class Goal():
    def __init__(self, subgoals, location, identifier):
        self.subgoals = subgoals
        self.location = location
        self.identifier = identifier

    def evaluate(self):
        pass # leaving blank for now, in final product would go through subgoals and either evaluate or send a request for them

class Request():
    def __init__(self, requester, identifier, goal):
        self.requester = requester
        self.identifier = identifier
        self.goal = goal
        self.response = Response(identifier, [], None, [])

class Response():
    def __init__(self, identifier, answers, status, loops):
        self.identifier = identifier
        self.answers = answers
        self.status = status
        self.loops = loops

BUF_SIZE = 1024 #may need to be changed
THIS_PRINCIPAL = "PYGEM" # unique identifier for this principal, in case two principals have same identifier to append
goals = []
requests = []
def main():
    s = socket.socket()
    host = socket.gethostname()
    port = 5000
    s.bind((host, port))

    s.listen(5)

    #needs to be multithreaded so we can handle requests and responses yeah?
    handle_incoming(s)

def handle_incoming(s: socket.socket):
    while True:
        connection, _address = s.accept()
        response = parse_input(connection)
        if response.status != None: #None would mean we got a request for a goal we dont even have knowledge of and cant provide a meaningful response to
            response_msg = json.dumps((response.__dict__))
            connection.send(response_msg)
            connection.close()



def parse_input(connection):
    request_data = connection.recv(BUF_SIZE)
    try:
        request_json = json.loads(request_data)
        request = Request(request_json['requester'], request_json['identifier'], request_json['goal'])
        loop = check_prefix(request.identifier)
        if loop:
            return Response(request.identifier, [], 'loop', []) # dont know what to put in loops list yet, havent gotten that far
        #requests.append(request)
        #Above commented out since I think we shoulld onlly be caring about requests we send out, otherwise we'll double up on loop
        #notifications, since in order to detect a loop, we had to have sent a request for a goal that ended up requesting from us,
        #meaning we had to receive a request and send it on
        foundGoal = False
        for goal in goals: # assumes
            if goal.identifier == request.goal:
                foundGoal = True
                if goal.location == None: # it must be here, but somme subgoals could be somewhere else.
                    answers = goal.evaluate()
                else: # goal must be at another principal
                    answers = requestGoal(request, goal)
        if not foundGoal:
            return request.response
        request.response.answers = answers
        request.response.status = "completed"
        return request.response
    except:
        print("Error parsing request data")
        return Response(request.identifier, [], None, [])

def check_prefix(identifier: str):
    identifiers = [x.identifier for x in requests]
    for identifiero in identifiers:
        if identifiero in identifier: # if another requests' identifier is in the one being checked, its prefiing it and we have a loop
            return True

    return False

def request_goal(request, goal: Goal):
    newRequest = Request(goal.location, request.identifier + THIS_PRINCIPAL + str(random.randint(0, 1000)), goal.identifier)
    requests.append(newRequest)
    connect_out = socket.socket()
    connect_out.connect(goal.location)
    connect_out.send(json.dumps(newRequest.__dict__))
    response_data = connect_out.recv(BUF_SIZE)
    response_json = json.loads(response_data)
    response = Response(response_json['identifier'], response_json['answers'], response_json['status'], response_json['loops'])
    #we're done with this request, so we'll clear it
    requests.remove(newRequest)
    return response.answers