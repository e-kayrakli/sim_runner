from benchmarks.npb import *
from benchmarks.npb_cseq import BenchmarkNPB_CSEQ
from benchmarks.ssca3 import *
from benchmarks.matrix_multiplication import *
from benchmarks.matrix_multiplication_seq import *
from benchmarks.sobel import *
from benchmarks.sobel_seq import *
from benchmarks.random_access import *
from benchmarks.random_access_seq import *
from benchmarks.random_access2 import *
from benchmarks.random_access2_seq import *
from benchmarks.matrix_multiplication import *
from benchmarks.georgetown_load_balancing import *
from benchmarks.upcbench_matrix_multiplication import *
from benchmarks.apo_stencil import *
from benchmarks.hello import *

from instance import *

from platforms.berkeley_tile import *
from platforms.berkeley_trace import *
from platforms.berkeley import *
from platforms.cray_xt5 import *
from platforms.cray_upc import *
from platforms.tilecc import *
from platforms.gcc import *
from platforms.gcc_upc import *
from platforms.simics import *

from util import get_hostname

def generate_instances(check_platform=False):
    print("Generating instances...")
    instances = []

    #instances.extend( get_instance_list(BenchmarkGeorgetownLoadBalancing(), PlatformCrayUPC(param_cores=[128, 256, 512, 1024]), check_platform) )
    #instances.extend( get_instance_list(BenchmarkGeorgetownLoadBalancing(), PlatformBerkeley(conduits=['ibv'], param_cores=[128, 256, 512]), check_platform) )

    instances.extend( get_instance_list(
        BenchmarkHello(),
        PlatformGCC(),
        check_platform) )


    return instances

    instances.extend( get_instance_list(
        BenchmarkNPB(minClass='C', maxClass='D', kernel_list=['ft']),
        PlatformCrayUPC(param_cores=[128, 256, 512, 1024]),
        check_platform) )

    instances.extend( get_instance_list(
        BenchmarkNPB(minClass='B', maxClass='C', kernel_list=None),
        PlatformCrayUPC(param_cores=[16, 32, 64, 128, 256, 512, 1024]),
        check_platform) )

    if get_hostname() == 'bulldozer-server':
        instances.extend(get_instance_list(BenchmarkUBMatrixMultiplication(), PlatformBerkeley(param_cores=[1, 2, 4, 8, 16, 32], conduits=['smp']), check_platform) ) #   disable_optimization=True, experimental=True
        return instances

    if False:
        instances.extend(get_instance_list(BenchmarkNPB(maxClass='B', minClass='B', kernel_list=['ft']), PlatformBerkeleyTrace(param_cores=core_list, conduits=['ibv']), check_platform))
        instances.extend(get_instance_list(BenchmarkNPB(minClass='B', maxClass='B', kernel_list=['ft']), PlatformBerkeley(param_cores=core_list, conduits=['ibv']), check_platform) ) #   disable_optimization=True, experimental=True
        instances.extend(get_instance_list(BenchmarkNPB(maxClass='A', minClass='A', kernel_list=['ft', 'cg', 'is', 'mg']), PlatformBerkeleyTrace(param_cores=core_list, conduits=['ibv']), check_platform))
        instances.extend(get_instance_list(BenchmarkNPB(minClass='A', maxClass='A', kernel_list=['ft', 'cg', 'is', 'mg']), PlatformBerkeley(param_cores=core_list, conduits=['ibv']), check_platform) ) #   disable_optimization=True, experimental=True

    #instances.extend( get_instance_list(BenchmarkNPB(minClass='A', maxClass='A'), PlatformBerkeleyTile(), check_platform) ) #   disable_optimization=True, experimental=True
    #instances.extend( get_instance_list(BenchmarkNPB_CSEQ(minClass='A', maxClass='A'), PlatformTileCC(), check_platform) )

    #instances.extend( get_instance_list(BenchmarkSSCA3(maxScale=3), PlatformCrayUPCxt5(), check_platform) )
    #instances.extend( get_instance_list(BenchmarkSSCA3(maxScale=2, withFFTW=False), PlatformBerkeleyTile()) )
    #instances.extend( get_instance_list(BenchmarkMatrixMultiplication(), PlatformBerkeleyTile(), check_platform) )
    #instances.extend( get_instance_list(BenchmarkSobel(), PlatformBerkeleyTile(), check_platform) )
    #instances.extend( get_instance_list(BenchmarkRandomAccess2(), PlatformBerkeleyTile(), check_platform) )
    if False:
        instances.extend( get_instance_list(BenchmarkMatrixMultiplication(), PlatformBerkeley(), check_platform) )
        instances.extend( get_instance_list(BenchmarkSobel(), PlatformBerkeley(), check_platform) )
        instances.extend( get_instance_list(BenchmarkRandomAccess(), PlatformBerkeley(), check_platform) )
        instances.extend( get_instance_list(BenchmarkRandomAccess(), PlatformBerkeleyTile(), check_platform) )
        instances.extend( get_instance_list(BenchmarkRandomAccessSeq(), PlatformTileCC(), check_platform) )
        instances.extend( get_instance_list(BenchmarkRandomAccessSeq(), PlatformGCC(), check_platform) )
        instances.extend( get_instance_list(BenchmarkRandomAccess2(), PlatformBerkeley(), check_platform) )
        instances.extend( get_instance_list(BenchmarkRandomAccess2Seq(), PlatformTileCC(), check_platform) )
        instances.extend( get_instance_list(BenchmarkRandomAccess2Seq(), PlatformGCC(), check_platform) )
        instances.extend( get_instance_list(BenchmarkSobelSeq(), PlatformTileCC(), check_platform) )
        instances.extend( get_instance_list(BenchmarkSobelSeq(), PlatformGCC(), check_platform) )
        instances.extend( get_instance_list(BenchmarkMatrixMultiplicationSeq(), PlatformTileCC(), check_platform) )
        instances.extend( get_instance_list(BenchmarkMatrixMultiplicationSeq(), PlatformGCC(), check_platform) )

    print(len( instances ), " instances available.")
    print("")

    return instances

