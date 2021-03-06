# Files module
import os
import magic
import re
import pefile
import hashlib
import pickle
import gzip
from . import entropy
from hashlib import sha256


class FileObject(object):

    # Below, the format is matching RE, file type,
    # and optional function to run on the file name
    FILE_TYPES = [
        ["PE.*MS Windows.*", "pefile", pefile.PE]
    ]

    def __init__(self, filename, load_file=True):
        """
        Creates a file object for a malware sample.

        :param filename:  The file name of the available malware sample.
        :param load_file:  Set to True to load the file.  This should be True
            in most circumstances.
        """
        # Save our data in a data object, so it can be saved
        self.malware = MalwareSample()

        # Default settings of members
        self.malware.runningentropy = entropy.RunningEntropy()
        self.malware.file_size = 0
        # The parsed info for the file...
        self.malware.parsedfile = None

        # Fill out other data here...
        self.malware.filename = filename
        self.malware.data = list()

        # Load up the file...
        if load_file:
            if not os.path.isfile(filename):
                raise ValueError("File {0} is not valid!".format(filename))
            self.malware.filetype = magic.from_file(self.malware.filename)
            self._read_file()
            self._parse_file_type()

    def _read_file(self):
        """
        Reads a file into a list of bytes.

        :return:  Nothing.
        """
        with open(self.malware.filename, 'rb') as f:
            hash_md5 = hashlib.md5()
            hash_sha256 = hashlib.sha256()
            byte = f.read(1)
            while byte != b"":
                hash_md5.update(byte)
                hash_sha256.update(byte)
                self.malware.data.append(byte)
                byte = f.read(1)
        self.malware.file_size = len(self.malware.data)
        self.malware.md5 = hash_md5.hexdigest()
        self.malware.sha256 = hash_sha256.hexdigest()

    def _parse_file_type(self):
        """
        Parses this file into its appropriate type.
        
        :return:  Nothing. 
        """
        for FILE_TYPE in self.FILE_TYPES:
            if re.match(FILE_TYPE[0], self.malware.filetype):
                self.malware.parsedfile = {"type": FILE_TYPE[1]}
                if (len(FILE_TYPE) > 2 and FILE_TYPE[2] is not None
                        and callable(FILE_TYPE[2])):
                    self.PE = FILE_TYPE[2](self.malware.filename)
                    self.malware.parsedfile['sections'] = dict()
                    for section in self.PE.sections:
                        section_name = section.Name.decode('UTF-8', 'ignore')
                        offset = section.PointerToRawData
                        length = section.SizeOfRawData
                        self.malware.parsedfile['sections'][section_name] = dict()
                        self.malware.parsedfile['sections'][section_name]['offset'] = offset
                        self.malware.parsedfile['sections'][section_name]['length'] = length
                        # TODO: Above may be section.Misc_VirtualSize - test this.
                        # More info:
                        # https://msdn.microsoft.com/en-us/library/ms809762.aspx

    def running_entropy(self, window_size=256, normalize=True):
        """
        Calculates the running entropy of the whole generic file object using a
        window size.

        :param window_size:  The running window size in bytes.
        :param normalize:  True if the output should be normalized
            between 0 and 1.
        :return: A list of running entropy values for the given window size.
        """
        entropy = self.malware.runningentropy.calculate(self.malware.data,
                                                        window=window_size,
                                                        normalize=normalize)
        if len(entropy) != self.malware.file_size - window_size + 1:
            raise Exception("This should not happen.  Check this code.")
        return entropy

    def entropy(self, normalize=True):
        """
        Calculates the entropy for the whole file.

        :param normalize:  True if the output should be normalized
            between 0 and 1.
        :return: An entropy value of the whole file.
        """
        entropy = self.malware.runningentropy.calculate(self.malware.data,
                                                window=len(self.malware.data),
                                                normalize=normalize)
        if len(entropy) > 1:
            raise Exception("This should not happen.  Check this code.")

        return entropy[0]

    def write(self, filename):
        """
        Write the file data to a pickled gzip file.

        :param filename:  The data file name
        :return: Nothing
        """
        # Remove any old data...
        try:
            os.remote(filename)
        except:
            pass

        # Zip up the pickle
        with gzip.open(filename, 'wb') as file:
            pickle.dump(self.malware, file)

    @staticmethod
    def read(filename):
        """
        Read the file data from a pickled gzip file.

        :param filename:  The data file name
        :return: Nothing
        """
        f = FileObject('', load_file=False)
        with gzip.open(filename, 'rb') as file:
            f.malware = pickle.load(file)
        # Parse up the file type, if available...
        # f._parse_file_type()
        return f


class MalwareSample(object):
    def __init__(self, filename=None, filetype=None,
                 file_size=None, md5=None, sha256=None, data=None,
                 runningentropy=None, parsedfile=None):
        """
        Object used to save malware data to pickled files for processing later.
        """
        self.filename = filename
        self.filetype = filetype
        self.file_size = file_size
        self.md5 = md5
        self.sha256 = sha256
        self.data = data
        self.runningentropy = runningentropy
        self.parsedfile = parsedfile


def sha256_file(filename):
    hasher = sha256()
    if os.path.isfile(filename):
        with open(filename, 'rb') as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()
    else:
        return ""