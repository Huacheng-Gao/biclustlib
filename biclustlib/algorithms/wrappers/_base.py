"""
    biclustlib: A Python library of biclustering algorithms and evaluation measures.
    Copyright (C) 2017  Victor Alexandre Padilha

    This file is part of biclustlib.

    biclustlib is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    biclustlib is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from time import sleep
from abc import ABCMeta, abstractmethod

from sklearn.utils.validation import check_array

from .._base import BaseBiclusteringAlgorithm
from ...models import Bicluster, Biclustering

import os, shutil, tempfile, subprocess
import numpy as np


class ExecutableWrapper(BaseBiclusteringAlgorithm, metaclass=ABCMeta):
    """This class defines the skeleton of a naive executable wrapper. In summary,
    in every execution, it will create a temporary directory, save the input data
    as a txt file, run the wrapped algorithm, parse the output files and remove the
    temporary directory.

    Parameters
    ----------
    exec_comm : str
        The command line command to run the wrapped executable.

    tmp_dir : str
        Temporary directory path, where temporary files will be stored.

    sleep : bool, default: True
        Whether to make a 1 second delay before running the wrapped executable.

    data_type : numpy.dtype, default: numpy.double
        The input data type required by the algorithm.
    """

    def __init__(self, data_filename='data.txt', output_filename='output.txt', data_type=np.double, sleep=1):
        super().__init__()

        self._data_filename = data_filename
        self._output_filename = output_filename
        self._data_type = data_type
        self._sleep = sleep

    def run(self, data):
        """Compute biclustering.

        Parameters
        ----------
        data : numpy.ndarray
        """
        self._validate_parameters()
        data = check_array(data, dtype=self._data_type, copy=True)

        tmp_dir = tempfile.mkdtemp()

        data_path = os.path.join(tmp_dir, self._data_filename)
        output_path = os.path.join(tmp_dir, self._output_filename)

        self._write_data(data_path, data)
        sleep(self._sleep)
        comm = self._get_command(data, data_path, output_path).split()
        subprocess.check_call(comm)
        biclustering = self._parse_output(output_path)

        shutil.rmtree(tmp_dir)

        return biclustering

    @abstractmethod
    def _get_command(self, data, data_path, output_path):
        pass

    @abstractmethod
    def _write_data(self, data_path, data):
        """Write input data to txt file."""
        pass

    @abstractmethod
    def _parse_output(self, output_path):
        """Parses the output file generated by the wrapped executable."""
        pass


class SklearnWrapper(BaseBiclusteringAlgorithm, metaclass=ABCMeta):
    """This class defines the skeleton of a wrapper for the scikit-learn
    package.
    """

    def __init__(self, constructor, **kwargs):
        self.wrapped_algorithm = constructor(**kwargs)

    def run(self, data):
        """Compute biclustering.

        Parameters
        ----------
        data : numpy.ndarray
        """
        self.wrapped_algorithm.fit(data)

        biclusters = []

        for rows, cols in zip(*self.wrapped_algorithm.biclusters_):
            b = Bicluster(rows, cols)
            biclusters.append(b)

        return Biclustering(biclusters)


# """Write input data to txt file."""
# header = self._get_header(data)
#
# if header is None:
#     header = ''
#
# row_names = self._get_row_names(data)
#
# if row_names is not None:
#     data = np.hstack((row_names[:, np.newaxis], data))
#
# with open(data_path, 'wb') as f:
#     np.savetxt(f, data, delimiter='\t', header=header, fmt='%s', comments='')
