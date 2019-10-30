import io
import os
import imp
import csv
import tensorflow as tf
import math
import numpy as np
import itertools
import h5py
from os import listdir
from os.path import isfile, join
from PIL import Image

from waymo_open_dataset.utils import range_image_utils
from waymo_open_dataset.utils import transform_utils
from waymo_open_dataset.utils import  frame_utils
from waymo_open_dataset import dataset_pb2 as open_dataset
from shapely.geometry import Polygon, LineString
import random
import sys

# TODO: Change this to your own setting
# os.environ['PYTHONPATH']='/env/python:~/github/waymo-open-dataset'
# m=imp.find_module('waymo_open_dataset', ['.'])
# imp.load_module('waymo_open_dataset', m[0], m[1], m[2])

TYPE_VEHICLE = 1
FRONT = 1
FPS = 10
VERIFY_THRESHOLD = 0.05

#Eager execution is enabled by default in TF 2.0 Therefore we need not enable it explicitly.
tf.enable_eager_execution()


total_frames = 0
skipped_frames = 0

# Change the folder path accordingly
image_folder_path = '/home/akm2215/training/images/'

"""
features:
[vx, vy, vz, dx, dy, vfx, vfy, vfz, afx, afy, afz]

labels:
[ax, ay, az]
"""

def write_to_csv(filename, feats, labels):
#     print(feats[0], labels[0])
    comb_np = np.hstack((feats, labels))
#     print(comb_np[0])
#     print(comb_np[0].tolist())
    with open(filename, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=',')
        for comb in comb_np:
            row = comb.tolist()
            csvwriter.writerow(row)
#     np.savetxt(filename, comb_np, delimiter=",")


def collect_vehicle_laser_labels(frame):
  v_laser_labels = []

  for ll in frame.laser_labels:
    v_laser_labels.append(ll)

  return v_laser_labels


def get_vehicle_pose(frame):
  pose = []
  for image in frame.images:
      pose = [t for t in image.pose.transform]

  return np.asarray(pose).reshape((4,4))


def get_current_car_velocity_wrt_GF(frame):
  """
  Return the speed v_x and v_y of the current car
  """
  for image in frame.images:
    return np.asarray([image.velocity.v_x, image.velocity.v_y, image.velocity.v_z])

  return None


def get_front_car_velocity_wrt_GF(front_car_label, vehicle_pose, v_cur_GF):
  v_front_VF = np.asarray([front_car_label.metadata.speed_x, front_car_label.metadata.speed_y, 0])
  _v_front_VF = np.hstack((v_front_VF, [0])) # padded 0 for matrix multiplication
  return np.matmul(vehicle_pose, _v_front_VF)[:3] - v_cur_GF


def get_relative_distance(front_car_label):
  return np.asarray([front_car_label.box.center_x, front_car_label.box.center_y])


def get_current_car_accel_GF_per_frame(dt, v_cur_GF, v_cur_GF_prev):
  return cal_aceleration(v_cur_GF, v_cur_GF_prev, dt) if v_cur_GF_prev is not None else np.asarray([0, 0, 0])


def get_front_car_GF_features_per_frame(dt, frame, vehicle_pose, front_car_label,
                                        v_cur_GF, v_front_GF_prev, verify=False):

  if verify and random.random() < VERIFY_THRESHOLD:
    verify_front_car_label(frame, front_car_label)

  relative_dist = get_relative_distance(front_car_label) # 2 * 1
  v_front_GF = get_front_car_velocity_wrt_GF(front_car_label, vehicle_pose, v_cur_GF) # 3 * 1
  a_front_GF = cal_aceleration(v_front_GF, v_front_GF_prev, dt) if v_front_GF_prev is not None else np.asarray([0, 0, 0]) # 3 * 1

  return np.hstack((relative_dist, v_front_GF, a_front_GF)), v_front_GF


def store_images(images, seg_name, fno):
    #file_name = image_folder_path + 'segment-' + seg_name + '-' + fno + '.h5'
    #hf = h5py.File(file_name, 'w')
    #for img in images:
    #    hf.create_dataset(str(img.name), data=tf.image.decode_jpeg(img.image).numpy())
    #hf.close()
    #return str(file_name)
    
    file_name = []
    
    for img in images:
        temp_name = str(image_folder_path + 'segment-' + seg_name + '-' + fno + '-' +str(img.name) +'.jpg')
        im = Image.open(io.BytesIO(img.image))
        im.save(temp_name)
        file_name.append(temp_name)
        
    return np.array(file_name)
    

