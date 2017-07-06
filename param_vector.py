class ParamVector(object):
    parameters = []
    vector = []
    class_ht = {}

    def __init__(self):
        self.init()
        self.init_vector()

    def init_vector(self):
        size = len(self.parameters)
        self.vector = []
        for i in range(size):
            self.vector.append(self.parameters[i].get_next_value(None))
        if not self.check_vector_validity():
            self.vector_next_valid()

    def vector_next_value(self, current):
        cur_value = self.vector[current]
        self.vector[current] = self.parameters[current].get_next_value(cur_value)
        return self.vector[current]

    def vector_next(self):
        current = len(self.parameters) - 1
        while current != -1:
            if self.vector_next_value(current) == None:
                self.vector_next_value(current)
                current = current - 1
            else:
                return self.vector
        return None

    def check_vector_validity(self, *args, **kwargs):
        return True

    def vector_next_valid(self, *args, **kwargs):
        while True:
            vec = self.vector_next()
            if vec == None:
                return None
            if self.check_vector_validity(*args, **kwargs):
                return vec

    def format_vector(self):
        s = ""
        for i in range(len(self.vector)):
            value = self.vector[i]
            default = self.parameters[i].default_value
            if default:
                if value == default:
                    continue

            frmt = self.parameters[i].dir_format
            if not self.parameters[i].dir_format:
                if type(value) is int:
                    frmt =  '%.4d'
                else:
                    frmt = '%s'
            s = s + frmt % value + '_'

        return s[:-1]

    def init(self):
        self.class_ht = {}
        for i in range(len(self.parameters)):
            name = self.parameters[i].__class__
            self.class_ht[ name ] = i
            name = self.parameters[i].__class__.__name__
            self.class_ht[ name ] = i
            if name.startswith('Param'):
                self.class_ht[name[5:]] = i

    def get_param_value(self, param_class):
        return self.vector[ self.class_ht[param_class] ]

    def set_param_value(self, param_class, value):
        self.vector[ self.class_ht[param_class] ] = value

    def __getitem__(self, item):
        return self.get_param_value(item)

    def get_ht_based_on_vector(self):
        ht = {}
        for i in range(len(self.parameters)):
            ht[ self.parameters[i].__class__.__name__ ] = self.vector[i]
            if hasattr(self.parameters[i], 'get_option'):
                ht[ self.parameters[i].__class__.__name__ + '_option'] = self.parameters[i].get_option(self.vector[i])
        return ht

    def write_info_file(self, filename):
        with open(filename, 'w') as f:
            for i in range(len(self.parameters)):
                f.write(self.parameters[i].__class__.__name__ +': ' + str(self.vector[i]) + '\n')

    def get_name(self):
        name = self.__class__.__name__
        prefix = ['Benchmark', 'Platform']
        for p in prefix:
            if name.startswith(p):
                name = name[len(p):]
                break
        return name

    def get_representation(self):
        s = ''
        for i in range(len(self.parameters)):
            s = s + str(self.parameters[i]) + '=' + str(self.vector[i]) + ', '
        return '[' + s[:-2] + ']'
