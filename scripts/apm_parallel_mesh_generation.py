#!/usr/bin/env python3
r"""
Little script designed to semi-automatically generate a mesh
"""
import argparse
from argparse import RawDescriptionHelpFormatter as RawDesc
from logging import DEBUG
import os
from ApertureMapModelTools import DataField, _get_logger
from ApertureMapModelTools.OpenFoam import ParallelMeshGen

#
desc_str = r"""
Description: Generates a blockMesh in parallel using the OpenFOAM utilties
blockMesh, mergeMeshes and stitchMesh. Uses the ParallelMeshGen class in
the OpenFoam submodule. When reading in a parameter file with the -r option
the file should be formatted with a single "key: value" pair on each line.
Valid mesh_types are: simple, symmetry, threshold and symmetry-threshold

Written By: Matthew stadelman
Date Written: 2016/08/16
Last Modfied: 2016/08/25
"""
# creating arg parser
parser = argparse.ArgumentParser(description=desc_str, formatter_class=RawDesc)

# adding arguments
parser.add_argument('-f', '--force', action='store_true',
                    help='''"force/overwrite mode",
                    allows program to overwrite existing files''')

parser.add_argument('-v', '--verbose', action='store_true',
                    help='''"verbose mode", debug messages are printed to
                    the screen''')

parser.add_argument('-r', '--read-file',
                    type=os.path.realpath, default=None,
                    help='reads a file to load mesh parameters from.')

parser.add_argument('-o', '--output-dir',
                    type=os.path.realpath, default=os.getcwd(),
                    help='''"output to", outputs all files to the specified
                    directory, sub-directories are created as needed''')

parser.add_argument('-sys', '--system-path',
                    type=os.path.realpath, default=os.getcwd(),
                    help='directory to copy the "system" directory from')

parser.add_argument('-np', type=int, default=8,
                    help='number of processors to use in mesh generation')

parser.add_argument('map_file', type=os.path.realpath,
                    help='aperture map input file to read in')

parser.add_argument('avg_fact', type=int,
                    help='horizontal averaging factor of map')

parser.add_argument('mesh_type', nargs='?', default='simple',
                    help='the type of mesh to generate')


def apm_parallel_mesh_generation():
    r"""
    Processes the command line arguments and generates the mesh
    """
    #
    namespace = parser.parse_args()
    if namespace.verbose:
        logger = _get_logger(ParallelMeshGen.__module__)
        logger.setLevel(DEBUG)
    #
    # initial mesh parameters
    mesh_params = {
        'convertToMeters': '2.680E-5',
        'numbersOfCells': '(1 1 1)',
        #
        'boundary.left.type': 'wall',
        'boundary.right.type': 'wall',
        'boundary.top.type': 'wall',
        'boundary.bottom.type': 'wall',
        'boundary.front.type': 'wall',
        'boundary.back.type': 'wall'
    }
    #
    # reading params file if supplied
    if namespace.read_file:
        print('Reading parameters file...')
        read_params_file(namespace.read_file, mesh_params)
    #
    # creating data field from aperture map
    print('Processing aperture map...')
    map_field = DataField(namespace.map_file)
    #
    # setting up mesh generator
    system_dir = os.path.join(namespace.system_path,'system')
    np = namespace.np
    kwargs = {'nprocs': np,
              'avg_fact': namespace.avg_fact,
              'mesh_params': mesh_params}
    #
    print('Setting generator up...')
    pmg = ParallelMeshGen(map_field, system_dir, **kwargs)
    #
    # creating the mesh
    print('Creating the mesh...')
    pmg.generate_mesh(namespace.mesh_type,
                      path=namespace.output_dir,
                      overwrite=namespace.force)
    #
    # moving mesh files out of region directory
    out_path = namespace.output_dir
    reg_dir = os.path.join(out_path, 'mesh-region0', '*')
    if namespace.force:
        os.system('cp -ralf {} {}'.format(reg_dir, out_path))
        os.system('rm -rf {}'.format(os.path.join(out_path, 'mesh-region0')))
    else:
        os.system('mv {} {}'.format(reg_dir, out_path))
        os.system('rmdir {}'.format(os.path.join(out_path, 'mesh-region0')))


def read_params_file(infile, mesh_params):
    r"""
    Reads the parameter file, updating mesh_params with the key value entries
    """
    with open(infile, 'r') as f:
        content = f.read()
        lines = content.split('\n')
        lines = [line.replace(':',' ') for line in lines if line]
    #
    # updating mesh_params with keys from infile
    for line in lines:
        line = line.strip()
        key, value = line.split(' ', maxsplit=1)
        value = value.strip()
        mesh_params[key] = value

#
if __name__ == '__main__':
    apm_parallel_mesh_generation()
