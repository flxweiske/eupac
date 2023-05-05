import numpy as np
import itertools
from scipy.stats import multinomial


class EUPAC:
    def __init__(self, regret_window, algorithm):
        self.regret_window = regret_window
        self.algorithm = algorithm

        self.reset()

    def reset(self):
        self.regret_list = []
        self.eupac_list = []
        self.algorithm.reset()

    def __call__(self, regrets):
        self._push_regret(regrets)
        eupac = self.algorithm(self.regret_list)
        self.eupac_list.append(eupac)
        return eupac

    def _push_regret(self, regrets):
        if hasattr(regrets, '__len__'):
            for regret in regrets:
                self.regret_list.append(regret)
        else:
            self.regret_list.append(regrets)
        self.regret_list = self.regret_list[-self.regret_window:]


class EUPACAlgorithm():
    def __init__(self, parameters):
        self.c1 = parameters['bound_window'] * (parameters['regret_at_lower'] * parameters['percentage_at_lower'] - parameters['regret_at_upper']
                                                * parameters['percentage_at_upper']) / (parameters['regret_at_lower'] - parameters['regret_at_upper'])
        self.c2 = parameters['bound_window'] * parameters['regret_at_lower'] * parameters['regret_at_upper'] * (
            parameters['percentage_at_upper'] - parameters['percentage_at_lower']) / (parameters['regret_at_lower'] - parameters['regret_at_upper'])
        self.p = 1 / parameters['bound_window'] / \
            parameters['percentage_at_lower'] / parameters['regret_at_lower'] ** 2

        self.additional_init(parameters)
        self.reset()

    def additional_init(self, parameters):
        raise NotImplementedError

    def reset(self):
        raise NotImplementedError

    def __call__(self, regret_list):
        raise NotImplementedError


class IntervalChecking(EUPACAlgorithm):
    def additional_init(self, parameters):
        self.floating = parameters.get('floating', .5)

        self.special_init(parameters)

    def __call__(self, regret_list):
        self.update_regret_density(regret_list)
        return self.get_eupac()

    def special_init(self, parameters):
        self.sample_window = parameters.get('sample_window', 3)
        self.sample_draw = parameters.get('sample_draw', self.sample_window + 1)
        # dist
        self.bounds = sorted([0] + [self.c2 / (self.sample_window - k - self.c1) for k in range(self.sample_window + 1)] + [np.inf])

        self._load_combinations()

    def reset(self):
        self.regret_counts = np.zeros((self.sample_window + 2,))
        self.regret_density = np.zeros((self.sample_window + 2,))
        self.regret_density[-1] = 1.  # all regrets are the worst

    def _load_combinations(self):
        self.bin_regrets = [(a + b) / 2 for a, b in zip(self.bounds[1:-1], self.bounds[:-2])]
        self.bin_regrets.append(self.bounds[-2] + 1)
        combinations = itertools.combinations_with_replacement(
            range(self.sample_window + 2), self.sample_draw)
        self.successes_list = []
        self.binned_regrets_list = []
        for combination in combinations:
            indices, counts = np.unique(combination, return_counts=True)
            successes = np.zeros((self.sample_window + 2,))
            for index, count in zip(indices, counts):
                successes[index] = count
            self.successes_list.append(successes)
            binned_regrets = []
            for c in combination:
                binned_regrets.append(self.bin_regrets[c])
            self.binned_regrets_list.append(binned_regrets)

    def update_regret_density(self, regret_list):
        # update floating average of distributions
        regret_histogram, _ = np.histogram(regret_list, bins=self.bounds)
        self.regret_counts = self.floating * self.regret_counts + (1 - self.floating) * regret_histogram
        self.regret_density = self.regret_counts / np.sum(self.regret_counts)

    def multinomial_without_checks(self, x, n, p):
        return np.exp(multinomial._logpmf(x, n, p))

    def get_eupac(self):
        eupac = 0
        for successes, binned_regrets in zip(self.successes_list, self.binned_regrets_list):
            eupac += self.multinomial_without_checks(successes, self.sample_draw,
                                     self.regret_density) * (1 - self._ic(binned_regrets))
        return eupac

    def _ic(self, regret_list):
        sorted_regrets = sorted(regret_list)
        sorted_regrets = [sr if sr > 0 else 0 for sr in sorted_regrets]
        any = 0

        # tau <= min regret
        any += self.c1 < 0 and (self.c2 + self.c1 * sorted_regrets[0] < sorted_regrets[0] * self.sample_window or self.c2 + self.c1 * sorted_regrets[0] <= 0) \
            or self.c1 <= self.sample_window and self.c2 + self.c1 * sorted_regrets[0] < sorted_regrets[0] * self.sample_window \
            or self.c1 > self.sample_window and self.c2 + self.c1 * sorted_regrets[0] * self.sample_window <= sorted_regrets[0] * self.sample_window \
            or self.c2 + self.c1 * sorted_regrets[0] < 0

        # regret k-1 < tau < regret k
        for k, regret in enumerate(sorted_regrets):
            if k == 0:
                continue
            any += self.c1 < 0 and (self.c2 + self.c1 * sorted_regrets[k] >= 0 and self.c2 + (self.c1 + k) * sorted_regrets[k] < sorted_regrets[k] * (1 + self.sample_window)
                                    or self.c2 + self.c1 * sorted_regrets[k-1] > 0 and self.c2 + self.c1 * sorted_regrets[k] <= 0) \
                or self.c1 >= 0 and (self.c2 + (self.c1 + k) * sorted_regrets[k] < sorted_regrets[k] * (1 + self.sample_window) and self.c1 + k <= 1 + self.sample_window
                                     or 1 + self.sample_window < self.c1 + k and self.c2 + (self.c1 + k) * sorted_regrets[k] <= sorted_regrets[k] * (1 + self.sample_window)) \
                or self.c2 + self.c1 * sorted_regrets[k] < 0

        return any >= 1
