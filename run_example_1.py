#!/usr/bin/python

from __future__ import print_function

import socket
import sys
import os
import subprocess

use_multiprocessing = True
if use_multiprocessing:
    import multiprocessing
    max_cpus = 31 # We might want to not run on the full number of cores, as Rosetta take about 2 Gb of memory per instance

###################################################################################################################################################################
# Important: The variables below are set to values that will make the run complete faster (as a tutorial example), but will not give scientifically valid results.
#            Please change them to the "normal" default values before a real run.
###################################################################################################################################################################

in_dir_name = 'inputs'
out_dir_name = 'output'

rosetta_scripts_path = os.path.expanduser('/storage/brno2/home/romanb/rosetta/rosetta.binary.linux.release-296/main/source/bin/rosetta_scripts.default.linuxgccrelease')
nstruct = 5 # Normally 35
max_minimization_iter = 250 # Normally 5000
abs_score_convergence_thresh = 1.0 # Normally 1.0
# number_backrub_trials = 1 # Normally 35000
# backrub_trajectory_stride = 5 # Can be whatever you want, if you would like to see results from earlier time points in the backrub trajectory. 7000 is a reasonable number, to give you three checkpoints for a 35000 step run, but you could also set it to 35000 for quickest run time (as the final minimization and packing steps will only need to be run one time).
# nstruct = 3 # Normally 35
# max_minimization_iter = 5 # Normally 5000
# abs_score_convergence_thresh = 200.0 # Normally 1.0
# number_backrub_trials = 10 # Normally 35000
# backrub_trajectory_stride = 5 # Can be whatever you want, if you would like to see results from earlier time points in the backrub trajectory. 7000 is a reasonable number, to give you three checkpoints for a 35000 step run, but you could also set it to 35000 for quickest run time (as the final minimization and packing steps will only need to be run one time).
path_to_script = 'ddG-no_backrub_control.xml'#'ddG-backrub.xml'

if not os.path.isfile(rosetta_scripts_path):
    print('ERROR: "rosetta_scripts_path" variable must be set to the location of the "rosetta_scripts" binary executable')
    print('This file might look something like: "rosetta_scripts.linuxgccrelease"')
    raise Exception('Rosetta scripts missing')

def run_flex_ddg( name, input_path, input_pdb_path, chains_to_move, nstruct_i ):
    output_directory = os.path.join( out_dir_name, os.path.join( name, '%02d' % nstruct_i ) )
    if not os.path.isdir(output_directory):
        os.makedirs(output_directory)

    flex_ddg_args = [
        os.path.abspath(rosetta_scripts_path),
        "-s %s" % os.path.abspath(input_pdb_path),
        '-parser:protocol', os.path.abspath(path_to_script),
        '-parser:script_vars',
        'chainstomove=' + chains_to_move,
        'mutate_resfile_relpath=' + os.path.abspath( os.path.join( input_path, 'nataa_mutations.resfile' ) ),
        # 'number_backrub_trials=%d' % number_backrub_trials,
        'max_minimization_iter=%d' % max_minimization_iter,
        'abs_score_convergence_thresh=%.1f' % abs_score_convergence_thresh,
        # 'backrub_trajectory_stride=%d' % backrub_trajectory_stride ,
        '-restore_talaris_behavior',
        '-in:file:fullatom',
        '-ignore_unrecognized_res',
        '-ignore_zero_occupancy false',
        '-ex1',
        '-ex2',
    ]

    log_path = os.path.join(output_directory, 'rosetta.out')

    print( 'Running Rosetta with args:' )
    print( ' '.join(flex_ddg_args) )
    print( 'Output logged to:', os.path.abspath(log_path) )
    print()

    outfile = open(log_path, 'w')
    process = subprocess.Popen(flex_ddg_args, stdout=outfile, stderr=subprocess.STDOUT, close_fds = True, cwd = output_directory)
    returncode = process.wait()
    outfile.close()

if __name__ == '__main__':
    cases = []
    for nstruct_i in range(1, nstruct + 1 ):
        for case_name in os.listdir(in_dir_name):
            case_path = os.path.join( in_dir_name, case_name )
            for f in os.listdir(case_path):
                if f.endswith('.pdb'):
                    input_pdb_path = os.path.join( case_path, f )
                    break

            with open( os.path.join( case_path, 'chains_to_move.txt' ), 'r' ) as f:
                chains_to_move = f.readlines()[0].strip()

            cases.append( (case_name, case_path, input_pdb_path, chains_to_move, nstruct_i) )

    if use_multiprocessing:
        n_cpus = 31  #
        print(f'Using {n_cpus} CPUs.')
        pool = multiprocessing.Pool(processes=n_cpus)

    for args in cases:
        if use_multiprocessing:
            pool.apply_async( run_flex_ddg, args = args )
        else:
            run_flex_ddg( *args )

    if use_multiprocessing:
        pool.close()
        pool.join()
