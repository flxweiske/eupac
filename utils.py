import inspect
import json

def debug(function):
    def wrapper(*args, **kwargs):
        args_name = inspect.getargspec(function)[0]
        tab_times = len(inspect.getouterframes(inspect.currentframe())) - 2
        print(tab_times * '\t' + ('>> {}({})'.format(function.__name__, args_name)))
        args_dict = dict(zip(args_name, args))
        for k, v in args_dict.items():
            print((tab_times + 1) * '\t' + k + ': ' + str(v))
        value = function(*args, **kwargs)
        print(tab_times * '\t' + ('<< {} = {}()'.format(value, function.__name__)))
        return value
    return wrapper

def with_parameters_from(filename):
    with open(filename, 'r') as f:
        return json.load(f)
