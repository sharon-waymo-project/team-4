import scipy.misc
import random
import pandas as pd

xs = []
ys = []


train_batch_pointer = 0
val_batch_pointer = 0


#with open("driving_dataset/data.txt") as f:
#    for line in f:
#        xs.append("driving_dataset/" + line.split()[0])
#        ys.append(float(line.split()[1]) * scipy.pi / 180)

df = pd.read_csv('/home/akm2215/results.csv')
df.columns = ['vx', 'vy', 'vz', 'dx', 'dy', 'vfx', 'vfy', 'vfz', 'afx', 'afy', 'afz','FRONT','FRONT_LEFT','SIDE_LEFT','FRONT_RIGHT','SIDE_RIGHT','ax','ay','az']

y_df = df.iloc[:,-3:]
ys = y_df.to_numpy()

x_df = df.loc[:,'FRONT']
xs = x_df.to_numpy()


num_images = len(xs)

c = list(zip(xs, ys))
random.shuffle(c)
xs, ys = zip(*c)

train_xs = xs[:int(len(xs) * 0.8)]
train_ys = ys[:int(len(xs) * 0.8)]

val_xs = xs[-int(len(xs) * 0.2):]
val_ys = ys[-int(len(xs) * 0.2):]

num_train_images = len(train_xs)
num_val_images = len(val_xs)

def LoadTrainBatch(batch_size):
    global train_batch_pointer
    x_out = []
    y_out = []
    for i in range(0, batch_size):
        x_out.append(scipy.misc.imresize(scipy.misc.imread(train_xs[(train_batch_pointer + i) % num_train_images])[-150:], [66, 200]) / 255.0)
        y_out.append([train_ys[(train_batch_pointer + i) % num_train_images]])
    train_batch_pointer += batch_size
    return x_out, y_out

def LoadValBatch(batch_size):
    global val_batch_pointer
    x_out = []
    y_out = []
    for i in range(0, batch_size):
        x_out.append(scipy.misc.imresize(scipy.misc.imread(val_xs[(val_batch_pointer + i) % num_val_images])[-150:], [66, 200]) / 255.0)
        y_out.append([val_ys[(val_batch_pointer + i) % num_val_images]])
    val_batch_pointer += batch_size
    return x_out, y_out
