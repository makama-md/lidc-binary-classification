import random
import os

from PIL import Image
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms as transforms

import pandas as pd
import re

# borrowed from http://pytorch.org/tutorials/advanced/neural_style_tutorial.html
# and http://pytorch.org/tutorials/beginner/data_loading_tutorial.html
# define a training image loader that specifies transforms on images. See documentation for more details.
tfms_train = transforms.Compose([
    transforms.Resize((224, 224)),
    # transforms.Resize((224, 224)),  # resize the image to 64x64 (remove if images are already 64x64),
    # transforms.RandomHorizontalFlip(),  # randomly flip image horizontally
    # transforms.RandomAffine(10, translate=(.1, .1), scale=(.1, .1), shear=.1, resample=False, fillcolor=0),
    transforms.ToTensor()])  # transform it into a torch tensor

# loader for evaluation, no horizontal flip
# eval_transformer = transforms.Compose([
#     # transforms.Resize((224, 224)),  # resize the image to 64x64 (remove if images are already 64x64)
#     transforms.ToTensor()])  # transform it into a torch tensor

tfms_eval = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor()
])

class LIDCDataset(Dataset):
    """
    A standard PyTorch definition of Dataset which defines the functions __len__ and __getitem__.
    """
    def __init__(self, data_dir, transform, df):
        """
        Store the filenames of the jpgs to use. Specifies transforms to apply on images.

        Args:
            data_dir: (string) directory containing the dataset
            transform: (torchvision.transforms) transformation to apply on image
        """
        self.data_dir = data_dir
        self.transform = transform
        self.df = df

        assert ("name" in df.columns) & ("label" in df.columns)

        # self.pids = os.listdir(data_dir)
        # self.segmdict = {}
        # for pid in self.pids:
        #     self.segmdict[pid] = pd.DataFrame(
        #         {"pid": str(pid),
        #          "segmentation_file": os.listdir(os.path.join(data_dir, pid))}
        #          )
        # self.df = pd.concat(self.segmdict, ignore_index = True)
        # self.df = pd.Series(self.segmdict)
        # self.df = self.df.reset_index()
        # self.df.columns = ["pid", "segmentation_file"]
        # self.df["pid"] = self.df.pid.astype(str)
        # self.df["segmentation_name"] = self.df.segmentation_file.apply(lambda x: x[:-4])
        # self.df["segmentation_path"] = self.df.apply(lambda x: os.path.join(self.data_dir, x["pid"], x["segmentation_file"]), axis = 1)
        # self.df["segmentation_id"] = self.df.apply(lambda x: x["pid"] + "_" + x["segmentation_name"], axis = 1)
        # self.df["label"] = self.df.segmentation_name.apply(lambda x: int("body" in x))

        # self.filenames = [os.listdir(os.path.join(data_dir, x)) for x in pids]
        # self.filenames = [item for sublist in self.filenames for item in sublist]
        # self.filenames = [f for f in self.filenames if f.endswith('.png')]

        # create dicts to go from pid to idx and vice versa
        # self.pids = [int(re.findall('\d+', x)[0]) for x in self.filenames]
        # self.ids        = list(self.df.segmentation_id)
        self.ids        = df.name.tolist()
        self.fpaths     = [os.path.join(data_dir, x) for x in self.df.name.tolist()]
        self.labels     = list(self.df.label)
        self.fpath_dict = dict(zip(self.ids, self.fpaths))
        self.label_dict = dict(zip(self.ids, self.labels))
        self.id_to_idx  = dict(zip(self.ids, range(len(self.ids))))
        self.idx_to_id  = dict(zip(range(len(self.ids)), self.ids))

        # self.labels = [int(os.path.split(filename)[-1][0]) for filename in self.filenames]
        # self.label_df = pd.read_csv(os.path.join(data_dir, "labels.csv"), index_col = "pid")
        # self.labels = self.label_df.label.to_dict()

    def print_test(self):
        print(self.df.shape)

    def __len__(self):
        # return size of dataset
        return len(self.ids)

    def __getitem__(self, idx):
        """
        Fetch index idx image and labels from dataset. Perform transforms on image.

        Args:
            idx: (int) index in [0, 1, ..., size_of_dataset-1]

        Returns:
            image: (Tensor) transformed image
            label: (int) corresponding label of image
        """
        # print("opening %s " % self.fpath_dict[self.idx_to_id[idx]])
        # image = Image.open(self.fpath_dict[self.idx_to_id[idx]]).convert("RGB")  # PIL image
        image = Image.open(self.fpath_dict[self.idx_to_id[idx]]).convert("L")  # L for grayscale
        image = self.transform(image)
        return image, self.label_dict[self.idx_to_id[idx]]


def fetch_dataloader(df, types = ["train"], data_dir = "data", params = None, batch_size = 128,
                     tfms = []):
    """
    Fetches the DataLoader object for each type in types from data_dir.

    Args:
        types: (list) has one or more of 'train', 'val', 'test' depending on which data is required
        data_dir: (string) directory containing the dataset
        df: pandas dataframe containing at least name, label and split
        params: (Params) hyperparameters

    Returns:
        data: (dict) contains the DataLoader object for each type in types
    """
    dataloaders = {}

    splits = [x for x in types if x in df.split.unique().tolist()]

    # for split in ['train', 'val', 'test']:
    for split in splits:
        if split in types:
            # path = os.path.join(data_dir, split)
            path = data_dir

            # use the train_transformer if training data, else use eval_transformer without random flip
            if split == 'train':
                dl = DataLoader(LIDCDataset(path, tfms_train, df[df.split.isin([split])]), 
                                        batch_size = batch_size,
                                        shuffle=True,
                                        num_workers=2,
                                        pin_memory=True)
                                        # batch_size=params.batch_size, 
                                        # num_workers=params.num_workers,
                                        # pin_memory=params.cuda)
            else:
                # dl = DataLoader(SEGMENTATIONDataset(path, eval_transformer, df[df.split.isin([split])]), 
                dl = DataLoader(LIDCDataset(path, tfms_eval, df[df.split.isin([split])]), 
                                batch_size = batch_size,
                                shuffle=False,
                                num_workers=2,
                                pin_memory=True)
                                # batch_size=params.batch_size, 
                                # num_workers=params.num_workers,
                                # pin_memory=params.cuda)

            dataloaders[split] = dl

    return dataloaders
