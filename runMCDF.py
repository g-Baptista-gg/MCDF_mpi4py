import os, sys, platform
import subprocess
import shutil
import re

# MCDFGME executable file name
exe_file = 'mcdfgme2019.exe'

# ARG_MAX of the machine for the parallel command
parallel_max_length = 2097152


# ---------------------------- #
#      PHYSICAL CONSTANTS      #
# ---------------------------- #

hbar = 6.582119569e-16


# -------------------------------------------- #
# Variables to configure the state calculation #
# -------------------------------------------- #

# Perform partial calculation of full calculation (partial for already started energy calculation)
partial = False

# Perform an automatic electron configuration calculation or read from file
label_auto = False

# Atomic number to calculate (Z)
atomic_number = ''
# Use standard nuclear parameters or not
nuc_massyorn = ''
# Nuclear mass for modifyed nuclear model
nuc_mass = 0
# Which nuclear model to use
nuc_model = ''
# Which machine are we runing in (only linnux or darwin are supported)
machine_type = ''
# Machine number of threads available
number_max_of_threads = ''
# User number of threads to use in the calculation
number_of_threads = ''
# Number of electrons in the configurations read from file
nelectrons = ''
# Directory name to hold the calculations
directory_name = ''

# --------------------------------------------------------------- #
# Variables to automatically determine the electron configuration #
#     More data for this algorithm is in Conf.csv and Fir.csv     #
# --------------------------------------------------------------- #

# Shells for the automatic determination of electron configuration
shells = ['1s', '2s', '2p', '3s', '3p', '3d', '4s', '4p', '4d', '4f', '5s', '5p', '5d', '5f', '5g', '6s', '6p', '6d', '6f', '6g', '6h', '7s', '7p', '7d']
# Occupation numbers for the automatic determination of electron configuration
electronspershell = [2, 2, 6, 2, 6, 10, 2, 6, 10, 14, 2, 6, 10, 14, 0, 2, 6, 10, 0, 0, 0, 2, 6, 0]

lines_conf = []
arr_conf = []
nb_lines_conf = 0
lines_fir = []
arr_fir = []
nb_lines_fir = 0
# Determined configuration shells
final_configuration = []
# Determined configuration string
configuration_string = ''


# ------------------------------------ #
# Variables for input and output files #
# ------------------------------------ #

# Files where the 1 hole and 2 holes user configurations are stored
file_conf_rad = "1hole_configurations.txt"
file_conf_aug = "2holes_configurations.txt"
file_conf_sat_aug = "3holes_configurations.txt"
file_conf_shakeup = "shakeup_configurations.txt"

# Log files to know where the calculation has stopped during the state calculation if something goes wrong
file_cycle_log_1hole = ''
file_cycle_log_2holes = ''
file_cycle_log_3holes = ''
file_cycle_log_shakeup = ''

# Log files to store the states readily sorted for rate calculations
file_sorted_1hole = ''
file_sorted_2holes = ''
file_sorted_3holes = ''
file_sorted_shakeup = ''

# Log files to store the calculated transitions
file_calculated_radiative = ''
file_calculated_auger = ''
file_calculated_shakeoff = ''
file_calculated_shakeup = ''

# File with the general parameters for the calculation
file_parameters = ''

# Files with the energy and convergence results for the various atomic states calculated
file_results = ''
file_final_results = ''
file_final_results_1hole = ''
file_final_results_2holes = ''
file_final_results_3holes = ''
file_final_results_shakeup = ''

# Files with the rates for diagram, auger, shake-off and shake-up transitions
file_rates = ''
file_rates_auger = ''
file_rates_shakeoff = ''
file_rates_shakeup = ''

# Files with the calculated diagram, auger, shake-off and shake-up spectra
file_rates_spectrum_diagram = ''
file_rates_spectrum_auger = ''
file_rates_spectrum_shakeoff = ''
file_rates_spectrum_shakeup = ''

# Files with rate sums, used for fluorescence yield determinations
file_rates_sums = ''
file_rates_sums_shakeoff = ''
file_rates_sums_shakeup = ''

# Files with level sums, used for spectra calculation
file_level_widths = ''
file_level_widths_shakeoff = ''
file_level_widths_shakeup = ''


# ------------------------------------------------------------------ #
# Variables with the electron configurations for 1 and 2 hole states #
#  This are the variables used to determine all 1 and 2 hole states  #
#                     that need to be calculated                     #
# ------------------------------------------------------------------ #

# Electron configurations for the 1 hole states
configuration_1hole = []
# Shells for labeling the LS configuration of 1 hole states
shell_array = []

# Electron configurations for the 2 holes states
configuration_2holes = []
# Shells for labeling the LS configuration of 2 holes states
shell_array_2holes = []

# Electron configurations for the 3 holes states
configuration_3holes = []
# Shells for labeling the LS configuration of 3 holes states
shell_array_3holes = []

# Electron configurations for the shake-up states
configuration_shakeup = []
# Shells for labeling the LS configuration of shake-up states
shell_array_shakeup = []

# Flag to control if we can calculate 3 holes state configurations
exist_3holes = False
# Flag to control if we can calculate shake-up state configurations
exist_shakeup = False

# ------------------------------------------------------------------- #
#        Variables to manage the calculated 1 and 2 hole states       #
# These variables will have the quantum numbers to identify the state #
#   as well as various parameters to evaluate the states convergence  #
# ------------------------------------------------------------------- #

# List of calculated 1 hole states and their convergence parameters
calculated1holeStates = []
# List of calculated 2 holes states and their convergence parameters
calculated2holesStates = []
# List of calculated 3 holes states and their convergence parameters
calculated3holesStates = []
# List of calculated shake-up states and their convergence parameters
calculatedShakeupStates = []

# List of 1 hole states that need to be calculated by hand
radiative_by_hand = []
# List of 2 holes states that need to be calculated by hand
auger_by_hand = []
# List of 3 holes states that need to be calculated by hand
sat_auger_by_hand = []
# List of shake-up states that need to be calculated by hand
shakeup_by_hand = []

# Flag to control if we chose to calculate 3 holes state configurations
calculate_3holes = False
# Flag to control if we chose to calculate shake-up state configurations
calculate_shakeup = False


# ------------------------------------------------------------------- #
#             Variables to manage the calculated transtions           #
#    These variables will have the quantum numbers to identify the    #
#      initial and final states as well as various parameters to      #
#                   evaluate the states convergence                   #
# ------------------------------------------------------------------- #

# List of calculated radiative transitions and their energy, rate and multipoles
calculatedRadiativeTransitions = []
# List of calculated auger transitions and their energy and rate
calculatedAugerTransitions = []
# List of calculated satellite transitions and their energy, rate and multipoles
calculatedSatelliteTransitions = []
# List of calculated shake-up transitions and their energy, rate and multipoles
calculatedShakeupTransitions = []


# -------------------------------------------------------- #
# Variables to determine if the state has converged or not #
# -------------------------------------------------------- #

# Energy difference threshold value
diffThreshold = 1.0
# Overlap difference threshold value
overlapsThreshold = 1E-6


# --------------------------------------------------------------------- #
# Variables to hold the string templates for MCDFGME input files (.f05) #
# --------------------------------------------------------------------- #

# String template for regular state calculation with 0 steps
f05Template = ''
# String template for regular state calculation with 10 steps
f05Template_10steps = ''
# String template for regular state calculation with 10 steps and modifyed orbital calculation
f05Template_10steps_Forbs = ''
# String template for radiative transition calculation
f05RadTemplate = ''
# String template for auger transition calculation
f05AugTemplate = ''

# String template for regular state calculation with 0 steps and nuclear mod options
f05Template_nuc = ''
# String template for regular state calculation with 10 steps and nuclear mod options
f05Template_10steps_nuc = ''
# String template for regular state calculation with 10 steps, modifyed orbital calculation and nuclear mod options
f05Template_10steps_Forbs_nuc = ''
# String template for radiative transition calculation and nuclear mod options
f05RadTemplate_nuc = ''
# String template for auger transition calculation and nuclear mod options
f05AugTemplate_nuc = ''

# String template for the .dat file required to configure the MCDFGME calculation directory
mdfgmeFile = '	   nblipa=75 tmp_dir=./tmp/\n	   f05FileName\n	   0.\n'


# ------------------------------------------ #
# Variables for root directory configuration #
# ------------------------------------------ #

# Root directory where the script is located
rootDir = os.getcwd()




def setupTemplates():
    global f05Template, f05Template_10steps, f05Template_10steps_Forbs, f05RadTemplate, f05AugTemplate
    global f05Template_nuc, f05Template_10steps_nuc, f05Template_10steps_Forbs_nuc, f05RadTemplate_nuc, f05AugTemplate_nuc
    
    with open("f05_2019.f05", "r") as template:
        f05Template = ''.join(template.readlines())
    with open("f05_2019nstep1.f05", "r") as template:
        f05Template_10steps = ''.join(template.readlines())
    with open("f05_2019nstep2.f05", "r") as template:
        f05Template_10steps_Forbs = ''.join(template.readlines())
    with open("f05_2019_radiative.f05", "r") as template:
        f05RadTemplate = ''.join(template.readlines())
    with open("f05_2019_auger.f05", "r") as template:
        f05AugTemplate = ''.join(template.readlines())
    
    
    with open("f05_2019r.f05", "r") as template:
        f05Template_nuc = ''.join(template.readlines())
    with open("f05_2019nstep1r.f05", "r") as template:
        f05Template_10steps_nuc = ''.join(template.readlines())
    with open("f05_2019nstep2r.f05", "r") as template:
        f05Template_10steps_Forbs_nuc = ''.join(template.readlines())
    with open("f05_2019_radiativer.f05", "r") as template:
        f05RadTemplate_nuc = ''.join(template.readlines())
    with open("f05_2019_augerr.f05", "r") as template:
        f05AugTemplate_nuc = ''.join(template.readlines())


def loadElectronConfigs():
    global lines_conf, arr_conf, nb_lines_conf, lines_fir, arr_fir, nb_lines_fir, final_configuration, configuration_string
    global configuration_1hole, shell_array
    global configuration_2holes, shell_array_2holes
    global configuration_3holes, shell_array_3holes
    global configuration_shakeup, shell_array_shakeup
    global exist_3holes, exist_shakeup, calculate_3holes, calculate_shakeup
    
    
    count = 0
    
    if label_auto:
        enum = int(atomic_number) - 1
        
        # Initialize the array of shells and electron number
        remain_elec = enum
        electron_array = []
        
        i = 0
        while remain_elec > 0:
            shell_array.append(shells[i])
            
            if remain_elec >= electronspershell[i]:
                configuration_string += "(" + shell_array[i] + ")" + str(electronspershell[i]) + " "
                electron_array.append(electronspershell[i])
            else:
                configuration_string += "(" + shell_array[i] + ")" + str(remain_elec) + " "
                electron_array.append(remain_elec)
            
            remain_elec -= electronspershell[i]
            i += 1
        
        exist_3holes = True
        exist_shakeup = True
        
        for i in range(len(shell_array)):
            # Generate the combinations of 1 hole configurations
            b = electron_array[:]
            b[i] -= 1
            
            if b[i] >= 0:
                configuration_1hole.append('')
                
                for j in range(len(shell_array)):
                    configuration_1hole[-1] += "(" + shell_array[j] + ")" + str(b[j]) + " "
                    
                    if j >= i:
                        # Generate the combinations of 2 hole configurations                        
                        b[j] -= 1
                        
                        if b[j] >= 0:
                            shell_array_2holes.append(shell_array[i] + "_" + shell_array[j])
                            configuration_2holes.append('')
                            
                            for h in range(len(shell_array)):
                                configuration_2holes[-1] += "(" + shell_array[h] + ")" + str(b[h]) + " "
                                
                                if h >= j:
                                    # Generate the combinations of 3 hole configurations
                                    b[h] -= 1
                                    
                                    if b[h] >= 0:
                                        shell_array_3holes.append(shell_array[i] + "_" + shell_array[j] + "_" + shell_array[h])
                                        configuration_3holes.append('')
                                        
                                        for k in range(len(shell_array)):
                                            configuration_3holes[-1] += "(" + shell_array[k] + ")" + str(b[k]) + " "
                                    
                                    b[h] += 1
                            
                            for h in range(len(shells)):
                                if h >= j:
                                    # Generate the combinations of shake-up configurations
                                    if h < len(shell_array):
                                        b[h] += 1
                                    
                                    if b[h] <= electronspershell[h]:
                                        shell_array_shakeup.append(shell_array[i] + "_" + shell_array[j] + "-" + shell_array[h])
                                        configuration_shakeup.append('')
                                        
                                        for k, shell in enumerate(shells):
                                            if k < len(shell_array):
                                                configuration_shakeup[-1] += "(" + shell_array[k] + ")" + str(b[k]) + " "
                                            elif h == k:
                                                configuration_shakeup[-1] += "(" + shell + ")1"
                                            
        
        
        print("Loaded the automatically generated electron configuration:\n\n")
        print("Element Z=" + atomic_number + "\n")
        print("Atom ground-state Neutral configuration:\n" + configuration_string + "\n")
        print("Number of occupied orbitals = " + str(count) + "\n")
        
        print("\nBoth 3 hole configurations and shake-up configurations were generated.\n")
        print "Would you like to calculate these configurations? - both, 3holes or shakeup : ",
        inp = raw_input().strip()
        while inp != 'both' or inp != '3holes' or inp != 'shakeup':
            print("\n keyword must be both, 3holes or shakeup!!!")
            print "Would you like to calculate this configurations? - both, 3holes or shakeup : ",
            inp = raw_input().strip()
        
        if inp == 'both':
            calculate_3holes = True
            calculate_shakeup = True
        elif inp == '3holes':
            calculate_3holes = True
        elif inp == 'shakeup':
            calculate_shakeup = True
    else:
        # Check if the files with the configurations for 1 and 2 holes to be read exist
        
        if os.path.exists(directory_name + "/backup_" + file_conf_rad) and os.path.exists(directory_name + "/backup_" + file_conf_aug):
            configuration_1hole = []
            shell_array = []
            
            with open(file_conf_rad, "r") as f:
                for line in f:
                    colum1, colum2 = line.strip().split(",")
                    configuration_1hole.append(colum1)
                    shell_array.append(colum2)
                    count += 1
            
            configuration_2holes = []
            shell_array_2holes = []
            
            with open(file_conf_aug, "r") as f:
                for line in f:
                    colum1, colum2 = line.strip().split(",")
                    configuration_2holes.append(colum1)
                    shell_array_2holes.append(colum2)
            
            print("Configuration files correctly loaded !!!\n")
        else:
            print("Configuration files do not exist !!! Place them alongside this script and name them:")
            print(file_conf_rad)
            print(file_conf_aug)
            sys.exit(1)
        
        
        # Check if the files with the configurations for 3 holes to be read exist
        
        if os.path.exists(directory_name + "/backup_" + file_conf_sat_aug):
            configuration_3holes = []
            shell_array = []
            
            with open(file_conf_sat_aug, "r") as f:
                for line in f:
                    colum1, colum2 = line.strip().split(",")
                    configuration_3holes.append(colum1)
                    shell_array_3holes.append(colum2)
                    count += 1
            
            print("Configuration files correctly loaded for 3 holes !!!\n")
        else:
            print("Configuration files do not exist for 3 holes !!! If you wish to calculate them, place the file alongside this script and name them:")
            print("backup_" + file_conf_sat_aug)
        
        
        # Check if the files with the configurations for shakeup to be read exist
        
        if os.path.exists(directory_name + "/backup_" + file_conf_shakeup):
            configuration_shakeup = []
            shell_array_shakeup = []
            
            with open(file_conf_shakeup, "r") as f:
                for line in f:
                    colum1, colum2 = line.strip().split(",")
                    configuration_shakeup.append(colum1)
                    shell_array_shakeup.append(colum2)
            
            print("Configuration files correctly loaded for Shake-up !!!\n")
        else:
            print("Configuration files do not exist for shake-up !!! If you wish to calculate them, place the file alongside this script and name them:")
            print("backup_" + file_conf_shakeup)
    


