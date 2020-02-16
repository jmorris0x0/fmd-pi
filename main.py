import multiprocessing as mp
import os
import random
import zmq
import json
#from hsc import *
import time
import numpy as np
import matplotlib.pyplot as plt
import math
import scipy.signal as sig


def sensor_process(): 
    #print("Sensor process started: {}".format(os.getpid()))
    time.sleep(1)
    context = zmq.Context()
    pub_socket = context.socket(zmq.PUB)
    pub_socket.setsockopt(zmq.SNDHWM, 100000)
    pub_socket.bind("tcp://*:5555")
    topic = 'sensor'

    t0 = time.time()
    while True:
        tn = time.time() - t0
        
        trend = 50 * math.sin(tn/5) + 50      
        signal = 10 * math.cos(8 * tn) + 10  
        noise = 2 * random.random()
        value = trend + signal + noise

        data = [tn, value]
        pub_socket.send_string(topic, zmq.SNDMORE)
        pub_socket.send_pyobj(data)
        time.sleep(0.01)


def butter_bandpass(lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a


def butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = lfilter(b, a, data)
    return y


def filter_process():
    #print("Processor process started: {}".format(os.getpid())) 
    context = zmq.Context()
    sub_socket = context.socket(zmq.SUB)
    sub_socket.connect("tcp://localhost:5555")
    sub_socket.setsockopt(zmq.SUBSCRIBE, b'sensor')

    context = zmq.Context()
    pub_socket = context.socket(zmq.PUB)
    pub_socket.setsockopt(zmq.SNDHWM, 100000)
    pub_socket.bind("tcp://*:5556")
    pub_topic = 'filter'


    #  finite impulse response filter
    b = sig.firwin(150, 0.004)

    # Construct initial conditions for lfilter for step response steady-state.
    z = sig.lfilter_zi(b, 1)
    
    while True:
        topic = sub_socket.recv_string()
        frame = sub_socket.recv_pyobj()
        tn = frame[0]
        value = frame[1]
        
        result, z = sig.lfilter(b, 1, [value], zi=z)

        #need to look at connect vs bind
        #https://stackoverflow.com/questions/30552925/how-to-handle-multiple-publishers-on-same-port-in-zmq

        data = [tn, result[0]]
        pub_socket.send_string(pub_topic, zmq.SNDMORE)
        pub_socket.send_pyobj(data)


def plotter_process_2(): 
    plots = [{'topic': b'sensor', 'port': '5555', 'label': 'Pressure [mmHg]', 'style': '-,g'},
            {'topic': b'filter', 'port': '5556', 'label': 'Pressure [mmHg]', 'style': '-,r'}]

    socket = [zmq.Context().socket(zmq.SUB)] * len(plots)

    for i in range(len(socket)):
        socket[i].connect("tcp://localhost:" + plots[i].get('port'))
        socket[i].setsockopt(zmq.SUBSCRIBE, plots[i].get('topic'))
        print(i)
    
    #x_vec = [[]] * len(plots)
    #y_vec = [[]] * len(plots)

    #plt.style.use('ggplot')
    #plt.ion()
    #fig,ax = plt.subplots(len(plots), 1, figsize=(12,7), sharex=True)
    #fig.align_ylabels(ax)


    #for i in range(len(ax)):
    #   ax[i].set_ylabel(plots[i].get('label'), fontsize=12)

    #line1, = ax[0].plot(x_vec[0], y_vec[0], '-,g', alpha=0.8)     
    #line2, = ax[1].plot(x_vec, y_vec, '-,r', alpha=0.8)





def plotter_process(): 
    plots = [{'topic': b'sensor', 'port': '5555', 'label': 'Pressure [mmHg]', 'style': '-,g'},
            {'topic': b'filter', 'port': '5556', 'label': 'Smooth Pressure [mmHg]', 'style': '-,r'}]

    context = zmq.Context()
    
    socket = []
    for i in range(0, len(plots)):
        socket.append(context.socket(zmq.SUB))
    
    for i in range(0, len(plots)):
        socket[i].connect("tcp://localhost:" + plots[i].get('port'))
        socket[i].setsockopt(zmq.SUBSCRIBE, plots[i].get('topic'))

    plt.style.use('ggplot')

    x_vec = [[]] * len(plots)
    y_vec = [[]] * len(plots)

    plt.ion()
    fig,ax = plt.subplots(len(plots), 1,figsize=(12,7), sharex=True)
    fig.align_ylabels(ax)

    for i in range(len(ax)):
       ax[i].set_ylabel(plots[i].get('label'), fontsize=12)

    line1, = ax[0].plot(x_vec[0], y_vec[0], '-,g', alpha=0.8)        

    plt.show()

    ax[0].set_xlim([0, 60])
    ax[0].set_ylim([0, 150])

    render = False
    count = 0

    while True:
        topic = socket[0].recv_string()
        #print(topic)

        frame = socket[0].recv_pyobj()
        #print(frame)
        #exit(0)

        x_vec.append(frame[0])
        y_vec.append(frame[1])
        
        if count == 25:
            count = 0
            line1.set_data(x_vec, y_vec)
 
            #if np.min(y_vec)<=line1.axes.get_ylim()[0] or np.max(y_vec)>=line1.axes.get_ylim()[1]:
            #    ax[0].set_ylim([np.min(y_vec)-np.std(y_vec),np.max(y_vec)+np.std(y_vec)])
        
            plt.pause(0.1)
 
        count += 1


if __name__ == "__main__": 
    # printing main program process id 
    print("Main process started: {}".format(os.getpid())) 
    if plt.get_backend() == "MacOSX":
        mp.set_start_method("forkserver") 
    # creating processes 
    p1 = mp.Process(target=sensor_process) 
    p2 = mp.Process(target=filter_process) 
    p3 = mp.Process(target=plotter_process) 

    # starting processes 
    p1.start() 
    p2.start()
    p3.start()
  
    # wait until processes are finished 
    p1.join() 
    p2.join() 
    p3.join()

