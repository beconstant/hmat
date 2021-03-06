import numpy as np

class BlackBox(object):
    def __init__(self, func, shape=None, perm=None, dtype=None, array_based=False):
        if type(func) == BlackBox:
            # copy constructor
            self.func = func.func
            self.shape = func.shape
            self.perm = None if func.perm is None else func.perm.copy()
            self.array_based = func.array_based
            self.dtype = func.dtype
        elif type(func) == np.ndarray:
            BlackBox.__init__(self,
                              lambda indices: func[indices],
                              shape=func.shape, perm=perm, dtype=func.dtype, array_based=True)
        else:
            self.func = func
            self.shape = shape
            self.perm = perm.copy() if perm is not None else None
            self.dtype = dtype if dtype is not None else np.float
            self.array_based = array_based

    def normalize(self, index, i):
        if type(index) == slice:
            start = index.start if index.start is not None else 0
            stop = index.stop if index.stop is not None else self.shape[i]
            step = index.step if index.step is not None else 1
            return np.arange(start, stop, step)

    def indices_unveil(self, indices):
        indices = np.asarray(indices)
        return np.vstack([np.repeat(indices[0], indices[1].size),
                   np.tile(indices[1], indices[0].size)]).T

    def permutate(self, perm):
        if self.perm is None:
            self.perm = perm.copy()
        else:
            self.perm = perm[self.perm].copy()

    def full_matrix(self):
        return self.__getitem__((slice(None, None, None), slice(None, None, None)))

    def __getitem__(self, indices):
        # TODO if func is ndarray, do we need to copy it values?
        if self.array_based:
            return self.func(indices)
        else:
            if type(indices) == int:
                return self.__getitem__((np.array([indices]), slice(None, None, None)))[0]
            if type(indices) == slice:
                return self.__getitem__((np.asarray(self.normalize(indices, 0)), slice(None, None, None)))
            indx, indy = indices[0], indices[1]
            if type(indx) == slice:
                indx = np.asarray(self.normalize(indx, 0))

            if type(indy) == slice:
                indy = np.asarray(self.normalize(indy, 1))

            if np.isscalar(indx):
                if np.isscalar(indy):
                    return self.func(np.array([indx, indy])[np.newaxis, :])[0]
                else:
                    if self.perm is not None:
                        indx = self.perm[indx]
                    return self.func(np.vstack([np.ones(len(indy))*indx, indy]).T)
            else:
                if self.perm is not None:
                    indx = self.perm[indx]
                if np.isscalar(indy):
                    return self.func(np.vstack([indx, np.ones(len(indx))*indy]).T)
                else:
                    if self.perm is not None:
                        indy = self.perm[indy]
                    if (len(indx) == 1 and len(indy) == 1):
                        return self.func(np.vstack(self.indices_unveil((indx, indy)))).reshape((len(indx), len(indy)))[0]
                    return self.func(self.indices_unveil((indx, indy))).reshape((len(indx), len(indy)))


def blackbox_test():
    def eq(a, b):
        return np.array_equal(a, b)


    A = np.random.random((10, 10))
    b = BlackBox(A)

    assert eq(b[:, :], A[:, :])
    assert eq(b[:, 1], A[:, 1])
    assert eq(b[:, [1, 2]], A[:, [1, 2]])
    assert eq(b[1, :], A[1, :])
    assert eq(b[[1, 2], :], A[[1, 2], :])
    assert eq(b[1, 2], A[1, 2])
    assert eq(b[[1], [2]], A[[1], [2]])
    assert eq(b[::2, ::3], A[::2, ::3])