def checkPartial():
    global directory_name, parallel_max_length, machine_type, number_max_of_threads
    global label_auto, atomic_number, nelectrons, nuc_massyorn, nuc_mass, nuc_model, number_of_threads
    global calculated1holeStates, calculated2holesStates, calculated3holesStates, calculatedShakeupStates
    global exist_3holes, exist_shakeup, calculate_3holes, calculate_shakeup
    
    
    print "Enter directory name for the calculations: ",
    inp = raw_input().strip()
    while inp == '':
        print("\n No input entered!!!\n\n")
        print "Enter directory name for the calculations: ",
        inp = raw_input().strip()

    while not os.path.exists(inp):
        print("\n Directory name does not exist!!!\n\n")
        print "Please input the name for the existing calculations directory: ",
        inp = raw_input().strip()
    
    
    directory_name = inp
    
    parallel_max_length = int(subprocess.check_output(['getconf', 'ARG_MAX']).strip())
    
    machine_type = platform.uname()[0]
    
    if machine_type == 'Darwin':
        number_max_of_threads = subprocess.check_output(['sysctl', '-n', 'hw.ncpu']).strip()
    else:
        number_max_of_threads = subprocess.check_output(['nproc']).strip()
    
    setupFiles()
    
    
    with open(file_parameters, "r") as fp:
        for line in fp:
            if "Electron configurations are:" in line:
                label_auto = line.replace("Electron configurations are:", "").strip() == "automatic"
            elif "3 hole configurations are being calculated!" in line:
                exist_3holes = True
                calculate_3holes = True
            elif "Shake-up configurations are being calculated!" in line:
                exist_shakeup = True
                calculate_shakeup = True
            elif "Atomic number Z= " in line:
                atomic_number = line.replace("Atomic number Z= ", "").strip()
            elif "Number of electrons:" in line:
                nelectrons = line.replace("Number of electrons:", "").strip()
            elif "Calculations performed with standard mass:" in line:
                nuc_massyorn = line.replace("Calculations performed with standard mass:", "").strip()
            elif "Nuclear mass:" in line:
                nuc_mass = int(line.replace("Nuclear mass:", "").strip())
            elif "Nuclear model:" in line:
                nuc_model = line.replace("Nuclear model:", "").strip()
            elif "Number of considered threads in the calculation=" in line:
                number_of_threads = line.replace("Number of considered threads in the calculation=", "").strip()
    
    if int(number_of_threads) > int(number_max_of_threads):
        print("Previous number of threads is greater than the current machine's maximum. Proceding with the current maximum threads...\n")
        number_of_threads = number_max_of_threads
    
    loadElectronConfigs()
    
    
    def readStateList():
        global calculated1holeStates, calculated2holesStates, calculate3holesStates, calculateShakeupStates
        
        complete_1hole = False
        complete_2holes = False
        complete_3holes = False
        complete_shakeup = False
        
        last_calculated_cycle_1hole = 0
        last_calculated_cycle_2holes = 0
        last_calculated_cycle_3holes = 0
        last_calculated_cycle_shakeup = 0
        
        last_calculated_state_1hole = [(0, 0, 0)]
        last_calculated_state_2holes = [(0, 0, 0)]
        last_calculated_state_3holes = [(0, 0, 0)]
        last_calculated_state_shakeup = [(0, 0, 0)]
        
        with open(file_cycle_log_1hole, "r") as calculated1hole:
            if "1 hole states discovery done." in calculated1hole.readline():
                calculated1hole.readline()
                for line in calculated1hole:
                    if "ListEnd" in line:
                        complete_1hole = True
                    
                    if "First Cycle Last Calculated:" in line:
                        last_calculated_cycle_1hole = 1
                    elif "Second Cycle Last Calculated:" in line:
                        last_calculated_cycle_1hole = 2
                    elif "Third Cycle Last Calculated:" in line:
                        last_calculated_cycle_1hole = 3
                    elif "Fourth Cycle Last Calculated:" in line or "CalculationFinalized" in line:
                        last_calculated_cycle_1hole = 4
                    elif last_calculated_cycle_1hole > 0 and line != "\n":
                        last_calculated_state_1hole = [tuple(int(qn) for qn in line.strip().split(", "))]
                    
                    if not complete_1hole:
                        calculated1holeStates.append([tuple(int(qn) for qn in line.strip().split(", "))])
        
        with open(file_cycle_log_2holes, "r") as calculated2holes:
            if "2 holes states discovery done." in calculated2holes.readline():
                calculated2holes.readline()
                for line in calculated2holes:
                    if "ListEnd" in line:
                        complete_2holes = True
                    
                    if "First Cycle Last Calculated:" in line:
                        last_calculated_cycle_2holes = 1
                    elif "Second Cycle Last Calculated:" in line:
                        last_calculated_cycle_2holes = 2
                    elif "Third Cycle Last Calculated:" in line:
                        last_calculated_cycle_2holes = 3
                    elif "Fourth Cycle Last Calculated:" in line or "CalculationFinalized" in line:
                        last_calculated_cycle_2holes = 4
                    elif last_calculated_cycle_2holes > 0 and line != "\n":
                        last_calculated_state_2holes = [tuple(int(qn) for qn in line.strip().split(", "))]
                    
                    if not complete_2holes:
                        calculated2holesStates.append([tuple(int(qn) for qn in line.strip().split(", "))])
        
        if calculate_3holes:
            with open(file_cycle_log_3holes, "r") as calculated3holes:
                if "3 holes states discovery done." in calculated3holes.readline():
                    calculated3holes.readline()
                    for line in calculated3holes:
                        if "ListEnd" in line:
                            complete_3holes = True
                        
                        if "First Cycle Last Calculated:" in line:
                            last_calculated_cycle_3holes = 1
                        elif "Second Cycle Last Calculated:" in line:
                            last_calculated_cycle_3holes = 2
                        elif "Third Cycle Last Calculated:" in line:
                            last_calculated_cycle_3holes = 3
                        elif "Fourth Cycle Last Calculated:" in line or "CalculationFinalized" in line:
                            last_calculated_cycle_3holes = 4
                        elif last_calculated_cycle_3holes > 0 and line != "\n":
                            last_calculated_state_3holes = [tuple(int(qn) for qn in line.strip().split(", "))]
                        
                        if not complete_3holes:
                            calculate3holesStates.append([tuple(int(qn) for qn in line.strip().split(", "))])
        
        if calculate_shakeup:
            with open(file_cycle_log_shakeup, "r") as calculatedShakeup:
                if "shake-up states discovery done." in calculatedShakeup.readline():
                    calculatedShakeup.readline()
                    for line in calculatedShakeup:
                        if "ListEnd" in line:
                            complete_shakeup = True
                        
                        if "First Cycle Last Calculated:" in line:
                            last_calculated_cycle_shakeup = 1
                        elif "Second Cycle Last Calculated:" in line:
                            last_calculated_cycle_shakeup = 2
                        elif "Third Cycle Last Calculated:" in line:
                            last_calculated_cycle_shakeup = 3
                        elif "Fourth Cycle Last Calculated:" in line or "CalculationFinalized" in line:
                            last_calculated_cycle_shakeup = 4
                        elif last_calculated_cycle_shakeup > 0 and line != "\n":
                            last_calculated_state_shakeup = [tuple(int(qn) for qn in line.strip().split(", "))]
                        
                        if not complete_shakeup:
                            calculateShakeupStates.append([tuple(int(qn) for qn in line.strip().split(", "))])
        
        return complete_1hole, complete_2holes, complete_3holes, complete_shakeup, \
                last_calculated_cycle_1hole, last_calculated_state_1hole, \
                last_calculated_cycle_2holes, last_calculated_state_2holes, \
                last_calculated_cycle_3holes, last_calculated_state_3holes, \
                last_calculated_cycle_shakeup, last_calculated_state_shakeup
    
    
    def readSortedStates():
        global calculated1holeStates, calculated2holesStates, calculated3holesStates, calculatedShakeupStates
        
        complete_sorted_1hole = False
        complete_sorted_2holes = False
        complete_sorted_3holes = False
        complete_sorted_shakeup = False
        
        with open(file_sorted_1hole, "r") as sorted_1hole:
            if len(sorted_1hole.readlines()) == len(calculated1holeStates):
                complete_sorted_1hole = True
        
        if complete_sorted_1hole:
            with open(file_sorted_1hole, "r") as sorted_1hole:
                calculated1holeStates = []
                for line in sorted_1hole:
                    state_nums = tuple(int(qn) for qn in line.strip().split("; ")[0].split(", "))
                    state_parameters = tuple(par if i == 0 else float(par) for i, par in enumerate(line.strip().split("; ")[1].split(", ")))
                    calculated1holeStates.append([state_nums, state_parameters])
        
        with open(file_sorted_2holes, "r") as sorted_2holes:
            if len(sorted_2holes.readlines()) == len(calculated2holesStates):
                complete_sorted_2holes = True
        
        if complete_sorted_2holes:
            with open(file_sorted_2holes, "r") as sorted_2holes:
                calculated2holesStates = []
                for line in sorted_2holes:
                    state_nums = tuple(int(qn) for qn in line.strip().split("; ")[0].split(", "))
                    state_parameters = tuple(par if i == 0 else float(par) for i, par in enumerate(line.strip().split("; ")[1].split(", ")))
                    calculated2holesStates.append([state_nums, state_parameters])
        
        if calculate_3holes:
            with open(file_sorted_3holes, "r") as sorted_3holes:
                if len(sorted_3holes.readlines()) == len(calculated3holesStates):
                    complete_sorted_3holes = True
            
            if complete_sorted_3holes:
                with open(file_sorted_3holes, "r") as sorted_3holes:
                    calculated3holesStates = []
                    for line in sorted_3holes:
                        state_nums = tuple(int(qn) for qn in line.strip().split("; ")[0].split(", "))
                        state_parameters = tuple(par if i == 0 else float(par) for i, par in enumerate(line.strip().split("; ")[1].split(", ")))
                        calculated3holesStates.append([state_nums, state_parameters])
        
        if calculate_shakeup:
            with open(file_sorted_shakeup, "r") as sorted_shakeup:
                if len(sorted_shakeup.readlines()) == len(calculatedShakeupStates):
                    complete_sorted_shakeup = True
            
            if complete_sorted_shakeup:
                with open(file_sorted_shakeup, "r") as sorted_shakeup:
                    calculatedShakeupStates = []
                    for line in sorted_shakeup:
                        state_nums = tuple(int(qn) for qn in line.strip().split("; ")[0].split(", "))
                        state_parameters = tuple(par if i == 0 else float(par) for i, par in enumerate(line.strip().split("; ")[1].split(", ")))
                        calculatedShakeupStates.append([state_nums, state_parameters])
        
        return complete_sorted_1hole, complete_sorted_2holes, complete_sorted_3holes, complete_sorted_shakeup
    
    
    def readTransitions():
        # Radiative transitions
        if os.path.isfile(file_calculated_radiative):
            with open(file_calculated_radiative, "r") as rad_calculated:
                rad_calculated.readline()
                for line in rad_calculated:
                    if line != "\n":
                        state_i = tuple(int(qn) for qn in line.strip().split(" => ")[0].split(", "))
                        state_f = tuple(int(qn) for qn in line.strip().split(" => ")[1].split(", "))
                        
                        last_rad_calculated = [state_i, state_f]
        else:
            last_rad_calculated = False
        
        # Auger transitions
        if os.path.isfile(file_calculated_auger):
            with open(file_calculated_auger, "r") as aug_calculated:
                aug_calculated.readline()
                for line in aug_calculated:
                    if line != "\n":
                        state_i = tuple(int(qn) for qn in line.strip().split(" => ")[0].split(", "))
                        state_f = tuple(int(qn) for qn in line.strip().split(" => ")[1].split(", "))
                        
                        last_aug_calculated = [state_i, state_f]
        else:
            last_aug_calculated = False
        
        # Shake-off transitions
        if os.path.isfile(file_calculated_shakeoff):
            with open(file_calculated_shakeoff, "r") as sat_calculated:
                sat_calculated.readline()
                for line in sat_calculated:
                    if line != "\n":
                        state_i = tuple(int(qn) for qn in line.strip().split(" => ")[0].split(", "))
                        state_f = tuple(int(qn) for qn in line.strip().split(" => ")[1].split(", "))
                        
                        last_sat_calculated = [state_i, state_f]
        else:
            last_sat_calculated = False
        
        # Shake-up transitions
        if os.path.isfile(file_calculated_shakeup):
            with open(file_calculated_shakeup, "r") as shakeup_calculated:
                shakeup_calculated.readline()
                for line in shakeup_calculated:
                    if line != "\n":
                        state_i = tuple(int(qn) for qn in line.strip().split(" => ")[0].split(", "))
                        state_f = tuple(int(qn) for qn in line.strip().split(" => ")[1].split(", "))
                        
                        last_shakeup_calculated = [state_i, state_f]
        else:
            last_shakeup_calculated = False
        
        
        return last_rad_calculated, last_aug_calculated, last_sat_calculated, last_shakeup_calculated
    
    
    if not os.path.isfile(exe_file):
        print("$\nERROR!!!!!\n")
        print("\nFile DOES NOT EXIST \nPlease place MCDFGME*.exe file alongside this script\n")
    else:
        print("\n############## Energy Calculations with MCDGME code  ##############\n\n")
        
        # Check if any of the files with transitions exist
        if any([os.path.isfile(file_calculated_radiative), os.path.isfile(file_calculated_auger), os.path.isfile(file_calculated_shakeoff), os.path.isfile(file_calculated_shakeup)]):
            print("\nFound files with the last calculated transitions.")
            
            # Check for consistency if the files with the states logs exist
            # Only the 1 hole and 2 hole are strictly necessary to continue with calculations
            if os.path.isfile(file_cycle_log_1hole) and os.path.isfile(file_cycle_log_2holes):
                print("\nFound file with the list of discovered states.")
                
                # Read the state list and get flags to perform some more flow control
                complete_1hole, complete_2holes, complete_3holes, complete_shakeup, \
                last_calculated_cycle_1hole, last_calculated_state_1hole, \
                last_calculated_cycle_2holes, last_calculated_state_2holes, \
                last_calculated_cycle_3holes, last_calculated_state_3holes, \
                last_calculated_cycle_shakeup, last_calculated_state_shakeup = readStateList()
                
                # If the 3 hole and shake-up configurations are supposed to be calculated
                if calculate_3holes and calculate_shakeup:
                    # Check if all state discovery lists are complete
                    # Also check if the last calculated cycles and states are the expected ones
                    if complete_1hole and complete_2holes and complete_3holes and complete_shakeup and \
                        last_calculated_cycle_1hole == 4 and last_calculated_cycle_2holes == 4 and last_calculated_cycle_3holes == 4 and last_calculated_cycle_shakeup == 4 \
                        last_calculated_state_1hole[0] == calculated1holeStates[-1][0] and last_calculated_state_2holes[0] == calculated2holesStates[-1][0] \
                        last_calculated_state_3holes[0] == calculated3holesStates[-1][0] and last_calculated_state_shakeup[0] == calculatedShakeupStates[-1][0]:
                        print("\nVerifyed that the file with the list of calculated states is consistent.")
                        print("Proceding with this list.")
                    else:
                        # Print some debug information if the flag values are not what expected
                        # This is done because transition files were already found
                        print("\nError while checking the file with calculated states.\n")
                        print("Flag                          -> Value ; Expected:")
                        print("Completed 1 hole              -> " + str(complete_1hole) + " ; True")
                        print("Completed 2 holes             -> " + str(complete_2holes) + " ; True")
                        print("Completed 3 holes             -> " + str(complete_3holes) + " ; True")
                        print("Completed Shake-up            -> " + str(complete_shakeup) + " ; True")
                        print("Last calculated cycle 1 hole  -> " + str(last_calculated_cycle_1hole) + "    ; 4")
                        print("Last calculated cycle 2 holes -> " + str(last_calculated_cycle_2holes) + "    ; 4")
                        print("Last calculated cycle 3 holes -> " + str(last_calculated_cycle_3holes) + "    ; 4")
                        print("Last calculated cycle shake-up-> " + str(last_calculated_cycle_shakeup) + "    ; 4")
                        print("Last calculated state 1 hole  -> " + ', '.join([str(qn) for qn in last_calculated_state_1hole[0]]) + " ; " + ', '.join([str(qn) for qn in calculated1holeStates[-1][0]]))
                        print("Last calculated state 2 holes -> " + ', '.join([str(qn) for qn in last_calculated_state_2holes[0]]) + " ; " + ', '.join([str(qn) for qn in calculated2holesStates[-1][0]]))
                        print("Last calculated state 3 holes -> " + ', '.join([str(qn) for qn in last_calculated_state_3holes[0]]) + " ; " + ', '.join([str(qn) for qn in calculated3holesStates[-1][0]]))
                        print("Last calculated state shake-up-> " + ', '.join([str(qn) for qn in last_calculated_state_shakeup[0]]) + " ; " + ', '.join([str(qn) for qn in calculatedShakeupStates[-1][0]]))
                        
                        print("\nPicking up from the last calculated states...\n")
                        
                        # Return the flags for later flow control to decide which calculations to perform and where to start those calculations
                        return complete_1hole, complete_2holes, complete_3holes, complete_shakeup, \
                                last_calculated_cycle_1hole, last_calculated_cycle_2holes, last_calculated_cycle_3holes, last_calculated_cycle_shakeup, \
                                last_calculated_state_1hole[0], last_calculated_state_2holes[0], last_calculated_state_3holes[0], last_calculated_state_shakeup[0]
                # If the 3 hole configurations are supposed to be calculated
                elif calculate_3holes:
                    # Check if all state discovery lists are complete, except for the shake-up ones
                    # Also check if the last calculated cycles and states are the expected ones
                    if complete_1hole and complete_2holes and complete_3holes and \
                        last_calculated_cycle_1hole == 4 and last_calculated_cycle_2holes == 4 and last_calculated_cycle_3holes == 4 \
                        last_calculated_state_1hole[0] == calculated1holeStates[-1][0] and last_calculated_state_2holes[0] == calculated2holesStates[-1][0] \
                        last_calculated_state_3holes[0] == calculated3holesStates[-1][0]:
                        print("\nVerifyed that the file with the list of calculated states is consistent.")
                        print("Proceding with this list.")
                    else:
                        # Print some debug information if the flag values are not what expected
                        # This is done because transition files were already found
                        print("\nError while checking the file with calculated states.\n")
                        print("Flag                          -> Value ; Expected:")
                        print("Completed 1 hole              -> " + str(complete_1hole) + " ; True")
                        print("Completed 2 holes             -> " + str(complete_2holes) + " ; True")
                        print("Completed 3 holes             -> " + str(complete_3holes) + " ; True")
                        print("Completed Shake-up            ->  N/A  ; N/A")
                        print("Last calculated cycle 1 hole  -> " + str(last_calculated_cycle_1hole) + "    ; 4")
                        print("Last calculated cycle 2 holes -> " + str(last_calculated_cycle_2holes) + "    ; 4")
                        print("Last calculated cycle 3 holes -> " + str(last_calculated_cycle_3holes) + "    ; 4")
                        print("Last calculated cycle shake-up->  N/A  ; N/A")
                        print("Last calculated state 1 hole  -> " + ', '.join([str(qn) for qn in last_calculated_state_1hole[0]]) + " ; " + ', '.join([str(qn) for qn in calculated1holeStates[-1][0]]))
                        print("Last calculated state 2 holes -> " + ', '.join([str(qn) for qn in last_calculated_state_2holes[0]]) + " ; " + ', '.join([str(qn) for qn in calculated2holesStates[-1][0]]))
                        print("Last calculated state 3 holes -> " + ', '.join([str(qn) for qn in last_calculated_state_3holes[0]]) + " ; " + ', '.join([str(qn) for qn in calculated3holesStates[-1][0]]))
                        print("Last calculated state shake-up->  N/A  ; N/A")
                        
                        print("\nPicking up from the last calculated states...\n")
                        
                        # Return the flags for later flow control to decide which calculations to perform and where to start those calculations
                        return complete_1hole, complete_2holes, complete_3holes, complete_shakeup, \
                                last_calculated_cycle_1hole, last_calculated_cycle_2holes, last_calculated_cycle_3holes, last_calculated_cycle_shakeup, \
                                last_calculated_state_1hole[0], last_calculated_state_2holes[0], last_calculated_state_3holes[0], last_calculated_state_shakeup[0]
                # If the shake-up configurations are supposed to be calculated
                elif calculate_shakeup:
                    # Check if all state discovery lists are complete, except for the shake-up ones
                    # Also check if the last calculated cycles and states are the expected ones
                    if complete_1hole and complete_2holes and complete_shakeup and \
                        last_calculated_cycle_1hole == 4 and last_calculated_cycle_2holes == 4 and last_calculated_cycle_shakeup == 4 \
                        last_calculated_state_1hole[0] == calculated1holeStates[-1][0] and last_calculated_state_2holes[0] == calculated2holesStates[-1][0] \
                        last_calculated_state_shakeup[0] == calculatedShakeupStates[-1][0]:
                        print("\nVerifyed that the file with the list of calculated states is consistent.")
                        print("Proceding with this list.")
                    else:
                        # Print some debug information if the flag values are not what expected
                        # This is done because transition files were already found
                        print("\nError while checking the file with calculated states.\n")
                        print("Flag                          -> Value ; Expected:")
                        print("Completed 1 hole              -> " + str(complete_1hole) + " ; True")
                        print("Completed 2 holes             -> " + str(complete_2holes) + " ; True")
                        print("Completed 3 holes             ->  N/A  ; N/A")
                        print("Completed Shake-up            -> " + str(complete_shakeup) + " ; True")
                        print("Last calculated cycle 1 hole  -> " + str(last_calculated_cycle_1hole) + "    ; 4")
                        print("Last calculated cycle 2 holes -> " + str(last_calculated_cycle_2holes) + "    ; 4")
                        print("Last calculated cycle 3 holes ->  N/A  ; N/A")
                        print("Last calculated cycle shake-up-> " + str(last_calculated_cycle_shakeup) + "    ; 4")
                        print("Last calculated state 1 hole  -> " + ', '.join([str(qn) for qn in last_calculated_state_1hole[0]]) + " ; " + ', '.join([str(qn) for qn in calculated1holeStates[-1][0]]))
                        print("Last calculated state 2 holes -> " + ', '.join([str(qn) for qn in last_calculated_state_2holes[0]]) + " ; " + ', '.join([str(qn) for qn in calculated2holesStates[-1][0]]))
                        print("Last calculated state 3 holes ->   N/A  ; N/A")
                        print("Last calculated state shake-up-> " + ', '.join([str(qn) for qn in last_calculated_state_shakeup[0]]) + " ; " + ', '.join([str(qn) for qn in calculatedShakeupStates[-1][0]]))
                        
                        print("\nPicking up from the last calculated states...\n")
                        
                        # Return the flags for later flow control to decide which calculations to perform and where to start those calculations
                        return complete_1hole, complete_2holes, complete_3holes, complete_shakeup, \
                                last_calculated_cycle_1hole, last_calculated_cycle_2holes, last_calculated_cycle_3holes, last_calculated_cycle_shakeup, \
                                last_calculated_state_1hole[0], last_calculated_state_2holes[0], last_calculated_state_3holes[0], last_calculated_state_shakeup[0]
            else:
                # Print the file names that are missing
                print("\nFile with the list of discovered states is missing: ")
                print("1 hole states -> " + file_cycle_log_1hole)
                print("2 holes states -> " + file_cycle_log_2holes)
                
                # Print the missing file names if the calculations where expected
                if calculate_3holes:
                    print("3 holes states -> " + file_cycle_log_3holes)
                if calculate_shakeup:
                    print("Shake-up states -> " + file_cycle_log_shakeup)
                
                print("\nReverting to full calculation...\n")
                
                # Return 1 as a flag to revert to a full calculation instead of a partial one as there are inconsistencies
                return 1
            
            # Check for consistency if the files with the sorted states exist
            # Only the 1 hole and 2 hole are strictly necessary to continue with calculations
            if os.path.isfile(file_sorted_1hole) and os.path.isfile(file_sorted_2holes):
                print("\nFound files with energy sorted calculated states.")
                
                # Check if the list of sorted states are complete by comparing the number of sorted states to the number of total states
                complete_sorted_1hole, complete_sorted_2holes, complete_sorted_3holes, complete_sorted_shakeup = readSortedStates()
                
                # If we expect to calculate the 3 hole states
                if calculate_3holes:
                    # Check if the sorted 3 hole states were completed
                    if not complete_sorted_3holes:
                        print("\nError while reading the sorted states files.")
                        print("There was a missmatch between the length of sorted states and calculated states for 3 hole configurations.")
                        print("Continuing with the full list of states and resorting them.")
                        
                        # Return 2 as a flag to continue the calculation with the list of total states and resort them
                        return 2
                
                # Check if the list of sorted states are complete for 1 hole and 2 hole states that are necessary for the main calculation
                if complete_sorted_1hole and complete_sorted_2holes:
                    print("\nEnergy sorted calculated states files are complete.")
                    print("Proceding while using this state list.")
                    
                    # Read the transition list for all possible transitons, independently if they are supposed to be calculated or not
                    last_rad_calculated, last_aug_calculated, last_sat_calculated, last_shakeup_calculated = readTransitions()
                    
                    # Radiative, Auger and Shake-off
                    
                    # Check if the last calculated radiative transition is the expected one
                    if type(last_rad_calculated) != type(True):
                        print("\nRead last calculated radiative transition.")
                        
                        if last_rad_calculated[0] == calculated1holeStates[-1][0] and last_rad_calculated[1] == calculated1holeStates[-1][0]:
                            last_rad_calculated = True
                    else:
                        print("\nError reading last calculated radiative transition.")
                        print("Redoing this calculation from the start.")
                    
                    # Check if the last calculated auger transition is the expected one
                    if type(last_aug_calculated) != type(True):
                        print("\nRead last calculated auger transition.")
                        
                        if last_aug_calculated[0] == calculated1holeStates[-1][0] and last_aug_calculated[1] == calculated2holesStates[-1][0]:
                            last_aug_calculated = True
                    else:
                        print("\nError reading last calculated auger transition.")
                        print("Redoing this calculation from the start.")
                    
                    # Check if the last calculated shake-off transition is the expected one
                    if type(last_sat_calculated) != type(True):
                        print("\nRead last calculated satellite transition.")
                        
                        if last_sat_calculated[0] == calculated2holesStates[-1][0] and last_sat_calculated[1] == calculated2holesStates[-1][0]:
                            last_sat_calculated = True
                    else:
                        print("\nError reading last calculated satellite transition.")
                        print("Redoing this calculation from the start.")
                    
                    
                    # Shake-up
                    
                    # If the shake-up transitions are supposed to be calculated
                    if calculate_shakeup:
                        # Check if the list of sorted states are complete for shake-up states
                        if complete_sorted_shakeup:
                            # Check if the last calcualted shake-up transition is the expected one
                            if type(last_shakeup_calculated) != type(True):
                                print("\nRead last calculated shake-up transition.")
                                
                                if last_shakeup_calculated[0] == calculatedShakeupStates[-1][0] and last_shakeup_calculated[1] == calculatedShakeupStates[-1][0]:
                                    last_shakeup_calculated = True
                            else:
                                print("\nError reading last calculated shake-up transition.")
                                print("Redoing this calculation from the start.")
                        else:
                            print("\nError while reading the sorted states files.")
                            print("There was a missmatch between the length of sorted states and calculated states for shake-up configurations.")
                            print("Continuing with the full list of states and resorting them.")
                            
                            # Return 2 as a flag to continue the calculation with the list of total states and resort them
                            return 2
                    
                    # Return the last calculated transitions to know where to start calculating from
                    return last_rad_calculated, last_aug_calculated, last_sat_calculated, last_shakeup_calculated
                else:
                    print("\nError while reading the sorted states files.")
                    print("There was a missmatch between the length of sorted states and calculated states.")
                    print("Continuing with the full list of states and resorting them.")
                    
                    # Return 2 as a flag to continue the calculation with the list of total states and resort them
                    return 2
            
            # Return 0 as a flag to know everything went as expected
            return 0
        
        
        # If there is no transition files, check if the files with the sorted states exist
        # Only the 1 hole and 2 hole are strictly necessary to continue with calculations
        if os.path.isfile(file_sorted_1hole) and os.path.isfile(file_sorted_2holes):
            print("\nFound files with the sorted list of calculated states.")
            
            # Check for consistency if the files with the states logs exist
            # Only the 1 hole and 2 hole are strictly necessary to continue with calculations
            if os.path.isfile(file_cycle_log_1hole) and os.path.isfile(file_cycle_log_2holes):
                print("Found file with the list of discovered states.")
                
                # Read the state list and get flags to perform some more flow control
                complete_1hole, complete_2holes, complete_3holes, complete_shakeup, \
                last_calculated_cycle_1hole, last_calculated_state_1hole, \
                last_calculated_cycle_2holes, last_calculated_state_2holes, \
                last_calculated_cycle_3holes, last_calculated_state_3holes, \
                last_calculated_cycle_shakeup, last_calculated_state_shakeup = readStateList()
                
                # If the 3 hole and shake-up configurations are supposed to be calculated
                if calculate_3holes and calculate_shakeup:
                    # Check if all state discovery lists are complete
                    # Also check if the last calculated cycles and states are the expected ones
                    if complete_1hole and complete_2holes and complete_3holes and complete_shakeup and \
                        last_calculated_cycle_1hole == 4 and last_calculated_cycle_2holes == 4 and last_calculated_cycle_3holes == 4 and last_calculated_cycle_shakeup == 4 \
                        last_calculated_state_1hole[0] == calculated1holeStates[-1][0] and last_calculated_state_2holes[0] == calculated2holesStates[-1][0] \
                        last_calculated_state_3holes[0] == calculated3holesStates[-1][0] and last_calculated_state_shakeup[0] == calculatedShakeupStates[-1][0]:
                        print("\nVerifyed that the file with the list of calculated states is consistent.")
                        print("Proceding with this list.")
                    else:
                        # Print some debug information if the flag values are not what expected
                        # This is done because transition files were already found
                        print("\nError while checking the file with calculated states.\n")
                        print("Flag                          -> Value ; Expected:")
                        print("Completed 1 hole              -> " + str(complete_1hole) + " ; True")
                        print("Completed 2 holes             -> " + str(complete_2holes) + " ; True")
                        print("Completed 3 holes             -> " + str(complete_3holes) + " ; True")
                        print("Completed Shake-up            -> " + str(complete_shakeup) + " ; True")
                        print("Last calculated cycle 1 hole  -> " + str(last_calculated_cycle_1hole) + "    ; 4")
                        print("Last calculated cycle 2 holes -> " + str(last_calculated_cycle_2holes) + "    ; 4")
                        print("Last calculated cycle 3 holes -> " + str(last_calculated_cycle_3holes) + "    ; 4")
                        print("Last calculated cycle shake-up-> " + str(last_calculated_cycle_shakeup) + "    ; 4")
                        print("Last calculated state 1 hole  -> " + ', '.join([str(qn) for qn in last_calculated_state_1hole[0]]) + " ; " + ', '.join([str(qn) for qn in calculated1holeStates[-1][0]]))
                        print("Last calculated state 2 holes -> " + ', '.join([str(qn) for qn in last_calculated_state_2holes[0]]) + " ; " + ', '.join([str(qn) for qn in calculated2holesStates[-1][0]]))
                        print("Last calculated state 3 holes -> " + ', '.join([str(qn) for qn in last_calculated_state_3holes[0]]) + " ; " + ', '.join([str(qn) for qn in calculated3holesStates[-1][0]]))
                        print("Last calculated state shake-up-> " + ', '.join([str(qn) for qn in last_calculated_state_shakeup[0]]) + " ; " + ', '.join([str(qn) for qn in calculatedShakeupStates[-1][0]]))
                        
                        print("\nPicking up from the last calculated states...\n")
                        
                        # Return the flags for later flow control to decide which calculations to perform and where to start those calculations
                        return complete_1hole, complete_2holes, complete_3holes, complete_shakeup, \
                                last_calculated_cycle_1hole, last_calculated_cycle_2holes, last_calculated_cycle_3holes, last_calculated_cycle_shakeup, \
                                last_calculated_state_1hole[0], last_calculated_state_2holes[0], last_calculated_state_3holes[0], last_calculated_state_shakeup[0]
                # If the 3 hole configurations are supposed to be calculated
                elif calculate_3holes:
                    # Check if all state discovery lists are complete, except for the shake-up ones
                    # Also check if the last calculated cycles and states are the expected ones
                    if complete_1hole and complete_2holes and complete_3holes and \
                        last_calculated_cycle_1hole == 4 and last_calculated_cycle_2holes == 4 and last_calculated_cycle_3holes == 4 \
                        last_calculated_state_1hole[0] == calculated1holeStates[-1][0] and last_calculated_state_2holes[0] == calculated2holesStates[-1][0] \
                        last_calculated_state_3holes[0] == calculated3holesStates[-1][0]:
                        print("\nVerifyed that the file with the list of calculated states is consistent.")
                        print("Proceding with this list.")
                    else:
                        # Print some debug information if the flag values are not what expected
                        # This is done because transition files were already found
                        print("\nError while checking the file with calculated states.\n")
                        print("Flag                          -> Value ; Expected:")
                        print("Completed 1 hole              -> " + str(complete_1hole) + " ; True")
                        print("Completed 2 holes             -> " + str(complete_2holes) + " ; True")
                        print("Completed 3 holes             -> " + str(complete_3holes) + " ; True")
                        print("Completed Shake-up            ->  N/A  ; N/A")
                        print("Last calculated cycle 1 hole  -> " + str(last_calculated_cycle_1hole) + "    ; 4")
                        print("Last calculated cycle 2 holes -> " + str(last_calculated_cycle_2holes) + "    ; 4")
                        print("Last calculated cycle 3 holes -> " + str(last_calculated_cycle_3holes) + "    ; 4")
                        print("Last calculated cycle shake-up->  N/A  ; N/A")
                        print("Last calculated state 1 hole  -> " + ', '.join([str(qn) for qn in last_calculated_state_1hole[0]]) + " ; " + ', '.join([str(qn) for qn in calculated1holeStates[-1][0]]))
                        print("Last calculated state 2 holes -> " + ', '.join([str(qn) for qn in last_calculated_state_2holes[0]]) + " ; " + ', '.join([str(qn) for qn in calculated2holesStates[-1][0]]))
                        print("Last calculated state 3 holes -> " + ', '.join([str(qn) for qn in last_calculated_state_3holes[0]]) + " ; " + ', '.join([str(qn) for qn in calculated3holesStates[-1][0]]))
                        print("Last calculated state shake-up->  N/A  ; N/A")
                        
                        print("\nPicking up from the last calculated states...\n")
                        
                        # Return the flags for later flow control to decide which calculations to perform and where to start those calculations
                        return complete_1hole, complete_2holes, complete_3holes, complete_shakeup, \
                                last_calculated_cycle_1hole, last_calculated_cycle_2holes, last_calculated_cycle_3holes, last_calculated_cycle_shakeup, \
                                last_calculated_state_1hole[0], last_calculated_state_2holes[0], last_calculated_state_3holes[0], last_calculated_state_shakeup[0]
                # If the shake-up configurations are supposed to be calculated
                elif calculate_shakeup:
                    # Check if all state discovery lists are complete, except for the shake-up ones
                    # Also check if the last calculated cycles and states are the expected ones
                    if complete_1hole and complete_2holes and complete_shakeup and \
                        last_calculated_cycle_1hole == 4 and last_calculated_cycle_2holes == 4 and last_calculated_cycle_shakeup == 4 \
                        last_calculated_state_1hole[0] == calculated1holeStates[-1][0] and last_calculated_state_2holes[0] == calculated2holesStates[-1][0] \
                        last_calculated_state_shakeup[0] == calculatedShakeupStates[-1][0]:
                        print("\nVerifyed that the file with the list of calculated states is consistent.")
                        print("Proceding with this list.")
                    else:
                        # Print some debug information if the flag values are not what expected
                        # This is done because transition files were already found
                        print("\nError while checking the file with calculated states.\n")
                        print("Flag                          -> Value ; Expected:")
                        print("Completed 1 hole              -> " + str(complete_1hole) + " ; True")
                        print("Completed 2 holes             -> " + str(complete_2holes) + " ; True")
                        print("Completed 3 holes             ->  N/A  ; N/A")
                        print("Completed Shake-up            -> " + str(complete_shakeup) + " ; True")
                        print("Last calculated cycle 1 hole  -> " + str(last_calculated_cycle_1hole) + "    ; 4")
                        print("Last calculated cycle 2 holes -> " + str(last_calculated_cycle_2holes) + "    ; 4")
                        print("Last calculated cycle 3 holes ->  N/A  ; N/A")
                        print("Last calculated cycle shake-up-> " + str(last_calculated_cycle_shakeup) + "    ; 4")
                        print("Last calculated state 1 hole  -> " + ', '.join([str(qn) for qn in last_calculated_state_1hole[0]]) + " ; " + ', '.join([str(qn) for qn in calculated1holeStates[-1][0]]))
                        print("Last calculated state 2 holes -> " + ', '.join([str(qn) for qn in last_calculated_state_2holes[0]]) + " ; " + ', '.join([str(qn) for qn in calculated2holesStates[-1][0]]))
                        print("Last calculated state 3 holes ->   N/A  ; N/A")
                        print("Last calculated state shake-up-> " + ', '.join([str(qn) for qn in last_calculated_state_shakeup[0]]) + " ; " + ', '.join([str(qn) for qn in calculatedShakeupStates[-1][0]]))
                        
                        print("\nPicking up from the last calculated states...\n")
                        
                        # Return the flags for later flow control to decide which calculations to perform and where to start those calculations
                        return complete_1hole, complete_2holes, complete_3holes, complete_shakeup, \
                                last_calculated_cycle_1hole, last_calculated_cycle_2holes, last_calculated_cycle_3holes, last_calculated_cycle_shakeup, \
                                last_calculated_state_1hole[0], last_calculated_state_2holes[0], last_calculated_state_3holes[0], last_calculated_state_shakeup[0]
            else:
                # Print the file names that are missing
                print("\nFile with the list of discovered states is missing: ")
                print("1 hole states -> " + file_cycle_log_1hole)
                print("2 holes states -> " + file_cycle_log_2holes)
                
                # Print the missing file names if the calculations where expected
                if calculate_3holes:
                    print("3 holes states -> " + file_cycle_log_3holes)
                if calculate_shakeup:
                    print("Shake-up states -> " + file_cycle_log_shakeup)
                
                print("\nReverting to full calculation...\n")
                
                # Return 1 as a flag to revert to a full calculation instead of a partial one as there are inconsistencies
                return 1
            
            # Check if the list of sorted states are complete by comparing the number of sorted states to the number of total states
            complete_sorted_1hole, complete_sorted_2holes, complete_sorted_3holes, complete_sorted_shakeup = readSortedStates()
            
            # If the 3 hole and shake-up configurations are supposed to be calculated
            if calculate_3holes and calculate_shakeup:
                # Check if the list of sorted states are complete for 1 hole, 2 hole, 3 hole and shake-up states
                if complete_sorted_1hole and complete_sorted_2holes and complete_sorted_3holes and complete_sorted_shakeup:
                    print("\nEnergy sorted calculated states files are complete.")
                    print("Proceding while using this state list.")
                    
                    # Return 3 as a flag that only the complete sorted states lists where found but that was what we expected
                    return 3
                else:
                    print("\nError while reading the sorted states files.")
                    print("There was a missmatch between the length of sorted states and calculated states.")
                    print("Continuing with the full list of states and resorting them.")
                    
                    # Return 2 as a flag to continue the calculation with the list of total states and resort them
                    return 2
            # If the 3 hole configurations are supposed to be calculated
            elif calculate_3holes:
                # Check if the list of sorted states are complete for 1 hole, 2 hole and 3 hole states
                if complete_sorted_1hole and complete_sorted_2holes and complete_sorted_3holes:
                    print("\nEnergy sorted calculated states files are complete.")
                    print("Proceding while using this state list.")
                    
                    # Return 3 as a flag that only the complete sorted states lists where found but that was what we expected
                    return 3
                else:
                    print("\nError while reading the sorted states files.")
                    print("There was a missmatch between the length of sorted states and calculated states.")
                    print("Continuing with the full list of states and resorting them.")
                    
                    # Return 2 as a flag to continue the calculation with the list of total states and resort them
                    return 2
            # If the shake-up configurations are supposed to be calculated
            elif calculate_shakeup:
                # Check if the list of sorted states are complete for 1 hole, 2 hole and shake-up states
                if complete_sorted_1hole and complete_sorted_2holes and complete_sorted_shakeup:
                    print("\nEnergy sorted calculated states files are complete.")
                    print("Proceding while using this state list.")
                    
                    # Return 3 as a flag that only the complete sorted states lists where found but that was what we expected
                    return 3
                else:
                    print("\nError while reading the sorted states files.")
                    print("There was a missmatch between the length of sorted states and calculated states.")
                    print("Continuing with the full list of states and resorting them.")
                    
                    # Return 2 as a flag to continue the calculation with the list of total states and resort them
                    return 2
            # If only 1 hole and 2 hole configurations are supposed to be calculated
            else:
                # Check if the list of sorted states are complete for 1 hole and 2 hole states
                if complete_sorted_1hole and complete_sorted_2holes:
                    print("\nEnergy sorted calculated states files are complete.")
                    print("Proceding while using this state list.")
                    
                    # Return 3 as a flag that only the complete sorted states lists where found but that was what we expected
                    return 3
                else:
                    print("\nError while reading the sorted states files.")
                    print("There was a missmatch between the length of sorted states and calculated states.")
                    print("Continuing with the full list of states and resorting them.")
                    
                    # Return 2 as a flag to continue the calculation with the list of total states and resort them
                    return 2
            
        
        # Check for consistency if the files with the states logs exist
        # Only the 1 hole and 2 hole are strictly necessary to continue with calculations
        if os.path.isfile(file_cycle_log_1hole) and os.path.isfile(file_cycle_log_2holes):
            print("\nFound file with the list of discovered states.")
            
            # Read the state list and get flags to perform some more flow control
            complete_1hole, complete_2holes, complete_3holes, complete_shakeup, \
            last_calculated_cycle_1hole, last_calculated_state_1hole, \
            last_calculated_cycle_2holes, last_calculated_state_2holes, \
            last_calculated_cycle_3holes, last_calculated_state_3holes, \
            last_calculated_cycle_shakeup, last_calculated_state_shakeup = readStateList()
            
            # If the 3 hole and shake-up configurations are supposed to be calculated
            if calculate_3holes and calculate_shakeup:
                # Check if all state discovery lists are complete
                # Also check if the last calculated cycles and states are the expected ones
                if complete_1hole and complete_2holes and complete_3holes and complete_shakeup and \
                    last_calculated_cycle_1hole == 4 and last_calculated_cycle_2holes == 4 and last_calculated_cycle_3holes == 4 and last_calculated_cycle_shakeup == 4 \
                    last_calculated_state_1hole[0] == calculated1holeStates[-1][0] and last_calculated_state_2holes[0] == calculated2holesStates[-1][0] \
                    last_calculated_state_3holes[0] == calculated3holesStates[-1][0] and last_calculated_state_shakeup[0] == calculatedShakeupStates[-1][0]:
                    print("\nVerifyed that the file with the list of calculated states is consistent.")
                    print("Proceding with this list.")
                else:
                    # Print some debug information if the flag values are not what expected
                    # This is done because transition files were already found
                    print("\nError while checking the file with calculated states.\n")
                    print("Flag                          -> Value ; Expected:")
                    print("Completed 1 hole              -> " + str(complete_1hole) + " ; True")
                    print("Completed 2 holes             -> " + str(complete_2holes) + " ; True")
                    print("Completed 3 holes             -> " + str(complete_3holes) + " ; True")
                    print("Completed Shake-up            -> " + str(complete_shakeup) + " ; True")
                    print("Last calculated cycle 1 hole  -> " + str(last_calculated_cycle_1hole) + "    ; 4")
                    print("Last calculated cycle 2 holes -> " + str(last_calculated_cycle_2holes) + "    ; 4")
                    print("Last calculated cycle 3 holes -> " + str(last_calculated_cycle_3holes) + "    ; 4")
                    print("Last calculated cycle shake-up-> " + str(last_calculated_cycle_shakeup) + "    ; 4")
                    print("Last calculated state 1 hole  -> " + ', '.join([str(qn) for qn in last_calculated_state_1hole[0]]) + " ; " + ', '.join([str(qn) for qn in calculated1holeStates[-1][0]]))
                    print("Last calculated state 2 holes -> " + ', '.join([str(qn) for qn in last_calculated_state_2holes[0]]) + " ; " + ', '.join([str(qn) for qn in calculated2holesStates[-1][0]]))
                    print("Last calculated state 3 holes -> " + ', '.join([str(qn) for qn in last_calculated_state_3holes[0]]) + " ; " + ', '.join([str(qn) for qn in calculated3holesStates[-1][0]]))
                    print("Last calculated state shake-up-> " + ', '.join([str(qn) for qn in last_calculated_state_shakeup[0]]) + " ; " + ', '.join([str(qn) for qn in calculatedShakeupStates[-1][0]]))
                    
                    print("\nPicking up from the last calculated states...\n")
                    
                    # Return the flags for later flow control to decide which calculations to perform and where to start those calculations
                    return complete_1hole, complete_2holes, complete_3holes, complete_shakeup, \
                            last_calculated_cycle_1hole, last_calculated_cycle_2holes, last_calculated_cycle_3holes, last_calculated_cycle_shakeup, \
                            last_calculated_state_1hole[0], last_calculated_state_2holes[0], last_calculated_state_3holes[0], last_calculated_state_shakeup[0]
            # If the 3 hole configurations are supposed to be calculated
            elif calculate_3holes:
                # Check if all state discovery lists are complete, except for the shake-up ones
                # Also check if the last calculated cycles and states are the expected ones
                if complete_1hole and complete_2holes and complete_3holes and \
                    last_calculated_cycle_1hole == 4 and last_calculated_cycle_2holes == 4 and last_calculated_cycle_3holes == 4 \
                    last_calculated_state_1hole[0] == calculated1holeStates[-1][0] and last_calculated_state_2holes[0] == calculated2holesStates[-1][0] \
                    last_calculated_state_3holes[0] == calculated3holesStates[-1][0]:
                    print("\nVerifyed that the file with the list of calculated states is consistent.")
                    print("Proceding with this list.")
                else:
                    # Print some debug information if the flag values are not what expected
                    # This is done because transition files were already found
                    print("\nError while checking the file with calculated states.\n")
                    print("Flag                          -> Value ; Expected:")
                    print("Completed 1 hole              -> " + str(complete_1hole) + " ; True")
                    print("Completed 2 holes             -> " + str(complete_2holes) + " ; True")
                    print("Completed 3 holes             -> " + str(complete_3holes) + " ; True")
                    print("Completed Shake-up            ->  N/A  ; N/A")
                    print("Last calculated cycle 1 hole  -> " + str(last_calculated_cycle_1hole) + "    ; 4")
                    print("Last calculated cycle 2 holes -> " + str(last_calculated_cycle_2holes) + "    ; 4")
                    print("Last calculated cycle 3 holes -> " + str(last_calculated_cycle_3holes) + "    ; 4")
                    print("Last calculated cycle shake-up->  N/A  ; N/A")
                    print("Last calculated state 1 hole  -> " + ', '.join([str(qn) for qn in last_calculated_state_1hole[0]]) + " ; " + ', '.join([str(qn) for qn in calculated1holeStates[-1][0]]))
                    print("Last calculated state 2 holes -> " + ', '.join([str(qn) for qn in last_calculated_state_2holes[0]]) + " ; " + ', '.join([str(qn) for qn in calculated2holesStates[-1][0]]))
                    print("Last calculated state 3 holes -> " + ', '.join([str(qn) for qn in last_calculated_state_3holes[0]]) + " ; " + ', '.join([str(qn) for qn in calculated3holesStates[-1][0]]))
                    print("Last calculated state shake-up->  N/A  ; N/A")
                    
                    print("\nPicking up from the last calculated states...\n")
                    
                    # Return the flags for later flow control to decide which calculations to perform and where to start those calculations
                    return complete_1hole, complete_2holes, complete_3holes, complete_shakeup, \
                            last_calculated_cycle_1hole, last_calculated_cycle_2holes, last_calculated_cycle_3holes, last_calculated_cycle_shakeup, \
                            last_calculated_state_1hole[0], last_calculated_state_2holes[0], last_calculated_state_3holes[0], last_calculated_state_shakeup[0]
            # If the shake-up configurations are supposed to be calculated
            elif calculate_shakeup:
                # Check if all state discovery lists are complete, except for the shake-up ones
                # Also check if the last calculated cycles and states are the expected ones
                if complete_1hole and complete_2holes and complete_shakeup and \
                    last_calculated_cycle_1hole == 4 and last_calculated_cycle_2holes == 4 and last_calculated_cycle_shakeup == 4 \
                    last_calculated_state_1hole[0] == calculated1holeStates[-1][0] and last_calculated_state_2holes[0] == calculated2holesStates[-1][0] \
                    last_calculated_state_shakeup[0] == calculatedShakeupStates[-1][0]:
                    print("\nVerifyed that the file with the list of calculated states is consistent.")
                    print("Proceding with this list.")
                else:
                    # Print some debug information if the flag values are not what expected
                    # This is done because transition files were already found
                    print("\nError while checking the file with calculated states.\n")
                    print("Flag                          -> Value ; Expected:")
                    print("Completed 1 hole              -> " + str(complete_1hole) + " ; True")
                    print("Completed 2 holes             -> " + str(complete_2holes) + " ; True")
                    print("Completed 3 holes             ->  N/A  ; N/A")
                    print("Completed Shake-up            -> " + str(complete_shakeup) + " ; True")
                    print("Last calculated cycle 1 hole  -> " + str(last_calculated_cycle_1hole) + "    ; 4")
                    print("Last calculated cycle 2 holes -> " + str(last_calculated_cycle_2holes) + "    ; 4")
                    print("Last calculated cycle 3 holes ->  N/A  ; N/A")
                    print("Last calculated cycle shake-up-> " + str(last_calculated_cycle_shakeup) + "    ; 4")
                    print("Last calculated state 1 hole  -> " + ', '.join([str(qn) for qn in last_calculated_state_1hole[0]]) + " ; " + ', '.join([str(qn) for qn in calculated1holeStates[-1][0]]))
                    print("Last calculated state 2 holes -> " + ', '.join([str(qn) for qn in last_calculated_state_2holes[0]]) + " ; " + ', '.join([str(qn) for qn in calculated2holesStates[-1][0]]))
                    print("Last calculated state 3 holes ->   N/A  ; N/A")
                    print("Last calculated state shake-up-> " + ', '.join([str(qn) for qn in last_calculated_state_shakeup[0]]) + " ; " + ', '.join([str(qn) for qn in calculatedShakeupStates[-1][0]]))
                    
                    print("\nPicking up from the last calculated states...\n")
                    
                    # Return the flags for later flow control to decide which calculations to perform and where to start those calculations
                    return complete_1hole, complete_2holes, complete_3holes, complete_shakeup, \
                            last_calculated_cycle_1hole, last_calculated_cycle_2holes, last_calculated_cycle_3holes, last_calculated_cycle_shakeup, \
                            last_calculated_state_1hole[0], last_calculated_state_2holes[0], last_calculated_state_3holes[0], last_calculated_state_shakeup[0]
        else:
            print("\nFiles with the previously calculated states directories could not be found.")
            print("Please do a full calculation first.")
            sys.exit(1)


