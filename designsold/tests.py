import numpy as np
from . import common
from itertools import cycle, islice

def wall_collision_test(**kwargs):
    walls = [[[.5, 0.], [.5, 1.]]]
    return common.Design(
            id='box',
            lights=np.array([[0., 0., 1.]]),
            walls=np.array(walls),
            centers=[[[0., 0.]]],
            radii=[[0.]],
            lowers=[[0.]],
            uppers=[[0.]],
            **kwargs) 

def agent_collision_test(**kwargs):
    walls = [[[2., 2.], [2., 3.]]]
    return common.Design(
            id='box',
            lights=np.array([[0., 0., 1.]]),
            walls=walls,
            centers=[[[0., 0.], [1., 0.]]],
            radii=[[0., 0.]],
            lowers=[[0., 180.]],
            uppers=[[0., 180.]])

def agent_frame_test(**kwargs):
    walls = [[[2., 2.], [2., 3.]]]
    return common.Design(
            id='box',
            lights=np.array([
                        [0., +.5, 1.],
                        [0., -.5, 1.], 
                        [-.5, 0., 1.], 
                        [+.5, 0., 1.]]),
            walls=walls,
            centers=[[[0., 0.]]],
            radii=[[0.,]],
            lowers=[[0.]],
            uppers=[[0.]])