def get_essentials_per_frame(dt, frame, front_car_label, v_cur_GF_prev, v_front_GF_prev, fno):
    img_file_name = store_images(frame.images, frame.context.name, fno)
    vehicle_pose = get_vehicle_pose(frame)
    v_cur_GF = get_current_car_velocity_wrt_GF(frame) # 3 * 1
    front_GF_feat, v_front_GF = get_front_car_GF_features_per_frame(dt, frame, vehicle_pose, front_car_label,
                                                                    v_cur_GF, v_front_GF_prev) # 8 * 1
    a_cur_GF = get_current_car_accel_GF_per_frame(dt, v_cur_GF, v_cur_GF_prev) # 3 * 1

    return np.hstack((v_cur_GF, front_GF_feat, img_file_name)), a_cur_GF, v_cur_GF, v_front_GF


def get_features_and_labels(frames):
  global total_frames
  global skipped_frames

  feat_set = []
  label_set = []

  dt = len(frames) * 1.0 / FPS / (len(frames) - 1)

  # init
  v_cur_GF_prev = None
  v_front_GF_prev = None
  fno = 0
  for frame in frames:
    total_frames += 1
    fno += 1

    # Capture the front car
    v_laser_labels = collect_vehicle_laser_labels(frame)
    front_car_label = get_front_car_laser_label(v_laser_labels)

    if front_car_label is None:
      skipped_frames += 1
      print("No front car captured, will skip this frame")
      continue

    feats, labels, v_cur_GF_prev, v_front_GF_prev = get_essentials_per_frame(dt, frame, front_car_label, v_cur_GF_prev, v_front_GF_prev, str(fno))
    feat_set.append(feats)
    label_set.append(labels)

  return np.asarray(feat_set), np.asarray(label_set)

def intersects(label):
  # Starting from the upper-left corner, clock direction
  bounding_box = Polygon([
      (label.box.center_x - 0.5 * label.box.length, label.box.center_y + 0.5 * label.box.width), 
      (label.box.center_x + 0.5 * label.box.length, label.box.center_y - 0.5 * label.box.width), 
      (label.box.center_x + 0.5 * label.box.length, label.box.center_y + 0.5 * label.box.width),
      (label.box.center_x - 0.5 * label.box.length, label.box.center_y - 0.5 * label.box.width)
  ])
  
  line = LineString([(0, 0), (label.box.center_x, 0)])
  
  return bounding_box.intersects(line)


def get_front_car_laser_label(labels):
  """
  Find the closest bounding box which intersects with y = 0 and its center_x is positive
  """

  front_car_label = None

  for label in labels:
    if label.box.center_x < 0:
      continue

    if intersects(label):
      if front_car_label is None or front_car_label.box.center_x > label.box.center_x:
        front_car_label = label

  return front_car_label


def cal_aceleration(v1, v2, dt):
  return (v2 - v1) / dt;

if __name__ == "__main__":
    seg_path = sys.argv[1]
    result_path = sys.argv[2]

    files = [join(seg_path, f) for f in listdir(seg_path) if isfile(join(seg_path, f))]

    print("Total files: ", len(files))

    feat_set = None
    label_set = None

    for i in range(len(files)):
      file = files[i]
      print(file)
      dataset = tf.data.TFRecordDataset(file, compression_type='')

      # Load frames from dataset
      frames = []
      for data in dataset:
          frame = open_dataset.Frame()
          frame.ParseFromString(bytearray(data.numpy()))
          frames.append(frame)

      print("filename:", file, "Num of frames:", len(frames))

      feats, labels = get_features_and_labels(frames)

      if len(feats) > 0:
          feat_set = np.vstack((feat_set, feats)) if feat_set is not None else feats
          label_set = np.vstack((label_set, labels)) if label_set is not None else labels

      print("Progress: ", i + 1, "/", len(files))
    
    write_to_csv(result_path, feat_set, label_set)
    print("Finished! Total_frames = ", total_frames, " skipped_frames = ", skipped_frames)