def checkOutput(currDir, currFileName):
    first = False
    firstOver = False
    
    Diff = -1.0
    
    welt = 0.0
    
    Overlaps = []
    
    percents = []
    highest_percent = 100.0
    
    accuracy = 0.0
    
    higher_config = ''
    
    failed_orbital = ''
    
    with open(currDir + "/" + currFileName + ".f06", "r") as output:
        outputContent = output.readlines()
        
        for i, line in enumerate(outputContent):
            if "Configuration(s)" in line and " 1 " in line:
                higher_config = outputContent[i + 1].strip()
            
            if "Common to all configurations" in line:
                higher_config = line.replace("Common to all configurations", "").strip()
            
            if "List of jj configurations with a weight >= 0.01%" in line:
                cnt = i + 1
                while True:
                    if outputContent[cnt] == "\n":
                        break
                    else:
                        percents.append((' '.join(outputContent[cnt].strip().split()[:-2]), float(outputContent[cnt].strip().split()[-2])))
                    
                    cnt += 1
                
                if percents != []:
                    highest = max(percents, key=lambda x: x[1])
                    higher_config += ' ' + highest[0]
                    highest_percent = highest[1]
            
            if "Variation of eigenenergy for the last" in line:
                cnt = i + 1
                while True:
                    if outputContent[cnt] == "\n":
                        break
                    else:
                        accuracy = round(float(outputContent[cnt].strip().split()[-1]), 6)
                    
                    cnt += 1
            
            if "Overlap integrals" in line and not firstOver and first:
                firstOver = True
                cnt = i + 1
                while True:
                    if outputContent[cnt] == "\n":
                        break
                    else:
                        Overlaps.append(float(outputContent[cnt].strip().split()[3]))
                        Overlaps.append(float(outputContent[cnt].strip().split()[-1]))
                    
                    cnt += 1
            
            if "ETOT (a.u.)" in line and not first:
                first = True
                Diff = abs(round(float(outputContent[i + 1].split()[1]) - float(outputContent[i + 1].split()[2]), 6))
            
            if "Etot_(Welt.)=" in line:
                welt = float(line.strip().split()[3])
            
            if "For orbital" in line:
                failed_orbital = line.strip().split()[-1].strip()
    
    return first, failed_orbital, max(Overlaps) if len(Overlaps) > 0 else 1.0, higher_config, highest_percent, accuracy, Diff, welt


def configureTransitionInputFile(template, \
                                currDir, currFileName, \
                                currDir_i, currFileName_i, \
                                config_i, jj_i, eigv_i, ne_i, \
                                currDir_f, currFileName_f, \
                                config_f, jj_f, eigv_f, ne_f, energy_diff = 0.0):
    
    
    wfiFile = currFileName_i
    wffFile = currFileName_f
    
    if len(wfiFile) > 7:
        wfiFile = "wfi"
    if len(wffFile) > 7:
        wffFile = "wff"
    
    fileString = template \
                .replace("mcdfgmelabel", "Z=" + atomic_number + " " + config_i + " 2J=" + str(jj_i) + " neig=" + str(eigv_i) + " => " + config_f + " 2J=" + str(jj_f) + " neig=" + str(eigv_f)) \
                .replace("mcdfgmeatomicnumber", atomic_number) \
                .replace("energylabel", str(energy_diff)) \
                .replace("mcdfgmeelectronnbi", str(ne_i)) \
                .replace("mcdfgmejji", str(jj_i)) \
                .replace("mcdfgmeelectronnbf", str(ne_f)) \
                .replace("mcdfgmejjf", str(jj_f)) \
                .replace("mcdfgmeconfigurationi", config_i) \
                .replace("mcdfgmeneigvi", str(eigv_i)) \
                .replace("mcdfgmewffilei", wfiFile) \
                .replace("mcdfgmeconfigurationf", config_f) \
                .replace("mcdfgmeneigvf", str(eigv_f)) \
                .replace("mcdfgmewffilef", wffFile)
    
    
    if nuc_massyorn == "y":
        fileString = fileString \
                    .replace("nuc_model_yorn", "n") \
                    .replace("    nuc_model_label :\n", "")
        if int(atomic_number) < 48:
            fileString = fileString \
                        .replace("    use_rms_def=n\n", "")
    else:
        fileString = fileString \
                    .replace("nuc_model_yorn", "y") \
                    .replace("nuc_model_label", nuc_model + " a=" + str(nuc_mass))
        if nuc_model == "uniform":
            fileString = fileString \
                        .replace("    use_rms_def=n\n", "")
    
    
    if not os.path.exists(currDir):
        os.makedirs(currDir)
        os.makedirs(currDir + "/tmp")
    
    with open(currDir + "/" + currFileName + ".f05", "w") as labelInput:
        labelInput.write(fileString)
    
    with open(currDir + "/mdfgme.dat", "w") as mdfgme:
        mdfgme.write(mdfgmeFile.replace("f05FileName", currFileName))
    
    return wfiFile, wffFile
    


def configureStateInputFile(template, currDir, currFileName, config, jj, eigv, failed_orbs = [], ne = ''):
    if ne == '':
        nelec = nelectrons
    else:
        nelec = ne
    
    fileString = template \
                .replace("mcdfgmelabel", "Z=" + atomic_number + " " + config + " 2J=" + str(jj) + " neig=" + str(eigv)) \
                .replace("mcdfgmeatomicnumber", atomic_number) \
                .replace("mcdfgmeelectronnb", str(nelec)) \
                .replace("mcdfgmejj", str(jj)) \
                .replace("mcdfgmeconfiguration", config) \
                .replace("mcdfgmeneigv", str(eigv)) \
                .replace("mcdfgmefailledorbital", '\n'.join(failed_orbs))
    
    
    if nuc_massyorn == "y":
        fileString = fileString \
                    .replace("nuc_model_yorn", "n") \
                    .replace("    nuc_model_label :\n", "")
        if int(atomic_number) < 48:
            fileString = fileString \
                        .replace("    use_rms_def=n\n", "")
    else:
        fileString = fileString \
                    .replace("nuc_model_yorn", "y") \
                    .replace("nuc_model_label", nuc_model + " a=" + str(nuc_mass))
        if nuc_model == "uniform":
            fileString = fileString \
                        .replace("    use_rms_def=n\n", "")
    
    
    if not os.path.exists(currDir):
        os.mkdir(currDir)
        os.mkdir(currDir + "/tmp")
    
    with open(currDir + "/" + currFileName + ".f05", "w") as labelInput:
        labelInput.write(fileString)
    
    with open(currDir + "/mdfgme.dat", "w") as mdfgme:
        mdfgme.write(mdfgmeFile.replace("f05FileName", currFileName))
    

def executeBatchStateCalculation(parallel_paths, log_file = '', state_list = [], log_line_header = ''):
    parallel_max_paths = (len(parallel_paths) * parallel_max_length / len(' '.join(parallel_paths))) / 17
    if len(parallel_paths) < parallel_max_paths:
        subprocess.check_output(['parallel -j' + number_of_threads + ' --bar ' + "'cd {//} && {/} && cd -'" + ' ::: ' + ' '.join(parallel_paths)], shell=True)
        if log_file != '' and state_list != [] and log_line_header != '':
            with open(log_file, "a") as log:
                log.write(log_line_header)
                log.write(', '.join([str(qn) for qn in state_list[-1][0]]) + "\n")
    else:
        for pl in range(len(parallel_paths) / parallel_max_paths):
            subprocess.check_output(['parallel -j' + number_of_threads + ' --bar ' + "'cd {//} && {/} && cd -'" + ' ::: ' + ' '.join(parallel_paths[(pl * parallel_max_paths):((pl + 1) * parallel_max_paths)])], shell=True)
            
            if log_file != '' and state_list != [] and log_line_header != '':
                with open(log_file, "a") as log:
                    if pl == 0:
                        log.write(log_line_header)
                    
                    log.write(', '.join([str(qn) for qn in state_list[((pl + 1) * parallel_max_paths) - 1][0]]) + "\n")
        
        
        subprocess.check_output(['parallel -j' + number_of_threads + ' --bar ' + "'cd {//} && {/} && cd -'" + ' ::: ' + ' '.join(parallel_paths[((pl + 1) * parallel_max_paths):])], shell=True)
        
        if log_file != '' and state_list != [] and log_line_header != '':
            with open(log_file, "a") as log:
                log.write(', '.join([str(qn) for qn in state_list[-1][0]]) + "\n")


def executeBatchTransitionCalculation(parallel_paths, \
                                    parallel_initial_src_paths, parallel_final_src_paths, \
                                    parallel_initial_dst_paths, parallel_final_dst_paths, \
                                    log_file = '', state_list = [], log_line_header = ''):
    parallel_max_paths = (len(parallel_paths) * parallel_max_length / len(' '.join(parallel_paths))) / 17
    if len(parallel_paths) < parallel_max_paths:
        # COPY .f09 WAVEFUNCTION FILES
        for wf_src, wf_dst in zip(parallel_initial_src_paths, parallel_initial_dst_paths):
            shutil.copy(wf_src, wf_dst)
        
        for wf_src, wf_dst in zip(parallel_final_src_paths, parallel_final_dst_paths):
            shutil.copy(wf_src, wf_dst)
        
        # EXECUTE PARALLEL JOB
        subprocess.check_output(['parallel -j' + number_of_threads + ' --bar ' + "'cd {//} && {/} && cd -'" + ' ::: ' + ' '.join(parallel_paths)], shell=True)
        
        # LOG THE CALCULATED STATES
        if log_file != '' and state_list != [] and log_line_header != '':
            with open(log_file, "a") as log:
                log.write(log_line_header)
                log.write(', '.join([str(qn) for qn in state_list[-1][0]]) + " => " + ', '.join([str(qn) for qn in state_list[-1][1]]) + "\n")
        
        # REMOVE THE .f09 WAVEFUNCTION FILES
        for wfi_dst, wff_dst in zip(parallel_initial_dst_paths, parallel_final_dst_paths):
            os.remove(wfi_dst)
            os.remove(wff_dst)
        
    else:
        for pl in range(len(parallel_paths) / parallel_max_paths):
            # COPY .f09 WAVEFUNCTION FILES FOR THIS BATCH
            for wf_src, wf_dst in zip(parallel_initial_src_paths[(pl * parallel_max_paths):((pl + 1) * parallel_max_paths)], parallel_initial_dst_paths[(pl * parallel_max_paths):((pl + 1) * parallel_max_paths)]):
                shutil.copy(wf_src, wf_dst)
            
            for wf_src, wf_dst in zip(parallel_final_src_paths[(pl * parallel_max_paths):((pl + 1) * parallel_max_paths)], parallel_final_dst_paths[(pl * parallel_max_paths):((pl + 1) * parallel_max_paths)]):
                shutil.copy(wf_src, wf_dst)
        
            
            # EXECUTE PARALLEL JOB FOR THIS BATCH
            subprocess.check_output(['parallel -j' + number_of_threads + ' --bar ' + "'cd {//} && {/} && cd -'" + ' ::: ' + ' '.join(parallel_paths[(pl * parallel_max_paths):((pl + 1) * parallel_max_paths)])], shell=True)
            
            
            # LOG THE CALCULATED STATES IN THIS BATCH
            if log_file != '' and state_list != [] and log_line_header != '':
                with open(log_file, "a") as log:
                    if pl == 0:
                        log.write(log_line_header)
                    
                    log.write(', '.join([str(qn) for qn in state_list[((pl + 1) * parallel_max_paths) - 1][0]]) + " => " + ', '.join([str(qn) for qn in state_list[((pl + 1) * parallel_max_paths) - 1][1]]) + "\n")
            
            
            # REMOVE THE .f09 WAVEFUNCTION FILES IN THIS BATCH
            for wfi_dst, wff_dst in zip(parallel_initial_dst_paths[(pl * parallel_max_paths):((pl + 1) * parallel_max_paths)], parallel_final_dst_paths[(pl * parallel_max_paths):((pl + 1) * parallel_max_paths)]):
                os.remove(wfi_dst)
                os.remove(wff_dst)
        
        
        # COPY .f09 WAVEFUNCTION FILES FOR THE LAST BATCH
        for wf_src, wf_dst in zip(parallel_initial_src_paths[((pl + 1) * parallel_max_paths):], parallel_initial_dst_paths[((pl + 1) * parallel_max_paths):]):
            shutil.copy(wf_src, wf_dst)
        
        for wf_src, wf_dst in zip(parallel_final_src_paths[((pl + 1) * parallel_max_paths):], parallel_final_dst_paths[((pl + 1) * parallel_max_paths):]):
            shutil.copy(wf_src, wf_dst)
        
        
        # EXECUTE PARALLEL JOB FOR THE LAST BATCH
        subprocess.check_output(['parallel -j' + number_of_threads + ' --bar ' + "'cd {//} && {/} && cd -'" + ' ::: ' + ' '.join(parallel_paths[((pl + 1) * parallel_max_paths):])], shell=True)
        
        
        # COPY .f09 WAVEFUNCTION FILES FOR THE LAST BATCH
        if log_file != '' and state_list != [] and log_line_header != '':
            with open(log_file, "a") as log:
                log.write(', '.join([str(qn) for qn in state_list[-1][0]]) + " => " + ', '.join([str(qn) for qn in state_list[-1][1]]) + "\n")
        
        
        # REMOVE THE .f09 WAVEFUNCTION FILES FOR THE LAST BATCH
        for wfi_dst, wff_dst in zip(parallel_initial_dst_paths[((pl + 1) * parallel_max_paths):], parallel_final_dst_paths[((pl + 1) * parallel_max_paths):]):
            os.remove(wfi_dst)
            os.remove(wff_dst)
        
    
    
def writeResults1hole(update=False):
    if not update:
        with open(file_cycle_log_1hole, "a") as log_1hole:
            log_1hole.write("CalculationFinalized\n")
    
    with open(file_results, "a") as resultDump:
        with open(file_final_results_1hole, "a") as stateResults_1hole:
            with open(file_final_results, "a") as stateResults:
                if not update:
                    resultDump.write("Fourth Cycle 1 Hole states\nShell, Shell index, 2J, Eigv, Higher Configuration, Percentage, Overlap, Accuracy, Energy Difference, Energy Welton\n")
                    stateResults_1hole.write("Calculated 1 Hole states\nShell, Shell index, 2J, Eigv, Higher Configuration, Percentage, Overlap, Accuracy, Energy Difference, Energy Welton\n")
                    stateResults.write("Calculated 1 Hole states\nShell, Shell index, 2J, Eigv, Higher Configuration, Percentage, Overlap, Accuracy, Energy Difference, Energy Welton\n")
                    for state in calculated1holeStates:
                        resultDump.write(shell_array[state[0][0]] + ", " + str(state[0][0]) + ", " + str(state[0][1]) + ", " + str(state[0][2]) + ", " + state[1][0] + ", " + str(state[1][1]) + ", " + str(state[1][2]) + ", " + str(state[1][3]) + ", " + str(state[1][4]) + ", " + str(state[1][5]) + "\n")
                        stateResults_1hole.write(shell_array[state[0][0]] + ", " + str(state[0][0]) + ", " + str(state[0][1]) + ", " + str(state[0][2]) + ", " + state[1][0] + ", " + str(state[1][1]) + ", " + str(state[1][2]) + ", " + str(state[1][3]) + ", " + str(state[1][4]) + ", " + str(state[1][5]) + "\n")
                        stateResults.write(shell_array[state[0][0]] + ", " + str(state[0][0]) + ", " + str(state[0][1]) + ", " + str(state[0][2]) + ", " + state[1][0] + ", " + str(state[1][1]) + ", " + str(state[1][2]) + ", " + str(state[1][3]) + ", " + str(state[1][4]) + ", " + str(state[1][5]) + "\n")
                
                if len(radiative_by_hand) > 0:
                    stateResults_1hole.write("1 Hole by Hand\n")
                    stateResults.write("1 Hole by Hand\n")
                    for counter in radiative_by_hand:
                        stateResults_1hole.write(shell_array[calculated1holeStates[counter][0][0]] + ", " + str(calculated1holeStates[counter][0][0]) + ", " + str(calculated1holeStates[counter][0][1]) + ", " + str(calculated1holeStates[counter][0][2]) + ", " + calculated1holeStates[counter][1][0] + ", " + str(calculated1holeStates[counter][1][1]) + ", " + str(calculated1holeStates[counter][1][2]) + ", " + str(calculated1holeStates[counter][1][3]) + ", " + str(calculated1holeStates[counter][1][4]) + ", " + str(calculated1holeStates[counter][1][5]) + "\n")
                        stateResults.write(shell_array[calculated1holeStates[counter][0][0]] + ", " + str(calculated1holeStates[counter][0][0]) + ", " + str(calculated1holeStates[counter][0][1]) + ", " + str(calculated1holeStates[counter][0][2]) + ", " + calculated1holeStates[counter][1][0] + ", " + str(calculated1holeStates[counter][1][1]) + ", " + str(calculated1holeStates[counter][1][2]) + ", " + str(calculated1holeStates[counter][1][3]) + ", " + str(calculated1holeStates[counter][1][4]) + ", " + str(calculated1holeStates[counter][1][5]) + "\n")
                else:
                    stateResults_1hole.write("All 1 Hole states have converged\n")
                    stateResults.write("All 1 Hole states have converged\n")


def writeResults2holes(update=False):
    if not update:
        with open(file_cycle_log_2holes, "a") as log_2holes:
            log_2holes.write("CalculationFinalized\n")
    
    with open(file_results, "a") as resultDump:
        with open(file_final_results_2holes, "a") as stateResults_2holes:
            with open(file_final_results, "a") as stateResults:
                if not update:
                    resultDump.write("Fourth Cycle 2 Hole states\nShell, Shell index, 2J, Eigv, Higher Configuration, Percentage, Overlap, Accuracy, Energy Difference, Energy Welton\n")
                    stateResults_2holes.write("Calculated 2 Hole states\nShell, Shell index, 2J, Eigv, Higher Configuration, Percentage, Overlap, Accuracy, Energy Difference, Energy Welton\n")
                    stateResults.write("Calculated 2 Hole states\nShell, Shell index, 2J, Eigv, Higher Configuration, Percentage, Overlap, Accuracy, Energy Difference, Energy Welton\n")
                    for state in calculated2holesStates:
                        resultDump.write(shell_array_2holes[state[0][0]] + ", " + str(state[0][0]) + ", " + str(state[0][1]) + ", " + str(state[0][2]) + ", " + state[1][0] + ", " + str(state[1][1]) + ", " + str(state[1][2]) + ", " + str(state[1][3]) + ", " + str(state[1][4]) + ", " + str(state[1][5]) + "\n")
                        stateResults_2holes.write(shell_array_2holes[state[0][0]] + ", " + str(state[0][0]) + ", " + str(state[0][1]) + ", " + str(state[0][2]) + ", " + state[1][0] + ", " + str(state[1][1]) + ", " + str(state[1][2]) + ", " + str(state[1][3]) + ", " + str(state[1][4]) + ", " + str(state[1][5]) + "\n")
                        stateResults.write(shell_array_2holes[state[0][0]] + ", " + str(state[0][0]) + ", " + str(state[0][1]) + ", " + str(state[0][2]) + ", " + state[1][0] + ", " + str(state[1][1]) + ", " + str(state[1][2]) + ", " + str(state[1][3]) + ", " + str(state[1][4]) + ", " + str(state[1][5]) + "\n")
                
                if len(auger_by_hand) > 0:
                    stateResults_2holes.write("2 Hole by Hand\n")
                    stateResults.write("2 Hole by Hand\n")
                    for counter in auger_by_hand:
                        stateResults_2holes.write(shell_array_2holes[calculated2holesStates[counter][0][0]] + ", " + str(calculated2holesStates[counter][0][0]) + ", " + str(calculated2holesStates[counter][0][1]) + ", " + str(calculated2holesStates[counter][0][2]) + ", " + calculated2holesStates[counter][1][0] + ", " + str(calculated2holesStates[counter][1][1]) + ", " + str(calculated2holesStates[counter][1][2]) + ", " + str(calculated2holesStates[counter][1][3]) + ", " + str(calculated2holesStates[counter][1][4]) + ", " + str(calculated2holesStates[counter][1][5]) + "\n")
                        stateResults.write(shell_array_2holes[calculated2holesStates[counter][0][0]] + ", " + str(calculated2holesStates[counter][0][0]) + ", " + str(calculated2holesStates[counter][0][1]) + ", " + str(calculated2holesStates[counter][0][2]) + ", " + calculated2holesStates[counter][1][0] + ", " + str(calculated2holesStates[counter][1][1]) + ", " + str(calculated2holesStates[counter][1][2]) + ", " + str(calculated2holesStates[counter][1][3]) + ", " + str(calculated2holesStates[counter][1][4]) + ", " + str(calculated2holesStates[counter][1][5]) + "\n")
                else:
                    stateResults_2holes.write("All 2 Hole states have converged\n")
                    stateResults.write("All 2 Hole states have converged\n")


def writeResults3holes(update=False):
    if not update:
        with open(file_cycle_log_3holes, "a") as log_3holes:
            log_3holes.write("CalculationFinalized\n")
    
    with open(file_results, "a") as resultDump:
        with open(file_final_results_3holes, "a") as stateResults_3holes:
            with open(file_final_results, "a") as stateResults:
                if not update:
                    resultDump.write("Fourth Cycle 3 Hole states\nShell, Shell index, 2J, Eigv, Higher Configuration, Percentage, Overlap, Accuracy, Energy Difference, Energy Welton\n")
                    stateResults_3holes.write("Calculated 3 Hole states\nShell, Shell index, 2J, Eigv, Higher Configuration, Percentage, Overlap, Accuracy, Energy Difference, Energy Welton\n")
                    stateResults.write("Calculated 3 Hole states\nShell, Shell index, 2J, Eigv, Higher Configuration, Percentage, Overlap, Accuracy, Energy Difference, Energy Welton\n")
                    for state in calculated3holesStates:
                        resultDump.write(shell_array_3holes[state[0][0]] + ", " + str(state[0][0]) + ", " + str(state[0][1]) + ", " + str(state[0][2]) + ", " + state[1][0] + ", " + str(state[1][1]) + ", " + str(state[1][2]) + ", " + str(state[1][3]) + ", " + str(state[1][4]) + ", " + str(state[1][5]) + "\n")
                        stateResults_3holes.write(shell_array_3holes[state[0][0]] + ", " + str(state[0][0]) + ", " + str(state[0][1]) + ", " + str(state[0][2]) + ", " + state[1][0] + ", " + str(state[1][1]) + ", " + str(state[1][2]) + ", " + str(state[1][3]) + ", " + str(state[1][4]) + ", " + str(state[1][5]) + "\n")
                        stateResults.write(shell_array_3holes[state[0][0]] + ", " + str(state[0][0]) + ", " + str(state[0][1]) + ", " + str(state[0][2]) + ", " + state[1][0] + ", " + str(state[1][1]) + ", " + str(state[1][2]) + ", " + str(state[1][3]) + ", " + str(state[1][4]) + ", " + str(state[1][5]) + "\n")
                
                if len(sat_auger_by_hand) > 0:
                    stateResults_3holes.write("3 Hole by Hand\n")
                    stateResults.write("3 Hole by Hand\n")
                    for counter in sat_auger_by_hand:
                        stateResults_3holes.write(shell_array_3holes[calculated3holesStates[counter][0][0]] + ", " + str(calculated3holesStates[counter][0][0]) + ", " + str(calculated3holesStates[counter][0][1]) + ", " + str(calculated3holesStates[counter][0][2]) + ", " + calculated3holesStates[counter][1][0] + ", " + str(calculated3holesStates[counter][1][1]) + ", " + str(calculated3holesStates[counter][1][2]) + ", " + str(calculated3holesStates[counter][1][3]) + ", " + str(calculated3holesStates[counter][1][4]) + ", " + str(calculated3holesStates[counter][1][5]) + "\n")
                        stateResults.write(shell_array_3holes[calculated3holesStates[counter][0][0]] + ", " + str(calculated3holesStates[counter][0][0]) + ", " + str(calculated3holesStates[counter][0][1]) + ", " + str(calculated3holesStates[counter][0][2]) + ", " + calculated3holesStates[counter][1][0] + ", " + str(calculated3holesStates[counter][1][1]) + ", " + str(calculated3holesStates[counter][1][2]) + ", " + str(calculated3holesStates[counter][1][3]) + ", " + str(calculated3holesStates[counter][1][4]) + ", " + str(calculated3holesStates[counter][1][5]) + "\n")
                else:
                    stateResults_3holes.write("All 3 Hole states have converged\n")
                    stateResults.write("All 3 Hole states have converged\n")


def writeResultsShakeup(update=False):
    if not update:
        with open(file_cycle_log_shakeup, "a") as log_shakeup:
            log_shakeup.write("CalculationFinalized\n")
    
    with open(file_results, "a") as resultDump:
        with open(file_final_results_shakeup, "a") as stateResults_shakeup:
            with open(file_final_results, "a") as stateResults:
                if not update:
                    resultDump.write("Fourth Cycle Shake-up states\nShell, Shell index, 2J, Eigv, Higher Configuration, Percentage, Overlap, Accuracy, Energy Difference, Energy Welton\n")
                    stateResults_shakeup.write("Calculated Shake-up states\nShell, Shell index, 2J, Eigv, Higher Configuration, Percentage, Overlap, Accuracy, Energy Difference, Energy Welton\n")
                    stateResults.write("Calculated Shake-up states\nShell, Shell index, 2J, Eigv, Higher Configuration, Percentage, Overlap, Accuracy, Energy Difference, Energy Welton\n")
                    for state in calculatedShakeupStates:
                        resultDump.write(shell_array_shakeup[state[0][0]] + ", " + str(state[0][0]) + ", " + str(state[0][1]) + ", " + str(state[0][2]) + ", " + state[1][0] + ", " + str(state[1][1]) + ", " + str(state[1][2]) + ", " + str(state[1][3]) + ", " + str(state[1][4]) + ", " + str(state[1][5]) + "\n")
                        stateResults_shakeup.write(shell_array_shakeup[state[0][0]] + ", " + str(state[0][0]) + ", " + str(state[0][1]) + ", " + str(state[0][2]) + ", " + state[1][0] + ", " + str(state[1][1]) + ", " + str(state[1][2]) + ", " + str(state[1][3]) + ", " + str(state[1][4]) + ", " + str(state[1][5]) + "\n")
                        stateResults.write(shell_array_shakeup[state[0][0]] + ", " + str(state[0][0]) + ", " + str(state[0][1]) + ", " + str(state[0][2]) + ", " + state[1][0] + ", " + str(state[1][1]) + ", " + str(state[1][2]) + ", " + str(state[1][3]) + ", " + str(state[1][4]) + ", " + str(state[1][5]) + "\n")
                
                if len(shakeup_by_hand) > 0:
                    stateResults_shakeup.write("Shake-up by Hand\n")
                    stateResults.write("Shake-up by Hand\n")
                    for counter in shakeup_by_hand:
                        stateResults_shakeup.write(shell_array_shakeup[calculatedShakeupStates[counter][0][0]] + ", " + str(calculatedShakeupStates[counter][0][0]) + ", " + str(calculatedShakeupStates[counter][0][1]) + ", " + str(calculatedShakeupStates[counter][0][2]) + ", " + calculatedShakeupStates[counter][1][0] + ", " + str(calculatedShakeupStates[counter][1][1]) + ", " + str(calculatedShakeupStates[counter][1][2]) + ", " + str(calculatedShakeupStates[counter][1][3]) + ", " + str(calculatedShakeupStates[counter][1][4]) + ", " + str(calculatedShakeupStates[counter][1][5]) + "\n")
                        stateResults.write(shell_array_shakeup[calculatedShakeupStates[counter][0][0]] + ", " + str(calculatedShakeupStates[counter][0][0]) + ", " + str(calculatedShakeupStates[counter][0][1]) + ", " + str(calculatedShakeupStates[counter][0][2]) + ", " + calculatedShakeupStates[counter][1][0] + ", " + str(calculatedShakeupStates[counter][1][1]) + ", " + str(calculatedShakeupStates[counter][1][2]) + ", " + str(calculatedShakeupStates[counter][1][3]) + ", " + str(calculatedShakeupStates[counter][1][4]) + ", " + str(calculatedShakeupStates[counter][1][5]) + "\n")
                else:
                    stateResults_shakeup.write("All Shake-up states have converged\n")
                    stateResults.write("All Shake-up states have converged\n")



