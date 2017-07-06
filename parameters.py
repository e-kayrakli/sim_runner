from time import strftime
import util

class Parameter(object):
    default_value = None
    dir_format = None

    def __init__(self):
        if len(self.valid_values) != len(set(self.valid_values)):
            raise NameError('Invalid parameter class')

    def __str__(self):
        return self.get_name()

    def __repr__(self):
        return self.get_name()

    def get_next_value(self, value):
        if value == None:
            return self.valid_values[0]

        new_idx = self.valid_values.index(value) + 1
        if new_idx >= len(self.valid_values):
            return None
        return self.valid_values[ new_idx ]

    def get_name(self):
        class_name = self.__class__.__name__

        if hasattr(self, 'name'):
            return name
        else:
            if class_name.startswith('AutoParam'):
                return class_name[len('AutoParam'):].lower()
            if class_name.startswith('Param'):
                return class_name[len('Param'):]
            return class_name.lower()

class ParamCores( Parameter ):
    def __init__(self, max=128, list=None):
        self.valid_values = []
        if list:
            for e in list:
                if e <= max:
                    self.valid_values.append(e)
        else:
            val = 1
            while val <= max:
                self.valid_values.append(val)
                val = val * 2

class ParamOptimization( Parameter ):
    valid_values = ['O0', 'O1', 'O2', 'O3']

class AutomaticParameter(object):
    def get_name(self):
        class_name = self.__class__.__name__

        if hasattr(self, 'name'):
            return name
        else:
            if class_name.startswith('AutoParam'):
                return class_name[len('AutoParam'):].lower()
            else:
                return class_name.lower()

    def get_value():
        raise NameError('Not implemented')

    def __str__(self):
        return self.get_name() + ': ' + self.get_value()

class AutoParamTime( AutomaticParameter ):
    def get_value(self):
        return strftime("%H:%M:%S")

class AutoParamDate( AutomaticParameter ):
    def get_value(self):
        return strftime("%Y-%m-%d")

class AutoParamHostname( AutomaticParameter ):
    def get_value(self):
        return util.get_hostname()

class AutoParamSVNRevision( AutomaticParameter ):
    def __init__(self, svn_path):
        self.svn_path = svn_path

    def get_value(self):
        return self.svn_path + ':' + util.get_svn_revision(self.svn_path)

