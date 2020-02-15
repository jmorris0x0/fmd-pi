from multiprocessing import Process 
import os
import random
import time
import zmq
import json


def sensor(): 
    print("Sensor process started: {}".format(os.getpid()))
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.setsockopt(zmq.SNDHWM, 100000)
    socket.bind("tcp://*:5555")
    topic = 'sensor'

    t0 = time.time()
    while True:
        tn = time.time() - t0
        data = [tn, random.random()]
        socket.send_string(topic, zmq.SNDMORE)
        socket.send_pyobj(data)
        time.sleep(0.01)


def processor(): 
    print("Processor process started: {}".format(os.getpid())) 
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect("tcp://localhost:5555")
    socket.setsockopt(zmq.SUBSCRIBE, b'sensor')

    while True:
        topic = socket.recv_string()
        frame = socket.recv_pyobj()
        print("processing: " + str(frame))


def plotter(): 
    # printing process id 
    print("Plotter process started: {}".format(os.getpid())) 


if __name__ == "__main__": 
    # printing main program process id 
    print("Main process started: {}".format(os.getpid())) 
  
    # creating processes 
    p1 = Process(target=sensor) 
    p2 = Process(target=processor) 
    p3 = Process(target=plotter) 

    # starting processes 
    p1.start() 
    p2.start()
    p3.start()
  
    # wait until processes are finished 
    p1.join() 
    p2.join() 
    p3.join()