def calculate1holeStates(starting_cycle = -1, starting_state = [(0, 0, 0)]):
    global calculated1holeStates, radiative_by_hand
    
    jj_vals = []
    
    parallel_1hole_paths = []
    
    
    # If no starting cycle has been specified
    if starting_cycle == -1:
        # -------------- DETERMINE 2J MAX VALUE -------------- #
        
        for i in range(len(shell_array)):
            currDir = rootDir + "/" + directory_name + "/radiative/" + shell_array[i]
            currFileName = shell_array[i]
            
            configureStateInputFile(f05Template_nuc, currDir, currFileName, configuration_1hole[i], "100" if int(nelectrons) % 2 == 0 else "101", "100")
            
            parallel_1hole_paths.append(currDir + "/" + exe_file)
            
        
        # Execute parallel batch job
        executeBatchStateCalculation(parallel_1hole_paths)
        
        
        
        # -------------- DETERMINE EIGENVALUE MAX VALUE -------------- #
        
        parallel_1hole_paths = []
        
        for i in range(len(shell_array)):
            currDir = rootDir + "/" + directory_name + "/radiative/" + shell_array[i]
            currFileName = shell_array[i]
            
            maxJJi = 0
            
            with open(currDir + "/" + currFileName + ".f06", "r") as labelOutput:
                for line in labelOutput.readlines():
                    if "!!!!! For state # 1 and configuration   1 highest 2Jz possible value is" in line:
                        maxJJi = int(line.split("!!!!! For state # 1 and configuration   1 highest 2Jz possible value is")[1].split()[0].strip())
            
            for jj in range(0 if maxJJi % 2 == 0 else 1, maxJJi + 1, 2):
                jj_vals.append((i, jj))
                
                currDir = rootDir + "/" + directory_name + "/radiative/" + shell_array[i] + "/2jj_" + str(jj)
                currFileName = shell_array[i] + "_" + str(jj)
                
                configureStateInputFile(f05Template_nuc, currDir, currFileName, configuration_1hole[i], jj, "100")
            
                parallel_1hole_paths.append(currDir + "/" + exe_file)
        
        # Execute parallel batch job
        executeBatchStateCalculation(parallel_1hole_paths)
    
    
        
        # -------------- FULL STATE CALCULATION -------------- #
        
        parallel_1hole_paths = []
        
        for i, jj in jj_vals:
            currDir = rootDir + "/" + directory_name + "/radiative/" + shell_array[i] + "/2jj_" + str(jj)
            currFileName = shell_array[i] + "_" + str(jj)
            
            maxEigvi = 0
            
            with open(currDir + "/" + currFileName + ".f06", "r") as jjiOutput:
                for line in jjiOutput.readlines():
                    if "The reference LS state for this calculation results in" in line:
                        maxEigvi = int(line.split("The reference LS state for this calculation results in")[1].strip().split()[0].strip())
            
            for eigv in range(1, maxEigvi + 1):
                
                calculated1holeStates.append([(i, jj, eigv)])
                
                currDir = rootDir + "/" + directory_name + "/radiative/" + shell_array[i] + "/2jj_" + str(jj) + "/eigv_" + str(eigv)
                currFileName = shell_array[i] + "_" + str(jj) + "_" + str(eigv)
                
                configureStateInputFile(f05Template_nuc, currDir, currFileName, configuration_1hole[i], jj, eigv)
                
                parallel_1hole_paths.append(currDir + "/" + exe_file)
        
        
        with open(file_cycle_log_1hole, "a") as log_1hole:
            log_1hole.write("1 hole states discovery done.\nList of all discovered states:\n")
            for state in calculated1holeStates:
                log_1hole.write(', '.join([str(qn) for qn in state[0]]) + "\n")
            
            log_1hole.write("ListEnd\n")
    
    
    # Variables to control if the last calculated state has been reached in each cycle
    found_cycle1 = False
    found_cycle2 = False
    found_cycle3 = False
    found_cycle4 = False
    
    # If no starting cycle has been defined or the starting cycle is 1
    if starting_cycle <= 1:
        # Counter for the first state to be calculated in the state lists
        start_counter = 0
        
        # If the starting cycle is 1 we search for the starting state in the list
        if starting_cycle == 1:
            counter = 0
            for state in calculated1holeStates:
                if found_cycle1 or starting_state == [(0, 0, 0)]:
                    i, jj, eigv = state[0]
                    
                    currDir = rootDir + "/" + directory_name + "/radiative/" + shell_array[i] + "/2jj_" + str(jj) + "/eigv_" + str(eigv)
                    currFileName = shell_array[i] + "_" + str(jj) + "_" + str(eigv)
                    
                    parallel_1hole_paths.append(currDir + "/" + exe_file)
                
                counter += 1
                
                # Search for the starting state
                if state[0] == starting_state:
                    found_cycle1 = True
                    start_counter = counter
                
        
        # Execute parallel batch job with logging of calculated state
        executeBatchStateCalculation(parallel_1hole_paths, file_cycle_log_1hole, calculated1holeStates[start_counter:], "First Cycle Last Calculated:\n")
    
    
    
    failed_first_cycle = []
    parallel_1hole_failed = []
    
    # -------------- FIRST CYCLE FOR CONVERGENCE CHECK -------------- #
    
    # If no starting cycle has been defined or the starting cycle is 1
    if starting_cycle <= 1:
        # Even if the starting cycle is 1 it means that the calculation has finished in the last executeBatchStateCalculation
        counter = 0
        for state in calculated1holeStates:
            i, jj, eigv = state[0]
            
            currDir = rootDir + "/" + directory_name + "/radiative/" + shell_array[i] + "/2jj_" + str(jj) + "/eigv_" + str(eigv)
            currFileName = shell_array[i] + "_" + str(jj) + "_" + str(eigv)
            
            converged, failed_orbital, overlap, higher_config, highest_percent, accuracy, Diff, welt = checkOutput(currDir, currFileName)
            
            calculated1holeStates[counter].append((higher_config, highest_percent, overlap, accuracy, Diff, welt))
            
            if not converged:
                
                configureStateInputFile(f05Template_10steps_nuc, currDir, currFileName, configuration_1hole[i], jj, eigv)
            
                parallel_1hole_failed.append(currDir + "/" + exe_file)
                failed_first_cycle.append(counter)
            else:
                if Diff < 0.0 or Diff >= diffThreshold or overlap >= overlapsThreshold:
                    configureStateInputFile(f05Template_10steps_nuc, currDir, currFileName, configuration_1hole[i], jj, eigv)
            
                    parallel_1hole_failed.append(currDir + "/" + exe_file)
                    failed_first_cycle.append(counter)
            
            counter += 1
        
        # -------------- PRINT FIRST CYCLE RESULTS -------------- #
        
        with open(file_results, "a") as resultDump:
            resultDump.write("First Cycle 1 Hole states\nShell, Shell index, 2J, Eigv, Higher Configuration, Percentage, Overlap, Accuracy, Energy Difference, Energy Welton\n")
            for state in calculated1holeStates:
                resultDump.write(shell_array[state[0][0]] + ", " + str(state[0][0]) + ", " + str(state[0][1]) + ", " + str(state[0][2]) + ", " + state[1][0] + ", " + str(state[1][1]) + ", " + str(state[1][2]) + ", " + str(state[1][3]) + ", " + str(state[1][4]) + ", " + str(state[1][5]) + "\n")
        
    
    
    
    # If no starting cycle has been defined or the starting cycle is 1 or 2
    if starting_cycle <= 2:
        # Counter for the first state to be calculated in the state lists
        start_counter = 0
        
        # If the starting cycle is 2 we search for the starting state in the list and fill in the failed_first_cycle list
        if starting_cycle == 2:
            counter = 0
            for state in calculated1holeStates:
                if found_cycle2 or starting_state == [(0, 0, 0)]:
                    i, jj, eigv = state[0]
                    
                    currDir = rootDir + "/" + directory_name + "/radiative/" + shell_array[i] + "/2jj_" + str(jj) + "/eigv_" + str(eigv)
                    currFileName = shell_array[i] + "_" + str(jj) + "_" + str(eigv)
                    
                    converged, failed_orbital, overlap, higher_config, highest_percent, accuracy, Diff, welt = checkOutput(currDir, currFileName)
                    
                    calculated1holeStates[counter].append((higher_config, highest_percent, overlap, accuracy, Diff, welt))
                    
                    if not converged:
                        # Only add this state to the calculation if we reached the starting state
                        if found_cycle2 or starting_state == [(0, 0, 0)]:
                            parallel_1hole_failed.append(currDir + "/" + exe_file)
                        
                        failed_first_cycle.append(counter)
                    else:
                        if Diff < 0.0 or Diff >= diffThreshold or overlap >= overlapsThreshold:
                            # Only add this state to the calculation if we reached the starting state
                            if found_cycle2 or starting_state == [(0, 0, 0)]:
                                parallel_1hole_failed.append(currDir + "/" + exe_file)
                            
                            failed_first_cycle.append(counter)
                
                counter += 1
                
                # Search for the starting state
                if state[0] == starting_state:
                    found_cycle2 = True
                    start_counter = counter
                
        
        if len(parallel_1hole_failed) == 0:
            writeResults1hole()
            return
        
        # Execute parallel batch job with logging of calculated state
        executeBatchStateCalculation(parallel_1hole_failed, file_cycle_log_1hole, calculated1holeStates[start_counter:], "Second Cycle Last Calculated:\n")
    
    
    failed_second_cycle = []
    parallel_1hole_failed = []
    
    
    # -------------- SECOND CYCLE FOR CONVERGENCE CHECK WITH FAILED ORBITALS -------------- #
    
    # If no starting cycle has been defined or the starting cycle is 1 or 2
    if starting_cycle <= 2:
        # Even if the starting cycle is 2 it means that the calculation has finished in the last executeBatchStateCalculation
        # After having filled the failed_first_cycle list we can continue the calculation
        for counter in failed_first_cycle:
            i, jj, eigv = calculated1holeStates[counter][0]
            
            currDir = rootDir + "/" + directory_name + "/radiative/" + shell_array[i] + "/2jj_" + str(jj) + "/eigv_" + str(eigv)
            currFileName = shell_array[i] + "_" + str(jj) + "_" + str(eigv)
            
            converged, failed_orbital, overlap, higher_config, highest_percent, accuracy, Diff, welt = checkOutput(currDir, currFileName)
            
            failed_orbs = [failed_orbital.strip() + "  1 5 0 1 :"]
            
            calculated1holeStates[counter][-1] = (higher_config, highest_percent, overlap, accuracy, Diff, welt, failed_orbs)
            
            if not converged:
                if failed_orbital != '':
                    configureStateInputFile(f05Template_10steps_Forbs_nuc, currDir, currFileName, configuration_1hole[i], jj, eigv, failed_orbs)
            
                    parallel_1hole_failed.append(currDir + "/" + exe_file)
                
                failed_second_cycle.append(counter)
            else:
                if Diff < 0.0 or Diff >= diffThreshold or overlap >= overlapsThreshold:
                    if failed_orbital != '':
                        configureStateInputFile(f05Template_10steps_Forbs_nuc, currDir, currFileName, configuration_1hole[i], jj, eigv, failed_orbs)
            
                        parallel_1hole_failed.append(currDir + "/" + exe_file)
                    
                    failed_second_cycle.append(counter)
            
        
        # -------------- PRINT SECOND CYCLE RESULTS -------------- #
        
        with open(file_results, "a") as resultDump:
            resultDump.write("Second Cycle 1 Hole states\nShell, Shell index, 2J, Eigv, Higher Configuration, Percentage, Overlap, Accuracy, Energy Difference, Energy Welton\n")
            for state in calculated1holeStates:
                resultDump.write(shell_array[state[0][0]] + ", " + str(state[0][0]) + ", " + str(state[0][1]) + ", " + str(state[0][2]) + ", " + state[1][0] + ", " + str(state[1][1]) + ", " + str(state[1][2]) + ", " + str(state[1][3]) + ", " + str(state[1][4]) + ", " + str(state[1][5]) + "\n")
    
    
    # If no starting cycle has been defined or the starting cycle is 1, 2 or 3
    if starting_cycle <= 3:
        # Counter for the first state to be calculated in the state lists
        start_counter = 0
        
        # If the starting cycle is 3 we search for the starting state in the list and fill in the failed_second_cycle list
        if starting_cycle == 3:
            counter = 0
            for state in calculated1holeStates:
                i, jj, eigv = state[0]
                
                currDir = rootDir + "/" + directory_name + "/radiative/" + shell_array[i] + "/2jj_" + str(jj) + "/eigv_" + str(eigv)
                currFileName = shell_array[i] + "_" + str(jj) + "_" + str(eigv)
                
                converged, failed_orbital, overlap, higher_config, highest_percent, accuracy, Diff, welt = checkOutput(currDir, currFileName)
                
                calculated1holeStates[counter].append((higher_config, highest_percent, overlap, accuracy, Diff, welt))
                
                if not converged:
                    # Only add this state to the calculation if we reached the starting state
                    if found_cycle3 or starting_state == [(0, 0, 0)]:
                        parallel_1hole_failed.append(currDir + "/" + exe_file)
                    
                    failed_second_cycle.append(counter)
                else:
                    if Diff < 0.0 or Diff >= diffThreshold or overlap >= overlapsThreshold:
                        # Only add this state to the calculation if we reached the starting state
                        if found_cycle3 or starting_state == [(0, 0, 0)]:
                            parallel_1hole_failed.append(currDir + "/" + exe_file)
                        
                        failed_second_cycle.append(counter)
                
                counter += 1
                
                if state[0] == starting_state:
                    found_cycle3 = True
                    start_counter = counter
                
        
        if len(parallel_1hole_failed) == 0:
            writeResults1hole()
            return
        
        # Execute parallel batch job with logging of calculated state
        executeBatchStateCalculation(parallel_1hole_failed, file_cycle_log_1hole, calculated1holeStates[start_counter:], "Third Cycle Last Calculated:\n")
    
    
    failed_third_cycle = []
    parallel_1hole_failed = []
    
    
    # -------------- THIRD CYCLE FOR CONVERGENCE CHECK WITH FAILED ORBITALS -------------- #
    
    # If no starting cycle has been defined or the starting cycle is 1 or 2
    if starting_cycle <= 3:
        # Even if the starting cycle is 3 it means that the calculation has finished in the last executeBatchStateCalculation
        # After having filled the failed_second_cycle list we can continue the calculation
        for counter in failed_second_cycle:
            i, jj, eigv = calculated1holeStates[counter][0]
            
            currDir = rootDir + "/" + directory_name + "/radiative/" + shell_array[i] + "/2jj_" + str(jj) + "/eigv_" + str(eigv)
            currFileName = shell_array[i] + "_" + str(jj) + "_" + str(eigv)
            
            converged, failed_orbital, overlap, higher_config, highest_percent, accuracy, Diff, welt = checkOutput(currDir, currFileName)
            
            failed_orbs = calculated1holeStates[counter][1][6]
            
            if failed_orbital != '':
                failed_orbs.append("    " + failed_orbital.strip() + "  1 5 0 1 :")
            
            
            if not converged:
                if failed_orbs[0] != "  1 5 0 1 :" and len(failed_orbs) == 2:
                    configureStateInputFile(f05Template_10steps_Forbs_nuc, currDir, currFileName, configuration_1hole[i], jj, eigv, failed_orbs)
            
                    parallel_1hole_failed.append(currDir + "/" + exe_file)
                elif len(failed_orbs) == 2:
                    del failed_orbs[0]
                    
                    configureStateInputFile(f05Template_10steps_Forbs_nuc, currDir, currFileName, configuration_1hole[i], jj, eigv, failed_orbs)
            
                    parallel_1hole_failed.append(currDir + "/" + exe_file)
                
                failed_third_cycle.append(counter)
            else:
                if Diff < 0.0 or Diff >= diffThreshold or overlap >= overlapsThreshold:
                    if failed_orbs[0] != "  1 5 0 1 :" and len(failed_orbs) == 2:
                        configureStateInputFile(f05Template_10steps_Forbs_nuc, currDir, currFileName, configuration_1hole[i], jj, eigv, failed_orbs)
            
                        parallel_1hole_failed.append(currDir + "/" + exe_file)
                    elif len(failed_orbs) == 2:
                        del failed_orbs[0]
                        
                        configureStateInputFile(f05Template_10steps_Forbs_nuc, currDir, currFileName, configuration_1hole[i], jj, eigv, failed_orbs)
            
                        parallel_1hole_failed.append(currDir + "/" + exe_file)
                
                failed_third_cycle.append(counter)
            
            calculated1holeStates[counter][-1] = (higher_config, highest_percent, overlap, accuracy, Diff, welt, failed_orbs)
            
        
        # -------------- PRINT THIRD CYCLE RESULTS -------------- #
        
        with open(file_results, "a") as resultDump:
            resultDump.write("Third Cycle 1 Hole states\nShell, Shell index, 2J, Eigv, Higher Configuration, Percentage, Overlap, Accuracy, Energy Difference, Energy Welton\n")
            for state in calculated1holeStates:
                resultDump.write(shell_array[state[0][0]] + ", " + str(state[0][0]) + ", " + str(state[0][1]) + ", " + str(state[0][2]) + ", " + state[1][0] + ", " + str(state[1][1]) + ", " + str(state[1][2]) + ", " + str(state[1][3]) + ", " + str(state[1][4]) + ", " + str(state[1][5]) + "\n")
    
    
    # If no starting cycle has been defined or the starting cycle is 1, 2, 3 or 4
    # Counter for the first state to be calculated in the state lists
    start_counter = 0
    
    # If the starting cycle is 4 we search for the starting state in the list and fill in the failed_third_cycle list
    if starting_cycle == 4:
        counter = 0
        for state in calculated1holeStates:
            i, jj, eigv = state[0]
            
            currDir = rootDir + "/" + directory_name + "/radiative/" + shell_array[i] + "/2jj_" + str(jj) + "/eigv_" + str(eigv)
            currFileName = shell_array[i] + "_" + str(jj) + "_" + str(eigv)
            
            converged, failed_orbital, overlap, higher_config, highest_percent, accuracy, Diff, welt = checkOutput(currDir, currFileName)
            
            calculated1holeStates[counter].append((higher_config, highest_percent, overlap, accuracy, Diff, welt))
            
            if not converged:
                # Only add this state to the calculation if we reached the starting state
                if found_cycle4 or starting_state == [(0, 0, 0)]:
                    parallel_1hole_failed.append(currDir + "/" + exe_file)
                
                failed_third_cycle.append(counter)
            else:
                if Diff < 0.0 or Diff >= diffThreshold or overlap >= overlapsThreshold:
                    # Only add this state to the calculation if we reached the starting state
                    if found_cycle4 or starting_state == [(0, 0, 0)]:
                        parallel_1hole_failed.append(currDir + "/" + exe_file)
                    
                    failed_third_cycle.append(counter)
            
            counter += 1
            
            if state[0] == starting_state:
                found_cycle4 = True
                start_counter = counter
            
    
    if len(parallel_1hole_failed) == 0:
        writeResults1hole()
        return
    
    # Execute parallel batch job with logging of calculated state
    executeBatchStateCalculation(parallel_1hole_failed, file_cycle_log_1hole, calculated1holeStates[start_counter:], "Fourth Cycle Last Calculated:\n")
    
    
    radiative_by_hand = []
    
    # -------------- FOURTH CYCLE TO CHECK WHICH STATES NEED TO BE REDONE BY HAND -------------- #
    
    # If no starting cycle has been defined or the starting cycle is 1, 2, 3 or 4
    for counter in failed_third_cycle:
        i, jj, eigv = calculated1holeStates[counter][0]
        
        currDir = rootDir + "/" + directory_name + "/radiative/" + shell_array[i] + "/2jj_" + str(jj) + "/eigv_" + str(eigv)
        currFileName = shell_array[i] + "_" + str(jj) + "_" + str(eigv)
        
        converged, failed_orbital, overlap, higher_config, highest_percent, accuracy, Diff, welt = checkOutput(currDir, currFileName)
        
        calculated1holeStates[counter][-1] = (higher_config, highest_percent, overlap, accuracy, Diff, welt)
        
        if not converged:
            radiative_by_hand.append(counter)
        else:
            if Diff < 0.0 or Diff >= diffThreshold or overlap >= overlapsThreshold:
                radiative_by_hand.append(counter)
    
    
    # -------------- WRITE RESULTS TO THE FILES -------------- #
    
    writeResults1hole()
    
    

def calculate2holesStates(starting_cycle = -1, starting_state = [(0, 0, 0)]):
    global calculated2holesStates, auger_by_hand
    
    jj_vals = []
    
    parallel_2holes_paths = []
    
    # If no starting cycle has been specified
    if starting_cycle == -1:
        # -------------- DETERMINE 2J MAX VALUE -------------- #
        
        for i in range(len(shell_array_2holes)):
            currDir = rootDir + "/" + directory_name + "/auger/" + shell_array_2holes[i]
            currFileName = shell_array_2holes[i]
            
            configureStateInputFile(f05Template_nuc, currDir, currFileName, configuration_2holes[i], "100" if int(nelectrons) - 1 % 2 == 0 else "101", "100", [], int(nelectrons) - 1)
            
            parallel_2holes_paths.append(currDir + "/" + exe_file)
            
        
        # Execute parallel batch job
        executeBatchStateCalculation(parallel_2holes_paths)
        
        
        parallel_2holes_paths = []
        
        # -------------- DETERMINE EIGENVALUE MAX VALUE -------------- #
        
        for i in range(len(shell_array_2holes)):
            currDir = rootDir + "/" + directory_name + "/auger/" + shell_array_2holes[i]
            currFileName = shell_array_2holes[i]
            
            maxJJi = 0
            
            with open(currDir + "/" + currFileName + ".f06", "r") as labelOutput:
                for line in labelOutput.readlines():
                    if "!!!!! For state # 1 and configuration   1 highest 2Jz possible value is" in line:
                        maxJJi = int(line.split("!!!!! For state # 1 and configuration   1 highest 2Jz possible value is")[1].split()[0].strip())
            
            for jj in range(0 if maxJJi % 2 == 0 else 1, maxJJi + 1, 2):
                jj_vals.append((i, jj))
                
                currDir = rootDir + "/" + directory_name + "/auger/" + shell_array_2holes[i] + "/2jj_" + str(jj)
                currFileName = shell_array_2holes[i] + "_" + str(jj)
                
                configureStateInputFile(f05Template_nuc, currDir, currFileName, configuration_2holes[i], jj, "100", [], int(nelectrons) - 1)
            
                parallel_2holes_paths.append(currDir + "/" + exe_file)
        
        # Execute parallel batch job
        executeBatchStateCalculation(parallel_2holes_paths)
        
        
        parallel_2holes_paths = []
        
        # -------------- FULL STATE CALCULATION -------------- #
        
        for i, jj in jj_vals:
            currDir = rootDir + "/" + directory_name + "/auger/" + shell_array_2holes[i] + "/2jj_" + str(jj)
            currFileName = shell_array_2holes[i] + "_" + str(jj)
            
            maxEigvi = 0
            
            with open(currDir + "/" + currFileName + ".f06", "r") as jjiOutput:
                for line in jjiOutput.readlines():
                    if "The reference LS state for this calculation results in" in line:
                        maxEigvi = int(line.split("The reference LS state for this calculation results in")[1].strip().split()[0].strip())
            
            for eigv in range(1, maxEigvi + 1):
                
                calculated2holesStates.append([(i, jj, eigv)])
                
                currDir = rootDir + "/" + directory_name + "/auger/" + shell_array_2holes[i] + "/2jj_" + str(jj) + "/eigv_" + str(eigv)
                currFileName = shell_array_2holes[i] + "_" + str(jj) + "_" + str(eigv)
                
                configureStateInputFile(f05Template_nuc, currDir, currFileName, configuration_2holes[i], jj, eigv, [], int(nelectrons) - 1)
                
                parallel_2holes_paths.append(currDir + "/" + exe_file)
        
        
        with open(file_cycle_log_2holes, "a") as log_2holes:
            log_2holes.write("2 holes states discovery done.\nList of all discovered states:\n")
            for state in calculated2holesStates:
                log_2holes.write(', '.join([str(qn) for qn in state[0]]) + "\n")
            
            log_2holes.write("ListEnd\n")
    
    
    
    # Variables to control if the last calculated state has been reached in each cycle
    found_cycle1 = False
    found_cycle2 = False
    found_cycle3 = False
    found_cycle4 = False
    
    # If no starting cycle has been defined or the starting cycle is 1
    if starting_cycle <= 1:
        # Counter for the first state to be calculated in the state lists
        start_counter = 0
        
        # If the starting cycle is 1 we search for the starting state in the list
        if starting_cycle == 1:
            counter = 0
            for state in calculated2holesStates:
                if found_cycle1 or starting_state == [(0, 0, 0)]:
                    i, jj, eigv = state[0]
                    
                    currDir = rootDir + "/" + directory_name + "/auger/" + shell_array_2holes[i] + "/2jj_" + str(jj) + "/eigv_" + str(eigv)
                    currFileName = shell_array_2holes[i] + "_" + str(jj) + "_" + str(eigv)
        
                    parallel_2holes_paths.append(currDir + "/" + exe_file)
                
                counter += 1
                
                # Search for the starting state
                if state[0] == starting_state:
                    found_cycle1 = True
                    start_counter = counter
                
        
        # Execute parallel batch job with logging of calculated state
        executeBatchStateCalculation(parallel_2holes_paths, file_cycle_log_2holes, calculated2holesStates[start_counter:], "First Cycle Last Calculated:\n")
    
    
    failed_first_cycle = []
    parallel_2holes_failed = []
    
    # -------------- FIRST CYCLE FOR CONVERGENCE CHECK -------------- #
    
    # If no starting cycle has been defined or the starting cycle is 1
    if starting_cycle <= 1:
        # Even if the starting cycle is 1 it means that the calculation has finished in the last executeBatchStateCalculation
        counter = 0
        for state in calculated2holesStates:
            i, jj, eigv = state[0]
            
            currDir = rootDir + "/" + directory_name + "/auger/" + shell_array_2holes[i] + "/2jj_" + str(jj) + "/eigv_" + str(eigv)
            currFileName = shell_array_2holes[i] + "_" + str(jj) + "_" + str(eigv)
            
            converged, failed_orbital, overlap, higher_config, highest_percent, accuracy, Diff, welt = checkOutput(currDir, currFileName)
            
            calculated2holesStates[counter].append((higher_config, highest_percent, overlap, accuracy, Diff, welt))
            
            if not converged:
                
                configureStateInputFile(f05Template_10steps_nuc, currDir, currFileName, configuration_2holes[i], jj, eigv, [], int(nelectrons) - 1)
            
                parallel_2holes_failed.append(currDir + "/" + exe_file)
                failed_first_cycle.append(counter)
            else:
                if Diff < 0.0 or Diff >= diffThreshold or overlap >= overlapsThreshold:
                    configureStateInputFile(f05Template_10steps_nuc, currDir, currFileName, configuration_2holes[i], jj, eigv, [], int(nelectrons) - 1)
            
                    parallel_2holes_failed.append(currDir + "/" + exe_file)
                    failed_first_cycle.append(counter)
            
            counter += 1
        
        # -------------- PRINT FIRST CYCLE RESULTS -------------- #
        
        with open(file_results, "a") as resultDump:
            resultDump.write("First Cycle 2 Hole states\nShell, Shell index, 2J, Eigv, Higher Configuration, Percentage, Overlap, Accuracy, Energy Difference, Energy Welton\n")
            for state in calculated2holesStates:
                resultDump.write(shell_array_2holes[state[0][0]] + ", " + str(state[0][0]) + ", " + str(state[0][1]) + ", " + str(state[0][2]) + ", " + state[1][0] + ", " + str(state[1][1]) + ", " + str(state[1][2]) + ", " + str(state[1][3]) + ", " + str(state[1][4]) + ", " + str(state[1][5]) + "\n")
        
    
    
    # If no starting cycle has been defined or the starting cycle is 1 or 2
    if starting_cycle <= 2:
        # Counter for the first state to be calculated in the state lists
        start_counter = 0
        
        # If the starting cycle is 2 we search for the starting state in the list and fill in the failed_first_cycle list
        if starting_cycle == 2:
            counter = 0
            for state in calculated2holesStates:
                if found_cycle2 or starting_state == [(0, 0, 0)]:
                    i, jj, eigv = state[0]
                    
                    currDir = rootDir + "/" + directory_name + "/auger/" + shell_array_2holes[i] + "/2jj_" + str(jj) + "/eigv_" + str(eigv)
                    currFileName = shell_array_2holes[i] + "_" + str(jj) + "_" + str(eigv)
                    
                    converged, failed_orbital, overlap, higher_config, highest_percent, accuracy, Diff, welt = checkOutput(currDir, currFileName)
                    
                    calculated2holesStates[counter].append((higher_config, highest_percent, overlap, accuracy, Diff, welt))
                    
                    if not converged:
                        # Only add this state to the calculation if we reached the starting state
                        if found_cycle2 or starting_state == [(0, 0, 0)]:
                            parallel_2holes_failed.append(currDir + "/" + exe_file)
                        
                        failed_first_cycle.append(counter)
                    else:
                        if Diff < 0.0 or Diff >= diffThreshold or overlap >= overlapsThreshold:
                            # Only add this state to the calculation if we reached the starting state
                            if found_cycle2 or starting_state == [(0, 0, 0)]:
                                parallel_2holes_failed.append(currDir + "/" + exe_file)
                            
                            failed_first_cycle.append(counter)
                
                counter += 1
                
                # Search for the starting state
                if state[0] == starting_state:
                    found_cycle2 = True
                    start_counter = counter
                
        
        if len(parallel_2holes_failed) == 0:
            writeResults2holes()
            return
        
        # Execute parallel batch job with logging of calculated state
        executeBatchStateCalculation(parallel_2holes_failed, file_cycle_log_2holes, calculated2holesStates[start_counter:], "Second Cycle Last Calculated:\n")
    
    
    failed_second_cycle = []
    parallel_2holes_failed = []
    
    
    # -------------- SECOND CYCLE FOR CONVERGENCE CHECK WITH FAILED ORBITALS -------------- #
    
    # If no starting cycle has been defined or the starting cycle is 1 or 2
    if starting_cycle <= 2:
        # Even if the starting cycle is 2 it means that the calculation has finished in the last executeBatchStateCalculation
        # After having filled the failed_first_cycle list we can continue the calculation
        for counter in failed_first_cycle:
            i, jj, eigv = calculated2holesStates[counter][0]
            
            currDir = rootDir + "/" + directory_name + "/auger/" + shell_array_2holes[i] + "/2jj_" + str(jj) + "/eigv_" + str(eigv)
            currFileName = shell_array_2holes[i] + "_" + str(jj) + "_" + str(eigv)
            
            converged, failed_orbital, overlap, higher_config, highest_percent, accuracy, Diff, welt = checkOutput(currDir, currFileName)
            
            failed_orbs = [failed_orbital.strip() + "  1 5 0 1 :"]
            
            
            calculated2holesStates[counter][-1] = (higher_config, highest_percent, overlap, accuracy, Diff, welt, failed_orbs)
            
            if not converged:
                if failed_orbital != '':
                    configureStateInputFile(f05Template_10steps_Forbs_nuc, currDir, currFileName, configuration_2holes[i], jj, eigv, failed_orbs, int(nelectrons) - 1)
                
                    parallel_2holes_failed.append(currDir + "/" + exe_file)
                
                failed_second_cycle.append(counter)
            else:
                if Diff < 0.0 or Diff >= diffThreshold or overlap >= overlapsThreshold:
                    if failed_orbital != '':
                        configureStateInputFile(f05Template_10steps_Forbs_nuc, currDir, currFileName, configuration_2holes[i], jj, eigv, failed_orbs, int(nelectrons) - 1)
            
                        parallel_2holes_failed.append(currDir + "/" + exe_file)
                    
                    failed_second_cycle.append(counter)
            
        
        # -------------- PRINT SECOND CYCLE RESULTS -------------- #
        
        with open(file_results, "a") as resultDump:
            resultDump.write("Second Cycle 2 Hole states\nShell, Shell index, 2J, Eigv, Higher Configuration, Percentage, Overlap, Accuracy, Energy Difference, Energy Welton\n")
            for state in calculated2holesStates:
                resultDump.write(shell_array_2holes[state[0][0]] + ", " + str(state[0][0]) + ", " + str(state[0][1]) + ", " + str(state[0][2]) + ", " + state[1][0] + ", " + str(state[1][1]) + ", " + str(state[1][2]) + ", " + str(state[1][3]) + ", " + str(state[1][4]) + ", " + str(state[1][5]) + "\n")
        
    
    
    # If no starting cycle has been defined or the starting cycle is 1, 2 or 3
    if starting_cycle <= 3:
        # Counter for the first state to be calculated in the state lists
        start_counter = 0
        
        # If the starting cycle is 3 we search for the starting state in the list and fill in the failed_second_cycle list
        if starting_cycle == 3:
            counter = 0
            for state in calculated2holesStates:
                i, jj, eigv = state[0]
                
                currDir = rootDir + "/" + directory_name + "/auger/" + shell_array_2holes[i] + "/2jj_" + str(jj) + "/eigv_" + str(eigv)
                currFileName = shell_array_2holes[i] + "_" + str(jj) + "_" + str(eigv)
        
                converged, failed_orbital, overlap, higher_config, highest_percent, accuracy, Diff, welt = checkOutput(currDir, currFileName)
                
                calculated2holesStates[counter].append((higher_config, highest_percent, overlap, accuracy, Diff, welt))
                
                if not converged:
                    # Only add this state to the calculation if we reached the starting state
                    if found_cycle3 or starting_state == [(0, 0, 0)]:
                        parallel_2holes_failed.append(currDir + "/" + exe_file)
                    
                    failed_second_cycle.append(counter)
                else:
                    if Diff < 0.0 or Diff >= diffThreshold or overlap >= overlapsThreshold:
                        # Only add this state to the calculation if we reached the starting state
                        if found_cycle3 or starting_state == [(0, 0, 0)]:
                            parallel_2holes_failed.append(currDir + "/" + exe_file)
                        
                        failed_second_cycle.append(counter)
                
                counter += 1
                
                if state[0] == starting_state:
                    found_cycle3 = True
                    start_counter = counter
                
        
        if len(parallel_2holes_failed) == 0:
            writeResults2holes()
            return
        
        # Execute parallel batch job with logging of calculated state
        executeBatchStateCalculation(parallel_2holes_failed, file_cycle_log_2holes, calculated2holesStates, "Third Cycle Last Calculated:\n")
    
    
    failed_third_cycle = []
    parallel_2holes_failed = []
    
    # -------------- THIRD CYCLE FOR CONVERGENCE CHECK WITH FAILED ORBITALS -------------- #
    
    # If no starting cycle has been defined or the starting cycle is 1 or 2
    if starting_cycle <= 3:
        # Even if the starting cycle is 3 it means that the calculation has finished in the last executeBatchStateCalculation
        # After having filled the failed_second_cycle list we can continue the calculation
        for counter in failed_second_cycle:
            i, jj, eigv = calculated2holesStates[counter][0]
            
            currDir = rootDir + "/" + directory_name + "/auger/" + shell_array_2holes[i] + "/2jj_" + str(jj) + "/eigv_" + str(eigv)
            currFileName = shell_array_2holes[i] + "_" + str(jj) + "_" + str(eigv)
            
            converged, failed_orbital, overlap, higher_config, highest_percent, accuracy, Diff, welt = checkOutput(currDir, currFileName)
            
            failed_orbs = calculated2holesStates[counter][1][6]
            
            if failed_orbital != '':
                failed_orbs.append("    " + failed_orbital + "  1 5 0 1 :")
            
            
            if not converged:
                if failed_orbs[0] != "  1 5 0 1 :" and len(failed_orbs) == 2:
                    configureStateInputFile(f05Template_10steps_Forbs_nuc, currDir, currFileName, configuration_2holes[i], jj, eigv, failed_orbs, int(nelectrons) - 1)
            
                    parallel_2holes_failed.append(currDir + "/" + exe_file)
                elif len(failed_orbs) == 2:
                    del failed_orbs[0]
                    
                    configureStateInputFile(f05Template_10steps_Forbs_nuc, currDir, currFileName, configuration_2holes[i], jj, eigv, failed_orbs, int(nelectrons) - 1)
            
                    parallel_2holes_failed.append(currDir + "/" + exe_file)
                
                failed_third_cycle.append(counter)
            else:
                if Diff < 0.0 or Diff >= diffThreshold or overlap >= overlapsThreshold:
                    if failed_orbs[0] != "  1 5 0 1 :" and len(failed_orbs) == 2:
                        configureStateInputFile(f05Template_10steps_Forbs_nuc, currDir, currFileName, configuration_2holes[i], jj, eigv, failed_orbs, int(nelectrons) - 1)
            
                        parallel_2holes_failed.append(currDir + "/" + exe_file)
                    elif len(failed_orbs) == 2:
                        del failed_orbs[0]
                        
                        configureStateInputFile(f05Template_10steps_Forbs_nuc, currDir, currFileName, configuration_2holes[i], jj, eigv, failed_orbs, int(nelectrons) - 1)
            
                        parallel_2holes_failed.append(currDir + "/" + exe_file)
                
                failed_third_cycle.append(counter)
            
            calculated2holesStates[counter][-1] = (higher_config, highest_percent, overlap, accuracy, Diff, welt, failed_orbs)
            
        
        # -------------- PRINT THIRD CYCLE RESULTS -------------- #
        
        with open(file_results, "a") as resultDump:
            resultDump.write("Third Cycle 2 Hole states\nShell, Shell index, 2J, Eigv, Higher Configuration, Percentage, Overlap, Accuracy, Energy Difference, Energy Welton\n")
            for state in calculated2holesStates:
                resultDump.write(shell_array_2holes[state[0][0]] + ", " + str(state[0][0]) + ", " + str(state[0][1]) + ", " + str(state[0][2]) + ", " + state[1][0] + ", " + str(state[1][1]) + ", " + str(state[1][2]) + ", " + str(state[1][3]) + ", " + str(state[1][4]) + ", " + str(state[1][5]) + "\n")
    
    
    # If no starting cycle has been defined or the starting cycle is 1, 2, 3 or 4
    # Counter for the first state to be calculated in the state lists
    start_counter = 0
    
    # If the starting cycle is 4 we search for the starting state in the list and fill in the failed_third_cycle list
    if starting_cycle == 4:
        counter = 0
        for state in calculated2holesStates:
            i, jj, eigv = state[0]
            
            currDir = rootDir + "/" + directory_name + "/auger/" + shell_array_2holes[i] + "/2jj_" + str(jj) + "/eigv_" + str(eigv)
            currFileName = shell_array_2holes[i] + "_" + str(jj) + "_" + str(eigv)
            
            converged, failed_orbital, overlap, higher_config, highest_percent, accuracy, Diff, welt = checkOutput(currDir, currFileName)
            
            calculated2holesStates[counter].append((higher_config, highest_percent, overlap, accuracy, Diff, welt))
            
            if not converged:
                # Only add this state to the calculation if we reached the starting state
                if found_cycle4 or starting_state == [(0, 0, 0)]:
                    parallel_2holes_failed.append(currDir + "/" + exe_file)
                
                failed_third_cycle.append(counter)
            else:
                if Diff < 0.0 or Diff >= diffThreshold or overlap >= overlapsThreshold:
                    # Only add this state to the calculation if we reached the starting state
                    if found_cycle4 or starting_state == [(0, 0, 0)]:
                        parallel_2holes_failed.append(currDir + "/" + exe_file)
                    
                    failed_third_cycle.append(counter)
            
            counter += 1
            
            if state[0] == starting_state:
                found_cycle4 = True
                start_counter = counter
            
    
    if len(parallel_2holes_failed) == 0:
        writeResults2holes()
        return
    
    # Execute parallel batch job with logging of calculated state
    executeBatchStateCalculation(parallel_2holes_failed, file_cycle_log_2holes, calculated2holesStates, "Fourth Cycle Last Calculated:\n")
    
    
    auger_by_hand = []
    
    # -------------- FOURTH CYCLE TO CHECK WHICH STATES NEED TO BE REDONE BY HAND -------------- #
    
    # If no starting cycle has been defined or the starting cycle is 1, 2, 3 or 4
    for counter in failed_third_cycle:
        i, jj, eigv = calculated2holesStates[counter][0]
        
        currDir = rootDir + "/" + directory_name + "/auger/" + shell_array_2holes[i] + "/2jj_" + str(jj) + "/eigv_" + str(eigv)
        currFileName = shell_array_2holes[i] + "_" + str(jj) + "_" + str(eigv)
        
        converged, failed_orbital, overlap, higher_config, highest_percent, accuracy, Diff, welt = checkOutput(currDir, currFileName)
        
        calculated2holesStates[counter][-1] = (higher_config, highest_percent, overlap, accuracy, Diff, welt)
        
        if not converged:
            auger_by_hand.append(counter)
        else:
            if Diff < 0.0 or Diff >= diffThreshold or overlap > overlapsThreshold:
                auger_by_hand.append(counter)
    
    
    # -------------- WRITE RESULTS TO THE FILES -------------- #
    
    writeResults2holes()
    


