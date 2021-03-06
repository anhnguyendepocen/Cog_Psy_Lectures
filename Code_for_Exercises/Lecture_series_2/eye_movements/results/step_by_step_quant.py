import matplotlib.pyplot as plt
import aux_funcs as af
import quant_funcs as qf
import pandas as pd
import numpy as np
import Image
"""
Tutorial 8 - Eye movements
"""
# variable of eye tracker and monitor
pixel_dim = 0.265 # Dimension of pixel [mm]
sampling_rate=350 # Sampling rate of eye-tracker [Hz]

# variables of participant
id    = 'to'   # initials of participant
sess  = 4      # session number

# import behavioral data as dictionary - contains design and button presses
bdata = af.data_to_dict('%s/%s_%d' %(id, id, sess))

# Question 1 - Exploring the raw data
# --------------------------------------
# Typing "bdata.keys()" gives you:
#['rt', 'search', 'nitems', 'trl', 'button', 'tpos_x', 'rot_offset', 'blk', 'tpos_y', 'target']

#rt         - reaction time
#search     - absence/presence [0,1]
#nitems     - number of figures in stimulus [4,8,12]
#trl        - trial number
#button     - absent/present participant response [6,7]
#rot_offset - offset angles for presence of odd-one-out
#blk        - block number
#tpos_y     - screen coordinates for y
#tpos_x     - screen coordinates for x
#target     - type: misaligned, aligned, filled gray, square [0,1,2,3]


# import eye tracking data edata [ block, time , x position , y position]
edata=np.asarray(pd.read_csv('%s/%s_%d_eye.txt' %(id, id, sess), names=['blk','time','xpos','ypos'], skiprows=1, sep=' '))


# 2. Simple plot showing difference between aligned and misaligned stimuli and scan path for nitems==4
# ---------------------------------
# Variables
trl   = 1         # data of trial 1
nitems = [4,8,12] # number of items
search = 0        # target absent
target = 0        # target misaligned

# extract trial number 1
eye_trial = edata[edata[:,0] == trl,]

# convert pixels to milimetres
points = eye_trial[:,2:4]*pixel_dim

# get subset data from bdata for target==0
sdata = af.get_subset(bdata, 'target', target)

plt.figure(1)
plt.subplot(3,1,1)
plt.imshow(Image.open('../stimuli/norm_fat_aligned_10.bmp'),cmap='gray')
plt.title('Item fat')
plt.subplot(3,1,2)
plt.imshow(Image.open('../stimuli/norm_thin_aligned_10.bmp'),cmap='gray')
plt.title('Item thin')
plt.subplot(3,1,3)
plt.plot(eye_trial[:,2], eye_trial[:,3])
plt.title('Scan path')

# More complex plot: shows scan path with stimulus underlay
# Rows differ in nitems: 4,8 & 12
# -------------------------------------------------------------
plt.figure(2)

# define labels for target types
conditions = {0: 'misaligned', 1: 'aligned'}

trial_select=np.zeros((20,3)) # initiate empty array to extract 20 trials for 3 different nitems
step = 1                      # step for plotting only
for n in range(3):            # loop through number of items
    
    # select trial based on presence of target and number of items
    trial_select[:,n] = sdata['trl'][np.logical_and(sdata['search']==search, sdata['nitems']==nitems[n])]
    
    # Plotting routine
    
    for trl in range(3):
        trial = trial_select[trl,n]
        trial_disp = af.create_display(bdata, trial )
        eye_trial = edata[edata[:,0] == trial,]
        
        plt.subplot(3,3,step)
        step=step+1
        plt.imshow(trial_disp, cmap = 'gray', vmin=0, vmax=255) # block background stimuli
        plt.hold(True)
        plt.plot(eye_trial[:,2]+960, eye_trial[:,3]+600, 'b.') # overlay eye tracking path
        plt.axis([300, 1660, 50, 1100])
        plt.suptitle('Scan path examples for %s condition with search : %s' %(conditions[target], search))
        

"""
Question 3 - Identify fixations based on velocity
Note: the below is an expanded version of qf.velocity_based_identification()
"""

# Variables
velocity_threshold = 430 # [ms] default value 100 degrees/sec --> 430 mm/s 
smooth_window      = 20  # sliding window for moving average smoothing [ms] 20 default value
duration_threshold = 80  # minimum fixation event duration [ms]  80 default value

# Plot eye movement path
plt.figure(3)
plt.subplot(1,4,1)
plt.plot(points[:,0],points[:,1])
plt.title("Scan path")
plt.tick_params(axis='both',which='both', bottom='off',top='off', left='off',right='off', labelbottom='off',labelleft='off')

# Calculate & Plot the velocities of path via the Euclidean distance between subsequent points.
plt.subplot(1,4,2)
plt.title("Processing stages")
veloc=[]
for k in range(len(points)-1):
    # euclidean distance
    ed = np.sqrt(np.sum((points[k,:]-points[k+1,:])**2))*sampling_rate
    veloc.append(ed)

