import numpy as np
import random
from PIL import Image
import os

"""
Auxiliary functions for data manipulation and conversion
"""

__all__ = ['get_trials', 'raw_to_trial', 'samples_to_ms', 'samples_to_ms_coord',
 'transform_coord', 'data_to_dict', 'get_subset',  'fix_index_to_fixations',
 'polar2cart','extract_time_positions','get_positions','create_display']

def get_trials(data, start, end):
    """
    Formatting function which splits the data into trials and removes the header.
    
    Parameters
    ----------
    data : string
        input data 
    start : int
        start point
    end : int
        end point trial identifier strings
    
    Returns
    ----------
    trials : string
        restructured data list
    """
    if data.find(start) == -1:
        print 'wrong trial identifier, try other than %s' %start
    trial_start = data.split(start)
    trials      = [ trl[:trl.index(end)] for trl in trial_start[1:] ]
    return trials


def raw_to_trial(trial):
    """
    extract from trial: time, xpos, ypos
    add trl_id and blk_id
    
    Parameters
    ----------
    trial : list
        trial number
    
    Returns
    ----------
    trl_samples : ndarray
        
    """
    trl_events  = trial.split("\n")
    trl_number  = np.int(trl_events[0].strip('_'))
    trl_samples = trl_events[1:-1]
    trl_samples = [t.split('\t') for t in trl_samples]
    trl_samples = [[trl_number, np.float(t[0]), np.float(t[1]), np.float(t[2])] for t in trl_samples if t[1].strip() != '.']
    return np.array(trl_samples)


def samples_to_ms(samples):
    """
    Time transformation
    
    Parameters
    ----------
    samples : 
    
    
    Returns
    ----------
    time : 
        
    """
    time = samples/1000.
    time = time-time[0]
    return time


def transform_coord(vector, position):
    """
    from [0,0] lower left to [0,0] in center
    
    Parameters
    ----------
    vector : 
    
    position : 
    
        
    Returns
    ----------
    new_pos :   
        
    """
    new_pos = vector-position
    return new_pos


def samples_to_ms_coord(trial_data, xpos, ypos):
    """
    Parameters
    ----------
    trial_data : 
        
    x_pos : 
        
    y_pos : 
    
    
    Returns
    ----------
    trial_data : 
        
    """
    trial_data[:,0] = samples_to_ms(trial_data[:,0])
    trial_data[:,1] = transform_coord(trial_data[:,1], xpos)
    trial_data[:,2] = transform_coord(trial_data[:,2], ypos)
    return trial_data


def data_to_dict(fname):
    """
    read tab separated data columns with headerline from logfile into dictionary
    
    Parameters
    ----------
    fname : 
            
    Returns
    ----------
    data_frame : 
        
    """
    if not os.path.isfile(fname):
        data_frame = 0
        print 'file does not exist'
    else:
        header = open(fname, 'r').readline().strip('\n\r').split('\t')
        data   = np.loadtxt(fname, skiprows = 1)
        data_frame = {}
        for var, var_name in enumerate(header):
            data_frame[var_name] = data[:,var]
    return data_frame


def get_subset(data, subset_variable, subset_value, subset_operator='eq'):
    """
    get subset of dictionary according to condition in one variable
    
    Parameters
    ----------
    data : 
        original dictionary
    subset_variable :
        key of variable
    subset_value : 
        value of condition
    subset_operator : 
    Values: eq - default, ue - unequal, gt - greater than, st - smaller than
   
    
    Returns
    ----------
    sub_data : 
        
     """
    sub_data = {}
    for var in data.keys():
        if subset_operator == 'eq':
            sub_data[var] = data[var][data[subset_variable] == subset_value]
        elif subset_operator == 'ue':
            sub_data[var] = data[var][data[subset_variable] != subset_value]
        elif subset_operator == 'gt':
            sub_data[var] = data[var][data[subset_variable] > subset_value]
        elif subset_operator == 'st':
            sub_data[var] = data[var][data[subset_variable] < subset_value]
    return sub_data


def millisecs_to_nsamples(ms, sampling_rate):
    """
    convert duration threshold in ms into duration threshold in number of sampling points
    Parameters
    ----------
    ms : 
        minimal fixation duration in ms
    sampling_rate : 
        sampling rate in number of samples per second
    
    Returns
    ----------
    minimal fixation duration in number of samples
    """
    return np.int(ms * sampling_rate/1000.)


