#!/usr/bin/env python3

from instance import *
from configuration import *

def run_benchmarks(instances, do_compilation=True, max_result=1, skip_running=True):
    nb_tasks = 225

    number_of_instances = len(instances)
    processed_instances = 0

    for inst in instances:
        processed_instances = processed_instances + 1
        inst_name = str(inst)
        nb_results = len(inst.results_ht)
        print('Processing %(processed_instances)d / %(number_of_instances)d : %(inst_name)s (%(nb_results)d) - ' % locals(), end='')
        if nb_results >= max_result:
            print('Pass')
            continue

        if skip_running:
            if inst.still_running:
                print('Running')
                continue

        print('OK')

        inst.platform.wait_nb_task(nb_tasks - 1)

        task = inst.create_new_task()
        task.prepare_run(do_compilation)
        task.run()
        task.precheck_result()

        print()

        inst.platform.wait_nb_task(nb_tasks - 1)

def main():
    instances = generate_instances(check_platform=True)
    #instances = [i for i in instances if 'O3' not in str(i)]
    instances_load_results(instances)
    instances_check_results(instances)
    run_benchmarks(instances, max_result=3)

    print("Done.")

if __name__ == "__main__":
    main()

