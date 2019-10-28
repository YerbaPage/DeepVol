import numpy as np
import tensorflow as tf
from scipy.stats import multivariate_normal as normal


class Equation(object):
    """Base class for defining PDE related function."""

    def __init__(self, dim, total_time, num_time_interval):
        self._dim = dim
        self._total_time = total_time
        self._num_time_interval = num_time_interval
        self._delta_t = (self._total_time + 0.0) / self._num_time_interval
        self._sqrt_delta_t = np.sqrt(self._delta_t)
        self._y_init = None

    def sample(self, num_sample):
        """Sample forward SDE."""
        raise NotImplementedError

    def f_tf(self, t, x, y, z):
        """Generator function in the PDE."""
        raise NotImplementedError

    def g_tf(self, t, x):
        """Terminal condition of the PDE."""
        raise NotImplementedError

    @property
    def y_init(self):
        return self._y_init

    @property
    def dim(self):
        return self._dim

    @property
    def num_time_interval(self):
        return self._num_time_interval

    @property
    def total_time(self):
        return self._total_time

    @property
    def delta_t(self):
        return self._delta_t


def get_equation(name, dim, total_time, num_time_interval):
    try:
        return globals()[name](dim, total_time, num_time_interval)
    except KeyError:
        raise KeyError("Equation for the required problem not found.")


class AllenCahn(Equation):
    def __init__(self, dim, total_time, num_time_interval):
        super(AllenCahn, self).__init__(dim, total_time, num_time_interval)
        self._x_init = np.zeros(self._dim)
        self._sigma = np.sqrt(2.0)

    def sample(self, num_sample):
        dw_sample = normal.rvs(size=[num_sample,
                                     self._dim,
                                     self._num_time_interval]) * self._sqrt_delta_t
        x_sample = np.zeros([num_sample, self._dim, self._num_time_interval + 1])
        x_sample[:, :, 0] = np.ones([num_sample, self._dim]) * self._x_init
        for i in range(self._num_time_interval):
            x_sample[:, :, i + 1] = x_sample[:, :, i] + self._sigma * dw_sample[:, :, i]
        return dw_sample, x_sample

    def f_tf(self, t, x, y, z):
        return y - tf.pow(y, 3)

    def g_tf(self, t, x):
        return 0.5 / (1 + 0.2 * tf.reduce_sum(tf.square(x), 1, keep_dims=True))


class HJB(Equation):
    def __init__(self, dim, total_time, num_time_interval):
        super(HJB, self).__init__(dim, total_time, num_time_interval)
        self._x_init = np.zeros(self._dim)
        self._sigma = np.sqrt(2.0)
        self._lambda = 1.0

    def sample(self, num_sample):
        dw_sample = normal.rvs(size=[num_sample,
                                     self._dim,
                                     self._num_time_interval]) * self._sqrt_delta_t
        x_sample = np.zeros([num_sample, self._dim, self._num_time_interval + 1])
        x_sample[:, :, 0] = np.ones([num_sample, self._dim]) * self._x_init
        for i in range(self._num_time_interval):
            x_sample[:, :, i + 1] = x_sample[:, :, i] + self._sigma * dw_sample[:, :, i]
        return dw_sample, x_sample

    def f_tf(self, t, x, y, z):
        return -self._lambda * tf.reduce_sum(tf.square(z), 1, keep_dims=True)

    def g_tf(self, t, x):
        return tf.log((1 + tf.reduce_sum(tf.square(x), 1, keep_dims=True)) / 2)


class PricingOption(Equation):
    def __init__(self, dim, total_time, num_time_interval):
        super(PricingOption, self).__init__(dim, total_time, num_time_interval)
        self._x_init = np.ones(self._dim) * 100
        self._sigma = 0.2
        self._mu_bar = 0.06
        self._rl = 0.04
        self._rb = 0.06
        self._alpha = 1.0 / self._dim

    def sample(self, num_sample):
        dw_sample = normal.rvs(size=[num_sample,
                                     self._dim,
                                     self._num_time_interval]) * self._sqrt_delta_t
        x_sample = np.zeros([num_sample, self._dim, self._num_time_interval + 1])
        x_sample[:, :, 0] = np.ones([num_sample, self._dim]) * self._x_init
        # for i in xrange(self._n_time):
        # 	x_sample[:, :, i + 1] = (1 + self._mu_bar * self._delta_t) * x_sample[:, :, i] + (
        # 		self._sigma * x_sample[:, :, i] * dw_sample[:, :, i])
        factor = np.exp((self._mu_bar-(self._sigma**2)/2)*self._delta_t)
        for i in range(self._num_time_interval):
            x_sample[:, :, i + 1] = (factor * np.exp(self._sigma * dw_sample[:, :, i])) * x_sample[:, :, i] # third index is time step
        return dw_sample, x_sample

    def f_tf(self, t, x, y, z):
        temp = tf.reduce_sum(z, 1, keep_dims=True) / self._sigma
        return -self._rl * y - (self._mu_bar - self._rl) * temp + (
            (self._rb - self._rl) * tf.maximum(temp - y, 0))

    def g_tf(self, t, x):
        temp = tf.reduce_max(x, 1, keep_dims=True)
        return tf.maximum(temp - 120, 0) - 2 * tf.maximum(temp - 150, 0)
    
    