def del_artefact(currwindow, xlim=640, ylim=512):
    """
    artefact removal based on geometry of screen,
    excludes x- and y-positions that are outside the screen coordinates
    Parameters
    ----------
    currwindow :    
        3 columns of raw data
    xlim :
        limits in x- and y-direction
    ylim : 
        
    Returns
    ----------
    currwindow : 
    3 columns of raw data with outliers removed
    """
    x = currwindow[:,0]
    y = currwindow[:,1]
    xdir = np.logical_and(np.greater(x, -xlim), np.less(x, xlim))
    ydir = np.logical_and(np.greater(y, -ylim), np.less(y, ylim))
    valid_idx = np.logical_and(xdir, ydir)
    return currwindow[valid_idx,:]





def pixel_to_degree(size_pixel, screen_pixel=[1920., 1200.], screen_mm=[518., 324.], view_dist=600.):
    """
    convert pixel into degrees of visual angle
    
    Parameters
    ----------
    pixel : 
        size in pixels
    screen_pixel :
        
    screen_mm : 
        
    view_dist in mm :   
        
    
    Returns
    ----------
    alpha : 
        angle in degrees
    
    """
    alpha_mm = size_pixel/(screen_pixel[0]/screen_mm[0])
    alpha    = np.degrees(2 * np.arctan2( alpha_mm, 2 * view_dist))
    return alpha


def pixel_to_mm(x, screen_pixel=1920., screen_mm=518.):
    """

    Parameters
    ----------
    x : 
        size in pixel
    screen_pixel : 
        screen size in pixel
    screen_mm :
        screen size in mm
    
    Returns
    ----------
    x :
    size in mm
    """
    return screen_mm/screen_pixel * x


def mm_to_visangle(x, view_distance=600.):
    """
    Parameters
    ----------
    x :
    size in mm
    view_distance :
    in mm
    
    Returns
    ----------
    x : 
    size in degree visual angle
    """
    return np.degrees(2 * np.arctan2(x, 2 * view_distance))



def fix_index_to_fixations(data_samples, fix_index, sampling_rate=1000.):
    """
    
    Parameters
    ----------
    data_samples : 
    
    fix_index :
    
    sampling_rate : float
        default = 1000.
    
    Returns
    ----------
    fixations : 
        
    """
    n_fix  = fix_index.shape[0]
    if n_fix == 0:
        fixations = nans((1,5))
    else:
        f_dur  = np.diff(fix_index) * (1000 / sampling_rate)
        s_dur  = (fix_index[1:,0] - fix_index[:-1,1]) * (1000 / sampling_rate)
        x_pos = [np.mean(data_samples[fix_index[k,0] :fix_index[k,1], 0]) for k in range(n_fix)]
        y_pos = [np.mean(data_samples[fix_index[k,0] :fix_index[k,1], 1]) for k in range(n_fix)]
        
        fixations = np.c_[range(n_fix), f_dur, np.r_[s_dur, np.nan],  x_pos, y_pos]
    return fixations


def nans(shape, dtype=float):
    """
    Creates a numpy array of given size containing NaN
    
    Parameters
    ----------
    shape : list
        shape of array [x,y]
    dtype : type
        data type of output
    Returns
    ----------
    a : ndarray (float64)
        array containing nans
    
    """
    a = np.empty(shape, dtype)
    a.fill(np.nan)
    return a

def polar2cart(r, theta):
    """
    Converts polar coordinates to cartesian coordinates. 
    Different frames of references in which the eye movements are described
    
    Parameters
    ----------
    r : array_like
        Radial coordinate *radius
    theta : array_like
        Angular coordinate *angle
    
    Returns
    ----------
    (x,y) : array_like
        Cartesian coordinates *position
    """
    x = r * np.cos(np.radians(theta))
    y = r * np.sin(np.radians(theta))
    return (x, y)
    
