from hsc import *

import time
import numpy as np
import matplotlib.pyplot as plt
import psutil

plt.ion()
plt.style.use('ggplot')
fig,ax = plt.subplots(3,1,figsize=(12,7),sharex=True)
fig.align_ylabels(ax)
cmap = plt.cm.Set1

ax[0].legend(bbox_to_anchor=(1.12,0.9))
ax[0].set_ylabel('Pressure [mmHg]',fontsize=12)
#pressure_line, = ax[0].plot(0, 0, '-o', label="pressure", lw=3)
# color=cmap(0)

ax[1].legend(bbox_to_anchor=(1.12,0.9))
ax[1].set_ylabel('Smoothed [mmHg]',fontsize=12)
#smoothed_line, = ax[1].plot(0, 0, '-o', label="pressure", lw=3)

#plt.show()
#plt.pause(0.1)

# These not only don't plot, they erase the whole graph
#pressure_line.set_data(0.4, 1)
#pressure_line.set_data(0.2, 1)

fig.show()
#i = 0
#x, y = [], []

#while True:
#    x.append(i)
#    y.append(psutil.cpu_percent())
#    ax[0].plot(x,y, color='b')
#    fig.canvas.draw()
#    time.sleep(0.1)
#    i += 1







sensor = HoneywellHSC()
t_vec = []
pressure_vec = []
smoothed_vec = []
t0 = time.time()
smooth_count = 1
i = 0
render = False

while True:
    if i == 4:
        render = True
        i = 0
    try:
        status, temp, pressure = sensor.get_data()
    except:
        continue

    t = time.time() - t0
    t_vec.append(t)
    pressure_vec.append(pressure)
    if render:
        ax[0].plot(t_vec, pressure_vec, color='b')

    lookback = min(smooth_count, 50)
    smoothed = sum(pressure_vec[-lookback: ]) / lookback
    smoothed_vec.append(smoothed)
    if render:
        ax[1].plot(t_vec, smoothed_vec, color='r')
        fig.canvas.draw()

        #ax[0].set_xlim(left=max(0, t-10), right=max(5, t+5))
        #ax[1].set_xlim(left=max(0, t-10), right=max(5, t+5))
        ax[0].set_xlim(left=0, right=20)
        ax[1].set_xlim(left=0, right=20)

    time.sleep(0.25)
    smooth_count += 1
    render = False
    i += 1


