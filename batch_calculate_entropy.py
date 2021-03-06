import argparse
from library.files import FileObject
from library.utils import Utils
import numpy
import os
import time
import shutil


def main(arguments=None):
    # Argument parsing
    parser = argparse.ArgumentParser(
        description='Calculates the entropy of a file.')
    parser.add_argument('MalwareDirectory',
                        help='The directory containing malware to analyze.')
    parser.add_argument('DataDirectory',
                        help='The directory that will contain the data files.')
    parser.add_argument("-w", "--window",
                        help="Window size, in bytes, for running entropy."
                             "Multiple windows can be identified as comma "
                             "separated values without spaces."
                             "", type=str, required=False)
    parser.add_argument("-n", "--nonormalize", action='store_true',
                        help="Disables entropy normalization."
                             "", required=False)
    parser.add_argument("-s", "--skipcalculated", action='store_true',
                        help="Skip already computed samples.  "
                             "This will not calculate any windows if ANY data exists."
                             "", required=False)
    parser.add_argument("-m", "--maxsamples", type=int, default=0,
                        help="Maximum number of samples to process, zero for all."
                             "", required=False)

    if isinstance(arguments, list):
        args = parser.parse_args(arguments)
    else:
        args = parser.parse_args()

    # Normalize setup...
    if args.nonormalize:
        normalize = False
    else:
        normalize = True

    # Find window sizes
    windows = None
    if args.window:
        windows = args.window.split(',')
        windows = [x.strip() for x in windows]
        windows = [int(x) for x in windows]

    # Delete old data...
    # try:
    #     shutil.rmtree(args.DataDirectory, ignore_errors=True)
    # except:
    #     pass

    # Create DB directory...
    try:
        os.mkdir(args.DataDirectory)
    except:
        pass

    # # Create the DB directory if needed...
    # try:
    #     os.stat(args.DBDirectory)
    # except:
    #     os.mkdir(args.DBDirectory)

    # Crawl the directories for malware and calculate rwe
    Utils.batch_running_window_entropy(args.MalwareDirectory,
                                       args.DataDirectory,
                                       window_sizes=windows,
                                       normalize=normalize,
                                       skipcalculated=args.skipcalculated)


if __name__ == "__main__":
    main()