def calculate3holesStates(starting_cycle = -1, starting_state = [(0, 0, 0)]):
    global calculated3holesStates, sat_auger_by_hand
    
    jj_vals = []
    
    parallel_3holes_paths = []
    
    # If no starting cycle has been specified
    if starting_cycle == -1:
        # -------------- DETERMINE 2J MAX VALUE -------------- #
        
        for i in range(len(shell_array_3holes)):
            currDir = rootDir + "/" + directory_name + "/3holes/" + shell_array_3holes[i]
            currFileName = shell_array_3holes[i]
            
            configureStateInputFile(f05Template_nuc, currDir, currFileName, configuration_3holes[i], "100" if int(nelectrons) - 2 % 2 == 0 else "101", "100", [], int(nelectrons) - 2)
            
            parallel_3holes_paths.append(currDir + "/" + exe_file)
            
        
        # Execute parallel batch job
        executeBatchStateCalculation(parallel_3holes_paths)
        
        
        parallel_3holes_paths = []
        
        # -------------- DETERMINE EIGENVALUE MAX VALUE -------------- #
        
        for i in range(len(shell_array_3holes)):
            currDir = rootDir + "/" + directory_name + "/3holes/" + shell_array_3holes[i]
            currFileName = shell_array_3holes[i]
            
            maxJJi = 0
            
            with open(currDir + "/" + currFileName + ".f06", "r") as labelOutput:
                for line in labelOutput.readlines():
                    if "!!!!! For state # 1 and configuration   1 highest 2Jz possible value is" in line:
                        maxJJi = int(line.split("!!!!! For state # 1 and configuration   1 highest 2Jz possible value is")[1].split()[0].strip())
            
            for jj in range(0 if maxJJi % 2 == 0 else 1, maxJJi + 1, 2):
                jj_vals.append((i, jj))
                
                currDir = rootDir + "/" + directory_name + "/3holes/" + shell_array_3holes[i] + "/2jj_" + str(jj)
                currFileName = shell_array_3holes[i] + "_" + str(jj)
                
                configureStateInputFile(f05Template_nuc, currDir, currFileName, configuration_3holes[i], jj, "100", [], int(nelectrons) - 2)
            
                parallel_3holes_paths.append(currDir + "/" + exe_file)
        
        # Execute parallel batch job
        executeBatchStateCalculation(parallel_3holes_paths)
        
        
        parallel_3holes_paths = []
        
        # -------------- FULL STATE CALCULATION -------------- #
        
        for i, jj in jj_vals:
            currDir = rootDir + "/" + directory_name + "/3holes/" + shell_array_3holes[i] + "/2jj_" + str(jj)
            currFileName = shell_array_3holes[i] + "_" + str(jj)
            
            maxEigvi = 0
            
            with open(currDir + "/" + currFileName + ".f06", "r") as jjiOutput:
                for line in jjiOutput.readlines():
                    if "The reference LS state for this calculation results in" in line:
                        maxEigvi = int(line.split("The reference LS state for this calculation results in")[1].strip().split()[0].strip())
            
            for eigv in range(1, maxEigvi + 1):
                
                calculated3holesStates.append([(i, jj, eigv)])
                
                currDir = rootDir + "/" + directory_name + "/3holes/" + shell_array_3holes[i] + "/2jj_" + str(jj) + "/eigv_" + str(eigv)
                currFileName = shell_array_3holes[i] + "_" + str(jj) + "_" + str(eigv)
                
                configureStateInputFile(f05Template_nuc, currDir, currFileName, configuration_3holes[i], jj, eigv, [], int(nelectrons) - 2)
                
                parallel_3holes_paths.append(currDir + "/" + exe_file)
        
        
        with open(file_cycle_log_3holes, "a") as log_3holes:
            log_3holes.write("3 holes states discovery done.\nList of all discovered states:\n")
            for state in calculated3holesStates:
                log_3holes.write(', '.join([str(qn) for qn in state[0]]) + "\n")
            
            log_3holes.write("ListEnd\n")
    
    
    
    # Variables to control if the last calculated state has been reached in each cycle
    found_cycle1 = False
    found_cycle2 = False
    found_cycle3 = False
    found_cycle4 = False
    
    # If no starting cycle has been defined or the starting cycle is 1
    if starting_cycle <= 1:
        # Counter for the first state to be calculated in the state lists
        start_counter = 0
        
        # If the starting cycle is 1 we search for the starting state in the list
        if starting_cycle == 1:
            counter = 0
            for state in calculated3holesStates:
                if found_cycle1 or starting_state == [(0, 0, 0)]:
                    i, jj, eigv = state[0]
                    
                    currDir = rootDir + "/" + directory_name + "/3holes/" + shell_array_3holes[i] + "/2jj_" + str(jj) + "/eigv_" + str(eigv)
                    currFileName = shell_array_3holes[i] + "_" + str(jj) + "_" + str(eigv)
        
                    parallel_3holes_paths.append(currDir + "/" + exe_file)
                
                counter += 1
                
                # Search for the starting state
                if state[0] == starting_state:
                    found_cycle1 = True
                    start_counter = counter
                
        
        # Execute parallel batch job with logging of calculated state
        executeBatchStateCalculation(parallel_3holes_paths, file_cycle_log_3holes, calculated3holesStates[start_counter:], "First Cycle Last Calculated:\n")
    
    
    failed_first_cycle = []
    parallel_3holes_failed = []
    
    # -------------- FIRST CYCLE FOR CONVERGENCE CHECK -------------- #
    
    # If no starting cycle has been defined or the starting cycle is 1
    if starting_cycle <= 1:
        # Even if the starting cycle is 1 it means that the calculation has finished in the last executeBatchStateCalculation
        counter = 0
        for state in calculated3holesStates:
            i, jj, eigv = state[0]
            
            currDir = rootDir + "/" + directory_name + "/3holes/" + shell_array_3holes[i] + "/2jj_" + str(jj) + "/eigv_" + str(eigv)
            currFileName = shell_array_3holes[i] + "_" + str(jj) + "_" + str(eigv)
            
            converged, failed_orbital, overlap, higher_config, highest_percent, accuracy, Diff, welt = checkOutput(currDir, currFileName)
            
            calculated3holesStates[counter].append((higher_config, highest_percent, overlap, accuracy, Diff, welt))
            
            if not converged:
                
                configureStateInputFile(f05Template_10steps_nuc, currDir, currFileName, configuration_3holes[i], jj, eigv, [], int(nelectrons) - 2)
            
                parallel_3holes_failed.append(currDir + "/" + exe_file)
                failed_first_cycle.append(counter)
            else:
                if Diff < 0.0 or Diff >= diffThreshold or overlap >= overlapsThreshold:
                    configureStateInputFile(f05Template_10steps_nuc, currDir, currFileName, configuration_3holes[i], jj, eigv, [], int(nelectrons) - 2)
            
                    parallel_3holes_failed.append(currDir + "/" + exe_file)
                    failed_first_cycle.append(counter)
            
            counter += 1
        
        # -------------- PRINT FIRST CYCLE RESULTS -------------- #
        
        with open(file_results, "a") as resultDump:
            resultDump.write("First Cycle 3 Hole states\nShell, Shell index, 2J, Eigv, Higher Configuration, Percentage, Overlap, Accuracy, Energy Difference, Energy Welton\n")
            for state in calculated3holesStates:
                resultDump.write(shell_array_3holes[state[0][0]] + ", " + str(state[0][0]) + ", " + str(state[0][1]) + ", " + str(state[0][2]) + ", " + state[1][0] + ", " + str(state[1][1]) + ", " + str(state[1][2]) + ", " + str(state[1][3]) + ", " + str(state[1][4]) + ", " + str(state[1][5]) + "\n")
        
    
    
    # If no starting cycle has been defined or the starting cycle is 1 or 2
    if starting_cycle <= 2:
        # Counter for the first state to be calculated in the state lists
        start_counter = 0
        
        # If the starting cycle is 2 we search for the starting state in the list and fill in the failed_first_cycle list
        if starting_cycle == 2:
            counter = 0
            for state in calculated3holesStates:
                if found_cycle2 or starting_state == [(0, 0, 0)]:
                    i, jj, eigv = state[0]
                    
                    currDir = rootDir + "/" + directory_name + "/3holes/" + shell_array_3holes[i] + "/2jj_" + str(jj) + "/eigv_" + str(eigv)
                    currFileName = shell_array_3holes[i] + "_" + str(jj) + "_" + str(eigv)
                    
                    converged, failed_orbital, overlap, higher_config, highest_percent, accuracy, Diff, welt = checkOutput(currDir, currFileName)
                    
                    calculated3holesStates[counter].append((higher_config, highest_percent, overlap, accuracy, Diff, welt))
                    
                    if not converged:
                        # Only add this state to the calculation if we reached the starting state
                        if found_cycle2 or starting_state == [(0, 0, 0)]:
                            parallel_3holes_failed.append(currDir + "/" + exe_file)
                        
                        failed_first_cycle.append(counter)
                    else:
                        if Diff < 0.0 or Diff >= diffThreshold or overlap >= overlapsThreshold:
                            # Only add this state to the calculation if we reached the starting state
                            if found_cycle2 or starting_state == [(0, 0, 0)]:
                                parallel_3holes_failed.append(currDir + "/" + exe_file)
                            
                            failed_first_cycle.append(counter)
                
                counter += 1
                
                # Search for the starting state
                if state[0] == starting_state:
                    found_cycle2 = True
                    start_counter = counter
                
        
        if len(parallel_3holes_failed) == 0:
            writeResults3holes()
            return
        
        # Execute parallel batch job with logging of calculated state
        executeBatchStateCalculation(parallel_3holes_failed, file_cycle_log_3holes, calculated3holesStates[start_counter:], "Second Cycle Last Calculated:\n")
    
    
    failed_second_cycle = []
    parallel_3holes_failed = []
    
    
    # -------------- SECOND CYCLE FOR CONVERGENCE CHECK WITH FAILED ORBITALS -------------- #
    
    # If no starting cycle has been defined or the starting cycle is 1 or 2
    if starting_cycle <= 2:
        # Even if the starting cycle is 2 it means that the calculation has finished in the last executeBatchStateCalculation
        # After having filled the failed_first_cycle list we can continue the calculation
        for counter in failed_first_cycle:
            i, jj, eigv = calculated3holesStates[counter][0]
            
            currDir = rootDir + "/" + directory_name + "/3holes/" + shell_array_3holes[i] + "/2jj_" + str(jj) + "/eigv_" + str(eigv)
            currFileName = shell_array_3holes[i] + "_" + str(jj) + "_" + str(eigv)
            
            converged, failed_orbital, overlap, higher_config, highest_percent, accuracy, Diff, welt = checkOutput(currDir, currFileName)
            
            failed_orbs = [failed_orbital.strip() + "  1 5 0 1 :"]
            
            
            calculated3holesStates[counter][-1] = (higher_config, highest_percent, overlap, accuracy, Diff, welt, failed_orbs)
            
            if not converged:
                if failed_orbital != '':
                    configureStateInputFile(f05Template_10steps_Forbs_nuc, currDir, currFileName, configuration_3holes[i], jj, eigv, failed_orbs, int(nelectrons) - 2)
                
                    parallel_3holes_failed.append(currDir + "/" + exe_file)
                
                failed_second_cycle.append(counter)
            else:
                if Diff < 0.0 or Diff >= diffThreshold or overlap >= overlapsThreshold:
                    if failed_orbital != '':
                        configureStateInputFile(f05Template_10steps_Forbs_nuc, currDir, currFileName, configuration_3holes[i], jj, eigv, failed_orbs, int(nelectrons) - 2)
            
                        parallel_3holes_failed.append(currDir + "/" + exe_file)
                    
                    failed_second_cycle.append(counter)
            
        
        # -------------- PRINT SECOND CYCLE RESULTS -------------- #
        
        with open(file_results, "a") as resultDump:
            resultDump.write("Second Cycle 3 Hole states\nShell, Shell index, 2J, Eigv, Higher Configuration, Percentage, Overlap, Accuracy, Energy Difference, Energy Welton\n")
            for state in calculated3holesStates:
                resultDump.write(shell_array_3holes[state[0][0]] + ", " + str(state[0][0]) + ", " + str(state[0][1]) + ", " + str(state[0][2]) + ", " + state[1][0] + ", " + str(state[1][1]) + ", " + str(state[1][2]) + ", " + str(state[1][3]) + ", " + str(state[1][4]) + ", " + str(state[1][5]) + "\n")
        
    
    
    # If no starting cycle has been defined or the starting cycle is 1, 2 or 3
    if starting_cycle <= 3:
        # Counter for the first state to be calculated in the state lists
        start_counter = 0
        
        # If the starting cycle is 3 we search for the starting state in the list and fill in the failed_second_cycle list
        if starting_cycle == 3:
            counter = 0
            for state in calculated3holesStates:
                i, jj, eigv = state[0]
                
                currDir = rootDir + "/" + directory_name + "/3holes/" + shell_array_3holes[i] + "/2jj_" + str(jj) + "/eigv_" + str(eigv)
                currFileName = shell_array_3holes[i] + "_" + str(jj) + "_" + str(eigv)
        
                converged, failed_orbital, overlap, higher_config, highest_percent, accuracy, Diff, welt = checkOutput(currDir, currFileName)
                
                calculated3holesStates[counter].append((higher_config, highest_percent, overlap, accuracy, Diff, welt))
                
                if not converged:
                    # Only add this state to the calculation if we reached the starting state
                    if found_cycle3 or starting_state == [(0, 0, 0)]:
                        parallel_3holes_failed.append(currDir + "/" + exe_file)
                    
                    failed_second_cycle.append(counter)
                else:
                    if Diff < 0.0 or Diff >= diffThreshold or overlap >= overlapsThreshold:
                        # Only add this state to the calculation if we reached the starting state
                        if found_cycle3 or starting_state == [(0, 0, 0)]:
                            parallel_3holes_failed.append(currDir + "/" + exe_file)
                        
                        failed_second_cycle.append(counter)
                
                counter += 1
                
                if state[0] == starting_state:
                    found_cycle3 = True
                    start_counter = counter
                
        
        if len(parallel_3holes_failed) == 0:
            writeResults3holes()
            return
        
        # Execute parallel batch job with logging of calculated state
        executeBatchStateCalculation(parallel_3holes_failed, file_cycle_log_3holes, calculated3holesStates, "Third Cycle Last Calculated:\n")
    
    
    failed_third_cycle = []
    parallel_3holes_failed = []
    
    # -------------- THIRD CYCLE FOR CONVERGENCE CHECK WITH FAILED ORBITALS -------------- #
    
    # If no starting cycle has been defined or the starting cycle is 1 or 2
    if starting_cycle <= 3:
        # Even if the starting cycle is 3 it means that the calculation has finished in the last executeBatchStateCalculation
        # After having filled the failed_second_cycle list we can continue the calculation
        for counter in failed_second_cycle:
            i, jj, eigv = calculated3holesStates[counter][0]
            
            currDir = rootDir + "/" + directory_name + "/3holes/" + shell_array_3holes[i] + "/2jj_" + str(jj) + "/eigv_" + str(eigv)
            currFileName = shell_array_3holes[i] + "_" + str(jj) + "_" + str(eigv)
            
            converged, failed_orbital, overlap, higher_config, highest_percent, accuracy, Diff, welt = checkOutput(currDir, currFileName)
            
            failed_orbs = calculated3holesStates[counter][1][6]
            
            if failed_orbital != '':
                failed_orbs.append("    " + failed_orbital + "  1 5 0 1 :")
            
            
            if not converged:
                if failed_orbs[0] != "  1 5 0 1 :" and len(failed_orbs) == 2:
                    configureStateInputFile(f05Template_10steps_Forbs_nuc, currDir, currFileName, configuration_3holes[i], jj, eigv, failed_orbs, int(nelectrons) - 2)
            
                    parallel_3holes_failed.append(currDir + "/" + exe_file)
                elif len(failed_orbs) == 2:
                    del failed_orbs[0]
                    
                    configureStateInputFile(f05Template_10steps_Forbs_nuc, currDir, currFileName, configuration_3holes[i], jj, eigv, failed_orbs, int(nelectrons) - 2)
            
                    parallel_3holes_failed.append(currDir + "/" + exe_file)
                
                failed_third_cycle.append(counter)
            else:
                if Diff < 0.0 or Diff >= diffThreshold or overlap >= overlapsThreshold:
                    if failed_orbs[0] != "  1 5 0 1 :" and len(failed_orbs) == 2:
                        configureStateInputFile(f05Template_10steps_Forbs_nuc, currDir, currFileName, configuration_3holes[i], jj, eigv, failed_orbs, int(nelectrons) - 2)
            
                        parallel_3holes_failed.append(currDir + "/" + exe_file)
                    elif len(failed_orbs) == 2:
                        del failed_orbs[0]
                        
                        configureStateInputFile(f05Template_10steps_Forbs_nuc, currDir, currFileName, configuration_3holes[i], jj, eigv, failed_orbs, int(nelectrons) - 2)
            
                        parallel_3holes_failed.append(currDir + "/" + exe_file)
                
                failed_third_cycle.append(counter)
            
            calculated3holesStates[counter][-1] = (higher_config, highest_percent, overlap, accuracy, Diff, welt, failed_orbs)
            
        
        # -------------- PRINT THIRD CYCLE RESULTS -------------- #
        
        with open(file_results, "a") as resultDump:
            resultDump.write("Third Cycle 3 Hole states\nShell, Shell index, 2J, Eigv, Higher Configuration, Percentage, Overlap, Accuracy, Energy Difference, Energy Welton\n")
            for state in calculated3holesStates:
                resultDump.write(shell_array_3holes[state[0][0]] + ", " + str(state[0][0]) + ", " + str(state[0][1]) + ", " + str(state[0][2]) + ", " + state[1][0] + ", " + str(state[1][1]) + ", " + str(state[1][2]) + ", " + str(state[1][3]) + ", " + str(state[1][4]) + ", " + str(state[1][5]) + "\n")
    
    
    # If no starting cycle has been defined or the starting cycle is 1, 2, 3 or 4
    # Counter for the first state to be calculated in the state lists
    start_counter = 0
    
    # If the starting cycle is 4 we search for the starting state in the list and fill in the failed_third_cycle list
    if starting_cycle == 4:
        counter = 0
        for state in calculated3holesStates:
            i, jj, eigv = state[0]
            
            currDir = rootDir + "/" + directory_name + "/3holes/" + shell_array_3holes[i] + "/2jj_" + str(jj) + "/eigv_" + str(eigv)
            currFileName = shell_array_3holes[i] + "_" + str(jj) + "_" + str(eigv)
            
            converged, failed_orbital, overlap, higher_config, highest_percent, accuracy, Diff, welt = checkOutput(currDir, currFileName)
            
            calculated3holesStates[counter].append((higher_config, highest_percent, overlap, accuracy, Diff, welt))
            
            if not converged:
                # Only add this state to the calculation if we reached the starting state
                if found_cycle4 or starting_state == [(0, 0, 0)]:
                    parallel_3holes_failed.append(currDir + "/" + exe_file)
                
                failed_third_cycle.append(counter)
            else:
                if Diff < 0.0 or Diff >= diffThreshold or overlap >= overlapsThreshold:
                    # Only add this state to the calculation if we reached the starting state
                    if found_cycle4 or starting_state == [(0, 0, 0)]:
                        parallel_3holes_failed.append(currDir + "/" + exe_file)
                    
                    failed_third_cycle.append(counter)
            
            counter += 1
            
            if state[0] == starting_state:
                found_cycle4 = True
                start_counter = counter
            
    
    if len(parallel_3holes_failed) == 0:
        writeResults3holes()
        return
    
    # Execute parallel batch job with logging of calculated state
    executeBatchStateCalculation(parallel_3holes_failed, file_cycle_log_3holes, calculated3holesStates, "Fourth Cycle Last Calculated:\n")
    
    
    sat_auger_by_hand = []
    
    # -------------- FOURTH CYCLE TO CHECK WHICH STATES NEED TO BE REDONE BY HAND -------------- #
    
    # If no starting cycle has been defined or the starting cycle is 1, 2, 3 or 4
    for counter in failed_third_cycle:
        i, jj, eigv = calculated3holesStates[counter][0]
        
        currDir = rootDir + "/" + directory_name + "/3holes/" + shell_array_3holes[i] + "/2jj_" + str(jj) + "/eigv_" + str(eigv)
        currFileName = shell_array_3holes[i] + "_" + str(jj) + "_" + str(eigv)
        
        converged, failed_orbital, overlap, higher_config, highest_percent, accuracy, Diff, welt = checkOutput(currDir, currFileName)
        
        calculated3holesStates[counter][-1] = (higher_config, highest_percent, overlap, accuracy, Diff, welt)
        
        if not converged:
            sat_auger_by_hand.append(counter)
        else:
            if Diff < 0.0 or Diff >= diffThreshold or overlap > overlapsThreshold:
                sat_auger_by_hand.append(counter)
    
    
    # -------------- WRITE RESULTS TO THE FILES -------------- #
    
    writeResults3holes()