# vectors in form of number of samples, dimensionality, and then time intervals
class PricingOptionNormal(Equation):
    def __init__(self, dim, total_time, num_time_interval):
        super(PricingOptionNormal, self).__init__(dim, total_time, num_time_interval)
        self._x_init = np.ones(self._dim) * 100;
        self._sigma = 0.2
        self._mu_bar = 0.04
        self._r = 0.04
        self._alpha = 1.0 / self._dim
    """    
    def sample(self, num_sample):
        dw_sample = normal.rvs(size=[num_sample,
                                     self._dim,
                                     self._num_time_interval]) * self._sqrt_delta_t
        x_sample = np.zeros([num_sample, self._dim, self._num_time_interval + 1])
        x_sample[:, :, 0] = np.ones([num_sample, self._dim]) * self._x_init
        
        print("x_sample", x_sample)
        # for i in xrange(self._n_time):
        # 	x_sample[:, :, i + 1] = (1 + self._mu_bar * self._delta_t) * x_sample[:, :, i] + (
        # 		self._sigma * x_sample[:, :, i] * dw_sample[:, :, i])
        factor = np.exp((self._mu_bar-(self._sigma**2)/2)*self._delta_t)
        for i in range(self._num_time_interval):
            x_sample[:, :, i + 1] = (factor * np.exp(self._sigma * dw_sample[:, :, i])) * x_sample[:, :, i] # third index is time step
        return dw_sample, x_sample

    def f_tf(self, t, x, y, z):
        return -self._r * y

    def g_tf(self, t, x):
        temp = tf.reduce_max(x, 1, keep_dims=True)
        return tf.maximum(temp - 120, 0)
    """
    def sample(self, num_sample):
        dw_sample = normal.rvs(size=[num_sample,
                                     self._num_time_interval]) * self._sqrt_delta_t
        x_sample = np.zeros([num_sample, self._num_time_interval + 1])
        x_sample[:, 0] = np.ones(num_sample) * self._x_init
        #print("xsample", x_sample)
        # for i in xrange(self._n_time):
        # 	x_sample[:, :, i + 1] = (1 + self._mu_bar * self._delta_t) * x_sample[:, :, i] + (
        # 		self._sigma * x_sample[:, :, i] * dw_sample[:, :, i])
        factor = np.exp((self._mu_bar-(self._sigma**2)/2)*self._delta_t)
        for i in range(self._num_time_interval):
            x_sample[:, i + 1] = (factor * np.exp(self._sigma * dw_sample[:, i])) * x_sample[:, i]
            
        #print("dw_sample", dw_sample)
        #print("x_sample", x_sample)
        #print("dim of dw", len(dw_sample))
        #print("dim of x_sample", len(x_sample))
        
        return np.reshape(dw_sample, (len(dw_sample), 1, self.num_time_interval)), np.reshape(x_sample, (len(x_sample), 1, self.num_time_interval + 1))

    def f_tf(self, t, x, y, z):
        #temp = tf.reduce_sum(z, 1, keep_dims=True) / self._sigma
        return -self._r * y

    def g_tf(self, t, x):
        temp = tf.reduce_max(x, 1, keep_dims=True)
        return tf.maximum(temp - 120, 0)
    
