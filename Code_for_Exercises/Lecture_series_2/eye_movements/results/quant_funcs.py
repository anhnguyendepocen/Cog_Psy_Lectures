import numpy as np
import aux_funcs as af
import pandas as pd

"""
Quantification functions for eye movement paths

"""

__all__ = [ 'calc_veloc', 'moving_average', 'velocity_based_identification','dispersion_based_identification' ]

def calc_veloc(raw_path):
    """
    Calculates point-to-point velocities along path, as the euclidian
    distance. (v=d/t, where t is the constant sampling rate)
    
    Parameters
    ----------
    raw_path : array_like (2 columns)
        Array containing containing x and y positions of eye tracking data 
    
    Returns
    ----------
    veloc : array_like (1 columns)
        Array containing the velocity as the euclidean distance between subsequent 
        points along the scan path.
    """
    veloc=[]
    for k in range(len(raw_path)-1):
        # euclidean distance
        ed = np.sqrt(np.sum((raw_path[k,:]-raw_path[k+1,:])**2))
        veloc.append(ed)
    return np.array(veloc)


def moving_average(velocity_samples, sampling_rate, window_size=None, mode=None):
    """
    smoothing of velocity samples with rectangular window of window_size
    
    Parameters
    ----------
    velocity_samples :
        difference vector (n-1) of original samples (n)
    sampling_rate :
        
    window_size :
    input in ms, smooth_window is converted into samples
    mode :
        one of 'full', 'valid', 'same'
    
    Returns
    ----------
    smoothed_velocity : 
        
    """
    smooth_window = round(window_size * sampling_rate/1000)
    window = np.ones(smooth_window)
    smoothed_velocity = np.convolve(velocity_samples, window, mode)/smooth_window
    return smoothed_velocity 


def velocity_based_identification(data_samples, velocity_threshold, duration_threshold,  smooth_window, sampling_rate=1000.):
    """
    Also known as velocity-threshold fixation identification (I-VT), this function
    seperates fixations from saccades based on their point-to-point velocities
    
    - Low velocity for fixations : <100 deg/sec
    - High velocity for saccades : >300 deg/sec
    
    fixations < velocity_threshold & > duration_threshold
    
    Parameters
    ----------
    data_samples : array_like
        x- and y-pos of each sample in deg visual angle
    sampling_rate : float
        number of samples/second
    velocity_threshold : int
        velocity in deg/sec < fixations [20 degress/sec Sen & Megaw]
    duration_threshold : int
        minimum duration of a fixation [ms]
    smooth_window : int
        size of smoothing window
    
    Returns
    ----------
    fixations : array_like
        Array of fixation points
        
    """
    # calculate point-to-point velocities
    velocity = calc_veloc(data_samples * sampling_rate)
    
    # smooth raw velocities with smoothing window
    velocity = moving_average(velocity, sampling_rate, smooth_window, 'same')
    
    # isolate velocities less than velocity threshold as fixations
    fix_velocities = np.array(velocity < velocity_threshold, dtype = int)
        
    # difference between subsequent velocities (out[n] = a[n+1] - a[n])
    fixation_index = np.diff(fix_velocities)
    
    # locations of where a change in velocity == 1
    # np.where()[0] gets array of locations
    fix_start = np.where(fixation_index == 1)[0]+1
    
    # assumption that eye movements start with fixation (i.e. velocity zero)
    fix_start = np.r_[0, fix_start]
    
    # add 1 index because difference-vector index shifted by one element
    nsamples = len(velocity)    
    fix_end   = np.nonzero(fixation_index == -1)[0]+1
    fix_end   = np.r_[fix_end, nsamples]
    
    if fix_velocities[-1] == 0:
        fix_end = fix_end[:-1]
    
    if fix_velocities[0] == 0:
        fix_start = fix_start[1:]
    
    fix_index = np.c_[fix_start, fix_end]
    
    # eliminate fixations with DUR < dur_crit ms
    critical_duration = duration_threshold * sampling_rate/1000
    fix_dur   = fix_index[:,1]-fix_index[:,0]
    fix_index = fix_index[fix_dur>critical_duration,:] # Indicies of fixation
    
    fixations = af.fix_index_to_fixations(data_samples, fix_index, sampling_rate)
    return fixations


