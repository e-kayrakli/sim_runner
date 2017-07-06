from . import jobscheduler_sge
from . import jobscheduler_slurm
from . import jobscheduler_null

def get_all_schedulers():
    return [jobscheduler_slurm.JobSchedulerSlurm, jobscheduler_sge.JobSchedulerSGE, jobscheduler_null.JobSchedulerNULL]

def get_current_scheduler():
    for sched in get_all_schedulers():
        if sched.is_available():
            return sched()
    return None

