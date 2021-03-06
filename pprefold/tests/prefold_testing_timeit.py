#!/usr/bin/env python

# Author: Aretas Gaspariunas
# the CLI parser for the program
# all files distributed with the repository must be located in the same folder for the
# program to be executable

# todo: decimal module; add static typing to .pyx
# loading modules and generating figures are two most performence consuming tasks
import timeit
start_time = timeit.default_timer()
if __name__ == '__main__':

    import argparse
    import re
    from fions import *
    #from fions import *

    elapsed = timeit.default_timer() - start_time
    print (elapsed)
    # CLI argument parser
    parser = argparse.ArgumentParser(
        description='''A CLI tool to predict foldability of a peptide sequence.\n
            The tool is inteded to be used with Python 3.6.\n
            For more information and support please visit: github.com/aretas2/preFold''',
        epilog='Example usage in CLI: "prefold.py -i foo.fasta')
    parser._action_groups.pop()
    required = parser.add_argument_group('required arguments')
    optional = parser.add_argument_group('optional arguments')
    required.add_argument('-i', '--fasta',
        help='Specify the FASTA file with a peptide sequence(s) for foldability prediciton ', required=True)
    optional.add_argument('-ph', '--ph_lvl',
        help='Specify the pH level to be used for the foldability prediction calculation (0.1 < pH < 14).', default=7.4, type=int)
    optional.add_argument('-pka', '--pka_table',
        help='Specify a file with amino acid residue pKa values to be used for the calculation', default='PKA_DATA_CRC.DAT')
    optional.add_argument('-ter', '--ter_include',
        help='Specify the flag for N and C terminal charges to be NOT included in the calculation', action='store_false')
    optional.add_argument('-s', '--step',
        help='Specify the step to be used in the sliding window approach to calculate foldability prediction',
            default=1, type=int)
    optional.add_argument('-k', '--window_size',
        help='Specify the window size to be used for the calculation', default=20, type=int)
    optional.add_argument('-csv', '--output_csv',
        help='Specify this flag if you wish the numerical output to be provided as a .csv file',
            action='store_true')
    optional.add_argument('-z', '--plot_charge',
        help='Specify this flag if you wish the charge of the sequence to be plotted', action='store_true')
    optional.add_argument('-hb', '--plot_hb',
        help='Specify this flag if you wish the phobicity of the sequence to be plotted', action='store_true')
    optional.add_argument('-b', '--boundry',
        help='Specify the boundry for calling disordered regions of peptide sequence', type=float, default=0.005)
    optional.add_argument('-f', '--figure_dpi',
        help='Specify the dpi (resolution) of a figure', type=int, default=200)
    args = parser.parse_args()

    if args.ph_lvl < 0.1 or args.ph_lvl > 14:
        parser.error('Please select pH value in range: 0.1 < pH < 14')

    if args.boundry < 0:
        args.boundry = abs(args.boundry)

    elapsed = timeit.default_timer() - start_time
    print (elapsed)
    # open and parse a fasta file
    try:
        sequence_dict = {} # here all the peptide sequence are stored
        with open(args.fasta) as fasta_file:
            file_2_string = fasta_file.read().split('>')
            for sequence in file_2_string:
                sequence_dict[sequence.split('\n')[0]] = ''.join(sequence.split
                    ('\n')[1:]).upper().replace('*', '')
            del sequence_dict['']
            # check if there a no more than 70 sequencies
            # if len(sequence_dict) > 60:
            #     sys.exit('''There are too many sequencies in the '{0}'file. \
            #         The program is designed to accept up to 60 sequencies at once'''.format(args.fasta))
            # else:
                # pass
            # check if the sequence is a peptide
            for key, value in sequence_dict.items():
                if re.search(r'S|V|L|I|M|F|R|H|Y|W|P|E|D|Q|N|K', value):
                    continue
                else:
                    sys.exit("The input '{0}' sequence(s) is not a peptide sequence".format(key))
            print ('Found {0} peptide sequence(s) in the FASTA file.'.format(len(sequence_dict)))
    except IOError:
        sys.exit('Could not open the file! Please make sure {0} is in fasta format'.format(args.fasta))

    # open and parse normalised amino acid hydrophobicity data
    hb_data_dict = {}
    with open ('HB_DATA_NORM.DAT') as hb_data:
        for line in hb_data:
            hb_data_dict[line.split()[0]] = float(line.split()[1])

    # open and parse pKa data
    try:
        pka_data_dict = {}
        with open (args.pka_table) as pka_data:
            for line in pka_data:
                pka_data_dict[line.split()[0]] = [float(i) for i in line.split()[1:]]
    except IOError:
        sys.exit('Could not open the file! Please make sure {0} is in the right format'.format(args.pka_table))
    elapsed = timeit.default_timer() - start_time
    print (elapsed)

    # performing hydrophobicity, charge and unfoldability data calculation using a sliding window
    data_dict = {}
    for key, value in sequence_dict.items():
        data_dict[key] = unfoldty_sliding_win (args.ph_lvl, args.window_size, args.step,
            value, args.ter_include, args.ter_include, pka_data_dict, hb_data_dict)

    elapsed = timeit.default_timer() - start_time
    print (elapsed)

            # returns pd dataframe with hb, charge and unfold column; stores in dict under the fasta tag as a key
        # TESTING

        #cy = timeit.timeit('fions_cy.unfoldty_sliding_win({}, {}, {}, {}, {}, {}, {}, {})'.format(args.ph_lvl, args.window_size, args.step, value, args.ter_include, args.ter_include, pka_data_dict, hb_data_dict), setup = 'import fions_cy', number=1000)
        # py = timeit.timeit('fions.unfoldty_sliding_win({0}, {1}, {2}, {3}, {4}, {5}, {6}, {7})'.format(args.ph_lvl, args.window_size, args.step, str(value), args.ter_include, args.ter_include, pka_data_dict, hb_data_dict), setup='import fions', number=1000)

        # print (py)
        #print ('Cython is {}x faster'.format(py/cy))

    # generating information statistics, general information and figures for the input
    figure_number = 1
    for key, value in data_dict.items():
        if args.output_csv is True:
            write_data_2_csv (key, value)
        print_data_info (value['unfoldability'], key, sequence_dict, hb_data_dict, pka_data_dict, args.ph_lvl, args.boundry)
        elapsed = timeit.default_timer() - start_time
        print (elapsed)

        generate_figure (value['unfoldability'], value['hydrophobicity'], value['charge'], args.window_size, key, figure_number, args.plot_hb, args.plot_charge, args.figure_dpi)
        figure_number += 1

        elapsed = timeit.default_timer() - start_time
        print (elapsed)