# vectors in form of number of samples, dimensionality, and then time intervals
class PricingOptionOneFactor(Equation):
    def __init__(self, dim, total_time, num_time_interval):
        super(PricingOptionOneFactor, self).__init__(dim, total_time, num_time_interval)
        self._num_assets = 1
        self._x_init = np.ones(self._num_assets) * 100
        self._r = 0.04
        
        self._y_init = np.ones(1) * 0.0989
        self._rho = -0.2949
        self._reversion_Rate = 0.7331
        self._mean_Rate = 0.3407
        self._vol_Of_Vol = 0.7068
        
        self._alpha = 1.0 / self._dim

    def sample(self, num_sample):
        dw_sample = normal.rvs([0, 0], [[self.delta_t, self._rho * self.delta_t], [self._rho * self.delta_t, self.delta_t]], size=[num_sample,
                                     self._num_time_interval])
        x_sample = np.zeros([num_sample, self._num_time_interval + 1])
        x_sample[:, 0] = np.ones(num_sample) * self._x_init
        
        y_sample = np.zeros([num_sample, self._num_time_interval + 1])
        y_sample[:, 0] = np.ones(num_sample) * self._y_init
        
        # for i in xrange(self._n_time):
        # 	x_sample[:, :, i + 1] = (1 + self._mu_bar * self._delta_t) * x_sample[:, :, i] + (
        # 		self._sigma * x_sample[:, :, i] * dw_sample[:, :, i])
        #factor = np.exp((self._mu_bar-(self._sigma**2)/2)*self._delta_t)
        for i in range(self._num_time_interval):
            y_sample[:, i + 1] = y_sample[:, i] + np.ones(num_sample) * self._reversion_Rate * self._mean_Rate * self.delta_t - self._reversion_Rate * np.maximum(y_sample[:, i], np.zeros(num_sample)) * self.delta_t + self._vol_Of_Vol * np.multiply(np.sqrt(np.maximum(y_sample[:, i], np.zeros(num_sample))), dw_sample[:, i, 1]) 
            x_sample[:, i + 1] = x_sample[:, i] * np.exp((np.ones(num_sample) * self._r - (np.power(np.maximum(y_sample[:, i + 1], np.zeros(num_sample)), 2)) / 2) * self.delta_t) * np.exp(np.multiply(np.sqrt(np.maximum(y_sample[:, i + 1], np.zeros(num_sample))), dw_sample[:, i, 0]))
   
        new_DW = np.zeros(shape = (0, self._dim, self._num_time_interval))
        for i in range(num_sample):
            currSample = dw_sample[i]
            currOne = currSample[:, 0] # gets the one used for W^(0) in stock price BM
            currTwo = currSample[:, 1] # gets the one used for W^(1) in vol process BM
            tempArray = np.ndarray(shape = (2, self._num_time_interval), buffer = np.append(currOne, currTwo))
            new_DW = np.append(new_DW, np.array([tempArray]), axis = 0)
            

        return new_DW, x_sample

    def f_tf(self, t, x, y, z):
        return -self._r * y

    def g_tf(self, t, x):
        temp = tf.reduce_max(x, 1, keep_dims=True)
        return tf.maximum(temp - 120, 0)


class PricingDefaultRisk(Equation):
    def __init__(self, dim, total_time, num_time_interval):
        super(PricingDefaultRisk, self).__init__(dim, total_time, num_time_interval)
        self._x_init = np.ones(self._dim) * 100.0
        self._sigma = 0.2
        self._rate = 0.02   # interest rate R
        self._delta = 2.0 / 3
        self._gammah = 0.2
        self._gammal = 0.02
        self._mu_bar = 0.02
        self._vh = 50.0
        self._vl = 70.0
        self._slope = (self._gammah - self._gammal) / (self._vh - self._vl)

    def sample(self, num_sample):
        dw_sample = normal.rvs(size=[num_sample,
                                     self._dim,
                                     self._num_time_interval]) * self._sqrt_delta_t
        x_sample = np.zeros([num_sample, self._dim, self._num_time_interval + 1])
        x_sample[:, :, 0] = np.ones([num_sample, self._dim]) * self._x_init
        for i in range(self._num_time_interval):
            x_sample[:, :, i + 1] = (1 + self._mu_bar * self._delta_t) * x_sample[:, :, i] + (
                self._sigma * x_sample[:, :, i] * dw_sample[:, :, i])
        return dw_sample, x_sample

    def f_tf(self, t, x, y, z):
        piecewise_linear = tf.nn.relu(
            tf.nn.relu(y - self._vh) * self._slope + self._gammah - self._gammal) + self._gammal
        return (-(1 - self._delta) * piecewise_linear - self._rate) * y

    def g_tf(self, t, x):
        return tf.reduce_min(x, 1, keep_dims=True)


