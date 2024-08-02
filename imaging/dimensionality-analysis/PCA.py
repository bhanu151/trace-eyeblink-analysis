
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import scipy.io
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import statistics as stat

%matplotlib notebook

# |%%--%%| <yNAvXEW7gq|RiadQMREi0>
r"""°°°
## Read dfbf
°°°"""
# |%%--%%| <RiadQMREi0|vLqbmBXlcM>

dfbf_file = "../../../soumyab/CalciumDataAnalysisResults/Preprocessed_files/G313/20200801/1/G313_20200801_wholeTrial_golshani_framebin3_gaussianKernel1.mat"

# |%%--%%| <vLqbmBXlcM|qolLUwRUOe>

data_mat = scipy.io.loadmat(dfbf_file)
dfbf = data_mat["dfbf"]
print(f"This dataset has {dfbf.shape[0]} cells recorded over {dfbf.shape[1]} trials with {dfbf.shape[2]} frames")

# |%%--%%| <qolLUwRUOe|S7AezQ3M0o>
r"""°°°
## Session parameters
°°°"""
# |%%--%%| <S7AezQ3M0o|bknkfmQJJx>

NUM_CELLS = dfbf.shape[0]
NUM_TRIALS = dfbf.shape[1]
NUM_FRAMES = dfbf.shape[2]
GROUP_SIZE = 5 #Number of trials per stim-type in multi-CS

CS_START_FRAME = int(8*NUM_FRAMES / 18)
TRACE_START_FRAME = int(8.05*NUM_FRAMES / 18)
US_START_FRAME = int(8.3*NUM_FRAMES / 18)
POST_START_FRAME = int(8.35*NUM_FRAMES / 18)
CS_START_FRAME

# |%%--%%| <bknkfmQJJx|HiwjJFwxFc>

def plot_trial_average(data):
    plt.figure()
    for i in range(data.shape[0]):
        plt.plot(np.arange(data.shape[2]), np.mean(data, axis=1)[i])
    plt.figure()
    plt.imshow(np.mean(data, axis=1))

# |%%--%%| <HiwjJFwxFc|eG5fp7JGEy>

def plot_cell_traces(data, cell_num):
    plt.figure()
    for i in range(data.shape[1]):
        plt.plot(np.arange(data.shape[2]), 2*i + data[cell_num,i,:])
    

# |%%--%%| <eG5fp7JGEy|BB0AYPvj0H>

def hex_to_RGB(hex_str):
    """ #FFFFFF -> [255,255,255]"""
    #Pass 16 to the integer function for change of base
    return [int(hex_str[i:i+2], 16) for i in range(1,6,2)]

# |%%--%%| <BB0AYPvj0H|tdBuUPhNvR>

def get_color_gradient(c1, c2, n):
    """
    Given two hex colors, returns a color gradient
    with n colors.
    """
    assert n > 1
    c1_rgb = np.array(hex_to_RGB(c1))/255
    c2_rgb = np.array(hex_to_RGB(c2))/255
    mix_pcts = [x/(n-1) for x in range(n)]
    rgb_colors = [((1-mix)*c1_rgb + (mix*c2_rgb)) for mix in mix_pcts]
    return ["#" + "".join([format(int(round(val*255)), "02x") for val in item]) for item in rgb_colors]

# |%%--%%| <tdBuUPhNvR|Zg6oDuPuPy>

plot_trial_average(dfbf)

# |%%--%%| <Zg6oDuPuPy|JYc4A0b123>

plot_cell_traces(dfbf, 35)

# |%%--%%| <JYc4A0b123|p9599EXq7j>
r"""°°°
## Reshaping the data to 2D
°°°"""
# |%%--%%| <p9599EXq7j|yCzOzozssl>

def reshape_data_3D_to_2D(data_3D):
    data_2D = np.reshape(data_3D, (data_3D.shape[0], data_3D.shape[1]*data_3D.shape[2])).T
    return data_2D

# |%%--%%| <yCzOzozssl|d9PvjrLxRR>