def dispersion_based_identification(data_samples, dispersion_threshold, duration_threshold, sampling_rate=1000.):
    """
    As fixations are low velocity, they tend to cluster. This method classifies
    fixations based on maximum cluster seperation. In other words, it computes
    fixations based on dispersion of sample points and minimum duration
    
    disperson = mean(max_horizontal_distance, max_vertical_distance)
    or D = (max(x)-min(x)) + (max(y)-min(y))
    
    Parameters
    ----------
    data_samples : 
        
    dispersion_threshold : 
        [deg/ visual angle]
    duration_threshold : 
        [ms]
    
    Returns
    ----------
    fixations :
        
    """
    data_samples_or = data_samples.copy()

    # Convert number of sample points into milliseconds
    duration_threshold_in = af.millisecs_to_nsamples(duration_threshold, sampling_rate)
    
    # Initialise arrays
    sacc_samples = 0
    fix_end   = 0
    fix_index = []
    
    # while there are still points (1 point removed through each iteration)
    while data_samples.shape[0] >= duration_threshold_in:
        
        # Initiate duration length (to be increased)
        duration_samples = duration_threshold_in
        
        # Extract window from data set
        window    = data_samples[:duration_samples,:]
    
        # calculate maximal horizontal and vertical distances, to calculate dispersion
        d_x = np.abs(np.max(window[:,0])-np.min(window[:,0]))
        d_y = np.abs(np.max(window[:,1])-np.min(window[:,1]))
        distances = np.array([d_x, d_y])
    
        # If disperson of window points <= threshold
        if np.mean(distances) <= dispersion_threshold:
        
            # While dispersion of window points <= threshold 
            # Keep adding points to cluster until dispersion exceeds maximum distance threshold
            while np.mean(distances) <= dispersion_threshold:
                duration_samples +=1 # increase window size by 1 each iteration
                if duration_samples > data_samples.shape[0]:
                    break
                window    = data_samples[:duration_samples,:]
                
                ## calculate distance
                d_x = np.abs(np.max(window[:,0])-np.min(window[:,0]))
                d_y = np.abs(np.max(window[:,1])-np.min(window[:,1]))
                distances = np.array([d_x, d_y])
            
            # Store indices of fixations
            fix_start = fix_end + sacc_samples
            fix_end   = fix_start + (duration_samples-1)
            sacc_samples = 0
            fix_index.append([fix_start, fix_end])
            
            # Remove window point from points
            data_samples = data_samples.take(np.arange(duration_samples, data_samples.shape[0]), axis=0)
        else:
            # Remove first point from points
            data_samples = data_samples.take(np.arange(1, data_samples.shape[0]), axis=0)
            sacc_samples +=1
    
    # Extract fixations from data samples using the stored indicies
    fixations = af.fix_index_to_fixations(data_samples_or, np.array(fix_index), sampling_rate)
    return fixations
        


def detect_fixations(id,sess=4, fix_algorithm ='velocity',sampling_rate = 1000.0,min_duration  = 100,smooth_window = 30, velocity_threshold = 50,dispersion_threshold = 1  ):
    """
    Use pre-defined thresholding functions to detect fixations.
    
    Parameters
    ----------
    id : string
        participant identification string
    sess : int
        block number default = 4
    fix_algorithm : string
        Either 'velocity' or 'dispersion'
    sampling_rate : float
        sampling rate [Hz] default = 1000.0
    min_duration : int
        minimum fixation duration [ms] default = 100
    smooth_window : int
        smoothing window [ms] default = 30
    velocity_threshold : int
        velocity threshold [deg/sec] default = 50
    dispersion_threshold : int
        dispersion threshold [deg/ visual angle] default = 1 
    
    Returns
    ----------
    """    
    #bdata = af.data_to_dict('%s/%s_%d' %(id, id, sess))
    edata=pd.read_csv('%s/%s_%d_eye.txt' %(id, id, sess),names=['blk','time','xpos','ypos'],skiprows=1,sep=' ')
    edata=np.asarray(edata)
    
    fix_out = np.array([])
    
    for trl in np.arange(1, 481):
        print('working on %s fixation_type %s' %(id, fix_algorithm))
        eye_trial = edata[edata[:,0] == trl,]
        # convert eye positions from pixels into deg visual angle
        points = af.mm_to_visangle( af.pixel_to_mm( eye_trial[:,2:4] ) )
        
        # blink detection and exclusion
        n_samples = points.shape[0]
        points_clean = af.del_artefact(points, xlim=24, ylim=15)
        n_samples_clean = points_clean.shape[0]
        if (n_samples - n_samples_clean) > 0:
            fixations = af.nans((1,5))
        else:
            if fix_algorithm == 'velocity':
                fixations = velocity_based_identification(points, velocity_threshold, min_duration,  smooth_window, sampling_rate)
            elif fix_algorithm == 'dispersion':
                fixations = dispersion_based_identification(points, dispersion_threshold, min_duration,  sampling_rate)
        
        if fix_out.shape[0] == 0:
            fix_out = np.c_[np.ones(fixations.shape[0]) * trl, fixations]
        else:
            fix_out = np.r_[fix_out, np.c_[np.repeat(trl, fixations.shape[0]), fixations]]
    
    
    # save file
    out = open('%s/%s_%d_%s.txt' %(id, id, sess, fix_algorithm), "w")
    out.write('# minimum duration: %d\n'     %min_duration)
    out.write('# smoothing window: %d\n'     %smooth_window)
    out.write('# velocity threshold: %d\n'   %velocity_threshold)
    out.write('# dispersion threshold: %d\n' %dispersion_threshold)
    out.write('trl fix_id fdur sdur xpos ypos\n')
    
    np.savetxt(out, fix_out, fmt='%d %1.2f %1.2f %1.2f %1.2f %1.2f', delimiter='\t')
    out.flush()
    out.close()
