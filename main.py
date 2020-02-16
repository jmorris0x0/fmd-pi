import multiprocessing as mp
import os
import random
import zmq
import json
#from hsc import *
import time
import numpy as np
import matplotlib.pyplot as plt
import psutil


def sensor(): 
    #print("Sensor process started: {}".format(os.getpid()))
    time.sleep(1)
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
    #print("Processor process started: {}".format(os.getpid())) 
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
    #print("Plotter process started: {}".format(os.getpid())) 
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect("tcp://localhost:5555")
    socket.setsockopt(zmq.SUBSCRIBE, b'sensor')

    plt.style.use('ggplot')

    x_vec = []
    y_vec = []

    plt.ion()
    fig,ax = plt.subplots(3,1,figsize=(12,7),sharex=True)
    fig.align_ylabels(ax)

    ax[0].set_ylabel('Pressure [mmHg]',fontsize=12)
    ax[1].set_ylabel('Smoothed [mmHg]',fontsize=12)

    line1, = ax[0].plot(x_vec,y_vec,'-,g',alpha=0.8)        

    plt.show()

    ax[0].set_xlim([0, 60])
    ax[0].set_ylim([0, 150])

    render = False
    count = 0

    while True:
        topic = socket.recv_string()
        frame = socket.recv_pyobj()

        x_vec.append(frame[0])
        y_vec.append(frame[1])
        
        if count == 50:
            count = 0
            line1.set_data(x_vec, y_vec)
 
            if np.min(y_vec)<=line1.axes.get_ylim()[0] or np.max(y_vec)>=line1.axes.get_ylim()[1]:
                ax[0].set_ylim([np.min(y_vec)-np.std(y_vec),np.max(y_vec)+np.std(y_vec)])
        
            plt.pause(0.1)
 
        count += 1


if __name__ == "__main__": 
    # printing main program process id 
    print("Main process started: {}".format(os.getpid())) 
    if plt.get_backend() == "MacOSX":
        mp.set_start_method("forkserver") 
    # creating processes 
    p1 = mp.Process(target=sensor) 
    p2 = mp.Process(target=processor) 
    p3 = mp.Process(target=plotter) 

    # starting processes 
    p1.start() 
    #p2.start()
    p3.start()
  
    # wait until processes are finished 
    p1.join() 
    #p2.join() 
    p3.join()

