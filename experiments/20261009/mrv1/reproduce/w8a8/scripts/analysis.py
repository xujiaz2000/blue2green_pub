import sys
from torch_npu.profiler.profiler import analyse
analyse(sys.argv[1])
