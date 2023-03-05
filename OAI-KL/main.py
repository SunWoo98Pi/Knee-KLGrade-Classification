# import ssl
import argparse
import torch
import numpy as np
import pandas as pd
from torch import nn, optim
# from torch.nn import functional as F
from torch.utils.data import DataLoader, SubsetRandomSampler
from torchvision import transforms
from sklearn.model_selection import KFold
from tqdm import tqdm
from dataset import ImageDataset
from early_stop import EarlyStopping
from model import model_return
# from my_custom_loss import my_ce_mse_loss

# ssl._create_default_https_context = ssl._create_unverified_context

def train_for_kfold(model, dataloader, criterion, optimizer, fold, epoch):
    train_loss = 0.0
    model.train() # model을 train mode로 변환 >> Dropout Layer 같은 경우 train시 동작 해야 함
    with torch.set_grad_enabled(True): # with문 : 자원의 효율적 사용, 객체의 life cycle을 설계 가능, 항상(True) gradient 연산 기록을 추적
        for batch in (tqdm(dataloader, desc=f'Fold {fold} Epoch {epoch} Train', unit='Batch')):
            optimizer.zero_grad() # 반복 시 gradient(기울기)를 0으로 초기화, gradient는 += 되기 때문
            image, labels = batch['image'].cuda(), batch['target'].cuda() # tensor를 gpu에 할당
            
            # labels = F.one_hot(labels, num_classes=5).float() # nn.MSELoss() 사용 시 필요
            output = model(image) # image(data)를 model에 넣어서 hypothesis(가설) 값을 획득
            
            loss = criterion(output, labels) # error, prediction loss를 계산
            train_loss += loss.item() # loss.item()을 통해 loss의 스칼라 값을 가져온다.

            loss.backward() # prediction loss를 back propagation으로 계산
            optimizer.step() # optimizer를 이용해 loss를 효율적으로 최소화 할 수 있게 parameter 수정
            
    return train_loss

def test_for_kfold(model, dataloader, criterion, fold, epoch):
    test_loss = 0.0
    model.eval() # model을 eval mode로 전환 >> Dropout Layer 같은 경우 eval시 동작 하지 않아야 함
    with torch.no_grad(): # gradient 연산 기록 추적 off
        for batch in (tqdm(dataloader, desc=f'Fold {fold} Epoch {epoch} Valid', unit='Batch')):
            image, labels = batch['image'].cuda(), batch['target'].cuda()
            
            # labels = F.one_hot(labels, num_classes=5).float() # nn.MSELoss() 사용 시 필요
            output = model(image)
            
            loss = criterion(output, labels)
            test_loss += loss.item()
             
    return test_loss

def train(dataset, args, batch_size, epochs, k, splits, foldperf):
    for fold, (train_idx, val_idx) in enumerate(splits.split(np.arange(len(dataset))), start=1):
        train_sampler = SubsetRandomSampler(train_idx) # data load에 사용되는 index, key의 순서를 지정하는데 사용, Sequential , Random, SubsetRandom, Batch 등 + Sampler
        test_sampler = SubsetRandomSampler(val_idx)
        train_loader = DataLoader(dataset, batch_size=batch_size, sampler=train_sampler) # Data Load
        test_loader = DataLoader(dataset, batch_size=batch_size, sampler=test_sampler)
        
        model_ft = model_return(args)
                
        if torch.cuda.device_count() > 1:
            model_ft = nn.DataParallel(model_ft) # model이 여러 대의 gpu에 할당되도록 병렬 처리
        model_ft.cuda() # model을 gpu에 할당

        criterion = nn.CrossEntropyLoss() # loss function
        # criterion = nn.MSELoss()
        # criterion = my_ce_mse_loss
        optimizer = optim.Adam(model_ft.parameters(), lr=args.learning_rate) # optimizer
        
        history = {'train_loss': [], 'test_loss': []}
            
        patience = 5
        delta = 0.1
        early_stopping = EarlyStopping(args, patience=patience, verbose=True, delta=delta)
        
        for epoch in range(1, epochs + 1):
            train_loss = train_for_kfold(model_ft, train_loader, criterion, optimizer, fold, epoch)
            test_loss = test_for_kfold(model_ft, test_loader, criterion, fold, epoch)

            train_loss = train_loss / len(train_loader)
            test_loss = test_loss / len(test_loader)

            print(f"Epoch: {epoch}/{epochs} \t Avg Train Loss: {train_loss:.3f} \t Avg Valid Loss: {test_loss:.3f}")
            
            history['train_loss'].append(train_loss)
            history['test_loss'].append(test_loss)
            
            early_stopping(test_loss, model_ft, args, fold, epoch)
            if early_stopping.early_stop:
                print("Early stopping")
                break
        
        foldperf[f"fold{fold}"] = history  
    
    tl_f, testl_f = [], []

    for f in range(1, k+1):
        tl_f.append(np.mean(foldperf[f'fold{f}']['train_loss']))
        testl_f.append(np.mean(foldperf[f'fold{f}']['test_loss']))

    print()
    print(f"Performance of {k} Fold Cross Validation")
    print(f"Avg Train Loss: {np.mean(tl_f):.3f} \t Avg Valid Loss: {np.mean(testl_f):.3f}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--model_type', dest='model_type', action='store')
    parser.add_argument('-i', '--image_size', type=int, default=224, dest='image_size', action='store')
    parser.add_argument('-l', '--learning_rate', type=float, default=0.0005, dest='learning_rate', action='store')
    args = parser.parse_args()
    
    image_size_tuple = (args.image_size, args.image_size)
    
    print(f"Model Type : {args.model_type}")
    print(f"Image Size : ({args.image_size}, {args.image_size})")
    print(f"Learning Rate : {args.learning_rate}")
    
    train_csv = pd.read_csv('./KneeXray/Train.csv')
    # train_csv = pd.read_csv(f'./KneeXray/Train_{image_size_tuple}.csv')
    transform = transforms.Compose([
                                    transforms.ToTensor(), # 0 ~ 1의 범위를 가지도록 정규화
                                    # transforms.Resize(image_size_tuple, transforms.InterpolationMode.BICUBIC),
                                    transforms.RandomHorizontalFlip(p=0.5),
                                    transforms.RandomRotation(20),
                                    transforms.Normalize([0.5,0.5,0.5],[0.5,0.5,0.5]), # -1 ~ 1의 범위를 가지도록 정규화
                                    ])
    dataset = ImageDataset(train_csv, image_size=args.image_size, transforms=transform)
    batch_size = 32
    epochs = 1
    k = 5
    torch.manual_seed(42)
    splits = KFold(n_splits=k, shuffle=True, random_state=42)
    foldperf = {}

    train(dataset, args, batch_size, epochs, k, splits, foldperf)