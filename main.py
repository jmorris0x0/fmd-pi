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


def sensor_process(sample_freq): 
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
        noise = 6 * random.random()
        value = trend + signal + noise

        data = [tn, value]

        pub_socket.send_string(topic, zmq.SNDMORE)
        pub_socket.send_pyobj(data)
        time.sleep(1/sample_freq)


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


def bandpass_filter(sample_freq):
    context = zmq.Context()
    sub_socket = context.socket(zmq.SUB)
    sub_socket.connect("tcp://localhost:5555")
    sub_socket.setsockopt(zmq.SUBSCRIBE, b'sensor')

    pub_socket = context.socket(zmq.PUB)
    pub_socket.setsockopt(zmq.SNDHWM, 100000)
    pub_socket.bind("tcp://*:5557")
    pub_topic = 'filter_2'


    lowcut = 0.5
    highcut = 25
    order = 4
    nyq = 0.5 * sample_freq
    low = lowcut / nyq
    high = highcut / nyq
    if high > 1: high = 0.999999999999
    print("Bandpass Wn: " + str([low, high]))
 
    b, a = sig.butter(order, [low, high], analog=False, btype='band')

    # Construct initial conditions for lfilter for step response steady-state.
    z = sig.lfilter_zi(b, a)
    
    while True:
        topic = sub_socket.recv_string()
        frame = sub_socket.recv_pyobj()
        tn = frame[0]
        value = frame[1]
        
        result, z = sig.lfilter(b, a, [value], zi=z)

        #need to look at connect vs bind
        #https://stackoverflow.com/questions/30552925/how-to-handle-multiple-publishers-on-same-port-in-zmq

        data = [tn, result[0]]

        pub_socket.send_string(pub_topic, zmq.SNDMORE)
        pub_socket.send_pyobj(data)



def lowpass_filter(sample_freq):
    context = zmq.Context()
    sub_socket = context.socket(zmq.SUB)
    sub_socket.connect("tcp://localhost:5555")
    sub_socket.setsockopt(zmq.SUBSCRIBE, b'sensor')

    pub_socket = context.socket(zmq.PUB)
    pub_socket.setsockopt(zmq.SNDHWM, 100000)
    pub_socket.bind("tcp://*:5556")
    pub_topic = 'filter_1'


    cutoff = 0.5
    order = 5
    nyq = 0.5 * sample_freq
    normal_cutoff = cutoff / nyq
 
    b, a = sig.butter(order, normal_cutoff, analog=False, btype='low')

    # Construct initial conditions for lfilter for step response steady-state.
    z = sig.lfilter_zi(b, a)
    
    while True:
        topic = sub_socket.recv_string()
        frame = sub_socket.recv_pyobj()
        tn = frame[0]
        value = frame[1]
        
        result, z = sig.lfilter(b, a, [value], zi=z)

        #need to look at connect vs bind
        #https://stackoverflow.com/questions/30552925/how-to-handle-multiple-publishers-on-same-port-in-zmq

        data = [tn, result[0]]

        pub_socket.send_string(pub_topic, zmq.SNDMORE)
        pub_socket.send_pyobj(data)


def plotter_process(sample_freq): 
    plots = [{'topic': b'sensor', 'port': '5555', 'label': 'P [mmHg]', 'y_lim': [0, 150], 'color': '#3465a4'},
             {'topic': b'filter_1', 'port': '5556', 'label': 'Low pass P [mmHg]', 'y_lim': [0, 150], 'color': '#cc0000'},
             {'topic': b'filter_2', 'port': '5557', 'label': 'Band pass P [mmHg]', 'y_lim': [-20, 20], 'color': 'g'}]

    plots_len = len(plots)
    context = zmq.Context()
    socket = []
    
    for i in range(0, plots_len):
        socket.append(context.socket(zmq.SUB))
    
    for i in range(0, plots_len):
        socket[i].connect("tcp://localhost:" + plots[i].get('port'))
        socket[i].setsockopt(zmq.SUBSCRIBE, plots[i].get('topic'))

    #plt.style.use('dark_background')
    plt.style.use('ggplot')
    
    x_vec = [[] for x in range(plots_len)]
    y_vec = [[] for x in range(plots_len)]

    plt.ion()
    fig,ax = plt.subplots(plots_len, 1,figsize=(12,7), sharex=True)
    fig.align_ylabels(ax)

    #plt.hlines([-a, a], 0, T, linestyles='--')
    #plt.grid(True)

    for i in range(len(ax)):
        ax[i].set_ylabel(plots[i].get('label'), fontsize=12)
        ax[i].set_xlim([0, 60])
        ax[i].set_ylim(plots[i].get('y_lim'))

    line = [[0] for x in range(plots_len)]

    for i in range(plots_len):
        line[i], = ax[i].plot(x_vec[i], y_vec[i], color=plots[i].get('color'), alpha=0.8)     
    
    plt.show()
    render = False
    count = 0

    while True:
        for i in range(0, plots_len):
            topic = socket[i].recv_string()
            frame = socket[i].recv_pyobj()            
            x_vec[i].append(frame[0])
            y_vec[i].append(frame[1])

        if count == sample_freq/5:
            count = 0
            
            for i in range(plots_len):
                line[i].set_data(x_vec[i], y_vec[i])
 
            #if np.min(y_vec)<=line1.axes.get_ylim()[0] or np.max(y_vec)>=line1.axes.get_ylim()[1]:
            #    ax[0].set_ylim([np.min(y_vec)-np.std(y_vec),np.max(y_vec)+np.std(y_vec)])

            plt.pause(0.001)
            #fig.canvas.draw()
            #fig.canvas.flush_events()
 
        count += 1


if __name__ == "__main__": 
    # printing main program process id 
    print("Main process started: {}".format(os.getpid())) 
    if plt.get_backend() == "MacOSX":
        mp.set_start_method("forkserver") 
    
    sample_freq = 1000
    # creating processes
    p1 = mp.Process(target=sensor_process, args=[sample_freq]) 
    p2 = mp.Process(target=bandpass_filter, args=[sample_freq])
    p3 = mp.Process(target=lowpass_filter, args=[sample_freq]) 
    p4 = mp.Process(target=plotter_process, args=[sample_freq]) 

    # starting processes 
    p1.start() 
    p2.start()
    p3.start()
    p4.start()

    # wait until processes are finished 
    p1.join() 
    p2.join() 
    p3.join()
    p4.join()

