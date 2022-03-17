import glob
import pandas as pd

a = glob.glob('./KneeXray/train/0_he/'+'*.png')
a_label = ['0' for x in range(0,len(a),1)]
b = glob.glob('./KneeXray/train/1_he/'+'*.png')
b_label = ['1' for x in range(0,len(b),1)]
c = glob.glob('./KneeXray/train/2_he/'+'*.png')
c_label = ['2' for x in range(0,len(c),1)]
d = glob.glob('./KneeXray/train/3_he/'+'*.png')
d_label = ['3' for x in range(0,len(d),1)]
e = glob.glob('./KneeXray/train/4_he/'+'*.png')
e_label = ['4' for x in range(0,len(e),1)]

file = a+b+c+d+e
label = a_label+b_label+c_label+d_label+e_label

a = pd.DataFrame({'data':file, 'label':label})
a. set_index('data', inplace=True)
a.to_csv('./KneeXray/Train_he.csv')


a = glob.glob('./KneeXray/test/0_he/'+'*.png')
a_label = ['0' for x in range(0,len(a),1)]
b = glob.glob('./KneeXray/test/1_he/'+'*.png')
b_label = ['1' for x in range(0,len(b),1)]
c = glob.glob('./KneeXray/test/2_he/'+'*.png')
c_label = ['2' for x in range(0,len(c),1)]
d = glob.glob('./KneeXray/test/3_he/'+'*.png')
d_label = ['3' for x in range(0,len(d),1)]
e = glob.glob('./KneeXray/test/4_he/'+'*.png')
e_label = ['4' for x in range(0,len(e),1)]

file = a+b+c+d+e
label = a_label+b_label+c_label+d_label+e_label

a = pd.DataFrame({'data':file, 'label':label})
a. set_index('data', inplace=True)
a.to_csv('./KneeXray/Test_he_correct.csv')