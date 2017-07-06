from instance import *
from benchmarks.barnes import *
from benchmarks.cholesky import *
from benchmarks.fft import *
from benchmarks.fmm import *
from benchmarks.ocean import *
from benchmarks.lu import *
from benchmarks.radiosity import *
from benchmarks.raytrace import *
from benchmarks.water_nsq import *
from benchmarks.npb_ft import *
from benchmarks.npb_mg import *
from benchmarks.npb_cg import *
from benchmarks.npb_lu import *
from benchmarks.npb_bt import *

from platforms.simics import *
from platforms.gems_trace import *

def generate_instances(check_platform=False):
    print("Generating instances...")
    instances = []


    instances.extend( get_instance_list(BenchmarkNPB_FT(), PlatformSimics(), check_platform) )
    instances.extend( get_instance_list(BenchmarkNPB_MG(), PlatformSimics(), check_platform) )
    instances.extend( get_instance_list(BenchmarkNPB_CG(), PlatformSimics(), check_platform) )
    instances.extend( get_instance_list(BenchmarkNPB_LU(), PlatformSimics(), check_platform) )
    instances.extend( get_instance_list(BenchmarkNPB_BT(), PlatformSimics(), check_platform) )

    instances.extend( get_instance_list(BenchmarkBarnes(), PlatformSimics(), check_platform) )
    instances.extend( get_instance_list(BenchmarkCholesky(), PlatformSimics(), check_platform) )
    instances.extend( get_instance_list(BenchmarkFFT(), PlatformSimics(), check_platform) )
    instances.extend( get_instance_list(BenchmarkFMM(), PlatformSimics(), check_platform) )
    instances.extend( get_instance_list(BenchmarkLU(), PlatformSimics(), check_platform) )
    instances.extend( get_instance_list(BenchmarkOcean(), PlatformSimics(), check_platform) )

    instances.extend( get_instance_list(BenchmarkRaytrace(), PlatformSimics(), check_platform) )
    instances.extend( get_instance_list(BenchmarkRadiosity(), PlatformSimics(), check_platform) )
    instances.extend( get_instance_list(BenchmarkWATER(), PlatformSimics(), check_platform) )

    if False:
    #if True:
        instances.extend( get_instance_list(BenchmarkBarnes(), PlatformGemsTrace(), check_platform) )
        instances.extend( get_instance_list(BenchmarkCholesky(), PlatformGemsTrace(), check_platform) )
        instances.extend( get_instance_list(BenchmarkFFT(), PlatformGemsTrace(), check_platform) )
        instances.extend( get_instance_list(BenchmarkFMM(), PlatformGemsTrace(), check_platform) )
        instances.extend( get_instance_list(BenchmarkLU(), PlatformGemsTrace(), check_platform) )
        instances.extend( get_instance_list(BenchmarkOcean(), PlatformGemsTrace(), check_platform) )
        instances.extend( get_instance_list(BenchmarkRaytrace(), PlatformGemsTrace(), check_platform) )
        instances.extend( get_instance_list(BenchmarkRadiosity(), PlatformGemsTrace(), check_platform) )
        instances.extend( get_instance_list(BenchmarkWATER(), PlatformGemsTrace(), check_platform) )

        instances.extend( get_instance_list(BenchmarkNPB_FT(), PlatformGemsTrace(), check_platform) )
        instances.extend( get_instance_list(BenchmarkNPB_MG(), PlatformGemsTrace(), check_platform) )
        instances.extend( get_instance_list(BenchmarkNPB_CG(), PlatformGemsTrace(), check_platform) )
        instances.extend( get_instance_list(BenchmarkNPB_LU(), PlatformGemsTrace(), check_platform) )
        instances.extend( get_instance_list(BenchmarkNPB_BT(), PlatformGemsTrace(), check_platform) )

    print(len( instances ), " instances available.")
    print("")

    return instances
