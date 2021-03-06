import torch
from torch.utils.data import Dataset
import os
import cv2
import glob
from torchvision import transforms
from PIL import Image
import numpy as np
from skimage import io
import csv


def read_annotation(file_pose, file_distracted):

    angles = {}
    head_pos = {}
    with open(file=file_pose, mode="r") as f:
        lines = f.readlines()
        for l in lines:
            data = l.rstrip().split('\t')
            angles[data[1]] = np.array([float(data[2]), float(data[3]), float(data[4])], dtype=np.float32)  # [yaw, roll, pitch]
            head_pos[data[1]] = np.array([float(data[107])/1920.0, float(data[108])/1080.0], dtype=np.float32)  # [x, y]

    distracted = {}
    with open(file=file_distracted, mode='r') as f:
        csv_reader = csv.reader(f)
        header = next(csv_reader)
        for data in csv_reader:
            distracted[data[0]] = np.array([float(data[1])], dtype=np.float32)

    return angles, head_pos, distracted


def make_samples(root, modal, n_sub=None):
    # get the list of the directory
    subjects = os.scandir(root)
    # initiate samplers
    samples = []
    # loop all subjects
    for subject in subjects:
        if int(subject.name.split('/')[-1]) in n_sub:
            # choose one image modal to process
            if str.lower(modal) == 'rgb':
                image_folder = os.path.join(subject.path, 'RGB')
            elif str.lower(modal) == 'depth':
                image_folder = os.path.join(subject.path, 'DEPTH')

            # read annotation and get yaw, roll and pitch
            angles, head_pos, distracted = read_annotation(os.path.join(subject.path, 'data.txt'),
                                                           os.path.join(subject.path, 'distracted.csv'))

            # create images path list
            for imgs in os.scandir(image_folder):
                samples.append((subject.name, imgs.path, angles[imgs.name.split('_')[0]],
                                head_pos[imgs.name.split('_')[0]], distracted[imgs.name]))

    return samples


class PandoraData(Dataset):
    def __init__(self, root='', split='train', modal='RGB', transform=None, target_transform=None):
        self.root = root
        self.transform = transform
        self.target_transform = target_transform
        self.split = split
        self.modal = modal
        if self.split == 'train':
            self.n_sub = [1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13, 15, 17, 18, 19, 21, 22]
        else:
            self.n_sub = [10, 14, 16, 20]
        self.samples = make_samples(root, modal=modal, n_sub=self.n_sub)

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, item):
        data = self.samples[item]
        img = cv2.imread(data[1])
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        # img = Image.fromarray(img)
        # if self.transform:
        #     img = self.transform(img)
        angle = data[2]
        head_pos = data[3]
        distracted = data[4]
        return img, angle, head_pos, distracted


if __name__ == '__main__':
    root = 'dataset/pandora/'
    dataset = PandoraData(root=root, modal='RGB')
    torch.save(dataset, os.path.join(root, 'pandora.bin'))



