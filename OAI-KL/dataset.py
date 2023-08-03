import torch
import cv2
from torch.utils.data import Dataset

class ImageDataset(Dataset):
    def __init__(self, df, image_size, transforms=None):
        self.data = df['data']
        self.label = df['label']
        self.image_size = (image_size, image_size)
        self.transforms = transforms
        
        if 'label' in df:
            self.target = df['label']
        else:
            self.target = None

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        data = self.data[idx]
        image = cv2.imread(data, cv2.IMREAD_GRAYSCALE)
        image = cv2.resize(image, dsize=self.image_size, interpolation=cv2.INTER_CUBIC)
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB) # OpenCV에서는 BGR 방식으로 표현

        if self.transforms:
            image = self.transforms(image=image)['image']

        if self.target is not None:
            return {
                'image': image.float(),
                'target': torch.tensor(self.target[idx], dtype=torch.long)
                }
        else: 
            return {
                'image': image.float()
                }
            
    def get_labels(self):
        return self.label.values