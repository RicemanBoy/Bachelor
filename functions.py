import numpy as np

def gen_data(name):
    x = [0,1,2,3,4,5,5,6,7,8,9]
    y = [0,1,2,3,4,5,5,6,7,8,9]

    data = np.array((x,y))
    np.savetxt("skibidi{}.txt".format(name), data, delimiter=",")