veloc = veloc
plt.plot(veloc,label='raw velocities')
plt.xlabel('Point on Sample path')
plt.ylabel('Velocity [ms]')

# Smooth raw velocities with smoothing window (cleaning up the data)
velocity_sm = qf.moving_average(veloc, sampling_rate, smooth_window, 'same')
plt.plot(velocity_sm, label='smoothed velocities')
plt.legend()
plt.title('smoothing')

# NOTE: The following code gets rather complicated :)
# In summary the following code groups sample points into fixations.
# Grouping is done based on velocity thresholds.
# Sampling points exceeding this threshold indicate a saccade, below indicate a fixation.
# Subsequent thresholded sampling points with the same label are grouped into a single saccade/fixation respectively.
# By averaging the x-y coordinates of all the sampling points belong to one fixation we determine the centre of that fixation.
# By adding all the duration of individual sampling points we calculate the duration of the fixation (e.g. sample frequency = 350Hz, fixation 80 samples long, sample_duration = 1000/350 = 2.86ms, 80*2.86 = 229 )
# This average for the fixation group is stored in the array fixations. 

# Isolate velocities less than velocity threshold as fixations  (i.e. fixation velocities = 1, saccades = 0)
fix_velocities = np.array(velocity_sm < velocity_threshold, dtype = int)
# Acts as high-pass filter for velocities above threshold.
plt.subplot(1,4,3)
plt.plot(fix_velocities,label='threshold window')
plt.title('thresholding')
plt.ylim([-0.5,1.5])

# Find difference between subsequent fixations with: out[n] = a[n+1] - a[n], this sets the first point in the fixation to be -1 and end point to be 1
fixation_index = np.diff(fix_velocities)
plt.plot(fixation_index,label='fixation index')
plt.ylim([-1.5,1.5])
plt.legend()

# Extract fixation start locations (np.where()[0] gets array of locations), add 1 index because difference-vector index shifted by one element
fix_start = np.where(fixation_index == 1)[0]+1

# Assume that eye movements start with fixation (i.e. velocity zero)
fix_start = np.r_[0, fix_start]

# Extract fixation end locations
nsamples = len(velocity_sm)    
fix_end   = np.nonzero(fixation_index == -1)[0]+1
fix_end   = np.r_[fix_end, nsamples]

if fix_velocities[-1] == 0:
    fix_end = fix_end[:-1]
if fix_velocities[0] == 0:
    fix_start = fix_start[1:]

# Recombine fixation start and end point into indicies
fix_index = np.c_[fix_start, fix_end]

# eliminate fixations with a duration less than critical threshold value
critical_duration = duration_threshold * sampling_rate/1000
fix_dur   = fix_index[:,1]-fix_index[:,0]
fix_index = fix_index[fix_dur>critical_duration,:] # Indicies of fixation

# Convert indices into positions, averaging the points withing a fixation region
n_fix  = fix_index.shape[0]
if n_fix == 0:
    fixations = af.nans((1,5))
else:
    f_dur  = np.diff(fix_index) * (1000 / sampling_rate)
    s_dur  = (fix_index[1:,0] - fix_index[:-1,1]) * (1000 / sampling_rate)
    x_pos = [np.mean(points[fix_index[k,0] :fix_index[k,1], 0]) for k in range(n_fix)]
    y_pos = [np.mean(points[fix_index[k,0] :fix_index[k,1], 1]) for k in range(n_fix)]
    
    fixations = np.c_[range(n_fix), f_dur, np.r_[s_dur, np.nan],  x_pos, y_pos]

plt.subplot(1,4,4)
plt.plot(points[:,0], points[:,1])
plt.plot(fixations[:,3], fixations[:,4], 'ro')
plt.title('Path with fixation points')
plt.tick_params(axis='both',which='both', bottom='off',top='off', left='off',right='off', labelbottom='off',labelleft='off')

"""
Question 4 - Path quantification - dispersion based 
"""

# There is an observation that samples with low velocities tend to cluster.
# This method classifies fixations as groups of consecutive points with a set dispersion.
# The dispersopm threshold is the maximum seperation of consecutive points.
# So sample points will be grouped into a fixation when the average of their maximum x & y distances remain under a certain threshold distance.
# Full routine methods can be seen in quant_funcs.py

# Variables
min_duration=100
dispersion_threshold=1 #[100-200]ms

# Extract fixations used dispersion based method
fixations_disp = qf.dispersion_based_identification(points, dispersion_threshold, min_duration, sampling_rate)

plt.figure(4)
plt.plot(points[:,0], points[:,1])
plt.plot(fixations_disp[:,3], fixations_disp[:,4], 'ro')
plt.title("Dispersion based")
plt.tick_params(axis='both',which='both', bottom='off',top='off', left='off',right='off', labelbottom='off',labelleft='off')




data_samples=points