def calculateShakeupStates(starting_cycle = -1, starting_state = [(0, 0, 0)]):
    global calculatedShakeupStates, shakeup_by_hand
    
    jj_vals = []
    
    parallel_shakeup_paths = []
    
    # If no starting cycle has been specified
    if starting_cycle == -1:
        # -------------- DETERMINE 2J MAX VALUE -------------- #
        
        for i in range(len(shell_array_shakeup)):
            currDir = rootDir + "/" + directory_name + "/shakeup/" + shell_array_shakeup[i]
            currFileName = shell_array_shakeup[i]
            
            configureStateInputFile(f05Template_nuc, currDir, currFileName, configuration_shakeup[i], "100" if int(nelectrons) % 2 == 0 else "101", "100", [], int(nelectrons))
            
            parallel_shakeup_paths.append(currDir + "/" + exe_file)
            
        
        # Execute parallel batch job
        executeBatchStateCalculation(parallel_shakeup_paths)
        
        
        parallel_shakeup_paths = []
        
        # -------------- DETERMINE EIGENVALUE MAX VALUE -------------- #
        
        for i in range(len(shell_array_shakeup)):
            currDir = rootDir + "/" + directory_name + "/shakeup/" + shell_array_shakeup[i]
            currFileName = shell_array_shakeup[i]
            
            maxJJi = 0
            
            with open(currDir + "/" + currFileName + ".f06", "r") as labelOutput:
                for line in labelOutput.readlines():
                    if "!!!!! For state # 1 and configuration   1 highest 2Jz possible value is" in line:
                        maxJJi = int(line.split("!!!!! For state # 1 and configuration   1 highest 2Jz possible value is")[1].split()[0].strip())
            
            for jj in range(0 if maxJJi % 2 == 0 else 1, maxJJi + 1, 2):
                jj_vals.append((i, jj))
                
                currDir = rootDir + "/" + directory_name + "/shakeup/" + shell_array_shakeup[i] + "/2jj_" + str(jj)
                currFileName = shell_array_shakeup[i] + "_" + str(jj)
                
                configureStateInputFile(f05Template_nuc, currDir, currFileName, configuration_shakeup[i], jj, "100", [], int(nelectrons))
            
                parallel_shakeup_paths.append(currDir + "/" + exe_file)
        
        # Execute parallel batch job
        executeBatchStateCalculation(parallel_shakeup_paths)
        
        
        parallel_shakeup_paths = []
        
        # -------------- FULL STATE CALCULATION -------------- #
        
        for i, jj in jj_vals:
            currDir = rootDir + "/" + directory_name + "/shakeup/" + shell_array_shakeup[i] + "/2jj_" + str(jj)
            currFileName = shell_array_shakeup[i] + "_" + str(jj)
            
            maxEigvi = 0
            
            with open(currDir + "/" + currFileName + ".f06", "r") as jjiOutput:
                for line in jjiOutput.readlines():
                    if "The reference LS state for this calculation results in" in line:
                        maxEigvi = int(line.split("The reference LS state for this calculation results in")[1].strip().split()[0].strip())
            
            for eigv in range(1, maxEigvi + 1):
                
                calculatedShakeupStates.append([(i, jj, eigv)])
                
                currDir = rootDir + "/" + directory_name + "/shakeup/" + shell_array_shakeup[i] + "/2jj_" + str(jj) + "/eigv_" + str(eigv)
                currFileName = shell_array_shakeup[i] + "_" + str(jj) + "_" + str(eigv)
                
                configureStateInputFile(f05Template_nuc, currDir, currFileName, configuration_shakeup[i], jj, eigv, [], int(nelectrons))
                
                parallel_shakeup_paths.append(currDir + "/" + exe_file)
        
        
        with open(file_cycle_log_shakeup, "a") as log_shakeup:
            log_shakeup.write("Shake-up states discovery done.\nList of all discovered states:\n")
            for state in calculatedShakeupStates:
                log_shakeup.write(', '.join([str(qn) for qn in state[0]]) + "\n")
            
            log_shakeup.write("ListEnd\n")
    
    
    
    # Variables to control if the last calculated state has been reached in each cycle
    found_cycle1 = False
    found_cycle2 = False
    found_cycle3 = False
    found_cycle4 = False
    
    # If no starting cycle has been defined or the starting cycle is 1
    if starting_cycle <= 1:
        # Counter for the first state to be calculated in the state lists
        start_counter = 0
        
        # If the starting cycle is 1 we search for the starting state in the list
        if starting_cycle == 1:
            counter = 0
            for state in calculatedShakeupStates:
                if found_cycle1 or starting_state == [(0, 0, 0)]:
                    i, jj, eigv = state[0]
                    
                    currDir = rootDir + "/" + directory_name + "/shakeup/" + shell_array_shakeup[i] + "/2jj_" + str(jj) + "/eigv_" + str(eigv)
                    currFileName = shell_array_shakeup[i] + "_" + str(jj) + "_" + str(eigv)
        
                    parallel_shakeup_paths.append(currDir + "/" + exe_file)
                
                counter += 1
                
                # Search for the starting state
                if state[0] == starting_state:
                    found_cycle1 = True
                    start_counter = counter
                
        
        # Execute parallel batch job with logging of calculated state
        executeBatchStateCalculation(parallel_shakeup_paths, file_cycle_log_shakeup, calculatedShakeupStates[start_counter:], "First Cycle Last Calculated:\n")
    
    
    failed_first_cycle = []
    parallel_shakeup_failed = []
    
    # -------------- FIRST CYCLE FOR CONVERGENCE CHECK -------------- #
    
    # If no starting cycle has been defined or the starting cycle is 1
    if starting_cycle <= 1:
        # Even if the starting cycle is 1 it means that the calculation has finished in the last executeBatchStateCalculation
        counter = 0
        for state in calculatedShakeupStates:
            i, jj, eigv = state[0]
            
            currDir = rootDir + "/" + directory_name + "/shakeup/" + shell_array_shakeup[i] + "/2jj_" + str(jj) + "/eigv_" + str(eigv)
            currFileName = shell_array_shakeup[i] + "_" + str(jj) + "_" + str(eigv)
            
            converged, failed_orbital, overlap, higher_config, highest_percent, accuracy, Diff, welt = checkOutput(currDir, currFileName)
            
            calculatedShakeupStates[counter].append((higher_config, highest_percent, overlap, accuracy, Diff, welt))
            
            if not converged:
                
                configureStateInputFile(f05Template_10steps_nuc, currDir, currFileName, configuration_shakeup[i], jj, eigv, [], int(nelectrons))
            
                parallel_shakeup_failed.append(currDir + "/" + exe_file)
                failed_first_cycle.append(counter)
            else:
                if Diff < 0.0 or Diff >= diffThreshold or overlap >= overlapsThreshold:
                    configureStateInputFile(f05Template_10steps_nuc, currDir, currFileName, configuration_shakeup[i], jj, eigv, [], int(nelectrons))
            
                    parallel_shakeup_failed.append(currDir + "/" + exe_file)
                    failed_first_cycle.append(counter)
            
            counter += 1
        
        # -------------- PRINT FIRST CYCLE RESULTS -------------- #
        
        with open(file_results, "a") as resultDump:
            resultDump.write("First Cycle Shake-up states\nShell, Shell index, 2J, Eigv, Higher Configuration, Percentage, Overlap, Accuracy, Energy Difference, Energy Welton\n")
            for state in calculatedShakeupStates:
                resultDump.write(shell_array_shakeup[state[0][0]] + ", " + str(state[0][0]) + ", " + str(state[0][1]) + ", " + str(state[0][2]) + ", " + state[1][0] + ", " + str(state[1][1]) + ", " + str(state[1][2]) + ", " + str(state[1][3]) + ", " + str(state[1][4]) + ", " + str(state[1][5]) + "\n")
        
    
    
    # If no starting cycle has been defined or the starting cycle is 1 or 2
    if starting_cycle <= 2:
        # Counter for the first state to be calculated in the state lists
        start_counter = 0
        
        # If the starting cycle is 2 we search for the starting state in the list and fill in the failed_first_cycle list
        if starting_cycle == 2:
            counter = 0
            for state in calculatedShakeupStates:
                if found_cycle2 or starting_state == [(0, 0, 0)]:
                    i, jj, eigv = state[0]
                    
                    currDir = rootDir + "/" + directory_name + "/shakeup/" + shell_array_shakeup[i] + "/2jj_" + str(jj) + "/eigv_" + str(eigv)
                    currFileName = shell_array_shakeup[i] + "_" + str(jj) + "_" + str(eigv)
                    
                    converged, failed_orbital, overlap, higher_config, highest_percent, accuracy, Diff, welt = checkOutput(currDir, currFileName)
                    
                    calculatedShakeupStates[counter].append((higher_config, highest_percent, overlap, accuracy, Diff, welt))
                    
                    if not converged:
                        # Only add this state to the calculation if we reached the starting state
                        if found_cycle2 or starting_state == [(0, 0, 0)]:
                            parallel_shakeup_failed.append(currDir + "/" + exe_file)
                        
                        failed_first_cycle.append(counter)
                    else:
                        if Diff < 0.0 or Diff >= diffThreshold or overlap >= overlapsThreshold:
                            # Only add this state to the calculation if we reached the starting state
                            if found_cycle2 or starting_state == [(0, 0, 0)]:
                                parallel_shakeup_failed.append(currDir + "/" + exe_file)
                            
                            failed_first_cycle.append(counter)
                
                counter += 1
                
                # Search for the starting state
                if state[0] == starting_state:
                    found_cycle2 = True
                    start_counter = counter
                
        
        if len(parallel_shakeup_failed) == 0:
            writeResultsShakeup()
            return
        
        # Execute parallel batch job with logging of calculated state
        executeBatchStateCalculation(parallel_shakeup_failed, file_cycle_log_shakeup, calculatedShakeupStates[start_counter:], "Second Cycle Last Calculated:\n")
    
    
    failed_second_cycle = []
    parallel_shakeup_failed = []
    
    
    # -------------- SECOND CYCLE FOR CONVERGENCE CHECK WITH FAILED ORBITALS -------------- #
    
    # If no starting cycle has been defined or the starting cycle is 1 or 2
    if starting_cycle <= 2:
        # Even if the starting cycle is 2 it means that the calculation has finished in the last executeBatchStateCalculation
        # After having filled the failed_first_cycle list we can continue the calculation
        for counter in failed_first_cycle:
            i, jj, eigv = calculatedShakeupStates[counter][0]
            
            currDir = rootDir + "/" + directory_name + "/shakeup/" + shell_array_shakeup[i] + "/2jj_" + str(jj) + "/eigv_" + str(eigv)
            currFileName = shell_array_shakeup[i] + "_" + str(jj) + "_" + str(eigv)
            
            converged, failed_orbital, overlap, higher_config, highest_percent, accuracy, Diff, welt = checkOutput(currDir, currFileName)
            
            failed_orbs = [failed_orbital.strip() + "  1 5 0 1 :"]
            
            
            calculatedShakeupStates[counter][-1] = (higher_config, highest_percent, overlap, accuracy, Diff, welt, failed_orbs)
            
            if not converged:
                if failed_orbital != '':
                    configureStateInputFile(f05Template_10steps_Forbs_nuc, currDir, currFileName, configuration_shakeup[i], jj, eigv, failed_orbs, int(nelectrons))
                
                    parallel_shakeup_failed.append(currDir + "/" + exe_file)
                
                failed_second_cycle.append(counter)
            else:
                if Diff < 0.0 or Diff >= diffThreshold or overlap >= overlapsThreshold:
                    if failed_orbital != '':
                        configureStateInputFile(f05Template_10steps_Forbs_nuc, currDir, currFileName, configuration_shakeup[i], jj, eigv, failed_orbs, int(nelectrons))
            
                        parallel_shakeup_failed.append(currDir + "/" + exe_file)
                    
                    failed_second_cycle.append(counter)
            
        
        # -------------- PRINT SECOND CYCLE RESULTS -------------- #
        
        with open(file_results, "a") as resultDump:
            resultDump.write("Second Cycle Shake-up states\nShell, Shell index, 2J, Eigv, Higher Configuration, Percentage, Overlap, Accuracy, Energy Difference, Energy Welton\n")
            for state in calculatedShakeupStates:
                resultDump.write(shell_array_shakeup[state[0][0]] + ", " + str(state[0][0]) + ", " + str(state[0][1]) + ", " + str(state[0][2]) + ", " + state[1][0] + ", " + str(state[1][1]) + ", " + str(state[1][2]) + ", " + str(state[1][3]) + ", " + str(state[1][4]) + ", " + str(state[1][5]) + "\n")
        
    
    
    # If no starting cycle has been defined or the starting cycle is 1, 2 or 3
    if starting_cycle <= 3:
        # Counter for the first state to be calculated in the state lists
        start_counter = 0
        
        # If the starting cycle is 3 we search for the starting state in the list and fill in the failed_second_cycle list
        if starting_cycle == 3:
            counter = 0
            for state in calculatedShakeupStates:
                i, jj, eigv = state[0]
                
                currDir = rootDir + "/" + directory_name + "/shakeup/" + shell_array_shakeup[i] + "/2jj_" + str(jj) + "/eigv_" + str(eigv)
                currFileName = shell_array_shakeup[i] + "_" + str(jj) + "_" + str(eigv)
        
                converged, failed_orbital, overlap, higher_config, highest_percent, accuracy, Diff, welt = checkOutput(currDir, currFileName)
                
                calculatedShakeupStates[counter].append((higher_config, highest_percent, overlap, accuracy, Diff, welt))
                
                if not converged:
                    # Only add this state to the calculation if we reached the starting state
                    if found_cycle3 or starting_state == [(0, 0, 0)]:
                        parallel_shakeup_failed.append(currDir + "/" + exe_file)
                    
                    failed_second_cycle.append(counter)
                else:
                    if Diff < 0.0 or Diff >= diffThreshold or overlap >= overlapsThreshold:
                        # Only add this state to the calculation if we reached the starting state
                        if found_cycle3 or starting_state == [(0, 0, 0)]:
                            parallel_shakeup_failed.append(currDir + "/" + exe_file)
                        
                        failed_second_cycle.append(counter)
                
                counter += 1
                
                if state[0] == starting_state:
                    found_cycle3 = True
                    start_counter = counter
                
        
        if len(parallel_shakeup_failed) == 0:
            writeResultsShakeup()
            return
        
        # Execute parallel batch job with logging of calculated state
        executeBatchStateCalculation(parallel_shakeup_failed, file_cycle_log_shakeup, calculatedShakeupStates, "Third Cycle Last Calculated:\n")
    
    
    failed_third_cycle = []
    parallel_shakeup_failed = []
    
    # -------------- THIRD CYCLE FOR CONVERGENCE CHECK WITH FAILED ORBITALS -------------- #
    
    # If no starting cycle has been defined or the starting cycle is 1 or 2
    if starting_cycle <= 3:
        # Even if the starting cycle is 3 it means that the calculation has finished in the last executeBatchStateCalculation
        # After having filled the failed_second_cycle list we can continue the calculation
        for counter in failed_second_cycle:
            i, jj, eigv = calculatedShakeupStates[counter][0]
            
            currDir = rootDir + "/" + directory_name + "/shakeup/" + shell_array_shakeup[i] + "/2jj_" + str(jj) + "/eigv_" + str(eigv)
            currFileName = shell_array_shakeup[i] + "_" + str(jj) + "_" + str(eigv)
            
            converged, failed_orbital, overlap, higher_config, highest_percent, accuracy, Diff, welt = checkOutput(currDir, currFileName)
            
            failed_orbs = calculatedShakeupStates[counter][1][6]
            
            if failed_orbital != '':
                failed_orbs.append("    " + failed_orbital + "  1 5 0 1 :")
            
            
            if not converged:
                if failed_orbs[0] != "  1 5 0 1 :" and len(failed_orbs) == 2:
                    configureStateInputFile(f05Template_10steps_Forbs_nuc, currDir, currFileName, configuration_shakeup[i], jj, eigv, failed_orbs, int(nelectrons))
            
                    parallel_shakeup_failed.append(currDir + "/" + exe_file)
                elif len(failed_orbs) == 2:
                    del failed_orbs[0]
                    
                    configureStateInputFile(f05Template_10steps_Forbs_nuc, currDir, currFileName, configuration_shakeup[i], jj, eigv, failed_orbs, int(nelectrons))
            
                    parallel_shakeup_failed.append(currDir + "/" + exe_file)
                
                failed_third_cycle.append(counter)
            else:
                if Diff < 0.0 or Diff >= diffThreshold or overlap >= overlapsThreshold:
                    if failed_orbs[0] != "  1 5 0 1 :" and len(failed_orbs) == 2:
                        configureStateInputFile(f05Template_10steps_Forbs_nuc, currDir, currFileName, configuration_shakeup[i], jj, eigv, failed_orbs, int(nelectrons))
            
                        parallel_shakeup_failed.append(currDir + "/" + exe_file)
                    elif len(failed_orbs) == 2:
                        del failed_orbs[0]
                        
                        configureStateInputFile(f05Template_10steps_Forbs_nuc, currDir, currFileName, configuration_shakeup[i], jj, eigv, failed_orbs, int(nelectrons))
            
                        parallel_shakeup_failed.append(currDir + "/" + exe_file)
                
                failed_third_cycle.append(counter)
            
            calculatedShakeupStates[counter][-1] = (higher_config, highest_percent, overlap, accuracy, Diff, welt, failed_orbs)
            
        
        # -------------- PRINT THIRD CYCLE RESULTS -------------- #
        
        with open(file_results, "a") as resultDump:
            resultDump.write("Third Cycle Shake-up states\nShell, Shell index, 2J, Eigv, Higher Configuration, Percentage, Overlap, Accuracy, Energy Difference, Energy Welton\n")
            for state in calculatedShakeupStates:
                resultDump.write(shell_array_shakeup[state[0][0]] + ", " + str(state[0][0]) + ", " + str(state[0][1]) + ", " + str(state[0][2]) + ", " + state[1][0] + ", " + str(state[1][1]) + ", " + str(state[1][2]) + ", " + str(state[1][3]) + ", " + str(state[1][4]) + ", " + str(state[1][5]) + "\n")
    
    
    # If no starting cycle has been defined or the starting cycle is 1, 2, 3 or 4
    # Counter for the first state to be calculated in the state lists
    start_counter = 0
    
    # If the starting cycle is 4 we search for the starting state in the list and fill in the failed_third_cycle list
    if starting_cycle == 4:
        counter = 0
        for state in calculatedShakeupStates:
            i, jj, eigv = state[0]
            
            currDir = rootDir + "/" + directory_name + "/shakeup/" + shell_array_shakeup[i] + "/2jj_" + str(jj) + "/eigv_" + str(eigv)
            currFileName = shell_array_shakeup[i] + "_" + str(jj) + "_" + str(eigv)
            
            converged, failed_orbital, overlap, higher_config, highest_percent, accuracy, Diff, welt = checkOutput(currDir, currFileName)
            
            calculatedShakeupStates[counter].append((higher_config, highest_percent, overlap, accuracy, Diff, welt))
            
            if not converged:
                # Only add this state to the calculation if we reached the starting state
                if found_cycle4 or starting_state == [(0, 0, 0)]:
                    parallel_shakeup_failed.append(currDir + "/" + exe_file)
                
                failed_third_cycle.append(counter)
            else:
                if Diff < 0.0 or Diff >= diffThreshold or overlap >= overlapsThreshold:
                    # Only add this state to the calculation if we reached the starting state
                    if found_cycle4 or starting_state == [(0, 0, 0)]:
                        parallel_shakeup_failed.append(currDir + "/" + exe_file)
                    
                    failed_third_cycle.append(counter)
            
            counter += 1
            
            if state[0] == starting_state:
                found_cycle4 = True
                start_counter = counter
            
    
    if len(parallel_shakeup_failed) == 0:
        writeResultsShakeup()
        return
    
    # Execute parallel batch job with logging of calculated state
    executeBatchStateCalculation(parallel_shakeup_failed, file_cycle_log_shakeup, calculatedShakeupStates, "Fourth Cycle Last Calculated:\n")
    
    
    shakeup_by_hand = []
    
    # -------------- FOURTH CYCLE TO CHECK WHICH STATES NEED TO BE REDONE BY HAND -------------- #
    
    # If no starting cycle has been defined or the starting cycle is 1, 2, 3 or 4
    for counter in failed_third_cycle:
        i, jj, eigv = calculatedShakeupStates[counter][0]
        
        currDir = rootDir + "/" + directory_name + "/shakeup/" + shell_array_shakeup[i] + "/2jj_" + str(jj) + "/eigv_" + str(eigv)
        currFileName = shell_array_shakeup[i] + "_" + str(jj) + "_" + str(eigv)
        
        converged, failed_orbital, overlap, higher_config, highest_percent, accuracy, Diff, welt = checkOutput(currDir, currFileName)
        
        calculatedShakeupStates[counter][-1] = (higher_config, highest_percent, overlap, accuracy, Diff, welt)
        
        if not converged:
            shakeup_by_hand.append(counter)
        else:
            if Diff < 0.0 or Diff >= diffThreshold or overlap > overlapsThreshold:
                shakeup_by_hand.append(counter)
    
    
    # -------------- WRITE RESULTS TO THE FILES -------------- #
    
    writeResultsShakeup()



def sortCalculatedStates():
    global calculated1holeStates, calculated2holesStates, calculate3holesStates, calculateShakeupStates
    
    calculated1holeStates.sort(key = lambda x: x[1][-1])
    
    with open(file_sorted_1hole, "w") as sorted_1hole:
        for state in calculated1holeStates:
            sorted_1hole.write(', '.join([str(qn) for qn in state[0]]) + "; " + ', '.join([str(par) for par in state[1]]) + "\n")
    
    
    calculated2holesStates.sort(key = lambda x: x[1][-1])
    
    with open(file_sorted_2holes, "w") as sorted_2holes:
        for state in calculated2holesStates:
            sorted_2holes.write(', '.join([str(qn) for qn in state[0]]) + "; " + ', '.join([str(par) for par in state[1]]) + "\n")
    
    
    if calculate_3holes:
        calculated3holesStates.sort(key = lambda x: x[1][-1])
        
        with open(file_sorted_3holes, "w") as sorted_3holes:
            for state in calculated3holesStates:
                sorted_3holes.write(', '.join([str(qn) for qn in state[0]]) + "; " + ', '.join([str(par) for par in state[1]]) + "\n")
    
    
    if calculate_shakeup:
        calculatedShakeupStates.sort(key = lambda x: x[1][-1])
        
        with open(file_sorted_shakeup, "w") as sorted_shakeup:
            for state in calculatedShakeupStates:
                sorted_shakeup.write(', '.join([str(qn) for qn in state[0]]) + "; " + ', '.join([str(par) for par in state[1]]) + "\n")
    



def readTransition(currDir, currFileName, radiative = True):
    energy = '0.0'
    rate = '0.0'
    
    multipoles = []
    
    with open(currDir + "/" + currFileName + ".f06", "r") as output:
        outputContent = output.readlines()
        
        if radiative:
            for i, line in enumerate(outputContent):
                if "Transition energy" in line:
                    energy = line.strip().split()[-2].strip()
                elif "total transition rate is:" in line:
                    rate = line.strip().split()[-2].strip()
                elif "Summary of transition rates" in line:
                    cnt = i + 3
                    while True:
                        if outputContent[cnt] == "\n":
                            break
                        elif "s-1" in outputContent[cnt]:
                            vals = outputContent[cnt].strip().split()
                            multipoles.append([vals[0], vals[1]])
                        
                        cnt += 1
            
            return energy, rate, multipoles
        else:
            for i, line in enumerate(outputContent):
                if "For Auger transition of energy" in line and "Total rate is" in line:
                    energy = line.replace("For Auger transition of energy", "").strip().split()[0]
                    rate = outputContent[i + 1].strip().split()[0]
                
            
            return energy, rate
    



def rates(starting_transition = [(0, 0, 0), (0, 0, 0)]):
    global calculatedRadiativeTransitions
    
    
    calculatedRadiativeTransitions = []
    
    parallel_initial_src_paths = []
    parallel_initial_dst_paths = []
    parallel_final_src_paths = []
    parallel_final_dst_paths = []
    
    parallel_transition_paths = []


    found_starting = False

    combCnt = 0
    for counter, state_f in enumerate(calculated1holeStates):
        for state_i in calculated1holeStates[(counter + 1):]:
            i, jj_i, eigv_i = state_i[0]
            f, jj_f, eigv_f = state_f[0]
            
            calculatedRadiativeTransitions.append([(i, jj_i, eigv_i), (f, jj_f, eigv_f)])
            
            if starting_transition == [(0, 0, 0), (0, 0, 0)] or found_starting:
                currDir = rootDir + "/" + directory_name + "/transitions/radiative/" + str(combCnt)
                currFileName = str(combCnt)
                
                currDir_i = rootDir + "/" + directory_name + "/radiative/" + shell_array[i] + "/2jj_" + str(jj_i) + "/eigv_" + str(eigv_i)
                currFileName_i = shell_array[i] + "_" + str(jj_i) + "_" + str(eigv_i)
                
                currDir_f = rootDir + "/" + directory_name + "/radiative/" + shell_array[f] + "/2jj_" + str(jj_f) + "/eigv_" + str(eigv_f)
                currFileName_f = shell_array[f] + "_" + str(jj_f) + "_" + str(eigv_f)
                
                wfiFile, wffFile = configureTransitionInputFile(f05RadTemplate_nuc, \
                                                                currDir, currFileName, \
                                                                currDir_i, currFileName_i, \
                                                                configuration_1hole[i], jj_i, eigv_i, nelectrons, \
                                                                currDir_f, currFileName_f, \
                                                                configuration_1hole[f], jj_f, eigv_f, nelectrons)
                
                parallel_initial_src_paths.append(currDir_i + "/" + currFileName_i + ".f09")
                parallel_final_src_paths.append(currDir_f + "/" + currFileName_f + ".f09")
                
                parallel_initial_dst_paths.append(currDir + "/" + wfiFile + ".f09")
                parallel_final_dst_paths.append(currDir + "/" + wffFile + ".f09")
                
                parallel_transition_paths.append(currDir + "/" + exe_file)
            
            combCnt += 1
            
            if [state_i[0], state_f[0]] == starting_transition:
                found_starting = True
    
    if len(parallel_transition_paths) > 0:
        executeBatchTransitionCalculation(parallel_transition_paths, \
                                        parallel_initial_src_paths, parallel_final_src_paths, \
                                        parallel_initial_dst_paths, parallel_final_dst_paths, \
                                        file_calculated_radiative, calculatedRadiativeTransitions, "Calculated transitions:\n")
    
    
    energies = []
    rates = []
    multipole_array = []
    
    total_rates = dict.fromkeys([state[0] for state in calculated1holeStates], 0.0)
    
    combCnt = 0
    for counter, state_f in enumerate(calculated1holeStates):
        for state_i in calculated1holeStates[(counter + 1):]:
            i, jj_i, eigv_i = state_i[0]
            f, jj_f, eigv_f = state_f[0]
            
            currDir = rootDir + "/" + directory_name + "/transitions/radiative/" + str(combCnt)
            currFileName = str(combCnt)
            
            energy, rate, multipoles = readTransition(currDir, currFileName)
            
            total_rates[state_i[0]] += float(rate)
            
            energies.append(energy)
            rates.append(rate)
            multipole_array.append(multipoles)
            
            combCnt += 1
    
    
    # -------------- WRITE RESULTS TO THE FILES -------------- #
    
    with open(file_rates, "w") as rad_rates:
        rad_rates.write("Calculated Radiative Transitions\nTransition register\tShell IS\tIS Configuration\tIS 2JJ\tIS eigenvalue\tIS higher configuration\tIS percentage\tShell FS\tFS Configuration\tFS 2JJ\tFS eigenvalue\tFS higher configuration\tFS percentage\ttransition energy [eV]\trate [s-1]\tnumber multipoles\ttotal rate from IS\tbranching ratio\n")
        combCnt = 0
        for counter, state_f in enumerate(calculated1holeStates):
            for state_i in calculated1holeStates[(counter + 1):]:
                i, jj_i, eigv_i = state_i[0]
                f, jj_f, eigv_f = state_f[0]
                
                calculatedRadiativeTransitions[combCnt].append((energies[combCnt], rates[combCnt], total_rates[state_i[0]], multipole_array[combCnt]))
                
                rad_rates.write(str(combCnt) + "\t" + \
                                shell_array[i] + "\t" + \
                                configuration_1hole[i] + "\t" + \
                                str(jj_i) + "\t" + \
                                str(eigv_i) + "\t" + \
                                str(state_i[1][0]) + "\t" + \
                                str(state_i[1][1]) + "\t" + \
                                shell_array[f] + "\t" + \
                                configuration_1hole[f] + "\t" + \
                                str(jj_f) + "\t" + \
                                str(eigv_f) + "\t" + \
                                str(state_f[1][0]) + "\t" + \
                                str(state_f[1][1]) + "\t" + \
                                str(energies[combCnt]) + "\t" + \
                                str(rates[combCnt]) + "\t" + \
                                str(len(multipole_array[combCnt])) + "\t" + \
                                str(total_rates[state_i[0]]) + "\t" + \
                                (str(float(rate) / total_rates[state_i[0]]) if total_rates[state_i[0]] != 0.0 else "0.0") + "\t" + \
                                '\t'.join(['\t'.join(pole) for pole in multipole_array[combCnt]]) + "\n")
                
                combCnt += 1
    
    


def rates_auger(starting_transition = [(0, 0, 0), (0, 0, 0)]):
    global calculatedAugerTransitions
    
    
    calculatedAugerTransitions = []
    
    parallel_initial_src_paths = []
    parallel_initial_dst_paths = []
    parallel_final_src_paths = []
    parallel_final_dst_paths = []
    
    parallel_transition_paths = []


    found_starting = False

    combCnt = 0
    for state_i in calculated1holeStates:
        welt_i = state_i[1][-1]
        
        for state_f in calculated2holesStates:
            energy_diff = welt_i - state_f[1][-1]
            
            if energy_diff <= 0:
                break
            
            i, jj_i, eigv_i = state_i[0]
            f, jj_f, eigv_f = state_f[0]
            
            calculatedAugerTransitions.append([(i, jj_i, eigv_i), (f, jj_f, eigv_f)])
            
            if starting_transition == [(0, 0, 0), (0, 0, 0)] or found_starting:
                currDir = rootDir + "/" + directory_name + "/transitions/auger/" + str(combCnt)
                currFileName = str(combCnt)
                
                currDir_i = rootDir + "/" + directory_name + "/radiative/" + shell_array[i] + "/2jj_" + str(jj_i) + "/eigv_" + str(eigv_i)
                currFileName_i = shell_array[i] + "_" + str(jj_i) + "_" + str(eigv_i)
                
                currDir_f = rootDir + "/" + directory_name + "/auger/" + shell_array_2holes[f] + "/2jj_" + str(jj_f) + "/eigv_" + str(eigv_f)
                currFileName_f = shell_array_2holes[f] + "_" + str(jj_f) + "_" + str(eigv_f)
                
                wfiFile, wffFile = configureTransitionInputFile(f05AugTemplate_nuc, \
                                                                currDir, currFileName, \
                                                                currDir_i, currFileName_i, \
                                                                configuration_1hole[i], jj_i, eigv_i, nelectrons, \
                                                                currDir_f, currFileName_f, \
                                                                configuration_2holes[f], jj_f, eigv_f, str(int(nelectrons) - 1), \
                                                                energy_diff)
                
                parallel_initial_src_paths.append(currDir_i + "/" + currFileName_i + ".f09")
                parallel_final_src_paths.append(currDir_f + "/" + currFileName_f + ".f09")
                
                parallel_initial_dst_paths.append(currDir + "/" + wfiFile + ".f09")
                parallel_final_dst_paths.append(currDir + "/" + wffFile + ".f09")
                
                parallel_transition_paths.append(currDir + "/" + exe_file)
            
            combCnt += 1
            
            if [state_i[0], state_f[0]] == starting_transition:
                found_starting = True
    
    if len(parallel_transition_paths) > 0:
        executeBatchTransitionCalculation(parallel_transition_paths, \
                                        parallel_initial_src_paths, parallel_final_src_paths, \
                                        parallel_initial_dst_paths, parallel_final_dst_paths, \
                                        file_calculated_auger, calculatedAugerTransitions, "Calculated transitions:\n")
    
    
    energies = []
    rates = []
    
    total_rates = []
    
    combCnt = 0
    for counter, state_i in enumerate(calculated1holeStates):
        welt_i = state_i[1][-1]
        
        total_rates.append(0.0)
        
        for state_f in calculated2holesStates:
            energy_diff = welt_i - state_f[1][-1]
            
            if energy_diff <= 0:
                break
            
            i, jj_i, eigv_i = state_i[0]
            f, jj_f, eigv_f = state_f[0]
            
            currDir = rootDir + "/" + directory_name + "/transitions/auger/" + str(combCnt)
            currFileName = str(combCnt)
            
            energy, rate = readTransition(currDir, currFileName, False)
            
            total_rates[counter] += float(rate)
            
            energies.append(energy)
            rates.append(rate)
            
            combCnt += 1
    
    
    # -------------- WRITE RESULTS TO THE FILES -------------- #
    
    with open(file_rates_auger, "w") as aug_rates:
        aug_rates.write("Calculated Auger Transitions\nTransition register\tShell IS\tIS Configuration\tIS 2JJ\tIS eigenvalue\tIS higher configuration\tIS percentage\tShell FS\tFS Configuration\tFS 2JJ\tFS eigenvalue\tFS higher configuration\tFS percentage\ttransition energy [eV]\trate [s-1]\ttotal rate from IS\tbranching ratio\n")
        combCnt = 0
        for counter, state_i in enumerate(calculated1holeStates):
            welt_i = state_i[1][-1]
            for state_f in calculated2holesStates:
                energy_diff = welt_i - state_f[1][-1]
            
                if energy_diff <= 0:
                    break
                
                i, jj_i, eigv_i = state_i[0]
                f, jj_f, eigv_f = state_f[0]
                
                calculatedAugerTransitions[combCnt].append((energies[combCnt], rates[combCnt], total_rates[counter]))
                
                
                aug_rates.write(str(combCnt) + "\t" + \
                                shell_array[i] + "\t" + \
                                configuration_1hole[i] + "\t" + \
                                str(jj_i) + "\t" + \
                                str(eigv_i) + "\t" + \
                                str(state_i[1][0]) + "\t" + \
                                str(state_i[1][1]) + "\t" + \
                                shell_array_2holes[f] + "\t" + \
                                configuration_2holes[f] + "\t" + \
                                str(jj_f) + "\t" + \
                                str(eigv_f) + "\t" + \
                                str(state_f[1][0]) + "\t" + \
                                str(state_f[1][1]) + "\t" + \
                                str(energies[combCnt]) + "\t" + \
                                str(rates[combCnt]) + "\t" + \
                                str(total_rates[counter]) + "\t" + \
                                (str(float(rate) / total_rates[counter]) if total_rates[counter] != 0.0 else "0.0") + "\n")
                
                combCnt += 1
    
    


