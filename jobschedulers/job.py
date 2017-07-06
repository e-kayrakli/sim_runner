class Job(object):
    def __init__(self, name=None, cmd=None, nb_cores=1, max_time=None, allow_grouping=False):
        self.name = name
        self.cmd = cmd
        self.nb_cores = nb_cores
        self.allow_grouping = allow_grouping
        self.path = None
        self.output = None
        self.set_max_time(max_time)
        self.jsfilename = 'job.qsub'
        self.jsout = '0004_run'

    def set_max_time(self, max_time=None):
        if max_time:
            self.max_time = int(max_time * 1.05 + 15*60)
        else:
            self.max_time = 3*24*3600


