import multiprocessing
import os
import sys


PACKAGE_PARENT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PACKAGE_PARENT)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    import hyge.probes.tao_dfs_probe_extended_body