def rates_satellite(starting_transition = [(0, 0, 0), (0, 0, 0)]):
    global calculatedSatelliteTransitions
    
    calculatedSatelliteTransitions = []
    
    parallel_initial_src_paths = []
    parallel_initial_dst_paths = []
    parallel_final_src_paths = []
    parallel_final_dst_paths = []
    
    parallel_transition_paths = []


    found_starting = False

    combCnt = 0
    for counter, state_f in enumerate(calculated2holesStates):
        for state_i in calculated2holesStates[(counter + 1):]:
            i, jj_i, eigv_i = state_i[0]
            f, jj_f, eigv_f = state_f[0]
            
            calculatedSatelliteTransitions.append([(i, jj_i, eigv_i), (f, jj_f, eigv_f)])
            
            if starting_transition == [(0, 0, 0), (0, 0, 0)] or found_starting:
                currDir = rootDir + "/" + directory_name + "/transitions/satellites/" + str(combCnt)
                currFileName = str(combCnt)
                
                currDir_i = rootDir + "/" + directory_name + "/auger/" + shell_array_2holes[i] + "/2jj_" + str(jj_i) + "/eigv_" + str(eigv_i)
                currFileName_i = shell_array_2holes[i] + "_" + str(jj_i) + "_" + str(eigv_i)
                
                currDir_f = rootDir + "/" + directory_name + "/auger/" + shell_array_2holes[f] + "/2jj_" + str(jj_f) + "/eigv_" + str(eigv_f)
                currFileName_f = shell_array_2holes[f] + "_" + str(jj_f) + "_" + str(eigv_f)
                
                wfiFile, wffFile = configureTransitionInputFile(f05RadTemplate_nuc, \
                                                                currDir, currFileName, \
                                                                currDir_i, currFileName_i, \
                                                                configuration_2holes[i], jj_i, eigv_i, str(int(nelectrons) - 1), \
                                                                currDir_f, currFileName_f, \
                                                                configuration_2holes[f], jj_f, eigv_f, str(int(nelectrons) - 1))
                
                parallel_initial_src_paths.append(currDir_i + "/" + currFileName_i + ".f09")
                parallel_final_src_paths.append(currDir_f + "/" + currFileName_f + ".f09")
                
                parallel_initial_dst_paths.append(currDir + "/" + wfiFile + ".f09")
                parallel_final_dst_paths.append(currDir + "/" + wffFile + ".f09")
                
                parallel_transition_paths.append(currDir + "/" + exe_file)
            
            combCnt += 1
            
            if [state_i[0], state_f[0]] == starting_transition:
                found_starting = True
    
    if len(parallel_transition_paths) > 0:
        executeBatchTransitionCalculation(parallel_transition_paths, \
                                        parallel_initial_src_paths, parallel_final_src_paths, \
                                        parallel_initial_dst_paths, parallel_final_dst_paths, \
                                        file_calculated_shakeoff, calculatedSatelliteTransitions, "Calculated transitions:\n")
    
    
    energies = []
    rates = []
    multipole_array = []
    
    total_rates = dict.fromkeys([state[0] for state in calculated2holesStates], 0.0)
    
    combCnt = 0
    for counter, state_f in enumerate(calculated2holesStates):
        for state_i in calculated2holesStates[(counter + 1):]:
            i, jj_i, eigv_i = state_i[0]
            f, jj_f, eigv_f = state_f[0]
            
            currDir = rootDir + "/" + directory_name + "/transitions/satellites/" + str(combCnt)
            currFileName = str(combCnt)
            
            energy, rate, multipoles = readTransition(currDir, currFileName)
            
            total_rates[state_i[0]] += float(rate)
            
            energies.append(energy)
            rates.append(rate)
            multipole_array.append(multipoles)
            
            combCnt += 1
    
    
    # -------------- WRITE RESULTS TO THE FILES -------------- #
    
    with open(file_rates_shakeoff, "w") as sat_rates:
        sat_rates.write("Calculated Satellite Transitions\nTransition register\tShell IS\tIS Configuration\tIS 2JJ\tIS eigenvalue\tIS higher configuration\tIS percentage\tShell FS\tFS Configuration\tFS 2JJ\tFS eigenvalue\tFS higher configuration\tFS percentage\ttransition energy [eV]\trate [s-1]\tnumber multipoles\ttotal rate from IS\tbranching ratio\n")
        combCnt = 0
        for counter, state_f in enumerate(calculated2holesStates):
            for state_i in calculated2holesStates[(counter + 1):]:
                i, jj_i, eigv_i = state_i[0]
                f, jj_f, eigv_f = state_f[0]
                
                calculatedSatelliteTransitions[combCnt].append((energies[combCnt], rates[combCnt], total_rates[state_i[0]], multipole_array[combCnt]))
                
                sat_rates.write(str(combCnt) + "\t" + \
                                shell_array_2holes[i] + "\t" + \
                                configuration_2holes[i] + "\t" + \
                                str(jj_i) + "\t" + \
                                str(eigv_i) + "\t" + \
                                str(state_i[1][0]) + "\t" + \
                                str(state_i[1][1]) + "\t" + \
                                shell_array_2holes[f] + "\t" + \
                                configuration_2holes[f] + "\t" + \
                                str(jj_f) + "\t" + \
                                str(eigv_f) + "\t" + \
                                str(state_f[1][0]) + "\t" + \
                                str(state_f[1][1]) + "\t" + \
                                str(energies[combCnt]) + "\t" + \
                                str(rates[combCnt]) + "\t" + \
                                str(len(multipole_array[combCnt])) + "\t" + \
                                str(total_rates[state_i[0]]) + "\t" + \
                                (str(float(rate) / total_rates[state_i[0]]) if total_rates[state_i[0]] != 0.0 else "0.0") + "\t" + \
                                '\t'.join(['\t'.join(pole) for pole in multipole_array[combCnt]]) + "\n")
                
                combCnt += 1



def calculateSpectra(radiative_done, auger_done, satellite_done):
    print("############ Calculating the sums ###################")
    

    print("number of vacancy configurations == " + str(len(shell_array)) + "\n")
    print("type of vacancy == " + ', '.join(shell_array) + "\n")
	
	
    multiplicity_JJ = [0] * len(shell_array)
    
    radiative_rate_per_shell = [0.0] * len(shell_array)
    
    auger_rate_per_shell = [0.0] * len(shell_array_2holes)
    
    print("\nCalculating shell rates and multiplicities for diagram and auger...\n")
    
    for state in calculated1holeStates:
        multiplicity_JJ[state[0][0]] += state[0][1] + 1
    
    for transition in calculatedRadiativeTransitions:
        state_i, state_f, pars = transition
        
        radiative_rate_per_shell[state_i[0]] += float(pars[1]) * (state_i[1] + 1)
    
    
    for transition in calculatedAugerTransitions:
        state_i, state_f, pars = transition

        auger_rate_per_shell[state_i[0]] += float(pars[1]) * (state_i[1] + 1)
    
    
    fluorescenceyield = []
    
    with open(file_rates_sums, "w") as rates_sums:
        for k in range(len(shell_array)):
            fluorescenceyield.append(radiative_rate_per_shell[k] / (auger_rate_per_shell[k] + radiative_rate_per_shell[k]))
            print("Fluorescence Yield for " + shell_array[k] + " = radiative (" + str(radiative_rate_per_shell[k]) + ") / radiative (" + str(radiative_rate_per_shell[k]) + ") + auger (" + str(auger_rate_per_shell[k]) + ") = " + str(fluorescenceyield[k]))
            rates_sums.write(shell_array[k] + "\n\n")
            rates_sums.write("multiplicity of states = " + str(multiplicity_JJ[k]) + "\n")
            rates_sums.write("radiative * multiplicity of states = " + str(radiative_rate_per_shell[k]) + "\n")
            rates_sums.write("auger * multiplicity of states = " + str(auger_rate_per_shell[k]) + "\n")
            rates_sums.write("Fluorescence Yield  = " + str(fluorescenceyield[k]) + "\n")
            rates_sums.write("\n\n\n")
    
    
    
    print("JJ multiplicity/shell == " + ', '.join([str(jj) for jj in multiplicity_JJ]) + "\n")


    print("\nCalculating shell rates and multiplicities for satellites...\n")
    
    multiplicity_JJ_sat = [0] * len(shell_array_2holes)
    
    radiative_rate_per_shell_sat = [0.0] * len(shell_array_2holes)
    
    for state in calculated2holesStates:
        multiplicity_JJ_sat[state[0][0]] += state[0][1] + 1
    
    for transition in calculatedSatelliteTransitions:
        state_i, state_f, pars = transition
        
        multiplicity_JJ_sat[state_i[0]] += state_i[1] + 1
        
        radiative_rate_per_shell_sat[state_i[0]] += float(pars[1]) * (state_i[1] + 1)
    
    
    with open(file_rates_sums_shakeoff, "w") as rates_sums_sat:
        for k in range(len(shell_array_2holes)):
            rates_sums_sat.write(shell_array_2holes[k] + "\n")
            rates_sums_sat.write("multiplicity of states = " + str(multiplicity_JJ_sat[k]) + "\n")
            rates_sums_sat.write("radiative * multiplicity of states = " + str(radiative_rate_per_shell_sat[k]) + "\n")
            rates_sums_sat.write("\n\n")
	
	
	print("JJ multiplicity/shell sat == " + ', '.join([str(jj) for jj in multiplicity_JJ_sat]) + "\n")
	

    print("\nCalculating total level widths for diagram, auger and satellite transitions...\n")
    
    rate_level_radiative = dict.fromkeys([state[0] for state in calculated1holeStates], 0.0)
    rate_level_auger = dict.fromkeys([state[0] for state in calculated1holeStates], 0.0)
    rate_level_radiative_sat = dict.fromkeys([state[0] for state in calculated2holesStates], 0.0)
    
    rate_level = dict.fromkeys([state[0] for state in calculated1holeStates], 0.0)
    rate_level_ev = dict.fromkeys([state[0] for state in calculated1holeStates], 0.0)
    
    for transition in calculatedRadiativeTransitions:
        state_i, state_f, pars = transition
        
        rate_level_radiative[state_i] += float(pars[1])
	
    for transition in calculatedAugerTransitions:
        state_i, state_f, pars = transition
        
        rate_level_auger[state_i] += float(pars[1])
    
    for state_i in rate_level:
        rate_level[state_i] = rate_level_radiative[state_i] + rate_level_auger[state_i]
        rate_level_ev[state_i] = rate_level[state_i] * hbar
    
    
    fluor_sat = dict.fromkeys([state[0] for state in calculated2holesStates], 0.0)
    shell_fl_dia = dict.fromkeys([state[0] for state in calculated2holesStates], 0.0)
    rate_level_sat = dict.fromkeys([state[0] for state in calculated2holesStates], 0.0)
    rate_level_sat_ev = dict.fromkeys([state[0] for state in calculated2holesStates], 0.0)
    
    
    for transition in calculatedSatelliteTransitions:
        state_i, state_f, pars = transition
        
        rate_level_radiative_sat[state_i] += float(pars[1])
    
    for transition in calculatedSatelliteTransitions:
        state_i, state_f, pars = transition
        
        shell_sat = shell_array_2holes[state_i[0]].split("_")
        #print(" shell 2 holes =  " + shell_array_2holes[state_i[0]] + "\n")
        
        #print(" shell 2 holes divided 1 = " + shell_sat[0] + "     2 = " + shell_sat[1] + "\n")
    
    
        k = shell_array.index(shell_sat[0])
        fluor_sat[state_i] = fluorescenceyield[k]
        shell_fl_dia[state_i] = shell_array[k]
        
        rate_level_sat[state_i] = rate_level_radiative_sat[state_i] / fluorescenceyield[k]
        
        rate_level_sat_ev[state_i] = rate_level_sat[state_i] * hbar
    
    
    print("############ Writing diagram level widths ###################")
    
    with open(file_level_widths, "w") as level_widths:
        level_widths.write(" Transition register \t  Shell \t Configuration \t 2JJ \t eigenvalue \t radiative width [s-1] \t  auger width [s-1] \t total width [s-1] \t total width [eV] \n")
        
        for counter, state_i in enumerate(rate_level):
            i, jj_i, eigv_i = state_i

            #print("\nLevel " + str(counter) + " :  " + shell_array[i] + " " + configuration_1hole[i] + " 2J=" + str(jj_i) + " neig=" + str(eigv_i) + "\n")
            #print("\tradiative width = " + str(rate_level_radiative[state_i]) + " s-1 \t auger width = " + str(rate_level_auger[state_i]) + " s-1 \t total width = " + str(rate_level[state_i]) + " s-1 \t total width (eV) = " + str(rate_level_ev[state_i]) + " eV \n")
            
            level_widths.write(str(counter) + " \t " + \
                               shell_array[i] + " \t " + \
                               configuration_1hole[i] + " \t " + \
                               str(jj_i) + " \t " + \
                               str(eigv_i) + " \t " + \
                               str(rate_level_radiative[state_i]) + " \t " + \
                               str(rate_level_auger[state_i]) + " \t " + \
                               str(rate_level[state_i]) + " \t " + \
                               str(rate_level_ev[state_i]) + "\n")


    print("############ Writing satellite level widths ###################")
    
    with open(file_level_widths_shakeoff, "w") as level_widths_sat:
        level_widths_sat.write(" Transition register \t index sorted \t  Shell \t Configuration \t 2JJ \t eigenvalue \t radiative width [s-1] \t  total width [s-1] \t total width [eV] \n")
        
        for counter, state_i in enumerate(rate_level_sat):
            i, jj_i, eigv_i = state_i
            
            #print("\nLevel " + str(counter) + " :  " + shell_array_2holes[i] + " " + configuration_2holes[i] + " 2J=" + str(jj_i) + " neig=" + str(eigv_i) + "\n")
            #print("\tradiative width = " + str(rate_level_radiative_sat[state_i]) + " s-1 \t total width = " + str(rate_level_sat[state_i]) + " s-1 \t total width (eV) = " + str(rate_level_sat_ev[state_i]) + " eV \n")
            
            level_widths_sat.write(str(counter) + " \t  " + \
                                   shell_array_2holes[i] + " \t " + \
                                   configuration_2holes[i] + " \t " + \
                                   str(jj_i) + " \t " + \
                                   str(eigv_i) + " \t " + \
                                   str(rate_level_radiative_sat[state_i]) + " \t " + \
                                   str(rate_level_sat[state_i]) + " \t " + \
                                   str(rate_level_sat_ev[state_i]) + " \t " + \
                                   str(shell_fl_dia[state_i]) + " \t " + \
                                   str(fluor_sat[state_i]) + "\n")
    

    
    # -------------------- WRITE DIAGRAM SPECTRUM -------------------- #
    
    inten_trans = []
    intensity_ev = []
    transition_width = []
    
    print("############ Writing diagram spectrum ###################")
    
    with open(file_rates_spectrum_diagram, "w") as spectrum_diagram:
        spectrum_diagram.write("Transition register \t Shell IS \t IS Configuration \t IS 2JJ \t IS eigenvalue \t IS higher configuration \t IS percentage \t Shell FS \tFS Configuration \t FS 2JJ \t FS eigenvalue \t FS higher configuration \t FS percentage \t transition energy [eV] \t intensity \t intensity [eV] \t width [eV] \n")
	
        combCnt = 0
        for counter, state_f in enumerate(calculated1holeStates):
            for state_i in calculated1holeStates[(counter + 1):]:
                i, jj_i, eigv_i = state_i[0]
                f, jj_f, eigv_f = state_f[0]
                
                
                inten_trans.append((float(jj_i + 1) / float(multiplicity_JJ[i])) * (float(calculatedRadiativeTransitions[combCnt][2][1]) / rate_level[state_i[0]]))
                intensity_ev.append(inten_trans[-1] * float(calculatedRadiativeTransitions[combCnt][2][0]))
                transition_width.append(rate_level_ev[state_i[0]] + rate_level_ev[state_f[0]])

                #print("\ntransition " + str(combCnt) + " : from " + configuration_1hole[i] + " 2J=" + str(jj_i) + " neig=" + str(eigv_i) + " -> " + configuration_1hole[f] + " 2J=" + str(jj_f) + " neig=" + str(eigv_f) + " = " + str(calculatedRadiativeTransitions[combCnt][2][1]) + " s-1  Energy = " + str(calculatedRadiativeTransitions[combCnt][2][0]) + " eV\n")
                #print(" Width = initial state (" + str(rate_level_ev[state_i[0]]) + " eV) + final state (" + str(rate_level_ev[state_f[0]]) + " eV) = " + str(transition_width[-1]) + " eV\n")

                #print(" Intensity =  " + str(inten_trans[-1]) + "\n")
                #print(str(jj_i) + " \t " + str(calculatedRadiativeTransitions[combCnt][2][1]) + " \t " + str(multiplicity_JJ[i]) + " \t " + str(rate_level[state_i[0]]) + "\n")
                
                spectrum_diagram.write(str(combCnt) + " \t " + \
                                       shell_array[i] + " \t " + \
                                       configuration_1hole[i] + " \t " + \
                                       str(jj_i) + " \t " + \
                                       str(eigv_i) + " \t " + \
                                       str(state_i[1][0]) + " \t " + \
                                       str(state_i[1][1]) + " \t " + \
                                       shell_array[f] + " \t " + \
                                       configuration_1hole[f] + " \t " + \
                                       str(jj_f) + " \t " + \
                                       str(eigv_f) + " \t " + \
                                       configuration_1hole[f] + "  \t " + \
                                       str(jj_f) + " \t " + \
                                       str(calculatedRadiativeTransitions[combCnt][2][0]) + " \t " + \
                                       str(inten_trans[-1]) + " \t " + \
                                       str(intensity_ev[-1]) + " \t " + \
                                       str(transition_width[-1]) + "\n")
                
                combCnt += 1
    
    
    # -------------------- WRITE AUGER SPECTRUM -------------------- #
    
    inten_auger = []
    intensity_auger_ev = []
    transition_width_auger = []
    
    print("############ Writing auger spectrum ###################\n")
    
    with open(file_rates_spectrum_auger, "w") as spectrum_auger:
        spectrum_auger.write("Transition register \t Shell IS \t IS Configuration \t IS 2JJ \t IS eigenvalue \t IS higher configuration \t IS percentage \t Shell FS \tFS Configuration \t FS 2JJ \t FS eigenvalue \t FS higher configuration \t FS percentage \t transition energy [eV] \t intensity \t intensity [eV] \t width [eV] \n")
        
        combCnt = 0
        for state_i in calculated1holeStates:
            welt_i = state_i[1][-1]
            
            for state_f in calculated2holesStates:
                energy_diff = welt_i - state_f[1][-1]
                
                if energy_diff <= 0:
                    break
                
                i, jj_i, eigv_i = state_i[0]
                f, jj_f, eigv_f = state_f[0]
                
                inten_auger.append((float(jj_i + 1) / float(multiplicity_JJ[i])) * (float(calculatedAugerTransitions[combCnt][2][1]) / rate_level[state_i[0]]) if multiplicity_JJ[i] > 0 and rate_level[state_i[0]] > 0 else 0.0)
                intensity_auger_ev.append(inten_auger[-1] * float(calculatedAugerTransitions[combCnt][2][0]))
                transition_width_auger.append(rate_level_ev[state_i[0]] + rate_level_sat_ev[state_f[0]])


                #print(str(combCnt) + " \t " + shell_array[i] + " \t " + configuration_1hole[i] + " \t " + str(jj_i) + " \t " + str(eigv_i) + " \t " + configuration_2holes[f] + " \t " + str(jj_f) + " \t " + str(eigv_f) + " \t " + str(calculatedAugerTransitions[combCnt][2][0]) + " \t " + str(inten_auger[-1]) + " \t " + str(intensity_auger_ev[-1]) + " \t " + str(transition_width_auger[-1]) + "\n")

                spectrum_auger.write(str(combCnt) + " \t " + \
                                     shell_array[i] + " \t " + \
                                     configuration_1hole[i] + " \t " + \
                                     str(jj_i) + " \t " + \
                                     str(eigv_i) + " \t " + \
                                     str(state_i[1][0]) + " \t " + \
                                     str(state_i[1][1]) + " \t " + \
                                     shell_array_2holes[f] + " \t " + \
                                     configuration_2holes[f] + " \t " + \
                                     str(jj_f) + " \t " + \
                                     str(eigv_f) + " \t " + \
                                     str(state_f[1][0]) + " \t " + \
                                     str(state_f[1][1]) + " \t " + \
                                     str(calculatedAugerTransitions[combCnt][2][0]) + " \t " + \
                                     str(inten_auger[-1]) + " \t " + \
                                     str(intensity_auger_ev[-1]) + " \t " + \
                                     str(transition_width_auger[-1]) + "\n")
                
                combCnt += 1
    
    
    # -------------------- WRITE SATELLITE SPECTRUM -------------------- #
    
    inten_trans_sat = []
    intensity_sat_ev = []
    transition_width_sat = []
    
    print("############ Writing satellite spectrum ###################\n")
    
    with open(file_rates_spectrum_shakeoff, "w") as spectrum_sat:
        spectrum_sat.write("Transition register \t Shell IS \t IS Configuration \t IS 2JJ \t IS eigenvalue \t IS higher configuration \t IS percentage \t Shell FS \tFS Configuration \t FS 2JJ \t FS eigenvalue \t FS higher configuration \t FS percentage \t transition energy [eV] \t intensity \t intensity [eV] \t width [eV] \n")
	
        combCnt = 0
        for counter, state_f in enumerate(calculated2holesStates):
            for state_i in calculated2holesStates[(counter + 1):]:
                i, jj_i, eigv_i = state_i[0]
                f, jj_f, eigv_f = state_f[0]
                
                inten_trans_sat.append((float(jj_i + 1) / float(multiplicity_JJ_sat[i])) * (float(calculatedSatelliteTransitions[combCnt][2][1]) / rate_level_sat[state_i[0]]) if multiplicity_JJ_sat[i] > 0 and rate_level_sat[state_i[0]] > 0 else 0.0)
                intensity_sat_ev.append(inten_trans_sat[-1] * float(calculatedSatelliteTransitions[combCnt][2][0]))
                transition_width_sat.append(rate_level_sat_ev[state_i[0]] + rate_level_sat_ev[state_f[0]])
                
                
                #print("\ntransition " + str(combCnt) + ": from " + configuration_2holes[i] + " 2J=" + str(jj_i) + " neig=" + str(eigv_i) + " -> " + configuration_2holes[f] + " 2J=" + str(jj_f) + " neig=" + str(eigv_f) + " rate = " + str(calculatedSatelliteTransitions[combCnt][2][1]) + " s-1  Energy = " + str(calculatedSatelliteTransitions[combCnt][2][0]) + " eV\n")
                #print(" Width = initial state (" + str(rate_level_sat_ev[state_i[0]]) + " eV) + final state (" + str(rate_level_sat_ev[state_f[0]]) + " eV) = " + str(transition_width_sat[-1]) + " eV\n")

                #print(" Intensity =  " + str(intensity_sat_ev[-1]) + "\n")
                #print(str(jj_i) + " \t " + str(calculatedSatelliteTransitions[combCnt][2][1]) + " \t " + str(multiplicity_JJ_sat[i]) + " \t " + str(rate_level_sat[state_i[0]]) + "\n")
                
                spectrum_sat.write(str(combCnt) + " \t " + \
                                   shell_array_2holes[i] + " \t " + \
                                   configuration_2holes[i] + " \t " + \
                                   str(jj_i) + " \t " + \
                                   str(eigv_i) + " \t " + \
                                   str(state_i[1][0]) + " \t " + \
                                   str(state_i[1][1]) + " \t " + \
                                   shell_array_2holes[f] + " \t " + \
                                   configuration_2holes[f] + " \t " + \
                                   str(jj_f) + " \t " + \
                                   str(eigv_f) + " \t " + \
                                   str(state_f[1][0]) + " \t " + \
                                   str(state_f[1][1]) + " \t " + \
                                   str(calculatedSatelliteTransitions[combCnt][2][0]) + " \t " + \
                                   str(inten_trans_sat[-1]) + " \t " + \
                                   str(intensity_sat_ev[-1]) + " \t " + \
                                   str(transition_width_sat[-1]) + "\n")
                
                combCnt += 1



def GetParameters():
    global radiative_by_hand, auger_by_hand, sat_auger_by_hand, shakeup_by_hand
    
    # Get the parameters from 1 hole states
    
    initial_radiative = radiative_by_hand[:]
    
    deleted_radiative = 0
    for j, counter in enumerate(initial_radiative):
        i, jj, eigv = calculated1holeStates[counter][0]
        
        currDir = rootDir + "/" + directory_name + "/radiative/" + shell_array[i] + "/2jj_" + str(jj) + "/eigv_" + str(eigv)
        currFileName = shell_array[i] + "_" + str(jj) + "_" + str(eigv)
        
        converged, failed_orbital, overlap, higher_config, highest_percent, accuracy, Diff, welt = checkOutput(currDir, currFileName)
        
        calculated1holeStates[counter][-1] = (higher_config, highest_percent, overlap, accuracy, Diff, welt)
        
        if converged and Diff >= 0.0 and Diff <= diffThreshold and overlap < overlapsThreshold:
            del radiative_by_hand[j - deleted_radiative]
            deleted_radiative += 1
    
    
    if len(radiative_by_hand) == 0:
        print("\n\nAll 1 hole states have converged!\n")
    
    writeResults1hole(True)
    
    
    # Get the parameters from 2 hole states
    
    initial_auger = auger_by_hand[:]
    
    deleted_auger = 0
    for j, counter in enumerate(initial_auger):
        i, jj, eigv = calculated2holesStates[counter][0]
        
        currDir = rootDir + "/" + directory_name + "/auger/" + shell_array_2holes[i] + "/2jj_" + str(jj) + "/eigv_" + str(eigv)
        currFileName = shell_array_2holes[i] + "_" + str(jj) + "_" + str(eigv)
        
        converged, failed_orbital, overlap, higher_config, highest_percent, accuracy, Diff, welt = checkOutput(currDir, currFileName)
        
        calculated2holesStates[counter][-1] = (higher_config, highest_percent, overlap, accuracy, Diff, welt)
        
        if converged and Diff >= 0.0 and Diff <= diffThreshold and overlap < overlapsThreshold:
            del auger_by_hand[j - deleted_auger]
            deleted_auger += 1
    
    
    if len(auger_by_hand) == 0:
        print("\n\nAll 2 hole states have converged!\n")
    
    writeResults2holes(True)
    
    
    # Get the parameters from 3 hole states
    if calculate_3holes:
        initial_sat_auger = sat_auger_by_hand[:]
        
        deleted_sat_auger = 0
        for j, counter in enumerate(initial_sat_auger):
            i, jj, eigv = calculated3holesStates[counter][0]
            
            currDir = rootDir + "/" + directory_name + "/3holes/" + shell_array_3holes[i] + "/2jj_" + str(jj) + "/eigv_" + str(eigv)
            currFileName = shell_array_3holes[i] + "_" + str(jj) + "_" + str(eigv)
            
            converged, failed_orbital, overlap, higher_config, highest_percent, accuracy, Diff, welt = checkOutput(currDir, currFileName)
            
            calculated3holesStates[counter][-1] = (higher_config, highest_percent, overlap, accuracy, Diff, welt)
            
            if converged and Diff >= 0.0 and Diff <= diffThreshold and overlap < overlapsThreshold:
                del sat_auger_by_hand[j - deleted_sat_auger]
                deleted_sat_auger += 1
        
        
        if len(sat_auger_by_hand) == 0:
            print("\n\nAll 3 hole states have converged!\n")
        
        writeResults3holes(True)
    
    
    # Get the parameters from shake-up states
    if calculate_shakeup:
        initial_shakeup = shakeup_by_hand[:]
        
        deleted_shakeup = 0
        for j, counter in enumerate(initial_shakeup):
            i, jj, eigv = calculatedShakeupStates[counter][0]
            
            currDir = rootDir + "/" + directory_name + "/shakeup/" + shell_array_shakeup[i] + "/2jj_" + str(jj) + "/eigv_" + str(eigv)
            currFileName = shell_array_shakeup[i] + "_" + str(jj) + "_" + str(eigv)
            
            converged, failed_orbital, overlap, higher_config, highest_percent, accuracy, Diff, welt = checkOutput(currDir, currFileName)
            
            calculatedShakeupStates[counter][-1] = (higher_config, highest_percent, overlap, accuracy, Diff, welt)
            
            if converged and Diff >= 0.0 and Diff <= diffThreshold and overlap < overlapsThreshold:
                del shakeup_by_hand[j - deleted_shakeup]
                deleted_shakeup += 1
        
        
        if len(shakeup_by_hand) == 0:
            print("\n\nAll shake-up states have converged!\n")
        
        writeResultsShakeup(True)
    

def loadParameters():
    for counter, state in enumerate(calculated1holeStates):
        i, jj, eigv = state[0]
        
        currDir = rootDir + "/" + directory_name + "/radiative/" + shell_array[i] + "/2jj_" + str(jj) + "/eigv_" + str(eigv)
        currFileName = shell_array[i] + "_" + str(jj) + "_" + str(eigv)
        
        converged, failed_orbital, overlap, higher_config, highest_percent, accuracy, Diff, welt = checkOutput(currDir, currFileName)
        
        calculated1holeStates[counter].append((higher_config, highest_percent, overlap, accuracy, Diff, welt))
    
    print("\nLoaded 1 hole states parameters.")
    
    
    for counter, state in enumerate(calculated2holesStates):
        i, jj, eigv = state[0]
        
        currDir = rootDir + "/" + directory_name + "/auger/" + shell_array_2holes[i] + "/2jj_" + str(jj) + "/eigv_" + str(eigv)
        currFileName = shell_array_2holes[i] + "_" + str(jj) + "_" + str(eigv)
        
        converged, failed_orbital, overlap, higher_config, highest_percent, accuracy, Diff, welt = checkOutput(currDir, currFileName)
        
        calculated2holesStates[counter].append((higher_config, highest_percent, overlap, accuracy, Diff, welt))
    
    print("\nLoaded 2 holes states parameters.\n")
    
    
    if calculate_3holes:
        for counter, state in enumerate(calculated3holesStates):
            i, jj, eigv = state[0]
            
            currDir = rootDir + "/" + directory_name + "/3holes/" + shell_array_3holes[i] + "/2jj_" + str(jj) + "/eigv_" + str(eigv)
            currFileName = shell_array_3holes[i] + "_" + str(jj) + "_" + str(eigv)
            
            converged, failed_orbital, overlap, higher_config, highest_percent, accuracy, Diff, welt = checkOutput(currDir, currFileName)
            
            calculated3holesStates[counter].append((higher_config, highest_percent, overlap, accuracy, Diff, welt))
        
        print("\nLoaded 3 holes states parameters.\n")
    
    
    if calculate_shakeup:
        for counter, state in enumerate(calculatedShakeupStates):
            i, jj, eigv = state[0]
            
            currDir = rootDir + "/" + directory_name + "/shakeup/" + shell_array_shakeup[i] + "/2jj_" + str(jj) + "/eigv_" + str(eigv)
            currFileName = shell_array_shakeup[i] + "_" + str(jj) + "_" + str(eigv)
            
            converged, failed_orbital, overlap, higher_config, highest_percent, accuracy, Diff, welt = checkOutput(currDir, currFileName)
            
            calculatedShakeupStates[counter].append((higher_config, highest_percent, overlap, accuracy, Diff, welt))
        
        print("\nLoaded shake-up states parameters.\n")
    


