from benchmarks.jacobi_test import *

from instance import *

from platforms.berkeley import *
from platforms.chapel import *
from platforms.cray_upc import *

def generate_instances(check_platform=False):
    print("Generating instances...")
    instances = []

    if False:
        instances.extend(
                get_instance_list(
                    BenchmarkJacobiTest(),
                    PlatformCrayUPC(param_cores=[1, 2, 4, 8, 16]
                        ), check_platform)
                    )

    instances.extend(
            get_instance_list(
                BenchmarkJacobiTest(is_chapel=True),
                PlatformChapel(param_cores=[1, 2, 4, 8, 16, 32]
                    ), check_platform)
                )

    instances.extend(
            get_instance_list(
                BenchmarkJacobiTest(),
                PlatformBerkeley(conduits=['smp'], param_cores=[1, 2, 4, 8, 16, 32]), check_platform) )

    print(len( instances ), " instances available.")
    print("")

    return instances

