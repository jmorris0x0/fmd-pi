import matplotlib.pyplot as plt
import numpy as np
import time

# use ggplot style for more sophisticated visuals
plt.style.use('ggplot')

size = 10
x_vec = []
y_vec = []

plt.ion()
fig,ax = plt.subplots(3,1,figsize=(12,7),sharex=True)
fig.align_ylabels(ax)

ax[0].set_ylabel('Pressure [mmHg]',fontsize=12)
ax[1].set_ylabel('Smoothed [mmHg]',fontsize=12)

line1, = ax[0].plot(x_vec,y_vec,'-,g',alpha=0.8)        

plt.show()

plt.xlim([0, 60])
plt.ylim([-1, 1])

t0 = time.time()

while True:
    x_vec.append(time.time() - t0)
    y_vec.append(np.random.randn(1))
    line1.set_data(x_vec, y_vec)

    if np.min(y_vec)<=line1.axes.get_ylim()[0] or np.max(y_vec)>=line1.axes.get_ylim()[1]:
        ax[0].set_ylim([np.min(y_vec)-np.std(y_vec),np.max(y_vec)+np.std(y_vec)])

    plt.pause(0.1)