def initializeEnergyCalc():
    global label_auto, atomic_number, nuc_massyorn, nuc_mass, nuc_model, machine_type, number_max_of_threads, number_of_threads, directory_name

    if not os.path.isfile(exe_file):
        print("$\nERROR!!!!!\n")
        print("\nFile DOES NOT EXIST \nPlease place MCDFGME*.exe file alongside this script\n")
    else:
        print("\n############## Energy Calculations with MCDGME code  ##############\n\n")
        
        
        print "Select option for the calculation of configurations - automatic or read (from file) : ",
        inp = raw_input().strip()
        while inp != 'automatic' and inp != 'read':
            print("\n keyword must be automatic or read!!!")
            print "Select option for the calculation of configurations - automatic or read (from file) : ",
            inp = raw_input().strip()
        
        label_auto = inp == 'automatic'
        
        
        print "Enter atomic number Z : ",
        inp = raw_input().strip()
        while not inp.isdigit():
            print("\natomic number must be an integer!!!")
            print "Enter atomic number Z : ",
            inp = raw_input().strip()
    
        atomic_number = inp
        
        print "Calculation with standard mass? (y or n) : ",
        inp = raw_input().strip()
        while inp != 'y' and inp != 'n':
            print("\n must be y or n!!!")
            print "Calculation with standard mass? (y or n) : ",
            inp = raw_input().strip()
    
        nuc_massyorn = inp
        
        if nuc_massyorn == 'n':
            print "Please enter the nuclear mass : ",
            inp = raw_input().strip()
            while not inp.isdigit():
                print("\nnuclear mass must be an integer!!!")
                print "Please enter the nuclear mass : ",
                inp = raw_input().strip()
    
            nuc_mass = int(inp)
            
            print "Please enter the nuclear model (uniform or fermi) : ",
            inp = raw_input().strip()
            while inp != 'uniform' and inp != 'fermi':
                print("\n must be uniform or fermi!!!")
                print "Please enter the nuclear model (uniform or fermi) : ",
                inp = raw_input().strip()
    
            nuc_model = inp
        
        
        parallel_max_length = int(subprocess.check_output(['getconf', 'ARG_MAX']).strip())
        
        machine_type = platform.uname()[0]
        
        if machine_type == 'Darwin':
            number_max_of_threads = subprocess.check_output(['sysctl', '-n', 'hw.ncpu']).strip()
        else:
            number_max_of_threads = subprocess.check_output(['nproc']).strip()
        
        
        print("Your " + machine_type + " machine has " + number_max_of_threads + " available threads")
        print "Enter the number of threads you want to be used in the calculation (For all leave it blank): ",
        inp = raw_input().strip()
        while not inp.isdigit() and inp != '':
            print("\nnumber of threads must be an integer!!!")
            print "Enter number of threads to be used in the calculation (For all leave it blank): ",
            inp = raw_input().strip()
    
        if inp == '':
            number_of_threads = number_max_of_threads
        elif int(inp) > int(number_max_of_threads):
            number_of_threads = number_max_of_threads
        else:
            number_of_threads = inp
        
        print("number of threads = " + number_of_threads + "\n")
        
        print "Enter directory name for the calculations: ",
        inp = raw_input().strip()
        while inp == '':
            print("\n No input entered!!!\n\n")
            print "Enter directory name for the calculations: ",
            inp = raw_input().strip()
    
        directory_name = inp
        
        if os.path.exists(directory_name):
            print("\n Directory name already exists!!!\n\n")
            print "Would you like to overwrite this directory? (y or n) : ",
            inp = raw_input().strip()
            while inp != 'y' and inp != 'n':
                print("\n must be y or n!!!")
                print "Would you like to overwrite this directory? (y or n) : ",
                inp = raw_input().strip()
            
            if inp == 'n':
                print "Please choose another name for the calculation directory: ",
                inp = raw_input().strip()
            else:
                print("\n This will erase any previous data in the directory " + directory_name)
                print "Are you sure you would like to proceed? (y or n) : ",
                inp = raw_input().strip()
                while inp != 'y' and inp != 'n':
                    print("\n must be y or n!!!")
                    print "Are you sure you would like to proceed? (y or n) : ",
                    inp = raw_input().strip()
                
                if inp == 'y':
                    shutil.rmtree(directory_name)
                    return
            
            
            while os.path.exists(inp):
                print("\n Directory name already exists!!!\n\n")
                print "Please choose another name for the calculation directory: ",
                inp = raw_input().strip()
            
            directory_name = inp



def setupElectronConfigs():
    global lines_conf, arr_conf, nb_lines_conf, lines_fir, arr_fir, nb_lines_fir, final_configuration, configuration_string, nelectrons
    global configuration_1hole, shell_array
    global configuration_2holes, shell_array_2holes
    global configuration_3holes, shell_array_3holes
    global configuration_shakeup, shell_array_shakeup
    global exist_3holes, exist_shakeup, calculate_3holes, calculate_shakeup

    count = 0
    
    if label_auto:
        enum = int(atomic_number) - 1
        
        # Initialize the array of shells and electron number
        remain_elec = enum
        electron_array = []
        
        i = 0
        while remain_elec > 0:
            shell_array.append(shells[i])
            
            if remain_elec >= electronspershell[i]:
                configuration_string += "(" + shell_array[i] + ")" + str(electronspershell[i]) + " "
                electron_array.append(electronspershell[i])
            else:
                configuration_string += "(" + shell_array[i] + ")" + str(remain_elec) + " "
                electron_array.append(remain_elec)
            
            remain_elec -= electronspershell[i]
            i += 1
        
        exist_3holes = True
        exist_shakeup = True
        
        for i in range(len(shell_array)):
            # Generate the combinations of 1 hole configurations
            b = electron_array[:]
            b[i] -= 1
            
            if b[i] >= 0:
                configuration_1hole.append('')
                
                for j in range(len(shell_array)):
                    configuration_1hole[-1] += "(" + shell_array[j] + ")" + str(b[j]) + " "
                    
                    if j >= i:
                        # Generate the combinations of 2 hole configurations                        
                        b[j] -= 1
                        
                        if b[j] >= 0:
                            shell_array_2holes.append(shell_array[i] + "_" + shell_array[j])
                            configuration_2holes.append('')
                            
                            for h in range(len(shell_array)):
                                configuration_2holes[-1] += "(" + shell_array[h] + ")" + str(b[h]) + " "
                                
                                if h >= j:
                                    # Generate the combinations of 3 hole configurations
                                    b[h] -= 1
                                    
                                    if b[h] >= 0:
                                        shell_array_3holes.append(shell_array[i] + "_" + shell_array[j] + "_" + shell_array[h])
                                        configuration_3holes.append('')
                                        
                                        for k in range(len(shell_array)):
                                            configuration_3holes[-1] += "(" + shell_array[k] + ")" + str(b[k]) + " "
                                    
                                    b[h] += 1
                            
                            for h in range(len(shells)):
                                if h >= j:
                                    # Generate the combinations of shake-up configurations
                                    if h < len(shell_array):
                                        b[h] += 1
                                    
                                    if b[h] <= electronspershell[h]:
                                        shell_array_shakeup.append(shell_array[i] + "_" + shell_array[j] + "-" + shell_array[h])
                                        configuration_shakeup.append('')
                                        
                                        for k, shell in enumerate(shells):
                                            if k < len(shell_array):
                                                configuration_shakeup[-1] += "(" + shell_array[k] + ")" + str(b[k]) + " "
                                            elif h == k:
                                                configuration_shakeup[-1] += "(" + shell + ")1"
                                            
        
        
        nelectrons = str(enum)
        
        print("Element Z=" + atomic_number + "\n")
        print("Atom ground-state Neutral configuration:\n" + configuration_string + "\n")
        print("Number of occupied orbitals = " + str(count) + "\n")
        
        print("\nBoth 3 hole configurations and shake-up configurations were generated.\n")
        print "Would you like to calculate these configurations? - both, 3holes or shakeup : ",
        inp = raw_input().strip()
        while inp != 'both' or inp != '3holes' or inp != 'shakeup':
            print("\n keyword must be both, 3holes or shakeup!!!")
            print "Would you like to calculate this configurations? - both, 3holes or shakeup : ",
            inp = raw_input().strip()
        
        if inp == 'both':
            calculate_3holes = True
            calculate_shakeup = True
        elif inp == '3holes':
            calculate_3holes = True
        elif inp == 'shakeup':
            calculate_shakeup = True
    else:
        # Check if the files with the configurations for 1 and 2 holes to be read exist
        
        if os.path.exists(file_conf_rad) and os.path.exists(file_conf_aug):
            configuration_1hole = []
            shell_array = []
            
            with open(file_conf_rad, "r") as f:
                for line in f:
                    colum1, colum2 = line.strip().split(",")
                    configuration_1hole.append(colum1)
                    shell_array.append(colum2)
                    count += 1
            
            electrons = []
            
            for config in configuration_1hole:
                electrons.append(0)
                
                shells = config.split()
                for shell in shells:
                    res = re.split('(\d+)', shell)
                    electrons[-1] += int(res[-2])
            
            for i, elec in enumerate(electrons[1:]):
                if elec - electrons[0] != 0:
                    print("Error: Unsuported varying number of electrons between 1 hole configurations.")
                    print("Electrons for configuration: " + configuration_1hole[i + 1] + "; were " + str(elec) + ", expected: " + str(electrons[0]))
                    print("Stopping...")
                    sys.exit(1)
            
            elec_1hole = electrons[0]
            
            configuration_2holes = []
            shell_array_2holes = []
            
            with open(file_conf_aug, "r") as f:
                for line in f:
                    colum1, colum2 = line.strip().split(",")
                    configuration_2holes.append(colum1)
                    shell_array_2holes.append(colum2)
            
            electrons = []
            
            for config in configuration_2holes:
                electrons.append(0)
                
                shells = config.split()
                for shell in shells:
                    res = re.split('(\d+)', shell)
                    electrons[-1] += int(res[-2])
            
            for i, elec in enumerate(electrons[1:]):
                if elec - electrons[0] != 0:
                    print("Error: Unsuported varying number of electrons between 1 hole configurations.")
                    print("Electrons for configuration: " + configuration_2holes[i + 1] + "; were " + str(elec) + ", expected: " + str(electrons[0]))
                    print("Stopping...")
                    sys.exit(1)
            
            elec_2holes = electrons[0]
            
            if elec_1hole != elec_2holes + 1:
                print("The number of electrons for 1 hole configurations have to be 1 more than for 2 holes configurations.")
                print("Number of electrons for 1 hole: " + str(elec_1hole) + "; 2 holes: " + str(elec_2holes))
                print("Stopping...")
                sys.exit(1)
            
            print("Configuration files correctly loaded !!!\n")
            shutil.copyfile(file_conf_rad, directory_name + "/backup_" + file_conf_rad)
            shutil.copyfile(file_conf_aug, directory_name + "/backup_" + file_conf_aug)
            
            print("backup of configuration files can be found at " + directory_name + "/backup_" + file_conf_rad + " and " + directory_name + "/backup_" + file_conf_aug + " !!!\n")
            
            nelectrons = str(elec_1hole)
            
            print("Number of electrons for this calculation was determined as: " + str(elec_1hole))
            print "Would you like to proceed with this value? (y or n) : ",
            inp = raw_input().strip()
            while inp != 'y' and inp != 'n':
                print("\n must be y or n!!!")
                print "Would you like to proceed with this value? (y or n) : ",
                inp = raw_input().strip()
            
            if inp == 'n':
                print("Warning: You are amazing if you know what you are doing but overwriting the number of electrons will probably lead to errors... good luck.")
                print "Enter number of electrons : ",
                nelectrons = raw_input().strip()
                while not nelectrons.isdigit():
                    print("\nnumber of electrons must be an integer!!!")
                    print "Enter number of electrons : ",
                    nelectrons = raw_input().strip()
        else:
            print("Configuration files do not exist !!! Place them alongside this script and name them:")
            print(file_conf_rad)
            print(file_conf_aug)
            sys.exit(1)
        
        
        # Check if the files with the configurations for 3 holes to be read exist
        
        if os.path.exists(file_conf_sat_aug):
            exist_3holes = True
            
            configuration_3holes = []
            shell_array = []
            
            with open(file_conf_sat_aug, "r") as f:
                for line in f:
                    colum1, colum2 = line.strip().split(",")
                    configuration_3holes.append(colum1)
                    shell_array_3holes.append(colum2)
                    count += 1
            
            electrons = []
            
            for config in configuration_3holes:
                electrons.append(0)
                
                shells = config.split()
                for shell in shells:
                    res = re.split('(\d+)', shell)
                    electrons[-1] += int(res[-2])
            
            for i, elec in enumerate(electrons[1:]):
                if elec - electrons[0] != 0:
                    print("Error: Unsuported varying number of electrons between 3 hole configurations.")
                    print("Electrons for configuration: " + configuration_3holes[i + 1] + "; were " + str(elec) + ", expected: " + str(electrons[0]))
                    print("Stopping...")
                    sys.exit(1)
            
            elec_3holes = electrons[0]
            
            if elec_2holes != elec_3holes + 1:
                print("The number of electrons for 2 hole configurations have to be 1 more than for 3 holes configurations.")
                print("Number of electrons for 3 hole: " + str(elec_3holes) + "; 2 holes: " + str(elec_2holes))
                print("Stopping...")
                sys.exit(1)
            
            print("Configuration file correctly loaded for 3 hole configurations !!!\n")
            shutil.copyfile(file_conf_sat_aug, directory_name + "/backup_" + file_conf_sat_aug)
            
            print("backup of configuration file can be found at " + directory_name + "/backup_" + file_conf_sat_aug + " !!!\n")
        else:
            print("Configuration files do not exist for 3 holes !!! If you wish to calculate them, place the file alongside this script and name them:")
            print(file_conf_sat_aug)
        
        
        # Check if the files with the configurations for shakeup to be read exist
        
        if os.path.exists(file_conf_shakeup):
            exist_shakeup = True
            
            configuration_shakeup = []
            shell_array_shakeup = []
            
            with open(file_conf_shakeup, "r") as f:
                for line in f:
                    colum1, colum2 = line.strip().split(",")
                    configuration_shakeup.append(colum1)
                    shell_array_shakeup.append(colum2)
            
            electrons = []
            
            for config in configuration_shakeup:
                electrons.append(0)
                
                shells = config.split()
                for shell in shells:
                    res = re.split('(\d+)', shell)
                    electrons[-1] += int(res[-2])
            
            for i, elec in enumerate(electrons[1:]):
                if elec - electrons[0] != 0:
                    print("Error: Unsuported varying number of electrons between shake-up configurations.")
                    print("Electrons for configuration: " + configuration_shakeup[i + 1] + "; were " + str(elec) + ", expected: " + str(electrons[0]))
                    print("Stopping...")
                    sys.exit(1)
            
            elec_shakeup = electrons[0]
            
            if elec_shakeup != elec_1hole:
                print("The number of electrons for shake-up configurations have to be the same as for 1 holes configurations.")
                print("Number of electrons for shake-up: " + str(elec_shakeup) + "; 1 holes: " + str(elec_1hole))
                print("Stopping...")
                sys.exit(1)
            
            print("Configuration files correctly loaded !!!\n")
            shutil.copyfile(file_conf_shakeup, directory_name + "/backup_" + file_conf_shakeup)
            
            print("backup of configuration files can be found at " + directory_name + "/backup_" + file_conf_sat_aug + " and " + directory_name + "/backup_" + file_conf_shakeup + " !!!\n")
        else:
            print("Configuration files do not exist for shake-up !!! If you wish to calculate them, place the file alongside this script and name them:")
            print(file_conf_shakeup)
        
        
        # Configure which configurations to calculate
        
        if exist_3holes and exist_shakeup:
            print("\nBoth 3 hole configurations and shake-up configurations exist.\n")
            print "Would you like to calculate these configurations? - both, 3holes or shakeup : ",
            inp = raw_input().strip()
            while inp != 'both' or inp != '3holes' or inp != 'shakeup':
                print("\n keyword must be both, 3holes or shakeup!!!")
                print "Would you like to calculate this configurations? - both, 3holes or shakeup : ",
                inp = raw_input().strip()
            
            if inp == 'both':
                calculate_3holes = True
                calculate_shakeup = True
            elif inp == '3holes':
                calculate_3holes = True
            elif inp == 'shakeup':
                calculate_shakeup = True
        elif exist_3holes:
            print("\nOnly 3 hole configurations exist.\n")
            print "Would you like to calculate these configurations? (y or n) : ",
            inp = raw_input().strip()
            while inp != 'y' or inp != 'n':
                print("\n keyword must be y or n!!!")
                print "Would you like to calculate these configurations? (y or n) : ",
                inp = raw_input().strip()
            
            if inp == 'y':
                calculate_3holes = True
        elif exist_shakeup:
            print("\nOnly shake-up configurations exist.\n")
            print "Would you like to calculate these configurations? (y or n) : ",
            inp = raw_input().strip()
            while inp != 'y' or inp != 'n':
                print("\n keyword must be y or n!!!")
                print "Would you like to calculate these configurations? (y or n) : ",
                inp = raw_input().strip()
            
            if inp == 'y':
                calculate_shakeup = True



def setupDirs():
    os.mkdir(directory_name)
    os.mkdir(directory_name + "/radiative")
    os.mkdir(directory_name + "/auger")
    os.mkdir(directory_name + "/transitions")


def setupFiles():
    global file_cycle_log_1hole, file_cycle_log_2holes, file_cycle_log_3holes, file_cycle_log_shakeup
    global file_sorted_1hole, file_sorted_2holes, file_sorted_3holes, file_sorted_shakeup
    global file_calculated_radiative, file_calculated_auger, file_calculated_shakeoff, file_calculated_shakeup
    global file_parameters, file_results, file_final_results
    global file_final_results_1hole, file_final_results_2holes, file_final_results_3holes, file_final_results_shakeup
    global file_rates, file_rates_auger, file_rates_shakeoff, file_rates_shakeup
    global file_rates_spectrum_diagram, file_rates_spectrum_auger, file_rates_spectrum_shakeoff, file_rates_spectrum_shakeup
    global file_rates_sums, file_rates_sums_shakeoff, file_rates_sums_shakeup
    global file_level_widths, file_level_widths_shakeoff, file_level_widths_shakeup
    
    
    file_cycle_log_1hole = rootDir + "/" + directory_name + "/" + directory_name + "_1hole_states_log.txt"
    file_cycle_log_2holes = rootDir + "/" + directory_name + "/" + directory_name + "_2holes_states_log.txt"
    file_cycle_log_3holes = rootDir + "/" + directory_name + "/" + directory_name + "_3holes_states_log.txt"
    file_cycle_log_shakeup = rootDir + "/" + directory_name + "/" + directory_name + "_shakeup_states_log.txt"
    
    file_sorted_1hole = rootDir + "/" + directory_name + "/" + directory_name + "_1hole_sorted.txt"
    file_sorted_2holes = rootDir + "/" + directory_name + "/" + directory_name + "_2holes_sorted.txt"
    file_sorted_3holes = rootDir + "/" + directory_name + "/" + directory_name + "_3holes_sorted.txt"
    file_sorted_shakeup = rootDir + "/" + directory_name + "/" + directory_name + "_shakeup_sorted.txt"
    
    file_calculated_radiative = rootDir + "/" + directory_name + "/" + directory_name + "_radiative_calculated.txt"
    file_calculated_auger = rootDir + "/" + directory_name + "/" + directory_name + "_auger_calculated.txt"
    file_calculated_shakeoff = rootDir + "/" + directory_name + "/" + directory_name + "_shakeoff_calculated.txt"
    file_calculated_shakeup = rootDir + "/" + directory_name + "/" + directory_name + "_shakeup_calculated.txt"
    
    file_parameters = rootDir + "/" + directory_name + "/calculation_parameters.txt"
    file_results = rootDir + "/" + directory_name + "/" + directory_name + "_results_all_cicles.txt"
    file_final_results = rootDir + "/" + directory_name + "/" + directory_name + "_results_energy_single_configuration.txt"

    file_final_results_1hole = rootDir + "/" + directory_name + "/" + directory_name + "_results_energy_single_configuration_1hole.txt"
    file_final_results_2holes = rootDir + "/" + directory_name + "/" + directory_name + "_results_energy_single_configuration_2holes.txt"
    file_final_results_3holes = rootDir + "/" + directory_name + "/" + directory_name + "_results_energy_single_configuration_3holes.txt"
    file_final_results_shakeup = rootDir + "/" + directory_name + "/" + directory_name + "_results_energy_single_configuration_shakeup.txt"

    file_rates = rootDir + "/" + directory_name + "/" + directory_name + "_rates_radiative.txt"
    file_rates_auger = rootDir + "/" + directory_name + "/" + directory_name + "_rates_auger.txt"
    file_rates_shakeoff = rootDir + "/" + directory_name + "/" + directory_name + "_rates_shakeoff.txt"
    file_rates_shakeup = rootDir + "/" + directory_name + "/" + directory_name + "_rates_shakeup.txt"
    
    file_rates_spectrum_diagram = rootDir + "/" + directory_name + "/" + directory_name + "_spectrum_diagram.txt"
    file_rates_spectrum_auger = rootDir + "/" + directory_name + "/" + directory_name + "_spectrum_auger.txt"
    file_rates_spectrum_shakeoff = rootDir + "/" + directory_name + "/" + directory_name + "_spectrum_shakeoff.txt"
    file_rates_spectrum_shakeup = rootDir + "/" + directory_name + "/" + directory_name + "_spectrum_shakeup.txt"
    
    file_rates_sums = rootDir + "/" + directory_name + "/" + directory_name + "_rates_sums.txt" 
    file_rates_sums_shakeoff = rootDir + "/" + directory_name + "/" + directory_name + "_rates_sums_shakeoff.txt" 
    file_rates_sums_shakeup = rootDir + "/" + directory_name + "/" + directory_name + "_rates_sums_shakeup.txt" 

    file_level_widths = rootDir + "/" + directory_name + "/" + directory_name + "_level_widths.txt"
    file_level_widths_shakeoff = rootDir + "/" + directory_name + "/" + directory_name + "_level_widths_shakeoff.txt"
    file_level_widths_shakeup = rootDir + "/" + directory_name + "/" + directory_name + "_level_widths_shakeup.txt"


def writeCalculationParameters():
    with open(file_parameters, 'w') as fp:
        fp.write("########################################## Output of the calculation parameters ##########################################################\n\n")
        fp.write("Electron configurations are: " + ("read" if not label_auto else "automatic") + "\n")
        
        if calculate_3holes:
            fp.write("3 hole configurations are being calculated!\n")
        if calculate_shakeup:
            fp.write("Shake-up configurations are being calculated!\n")
        
        fp.write("Atomic number Z= " + atomic_number + "\n")
        fp.write("Number of electrons: " + nelectrons + "\n")
        fp.write("Calculations performed with standard mass: " + nuc_massyorn + "\n")
        
        if nuc_massyorn == 'n':
            fp.write("Nuclear mass: " + str(nuc_mass) + "\n")
            fp.write("Nuclear model: " + nuc_model + "\n")
        
        fp.write("Number of considered threads in the calculation= " + number_of_threads + "\n")


def InitialPrompt():
    global partial
    
    os.system('clear')
    
    print("\n\n         #########################################################################################################################")
    print("         #########################################################################################################################")
    print("         ####                                                                                                                 ####")
    print("         ####            !!! Python script to paralellize MCDFGME calculations for a specific Atomic System !!!               ####")
    print("         ####                 !!! This was written based on a previous Bash script by Jorge Machado !!!                       ####")
    print("         ####                                                                                                                 ####")
    print("         ####        Original Author: Jorge Machado                                                                           ####")
    print("         ####        email: jfd.machado@fct.unl.pt                                                                            ####")
    print("         ####        Last update: 17/05/2021                                                                                  ####")
    print("         ####                                                                                                                 ####")
    print("         ####        Current Author: Daniel Pinheiro                                                                          ####")
    print("         ####        email: ds.pinheiro@campus.fct.unl.pt                                                                     ####")
    print("         ####        Last update: 16/03/2023                                                                                  ####")
    print("         ####                                                                                                                 ####")
    print("         ####    Calculates:                                                                                                  ####")
    print("         ####                                                                                                                 ####")
    print("         ####    1- all one and two vacancy levels for the selected Z system                                                  ####")
    print("         ####    2- after reaching convergence of all levels, calculates all energetically allowed transition rates           ####")
    print("         ####       (radiative, auger and satellites)                                                                         ####")
    print("         ####    3- Calculates all the sums to get fluorescence yields, level widths, etc...                                  ####")
    print("         ####    4- Calculates the overlaps between the wave functions of two sates to get shake probabilities                ####")
    print("         ####    5- It produces several output files with diverse atomic parameters and a file with the theoretical spectrum  ####")
    print("         ####       (transition energy, natural width and intensity to generate a theoretical spectra)                        ####")
    print("         ####                                                                                                                 ####")
    print("         ####                                                                                                                 ####")
    print("         ####    Documentation, as well as different versions for different programing languages will be available at:        ####")
    print("         ####    (github)                                                                                                     ####")
    print("         ####                                                                                                                 ####")
    print("         ####                                                                                                                 ####")
    print("         #########################################################################################################################")
    print("         ######################################################################################################################### \n\n\n\n\n")
    
    print "Select option for the calculation - full or partial (if energy calculation has been already performed) : ",
    inp = raw_input().strip()
    while inp != 'full' and inp != 'partial':
        print("\n keyword must be full or partial!!!")
        print "Select option for the calculation - full or partial (if energy calculation has been already performed) : ",
        inp = raw_input().strip()
    
    partial = inp == 'partial'
    

def midPrompt(partial_check=False):
    if not partial_check:
        print("\n\nPlease check for convergence of the 1 and 2 holes states.")
        print("File " + file_final_results + " contains the results for both calculations, as well as a list of flagged states.")
        print("Files " + file_final_results_1hole + " and " + file_final_results_2holes + "contain the results 1 and 2 holes respectively, as well as a list of flagged states.")
        #print("A helper script \"checkConvergence.py\" can also be used to check the convergence before continuing.")
        #print("This script will tell you which states did not reach proper convergence.\n")
        
        print("To re-check flagged states please type GetParameters.")
        print("If you would like to continue the rates calculation with the current states please type:\n")
        print("All - A full rate calculation will be performed for diagram, auger and satellite (shake-off and shake-up) decays, including the spectra calculations afterwards.\n")
        print("Simple - A rate calculation will be performed for diagram and auger decays, including the spectra calculations afterwards.\n")
        print("rates_all - A rate calculation will be performed for diagram, auger and satellite (shake-off and shake-up) decays, without any spectra calculations.\n")
        print("rates - A rate calculation will be performed for diagram and auger decays, without any spectra calculations.\n")
        inp = raw_input().strip()
        while inp != "Continue" and inp != "All" and inp != "Simple" and inp != "rates_all" and inp != "rates":
            if inp == "GetParameters":
                GetParameters()
                print("New flagged states parameters can be found in the files " + file_final_results + ", " + file_final_results_1hole + ", " + file_final_results_2holes + ", for both 1 and 2 holes states.\n\n")
            
            print("To recheck flagged states please type GetParameters.")
            print("If you would like to continue the rates calculation with the current states please type Continue.\n")
            inp = raw_input().strip()


        type_calc = inp
        
        print("Continuing rate calculation with the current 1 and 2 holes states.\n")
        
        with open(file_parameters, "a") as fp:
            fp.write("\nCalculation performed for: " + type_calc + "\n")
        
        print(80*"-" + "\n")
    else:
        with open(file_parameters, "r") as fp:
            for line in fp:
                if "Calculation performed for: " in line:
                    type_calc = line.replace("Calculation performed for: ", "").strip()
        
        prev_type_calc = type_calc
        
        print("\nCalculation was previously loaded as: " + type_calc)
        print "Would you like to proceed with this configuration? (y or n): ",
        inp = raw_input().strip()
        while inp != "y" and inp != "n":
            print("\n must be y or n!!!")
            print "Would you like to proceed with this configuration? (y or n): ",
            inp = raw_input().strip()
        
        if inp == "n":
            print("Choose a new type of calculation:\n")
            print("All - A full rate calculation will be performed for diagram, auger and satellite (shake-off and shake-up) decays, including the spectra calculations afterwards.\n")
            print("Simple - A rate calculation will be performed for diagram and auger decays, including the spectra calculations afterwards.\n")
            print("rates_all - A rate calculation will be performed for diagram, auger and satellite (shake-off and shake-up) decays, without any spectra calculations.\n")
            print("rates - A rate calculation will be performed for diagram and auger decays, without any spectra calculations.\n")
            inp = raw_input().strip()
            while inp != "Continue" and inp != "All" and inp != "Simple" and inp != "rates_all" and inp != "rates":
                print("Must be either: All, Simple, rates_all or rates!!!\n")
                print("Choose a new type of calculation:\n")
                print("All - A full rate calculation will be performed for diagram, auger and satellite (shake-off and shake-up) decays, including the spectra calculations afterwards.\n")
                print("Simple - A rate calculation will be performed for diagram and auger decays, including the spectra calculations afterwards.\n")
                print("rates_all - A rate calculation will be performed for diagram, auger and satellite (shake-off and shake-up) decays, without any spectra calculations.\n")
                print("rates - A rate calculation will be performed for diagram and auger decays, without any spectra calculations.\n")
                inp = raw_input().strip()
            
            type_calc = inp
            
            parametersFileString = ''
            
            with open(file_parameters, "r") as fp:
                parametersFileString = ''.join(fp.readlines())
            
            with open(file_parameters, "w") as fp:
                fp.write(parametersFileString.replace("Calculation performed for: " + prev_type_calc, "Calculation performed for: " + type_calc)
        
    
    return type_calc



if __name__ == "__main__":
    InitialPrompt()
    
    
    resort = True
    
    redo_energy_calc = False
    
    redo_transitions = False
    
    redo_rad = False
    redo_aug = False
    redo_sat = False
    
    partial_rad = False
    partial_aug = False
    partial_sat = False
    
    
    radiative_done = False
    auger_done = False
    satellite_done = False
    
    
    if not partial:
        initializeEnergyCalc()
        
        setupDirs()
        setupFiles()
        setupElectronConfigs()
        
        writeCalculationParameters()
    else:
        flags = checkPartial()
        
        if type(flags) == type(0):
            if flags == 1:
                partial = False
            elif flags == 2:
                loadParameters()
            elif flags == 3:
                resort = False
        else:
            if len(flags) > 3:
                redo_energy_calc = True
                
                complete_1hole, complete_2holes, last_calculated_cycle_1hole, last_calculated_cycle_2holes, last_calculated_state_1hole, last_calculated_state_2holes = flags
            elif len(flags) == 3:
                resort = False
                redo_transitions = True
                
                last_rad_calculated, last_aug_calculated, last_sat_calculated = flags
                
                if type(last_rad_calculated) == type(True):
                    if not last_rad_calculated:
                        redo_rad = True
                    else:
                        radiative_done = True
                else:
                    partial_rad = True
                if type(last_aug_calculated) == type(True):
                    if not last_aug_calculated:
                        redo_aug = True
                    else:
                        auger_done = True
                else:
                    partial_aug = True
                if type(last_sat_calculated) == type(True):
                    if not last_sat_calculated:
                        redo_sat = True
                    else:
                        satellite_done = True
                else:
                    partial_sat = True
    
    
    setupTemplates()
    
    type_calc = ''
    
    if not partial:
        calculate1holeStates()
        calculate2holesStates()
        if calculate_3holes:
            calculate3holesStates()
        if calculate_shakeup:
            calculateShakeupStates()
        
        type_calc = midPrompt()
    elif redo_energy_calc:
        if not complete_1hole:
            calculate1holeStates(last_calculated_cycle_1hole, last_calculated_state_1hole)
        if not complete_2holes:
            calculate2holesStates(last_calculated_cycle_2holes, last_calculated_state_2holes)
    
    
    if resort:
        print("\nSorting lists of states...")
        sortCalculatedStates()
    
    
    if not partial:
        rates()
        radiative_done = True
        
        rates_auger()
        auger_done = True
        
        if type_calc == "All" or type_calc == "rates_all":
            rates_satellite()
            satellite_done = True
    elif redo_transitions:
        type_calc = midPrompt(True)
        
        if redo_rad:
            rates()
            radiative_done = True
        elif partial_rad:
            rates(last_rad_calculated)
            radiative_done = True
        
        if redo_aug:
            rates_auger()
            auger_done = True
        elif partial_aug:
            rates_auger(last_aug_calculated)
            auger_done = True
        
        if type_calc == "All" or type_calc == "rates_all":
            if redo_sat:
                rates_satellite()
                satellite_done = True
            elif partial_sat:
                rates_satellite(last_sat_calculated)
                satellite_done = True
       
       
    
    if type_calc == "All" or type_calc == "Simple":
        calculateSpectra(radiative_done, auger_done, satellite_done)
