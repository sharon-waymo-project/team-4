import matplotlib.pyplot as plt
import random
from itertools import count
from matplotlib.animation import FuncAnimation
from matplotlib import animation
import matplotlib.gridspec as gridspec
import numpy as np
import sys
import os

x_vals = []
y_vals_mag = []
y_vals_x = []
y_vals_y = []
y_vals_z = []
#y_vals_5 = []
y_deg1 = []
y_deg2 = []
y_deg3 = []
arr = np.load('./frame_acc_new.npy',allow_pickle=True)
# fig = plt.figure(constrained_layout=True)
# gs = gridspec.GridSpec(6, 6)
# ax1 = fig.add_subplot(gs[0, 0:3])
# ax2 = fig.add_subplot(gs[0,3:])
# ax3 = fig.add_subplot(gs[1,0:3])
# ax4 = fig.add_subplot(gs[1,3:])
# ax5 = fig.add_subplot(gs[2,1:5])

Writer = animation.writers['ffmpeg']
writer = Writer(fps=10, metadata=dict(artist='Me'), bitrate=1800)



f = plt.figure(figsize=(10,8))
ax1 = f.add_subplot(321)
ax2 = f.add_subplot(322)
ax3 = f.add_subplot(323)
ax4 = f.add_subplot(324)
ax5 = f.add_subplot(325)
#ax6 = f.add_subplot(326)
index = count()
#idx = count()
def animate(i):
	c = next(index)
	print(c)
	x_vals.append(c)
	
	val1 = np.sqrt(sum((arr[c]['info'][1])**2))
	
	val1_x = arr[c]['info'][1][0]
	val1_y= arr[c]['info'][1][1]
	val1_z = arr[c]['info'][1][2]
	
	deg1 = np.degrees(np.arccos((val1_x)/(val1)))
	deg2 = np.degrees(np.arccos((val1_y)/(val1)))
	deg3 = np.degrees(np.arccos((val1_z)/(val1)))
	#print(deg1)
	y_deg1.append(deg1)
	y_deg2.append(deg2)
	y_deg3.append(deg3)
	y_vals_mag.append(val1)
	y_vals_x.append(val1_x)
	y_vals_y.append(val1_y)
	y_vals_z.append(val1_z)
	
	ax1.cla()
	ax2.cla()
	ax3.cla()
	ax4.cla()
	ax5.cla()
	#ax6.cla()
	#plt.plot(x_vals,y_vals)
	ax1.set_title('Acceleration Magnitute')
	ax2.set_title('Accelation in X')
	ax3.set_title('Accelation in Y')
	ax4.set_title('Accelation in Z')
	ax5.set_title('Angles')
	ax1.set_xticklabels([])
	ax2.set_xticklabels([])
	ax3.set_xticklabels([])
	ax4.set_xticklabels([])
	ax5.set_xticklabels([])
	ax1.plot(x_vals,y_vals_mag)
	ax2.plot(x_vals,y_vals_x)
	ax3.plot(x_vals,y_vals_y)
	ax4.plot(x_vals,y_vals_z)
	
	#ax5.plot(x_vals,y_vals_5)

	ax5.plot(x_vals,y_deg1,label=r'$ \cos(\alpha) $')
	ax5.plot(x_vals,y_deg2,label=r'$ \cos(\beta) $')
	ax5.plot(x_vals,y_deg3,label=r'$ \cos(\gamma) $')
	ax5.legend()

	


ani= FuncAnimation(f,animate, frames = 196, interval=100, repeat=False)

ani.save('basic_animation_latest.mp4', writer=writer)
#set_size(5,5)

#fig = plt.gcf()
#fig.set_figheight(15)
#fig.set_figwidth(15)
plt.tight_layout()
plt.show()