def extract_time_positions(id='mm',sess=1):    
    """
    Conversion function from raw data into time vs position data.
    
    Parameters
    ----------    
    id : string
        values == ['ipa','ipr',kvdb','mm','sk','to','tp','vf']
    sess : int
        values == [1:5]
        
    Returns
    ----------
    writes 'ID_SESS_eye.txt' file.
    """     
    
    # read raw data files into string variable d
    d = open('%s/%s_%d.asc' %(id, id, sess)).read()
    
    # separate raw data into list of trials
    raw_trials = get_trials(d, 'trial_start', 'BUTTON')
    
    all_trials = []
    
    for trl_nr, raw_trial in enumerate(raw_trials):
        print trl_nr
        # single trial conversion list into numpy array
        trial_data = raw_to_trial(raw_trial)
        
        # single trial conversion of samples into timesteps and screen coordinates
        trial_data[:,1:] = samples_to_ms_coord(trial_data[:,1:], 960, 600)
        
        all_trials.append(trial_data)
    
    all_trials = np.concatenate(all_trials, axis=0)
    
    # write dataout in text file
    out = open('%s/%s_%d_eye.txt' %(id, id, sess), 'w')
    out.write('blk time xpos ypos\n')
    np.savetxt(out, all_trials, fmt='%d %1.5f %1.2f %1.2f', delimiter='\t')
    out.flush()
    out.close()
    #return print "File conversion saved"
    

def get_positions(nitems, offset, radius=400):
    """
    Determines the [x,y] positions of search items given the number of items, 
    any rotational offset and the radius of search circle area.
    
    Parameters
    -----------    
    nitems : int
        Number of items
    offset : int
        Rotational offset of items
    radius : int, optional
        Radius with default value
    
    Returns
    ----------
    screen positions : dict
        x & y coordinates for each item
    
    """
    positions     = np.arange(1, 360, 360/float(nitems))
    positions_off = positions + offset
    
    screen_positions = {'x': [], 'y': []}
    
    for k in np.arange(nitems):
        #print k, positions_off[k]
        x, y = polar2cart(radius, positions_off[k])
        screen_positions['x'].append(x)
        screen_positions['y'].append(y)
    return screen_positions


def create_display(log_data, trial, target=False):
    """
    Plots the background image stimuli, given the condition number, number of 
    items, item figure type and rotational offset, upon which the eye tracking 
    path is plotted.
    
    Parameters
    -----------
    log_data : array_like
        input data
    trial : int
        experimental trial number
    target : boolean, optional
        default - False
    
    Returns
    -----------
    im_base : array_like
        output stimuli (underlay)
    
    """
    conditions = {0: 'misaligned', 1: 'aligned', 2: 'filled', 3: 'noinducer'}
    
    # "[log_data['trial'] == trial])" selects trial number
    cond    = np.int(log_data['target'][log_data['trl'] == trial])
    n_items = log_data['nitems'][log_data['trl'] == trial]
    offset  = log_data['rot_offset'][log_data['trl'] == trial]
    positions = get_positions(n_items, offset)
    
    targ_x = log_data['tpos_x'][log_data['trl'] == trial]
    targ_y = log_data['tpos_y'][log_data['trl'] == trial]
    
    im_base = Image.new('L', (1920, 1200), 128)
    if random.randint(0,1) == 1:
        dist_type = 'thin'
        #targ_type = 'fat'
    else:
        dist_type = 'fat'
        #targ_type = 'thin'
    
    im_distractor = Image.open('../stimuli/norm_%s_%s_10.bmp' %(dist_type, conditions[cond]))
    new_dist   = im_distractor.resize((110,110))
    
    loc_offset = 55
    for k in np.arange(np.int(n_items)):
        xpos = np.round(positions['x'][k])+960
        ypos = np.round(positions['y'][k])+600
        ul_x = np.int(min(xpos+loc_offset, xpos-loc_offset))
        ul_y = np.int(min(ypos+loc_offset, ypos-loc_offset))
        lr_x = np.int(max(xpos+loc_offset, xpos-loc_offset))
        lr_y = np.int(max(ypos+loc_offset, ypos-loc_offset))
        
        im_base.paste(new_dist, (ul_x, ul_y, lr_x, lr_y))
    
    if target:
        #im_target     = Image.open('../stimuli/norm_fat_aligned_10.bmp')
        #new_target = im_target.resize((110,110))
        t_ul_x = np.int(min(targ_x+55, targ_x-55))
        t_ul_y = np.int(min(targ_y+55, targ_y-55))
        t_lr_x = np.int(min(targ_x+55, targ_x-55))
        t_lr_y = np.int(min(targ_y+55, targ_y-55))
        im_base.paste(new_dist, (t_ul_x, t_ul_y, t_lr_x, t_lr_y))
    
    return im_base