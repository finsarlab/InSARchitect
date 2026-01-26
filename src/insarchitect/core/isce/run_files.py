import isce

from topsStack import stackSentinel

def main():
    args = [
        '-d', "/home/daruma/workdir/galapagos/DEM",
        '-o', "/home/daruma/workdir/S1orbits",
        '-a', "/home/daruma/workdir/S1orbits",
        '-s', "/home/daruma/workdir/galapagos/SLC"
    ]
    stackSentinel.main(iargs=args)
