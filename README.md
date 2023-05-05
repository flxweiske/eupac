# Robust and Cheap Safety Measure for Exoskeletal Learning Control with Estimated Uniform PAC (EUPAC)
This is the supplementary repository for Estimated Uniform PAC (EUPAC). For the original content, please refer to the according publication.

## Installation
Clone the repository to a local folder on your machine as seen fit.
```
git clone https://github.com/flxweiske/eupac
```

## Usage
The implementation of EUPAC can be found in ```eupac.py```.

### Configuration
You need a EUPAC configuration to load the EUPAC algorithm. A ```EUPACConfig.json``` has to be like
```
{
  "regret_at_lower": float,
  "percentage_at_lower": float,
  "regret_at_upper": float,
  "percentage_at_upper": float,
  "bound_window": int,
  "sample_window": int,
  "floating": float = 0.5,
}
```
- ```regret_at_lower``` defines the lower regret threshold that regrets needs to have in ```percentage_at_lower``` of all cases to be categorized as safe regrets with the Uniform PAC condition within EUPAC
- ```percentage_at_lower``` defines the number of regrets in relation to ```bound_window``` that need to have ```regret_at_lower``` to be categorized as safe regrets with the Uniform PAC condition within EUPAC
- ```regret_at_upper``` defines the upper regret threshold that regrets needs to have in ```percentage_at_upper``` of all cases to be categorized as safe regrets with the Uniform PAC condition within EUPAC
- ```percentage_at_upper``` defines the number of regrets in relation to ```bound_window``` that need to have ```regret_at_upper``` to be categorized as safe regrets with the Uniform PAC condition within EUPAC
- ```bound_window``` is the reference window size that is used in percentage calculations for the still safe regrets by Uniform PAC within EUPAC
- ```sample_window``` is the number of multinomial samples to be used for the joint regret probability estimate
- ```floating``` is the weighting within the averaging of old vs. new regret density estimates

See under ```cfg/``` for 2 examples from the simulation study of the publication.

### EUPAC by Interval Checking
With the configuration you can initialize EUPAC and start using it like
```
from eupac import EUPAC, IntervalChecking
from utils import with_parameters_from

# initialization
regret_window = 30  # number of binned regrets to use
eu = EUPAC(regret_window, IntervalChecking(with_parameters_from("EUPACConfig.json")))

# usage
# one single new regret
new_regret = 10
eu(new_regret)

# a list of new regrets
new_regrets = [1, 2, 3, 4, 5, 6]
eu(new_regrets)
```
Each call to the EUPAC object
- pushes the regrets to an internal saving list
- uses the specified algorithm to calculate the EUPAC value with all regrets seen so far
- pushes the EUPAC value to an internal saving list

EUPAC by ```IntervalChecking``` uses the algorithm proposed in the publication. There are 2 main methods implemented:
- ```IntervalChecking.update_regret_density```, that bins the new regrets in the bins to be used, counts them and updates the internal regret density estimate via averaging with the previous estimate, and
- ```IntervalChecking.get_eupac```, that calculates the conditionalized probability sum using all multinomial cases and the internal ```_ic```-method to check all interval conditions as proposed in the publication

Please refer to the original publication and the supplementary materials on this repository for further details.

## Supplementary Material
Under the ```supplementary/``` folder you can find
- the ```supplementary material.pdf``` containing information about the derivation of EUPAC, its algorithm and a discussion about the actual learning results, and
- learning curves differentiated by the three categories: environment number of joints, RL algorithm and CBF/no CBF under ```images/```