def perform_PCA(x, y, num_trials=None):
    x = StandardScaler().fit_transform(x)
    pca = PCA(n_components=3)
    principalComponents = pca.fit_transform(x)

    principalDf = pd.DataFrame(data = principalComponents
             , columns = ['PC1', 'PC2', 'PC3'])
    finalDf = pd.concat([principalDf, pd.Series(y, name="US_type")], axis = 1)
    print(pca.explained_variance_ratio_)
    
    
    #Plot datapoints as scatter
    fig = plt.figure(figsize = (8,8))
    ax = fig.add_subplot(projection='3d')
    
    ax.set_xlabel('PC1', fontsize = 15)
    ax.set_ylabel('PC2', fontsize = 15)
    ax.set_zlabel('PC3', fontsize = 15)
    ax.set_title('3 component PCA', fontsize = 20)
    targets = [0, 1]
    colors = ['r', 'b']
    for target, color in zip(targets,colors):
        indicesToKeep = finalDf['US_type'] == target
        ax.scatter(finalDf.loc[indicesToKeep, 'PC1']
                   , finalDf.loc[indicesToKeep, 'PC2']
                   , finalDf.loc[indicesToKeep, 'PC3']
                   , c = color
                   , s = 50
                   , alpha = 0.5)
    ax.legend(targets)
    ax.grid()
    
    #Plot datapoints as traces
    num_frames = np.int(x.shape[0] / num_trials)
    fig2 = plt.figure(figsize = (8,8))
    ax2 = fig2.add_subplot(projection='3d')
    
    ax2.set_xlabel('PC1', fontsize = 15)
    ax2.set_ylabel('PC2', fontsize = 15)
    ax2.set_zlabel('PC3', fontsize = 15)
    ax2.set_title('3 component PCA', fontsize = 20)
    targets = [0, 1]
    for t_num in range(num_trials):
        
#     colors = ['r', 'b']
#     for t_num in range(num_trials):
#         color = colors[stat.mode(y[t_num*num_frames:(t_num+1)*num_frames])]
#         ax2.plot(finalDf.loc[t_num*num_frames:(t_num+1)*num_frames, 'PC1']
#                    , finalDf.loc[t_num*num_frames:(t_num+1)*num_frames, 'PC2']
#                    , finalDf.loc[t_num*num_frames:(t_num+1)*num_frames, 'PC3']
#                    , c = color
#                    , alpha = 0.5)
#     ax2.legend(targets)
#     ax2.grid()

# |%%--%%| <d9PvjrLxRR|RjSuDuUZcG>
r"""°°°
# PCA on whole dataset
°°°"""
# |%%--%%| <RjSuDuUZcG|oidA3OQiQP>

dataset = dfbf
X = reshape_data_3D_to_2D(dataset)
Y = np.array([(i//(GROUP_SIZE*dataset.shape[2]))%2 for i in range(X.shape[0])])
perform_PCA(X, Y, num_trials=dfbf.shape[1])

# |%%--%%| <oidA3OQiQP|i0oAZ8gjus>
r"""°°°
# Pre-stim data
°°°"""
# |%%--%%| <i0oAZ8gjus|OlC6fMdGvu>

dataset = dfbf[:,:,:CS_START_FRAME]
print(dataset.shape)
X = reshape_data_3D_to_2D(dataset)
Y = np.array([(i//(GROUP_SIZE*dataset.shape[2]))%2 for i in range(X.shape[0])])
perform_PCA(X, Y, num_trials=dfbf.shape[1])

# |%%--%%| <OlC6fMdGvu|9R6ysDqL31>
r"""°°°
# CS to US data
°°°"""
# |%%--%%| <9R6ysDqL31|nPobsXD2zj>

dataset = dfbf[:,:,CS_START_FRAME:POST_START_FRAME]
X = reshape_data_3D_to_2D(dataset)
Y = np.array([(i//(GROUP_SIZE*dataset.shape[2]))%2 for i in range(X.shape[0])])
perform_PCA(X, Y, num_trials=dfbf.shape[1])

# |%%--%%| <nPobsXD2zj|bw2yDSXLHg>
r"""°°°
# Post data
°°°"""
# |%%--%%| <bw2yDSXLHg|nzdMabOmbk>

dataset = dfbf[:,:,POST_START_FRAME:]
X = reshape_data_3D_to_2D(dataset)
Y = np.array([(i//(GROUP_SIZE*dataset.shape[2]))%2 for i in range(X.shape[0])])
perform_PCA(X, Y, num_trials=dfbf.shape[1])