class BurgesType(Equation):
    def __init__(self, dim, total_time, num_time_interval):
        super(BurgesType, self).__init__(dim, total_time, num_time_interval)
        self._x_init = np.zeros(self._dim)
        self._y_init = 1 - 1.0 / (1 + np.exp(0 + np.sum(self._x_init) / self._dim))
        self._sigma = self._dim + 0.0

    def sample(self, num_sample):
        dw_sample = normal.rvs(size=[num_sample,
                                     self._dim,
                                     self._num_time_interval]) * self._sqrt_delta_t
        x_sample = np.zeros([num_sample, self._dim, self._num_time_interval + 1])
        x_sample[:, :, 0] = np.ones([num_sample, self._dim]) * self._x_init
        for i in range(self._num_time_interval):
            x_sample[:, :, i + 1] = x_sample[:, :, i] + self._sigma * dw_sample[:, :, i]
        return dw_sample, x_sample

    def f_tf(self, t, x, y, z):
        return (y - (2 + self._dim) / 2.0 / self._dim) * tf.reduce_sum(z, 1, keep_dims=True)

    def g_tf(self, t, x):
        return 1 - 1.0 / (1 + tf.exp(t + tf.reduce_sum(x, 1, keep_dims=True) / self._dim))


class QuadraticGradients(Equation):
    def __init__(self, dim, total_time, num_time_interval):
        super(QuadraticGradients, self).__init__(dim, total_time, num_time_interval)
        self._alpha = 0.4
        self._x_init = np.zeros(self._dim)
        base = self._total_time + np.sum(np.square(self._x_init) / self._dim)
        self._y_init = np.sin(np.power(base, self._alpha))

    def sample(self, num_sample):
        dw_sample = normal.rvs(size=[num_sample,
                                     self._dim,
                                     self._num_time_interval]) * self._sqrt_delta_t
        x_sample = np.zeros([num_sample, self._dim, self._num_time_interval + 1])
        x_sample[:, :, 0] = np.ones([num_sample, self._dim]) * self._x_init
        for i in range(self._num_time_interval):
            x_sample[:, :, i + 1] = x_sample[:, :, i] + dw_sample[:, :, i]
        return dw_sample, x_sample

    def f_tf(self, t, x, y, z):
        x_square = tf.reduce_sum(tf.square(x), 1, keep_dims=True)
        base = self._total_time - t + x_square / self._dim
        base_alpha = tf.pow(base, self._alpha)
        derivative = self._alpha * tf.pow(base, self._alpha - 1) * tf.cos(base_alpha)
        term1 = tf.reduce_sum(tf.square(z), 1, keep_dims=True)
        term2 = -4.0 * (derivative ** 2) * x_square / (self._dim ** 2)
        term3 = derivative
        term4 = -0.5 * (
            2.0 * derivative + 4.0 / (self._dim ** 2) * x_square * self._alpha * (
                (self._alpha - 1) * tf.pow(base, self._alpha - 2) * tf.cos(base_alpha) - (
                    self._alpha * tf.pow(base, 2 * self._alpha - 2) * tf.sin(base_alpha)
                    )
                )
            )
        return term1 + term2 + term3 + term4

    def g_tf(self, t, x):
        return tf.sin(
            tf.pow(tf.reduce_sum(tf.square(x), 1, keep_dims=True) / self._dim, self._alpha))


class ReactionDiffusion(Equation):
    def __init__(self, dim, total_time, num_time_interval):
        super(ReactionDiffusion, self).__init__(dim, total_time, num_time_interval)
        self._kappa = 0.6
        self._lambda = 1 / np.sqrt(self._dim)
        self._x_init = np.zeros(self._dim)
        self._y_init = 1 + self._kappa + np.sin(self._lambda * np.sum(self._x_init)) * np.exp(
            -self._lambda * self._lambda * self._dim * self._total_time / 2)

    def sample(self, num_sample):
        dw_sample = normal.rvs(size=[num_sample,
                                     self._dim,
                                     self._num_time_interval]) * self._sqrt_delta_t
        x_sample = np.zeros([num_sample, self._dim, self._num_time_interval + 1])
        x_sample[:, :, 0] = np.ones([num_sample, self._dim]) * self._x_init
        for i in range(self._num_time_interval):
            x_sample[:, :, i + 1] = x_sample[:, :, i] + dw_sample[:, :, i]
        return dw_sample, x_sample

    def f_tf(self, t, x, y, z):
        exp_term = tf.exp((self._lambda ** 2) * self._dim * (t - self._total_time) / 2)
        sin_term = tf.sin(self._lambda * tf.reduce_sum(x, 1, keep_dims=True))
        temp = y - self._kappa - 1 - sin_term * exp_term
        return tf.minimum(tf.constant(1.0, dtype=tf.float64), tf.square(temp))

    def g_tf(self, t, x):
        return 1 + self._kappa + tf.sin(self._lambda * tf.reduce_sum(x, 1, keep_dims=True))

