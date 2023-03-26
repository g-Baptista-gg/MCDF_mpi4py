import os, sys, platform
import subprocess
import shutil
import copy

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

# Log files to know where the calculation has stopped during the state calculation if something goes wrong
file_cycle_log_1hole = ''
file_cycle_log_2holes = ''

# Log files to store the states readily sorted for rate calculations
file_sorted_1hole = ''
file_sorted_2holes = ''

# Log files to store the calculated transitions
file_calculated_radiative = ''
file_calculated_auger = ''
file_calculated_sat = ''

# File with the general parameters for the calculation
file_parameters = ''

# Files with the energy and convergence results for the various atomic states calculated
file_results = ''
file_final_results = ''
file_final_results_1hole = ''
file_final_results_2holes = ''

# Files with the rates for diagram, auger and satellite transitions
file_rates = ''
file_rates_auger = ''
file_rates_satellites = ''

# Files with the calculated diagram, auger and satellite spectra
file_rates_spectrum_diagram = ''
file_rates_spectrum_auger = ''
file_rates_spectrum_sat = ''

# Files with rate sums, used for fluorescence yield determinations
file_rates_sums = ''
file_rates_sums_sat = ''

# Files with level sums, used for spectra calculation
file_level_widths = ''
file_level_widths_sat = ''


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


# ------------------------------------------------------------------- #
#        Variables to manage the calculated 1 and 2 hole states       #
# These variables will have the quantum numbers to identify the state #
#   as well as various parameters to evaluate the states convergence  #
# ------------------------------------------------------------------- #

# List of calculated 1 hole states and their convergence parameters
calculated1holeStates = []
# List of calculated 2 holes states and their convergence parameters
calculated2holesStates = []

# List of 1 hole states that need to be calculated by hand
radiative_by_hand = []
# List of 2 holes states that need to be calculated by hand
auger_by_hand = []


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


def checkPartial():
    global calculated1holeStates, calculated2holesStates
    
    def readStateList():
        global calculated1holeStates, calculated2holesStates
        
        complete_1hole = False
        complete_2holes = False
        
        last_calculated_cycle_1hole = 0
        last_calculated_cycle_2holes = 0
        
        last_calculated_state_1hole = [(0, 0, 0)]
        last_calculated_state_2holes = [(0, 0, 0)]
        
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
                    elif "Fourth Cycle Last Calculated:" in line:
                        last_calculated_cycle_1hole = 4
                    elif last_calculated_cycle_1hole > 0 and line != "\n":
                        last_calculated_state_1hole = [(int(qn) for qn in line.strip().split(", "))]
                    
                    if not complete_1hole:
                        calculated1holeStates.append([(int(qn) for qn in line.strip().split(", "))])
        
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
                    elif "Fourth Cycle Last Calculated:" in line:
                        last_calculated_cycle_2holes = 4
                    elif last_calculated_cycle_2holes > 0 and line != "\n":
                        last_calculated_state_2holes = [(int(qn) for qn in line.strip().split(", "))]
                    
                    if not complete_2holes:
                        calculated2holesStates.append([(int(qn) for qn in line.strip().split(", "))])
        
        return complete_1hole, complete_2holes, last_calculated_cycle_1hole, last_calculated_state_1hole, last_calculated_cycle_2holes, last_calculated_state_2holes
    
    
    def readSortedStates():
        global calculated1holeStates, calculated2holesStates
        
        complete_sorted_1hole = False
        complete_sorted_2holes = False
        
        with open(file_sorted_1hole, "r") as sorted_1hole:
            if len(sorted_1hole.readlines()) - 1 == len(calculated1holeStates):
                complete_sorted_1hole = True
        
        if complete_sorted_1hole:
            with open(file_sorted_1hole, "r") as sorted_1hole:
                calculated1holeStates = []
                for line in sorted_1hole:
                    state_nums = (int(qn) for qn in line.strip().split("; ")[0].split(", "))
                    state_parameters = (par if i == 0 else float(par) for i, par in enumerate(line.strip().split("; ")[0].split(", ")))
                    calculated1holeStates.append([state_nums, state_parameters])
        
        with open(file_sorted_2holes, "r") as sorted_2holes:
            if len(sorted_2holes.readlines()) - 1 == len(calculated2holesStates):
                complete_sorted_2holes = True
        
        if complete_sorted_2holes:
            with open(file_sorted_2holes, "r") as sorted_2holes:
                calculated2holesStates = []
                for line in sorted_2holes:
                    state_nums = (int(qn) for qn in line.strip().split("; ")[0].split(", "))
                    state_parameters = (par if i == 0 else float(par) for i, par in enumerate(line.strip().split("; ")[0].split(", ")))
                    calculated2holesStates.append([state_nums, state_parameters])
        
        return complete_sorted_1hole, complete_sorted_2holes
    
    
    def readTransitions():
        if os.path.isfile(file_calculated_radiative):
            with open(file_calculated_radiative, "r") as rad_calculated:
                rad_calculated.readline()
                for line in rad_calculated:
                    if line != "\n":
                        state_i = (int(qn) for qn in line.strip().split("; ")[0].split(", "))
                        state_f = (int(qn) for qn in line.strip().split("; ")[1].split(", "))
                        
                        last_rad_calculated = [state_i, state_f]
        else:
            last_rad_calculated = False
        
        if os.path.isfile(file_calculated_auger):
            with open(file_calculated_auger, "r") as aug_calculated:
                aug_calculated.readline()
                for line in aug_calculated:
                    if line != "\n":
                        state_i = (int(qn) for qn in line.strip().split("; ")[0].split(", "))
                        state_f = (int(qn) for qn in line.strip().split("; ")[1].split(", "))
                        
                        last_aug_calculated = [state_i, state_f]
        else:
            last_aug_calculated = False
        
        if os.path.isfile(file_calculated_sat):
            with open(file_calculated_sat, "r") as sat_calculated:
                sat_calculated.readline()
                for line in sat_calculated:
                    if line != "\n":
                        state_i = (int(qn) for qn in line.strip().split("; ")[0].split(", "))
                        state_f = (int(qn) for qn in line.strip().split("; ")[1].split(", "))
                        
                        last_sat_calculated = [state_i, state_f]
        else:
            last_sat_calculated = False
        
        return last_rad_calculated, last_aug_calculated, last_sat_calculated
    
    
    if not os.path.isfile(exe_file):
        print("$\nERROR!!!!!\n")
        print("\nFile DOES NOT EXIST \nPlease place MCDFGME*.exe file alongside this script\n")
    else:
        if any([os.path.isfile(file_calculated_radiative), os.path.isfile(file_calculated_auger), os.path.isfile(file_calculated_sat)]):
            print("Found files with the last calculated transitions.")
            
            if os.path.isfile(file_cycle_log_1hole) and os.path.isfile(file_cycle_log_2holes):
                print("Found file with the list of discovered states.")
                complete_1hole, complete_2holes, last_calculated_cycle_1hole, last_calculated_state_1hole, last_calculated_cycle_2holes, last_calculated_state_2holes = readStateList()
                
                if complete_1hole and complete_2holes and last_calculated_cycle_1hole == 4 and last_calculated_cycle_2holes == 4 and last_calculated_state_1hole[0] == calculated1holeStates[-1][0] and last_calculated_state_2holes[0] == calculated2holesStates[-1][0]:
                    print("Verifyed that the file with the list of calculated states is consistent.")
                    print("Proceding with this list.")
                else:
                    print("Error while checking the file with calculated states.\n")
                    print("Flag -> Value ; Expected:")
                    print("Completed 1 hole              -> " + str(complete_1hole) + " ; True")
                    print("Completed 2 holes             -> " + str(complete_2holes) + " ; True")
                    print("Last calculated cycle 1 hole  -> " + str(last_calculated_cycle_1hole) + "    ; 4")
                    print("Last calculated cycle 2 holes -> " + str(last_calculated_cycle_2holes) + "    ; 4")
                    print("Last calculated state 1 hole  -> " + str(last_calculated_state_1hole[0]) + " ; " + calculated1holeStates[-1][0])
                    print("Last calculated state 2 holes -> " + str(last_calculated_state_2holes[0]) + " ; " + calculated2holesStates[-1][0])
                    
                    print("\nPicking up from the last calculated states...\n")
                    
                    return complete_1hole, complete_2holes, last_calculated_cycle_1hole, last_calculated_cycle_2holes, last_calculated_state_1hole[0], last_calculated_state_2holes[0]
                
            else:
                print("File with the list of discovered states is missing: ")
                print("1 hole states -> " + file_cycle_log_1hole)
                print("2 holes states -> " + file_cycle_log_2holes)
                print("\nReverting to full calculation...\n")
                
                return 1
            
            if os.path.isfile(file_sorted_1hole) and os.path.isfile(file_sorted_2holes):
                print("Found files with energy sorted calculated states.")
                
                complete_sorted_1hole, complete_sorted_2holes = readSortedStates()
                
                if complete_sorted_1hole and complete_sorted_2holes:
                    print("Energy sorted calculated states files are complete.")
                    print("Proceding while using this state list.")
                    
                    last_rad_calculated, last_aug_calculated, last_sat_calculated = readTransitions()
                    
                    if type(last_rad_calculated) != type(True):
                        print("\nRead last calculated radiative transition.")
                        
                        if last_rad_calculated[0] == calculated1holeStates[-1][0] and last_rad_calculated[1] == calculated1holeStates[-1][0]:
                            last_rad_calculated = True
                    else:
                        print("\nError reading last calculated radiative transition.")
                        print("Redoing this calculation from the start.")
                    if type(last_aug_calculated) != type(True):
                        print("\nRead last calculated auger transition.")
                        
                        if last_aug_calculated[0] == calculated1holeStates[-1][0] and last_aug_calculated[1] == calculated2holesStates[-1][0]:
                            last_aug_calculated = True
                    else:
                        print("\nError reading last calculated auger transition.")
                        print("Redoing this calculation from the start.")
                    if type(last_sat_calculated) != type(True):
                        print("\nRead last calculated satellite transition.")
                        
                        if last_sat_calculated[0] == calculated2holesStates[-1][0] and last_sat_calculated[1] == calculated2holesStates[-1][0]:
                            last_sat_calculated = True
                    else:
                        print("\nError reading last calculated satellite transition.")
                        print("Redoing this calculation from the start.")
                    
                    return last_rad_calculated, last_aug_calculated, last_sat_calculated
                else:
                    print("Error while reading the sorted states files.")
                    print("There was a missmatch between the length of sorted states and calculated states.")
                    print("Continuing with the full list of states and resorting them.")
                    
                    return 2
            
            return 0
        
        if os.path.isfile(file_sorted_1hole) and os.path.isfile(file_sorted_2holes):
            print("Found files with the sorted list of calculated states.")
            
            if os.path.isfile(file_cycle_log_1hole) and os.path.isfile(file_cycle_log_2holes):
                print("Found file with the list of discovered states.")
                complete_1hole, complete_2holes, last_calculated_cycle_1hole, last_calculated_state_1hole, last_calculated_cycle_2holes, last_calculated_state_2holes = readStateList()
                
                if complete_1hole and complete_2holes and last_calculated_cycle_1hole == 4 and last_calculated_cycle_2holes == 4 and last_calculated_state_1hole[0] == calculated1holeStates[-1][0] and last_calculated_state_2holes[0] == calculated2holesStates[-1][0]:
                    print("Verifyed that the file with the list of calculated states is consistent.")
                    print("Proceding with this list.")
                else:
                    print("Error while checking the file with calculated states.\n")
                    print("Flag -> Value ; Expected:")
                    print("Completed 1 hole              -> " + str(complete_1hole) + " ; True")
                    print("Completed 2 holes             -> " + str(complete_2holes) + " ; True")
                    print("Last calculated cycle 1 hole  -> " + str(last_calculated_cycle_1hole) + "    ; 4")
                    print("Last calculated cycle 2 holes -> " + str(last_calculated_cycle_2holes) + "    ; 4")
                    print("Last calculated state 1 hole  -> " + str(last_calculated_state_1hole[0]) + " ; " + calculated1holeStates[-1][0])
                    print("Last calculated state 2 holes -> " + str(last_calculated_state_2holes[0]) + " ; " + calculated2holesStates[-1][0])
                    
                    print("\nPicking up from the last calculated states...\n")
                    
                    return complete_1hole, complete_2holes, last_calculated_cycle_1hole, last_calculated_cycle_2holes, last_calculated_state_1hole[0], last_calculated_state_2holes[0]
                
            else:
                print("File with the list of discovered states is missing: ")
                print("1 hole states -> " + file_cycle_log_1hole)
                print("2 holes states -> " + file_cycle_log_2holes)
                print("\nReverting to full calculation...\n")
                
                return 1
            
            complete_sorted_1hole, complete_sorted_2holes = readSortedStates()
            
            if complete_sorted_1hole and complete_sorted_2holes:
                print("Energy sorted calculated states files are complete.")
                print("Proceding while using this state list.")
                
                return 3
            else:
                print("Error while reading the sorted states files.")
                print("There was a missmatch between the length of sorted states and calculated states.")
                print("Continuing with the full list of states and resorting them.")
                
                return 2
            
        
        if os.path.isfile(file_cycle_log_1hole) and os.path.isfile(file_cycle_log_2holes):
            print("Found file with the list of discovered states.")
            complete_1hole, complete_2holes, last_calculated_cycle_1hole, last_calculated_state_1hole, last_calculated_cycle_2holes, last_calculated_state_2holes = readStateList()
            
            if complete_1hole and complete_2holes and last_calculated_cycle_1hole == 4 and last_calculated_cycle_2holes == 4 and last_calculated_state_1hole[0] == calculated1holeStates[-1][0] and last_calculated_state_2holes[0] == calculated2holesStates[-1][0]:
                print("Verifyed that the file with the list of calculated states is consistent.")
                print("Proceding with this list.")
                
                return 0
            else:
                print("Error while checking the file with calculated states.\n")
                print("Flag -> Value ; Expected:")
                print("Completed 1 hole              -> " + str(complete_1hole) + " ; True")
                print("Completed 2 holes             -> " + str(complete_2holes) + " ; True")
                print("Last calculated cycle 1 hole  -> " + str(last_calculated_cycle_1hole) + "    ; 4")
                print("Last calculated cycle 2 holes -> " + str(last_calculated_cycle_2holes) + "    ; 4")
                print("Last calculated state 1 hole  -> " + str(last_calculated_state_1hole[0]) + " ; " + calculated1holeStates[-1][0])
                print("Last calculated state 2 holes -> " + str(last_calculated_state_2holes[0]) + " ; " + calculated2holesStates[-1][0])
                
                print("\nPicking up from the last calculated states...\n")
                
                return complete_1hole, complete_2holes, last_calculated_cycle_1hole, last_calculated_cycle_2holes, last_calculated_state_1hole[0], last_calculated_state_2holes[0]
        else:
            print("Files with the previously calculated states directories could not be found.")
            print("Please do a full calculation first.")
            sys.exit(1)


def checkOutput(currDir, currFileName):
    first = False
    firstOver = False
    
    Diff = 0.0
    
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
                Diff = round(float(outputContent[i + 1].split()[1]) - float(outputContent[i + 1].split()[2]), 6)
            
            if "Etot_(Welt.)=" in line:
                welt = float(line.strip().split()[3])
            
            if "For orbital" in line:
                failed_orbital = line.strip().split()[-1].strip()
    
    return first, failed_orbital, max(Overlaps), higher_config, highest_percent, accuracy, Diff, welt


def configureTransitionInputFile(f05RadTemplate_nuc, \
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
    


def configureStateInputFile(template, currDir, currFileName, config, jj, eigv, ne = nelectrons, failed_orbs = []):
    fileString = template \
                .replace("mcdfgmelabel", "Z=" + atomic_number + " " + config + " 2J=" + str(jj) + " neig=" + str(eigv)) \
                .replace("mcdfgmeatomicnumber", atomic_number) \
                .replace("mcdfgmeelectronnb", str(ne)) \
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
                log.write(', '.join(state_list[-1][0]) + "\n")
    else:
        for pl in range(len(parallel_paths) / parallel_max_paths):
            subprocess.check_output(['parallel -j' + number_of_threads + ' --bar ' + "'cd {//} && {/} && cd -'" + ' ::: ' + ' '.join(parallel_paths[(pl * parallel_max_paths):((pl + 1) * parallel_max_paths)])], shell=True)
            
            if log_file != '' and state_list != [] and log_line_header != '':
                with open(log_file, "a") as log:
                    if pl == 0:
                        log.write(log_line_header)
                    
                    log.write(', '.join(state_list[((pl + 1) * parallel_max_paths) - 1][0]) + "\n")
        
        
        subprocess.check_output(['parallel -j' + number_of_threads + ' --bar ' + "'cd {//} && {/} && cd -'" + ' ::: ' + ' '.join(parallel_paths[((pl + 1) * parallel_max_paths):])], shell=True)
        
        if log_file != '' and state_list != [] and log_line_header != '':
            with open(log_file, "a") as log:
                log.write(', '.join(state_list[-1][0]) + "\n")


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
                log.write(', '.join(state_list[-1][0]) + " => " + ', '.join(state_list[-1][1]) + "\n")
        
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
                    
                    log.write(', '.join(state_list[((pl + 1) * parallel_max_paths) - 1][0]) + " => " + ', '.join(state_list[((pl + 1) * parallel_max_paths) - 1][1]) + "\n")
            
            
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
                log.write(', '.join(state_list[-1][0]) + " => " + ', '.join(state_list[-1][1]) + "\n")
        
        
        # REMOVE THE .f09 WAVEFUNCTION FILES FOR THE LAST BATCH
        for wfi_dst, wff_dst in zip(parallel_initial_dst_paths[((pl + 1) * parallel_max_paths):], parallel_final_dst_paths[((pl + 1) * parallel_max_paths):]):
            os.remove(wfi_dst)
            os.remove(wff_dst)
        
    
    

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
            log_1hole.write("1 hole states discovery done.\nList of all calculated states:\n")
            for state in calculated1holeStates:
                log_1hole.write(', '.join(state[0]))
            
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
                if found_cycle1:
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
                if Diff >= diffThreshold or overlap >= overlapsThreshold:
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
                if found_cycle2:
                    i, jj, eigv = state[0]
                    
                    currDir = rootDir + "/" + directory_name + "/radiative/" + shell_array[i] + "/2jj_" + str(jj) + "/eigv_" + str(eigv)
                    currFileName = shell_array[i] + "_" + str(jj) + "_" + str(eigv)
                    
                    converged, failed_orbital, overlap, higher_config, highest_percent, accuracy, Diff, welt = checkOutput(currDir, currFileName)
                    
                    calculated1holeStates[counter].append((higher_config, highest_percent, overlap, accuracy, Diff, welt))
                    
                    if not converged:
                        # Only add this state to the calculation if we reached the starting state
                        if found_cycle2:
                            parallel_1hole_failed.append(currDir + "/" + exe_file)
                        
                        failed_first_cycle.append(counter)
                    else:
                        if Diff >= diffThreshold or overlap >= overlapsThreshold:
                            # Only add this state to the calculation if we reached the starting state
                            if found_cycle2:
                                parallel_1hole_failed.append(currDir + "/" + exe_file)
                            
                            failed_first_cycle.append(counter)
                
                counter += 1
                
                # Search for the starting state
                if state[0] == starting_state:
                    found_cycle2 = True
                    start_counter = counter
                
        
        # Execute parallel batch job with logging of calculated state
        executeBatchStateCalculation(parallel_1hole_failed, file_cycle_log_1hole, calculated1holeStates[start_counter:], "Second Cycle Last Calculated:\n")
    
    
    failed_second_cycle = []
    parallel_1hole_failed = []
    
    failed_orbs = []
    
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
            
            failed_orbs = ["    " + failed_orbital + "  1 5 0 1 :"]
            
            calculated1holeStates[counter][-1] = (higher_config, highest_percent, overlap, accuracy, Diff, welt, failed_orbs)
            
            if not converged:
                if failed_orbital != '':
                    configureStateInputFile(f05Template_10steps_Forbs_nuc, currDir, currFileName, configuration_1hole[i], jj, eigv, failed_orbs)
            
                    parallel_1hole_failed.append(currDir + "/" + exe_file)
                
                failed_second_cycle.append(counter)
            else:
                if Diff >= diffThreshold or overlap >= overlapsThreshold:
                    if failed_orbital != '':
                        configureStateInputFile(f05Template_10steps_nuc, currDir, currFileName, configuration_1hole[i], jj, eigv, failed_orbs)
            
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
                    if found_cycle3:
                        parallel_1hole_failed.append(currDir + "/" + exe_file)
                    
                    failed_second_cycle.append(counter)
                else:
                    if Diff >= diffThreshold or overlap >= overlapsThreshold:
                        # Only add this state to the calculation if we reached the starting state
                        if found_cycle3:
                            parallel_1hole_failed.append(currDir + "/" + exe_file)
                        
                        failed_second_cycle.append(counter)
                
                counter += 1
                
                if state[0] == starting_state:
                    found_cycle3 = True
                    start_counter = counter
                
        
        # Execute parallel batch job with logging of calculated state
        executeBatchStateCalculation(parallel_1hole_failed, file_cycle_log_1hole, calculated1holeStates[start_counter:], "Third Cycle Last Calculated:\n")
    
    
    failed_third_cycle = []
    parallel_1hole_failed = []
    
    failed_orbs = []
    
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
            
            failed_orbs = calculated1holeStates[counter][1][5]
            
            if failed_orbital != '':
                failed_orbs.append("    " + failed_orbital + "  1 5 0 1 :")
            
            
            if not converged:
                if failed_orbs[0] != "      1 5 0 1 :" and len(failed_orbs) == 2:
                    configureStateInputFile(f05Template_10steps_nuc, currDir, currFileName, configuration_1hole[i], jj, eigv, failed_orbs)
            
                    parallel_1hole_failed.append(currDir + "/" + exe_file)
                elif len(failed_orbs) == 2:
                    del failed_orbs[0]
                    
                    configureStateInputFile(f05Template_10steps_nuc, currDir, currFileName, configuration_1hole[i], jj, eigv, failed_orbs)
            
                    parallel_1hole_failed.append(currDir + "/" + exe_file)
                
                failed_third_cycle.append(counter)
            else:
                if Diff >= diffThreshold or overlap >= overlapsThreshold:
                    if failed_orbs[0] != "      1 5 0 1 :" and len(failed_orbs) == 2:
                        configureStateInputFile(f05Template_10steps_nuc, currDir, currFileName, configuration_1hole[i], jj, eigv, failed_orbs)
            
                        parallel_1hole_failed.append(currDir + "/" + exe_file)
                    elif len(failed_orbs) == 2:
                        del failed_orbs[0]
                        
                        configureStateInputFile(f05Template_10steps_nuc, currDir, currFileName, configuration_1hole[i], jj, eigv, failed_orbs)
            
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
                if found_cycle4:
                    parallel_1hole_failed.append(currDir + "/" + exe_file)
                
                failed_third_cycle.append(counter)
            else:
                if Diff >= diffThreshold or overlap >= overlapsThreshold:
                    # Only add this state to the calculation if we reached the starting state
                    if found_cycle4:
                        parallel_1hole_failed.append(currDir + "/" + exe_file)
                    
                    failed_third_cycle.append(counter)
            
            counter += 1
            
            if state[0] == starting_state:
                found_cycle4 = True
                start_counter = counter
            
    
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
            if Diff >= diffThreshold or overlap >= overlapsThreshold:
                radiative_by_hand.append(counter)
    
    
    # -------------- WRITE RESULTS TO THE FILES -------------- #
    
    with open(file_results, "a") as resultDump:
        with open(file_final_results_1hole, "a") as stateResults_1hole:
            with open(file_final_results, "a") as stateResults:
                resultDump.write("Fourth Cycle 1 Hole states\nShell, Shell index, 2J, Eigv, Higher Configuration, Percentage, Overlap, Accuracy, Energy Difference, Energy Welton\n")
                stateResults_1hole.write("Calculated 1 Hole states\nShell, Shell index, 2J, Eigv, Higher Configuration, Percentage, Overlap, Accuracy, Energy Difference, Energy Welton\n")
                stateResults.write("Calculated 1 Hole states\nShell, Shell index, 2J, Eigv, Higher Configuration, Percentage, Overlap, Accuracy, Energy Difference, Energy Welton\n")
                for state in calculated1holeStates:
                    resultDump.write(shell_array[state[0][0]] + ", " + str(state[0][0]) + ", " + str(state[0][1]) + ", " + str(state[0][2]) + ", " + state[1][0] + ", " + str(state[1][1]) + ", " + str(state[1][2]) + ", " + str(state[1][3]) + ", " + str(state[1][4]) + ", " + str(state[1][5]) + "\n")
                    stateResults_1hole.write(shell_array[state[0][0]] + ", " + str(state[0][0]) + ", " + str(state[0][1]) + ", " + str(state[0][2]) + ", " + state[1][0] + ", " + str(state[1][1]) + ", " + str(state[1][2]) + ", " + str(state[1][3]) + ", " + str(state[1][4]) + ", " + str(state[1][5]) + "\n")
                    stateResults.write(shell_array[state[0][0]] + ", " + str(state[0][0]) + ", " + str(state[0][1]) + ", " + str(state[0][2]) + ", " + state[1][0] + ", " + str(state[1][1]) + ", " + str(state[1][2]) + ", " + str(state[1][3]) + ", " + str(state[1][4]) + ", " + str(state[1][5]) + "\n")
                
                stateResults_1hole.write("1 Hole by Hand\n")
                stateResults.write("1 Hole by Hand\n")
                for counter in radiative_by_hand:
                    stateResults_1hole.write(shell_array[calculated1holeStates[counter][0][0]] + ", " + str(calculated1holeStates[counter][0][0]) + ", " + str(calculated1holeStates[counter][0][1]) + ", " + str(calculated1holeStates[counter][0][2]) + ", " + calculated1holeStates[counter][1][0] + ", " + str(calculated1holeStates[counter][1][1]) + ", " + str(calculated1holeStates[counter][1][2]) + ", " + str(calculated1holeStates[counter][1][3]) + ", " + str(calculated1holeStates[counter][1][4]) + ", " + str(calculated1holeStates[counter][1][5]) + "\n")
                    stateResults.write(shell_array[calculated1holeStates[counter][0][0]] + ", " + str(calculated1holeStates[counter][0][0]) + ", " + str(calculated1holeStates[counter][0][1]) + ", " + str(calculated1holeStates[counter][0][2]) + ", " + calculated1holeStates[counter][1][0] + ", " + str(calculated1holeStates[counter][1][1]) + ", " + str(calculated1holeStates[counter][1][2]) + ", " + str(calculated1holeStates[counter][1][3]) + ", " + str(calculated1holeStates[counter][1][4]) + ", " + str(calculated1holeStates[counter][1][5]) + "\n")
    
    

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
            
            configureStateInputFile(f05Template_nuc, currDir, currFileName, configuration_2holes[i], "100" if int(nelectrons) - 1 % 2 == 0 else "101", "100", int(nelectrons) - 1)
            
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
                
                configureStateInputFile(f05Template_nuc, currDir, currFileName, configuration_2holes[i], jj, "100", int(nelectrons) - 1)
            
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
                
                configureStateInputFile(f05Template_nuc, currDir, currFileName, configuration_2holes[i], jj, eigv, int(nelectrons) - 1)
                
                parallel_2holes_paths.append(currDir + "/" + exe_file)
            
        
        with open(file_cycle_log_2holes, "a") as log_2holes:
            log_2holes.write("2 holes states discovery done.\nList of all calculated states:\n")
            for state in calculated2holesStates:
                log_2holes.write(', '.join(state[0]))
            
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
                if found_cycle1:
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
                
                configureStateInputFile(f05Template_10steps_nuc, currDir, currFileName, configuration_2holes[i], jj, eigv, int(nelectrons) - 1)
            
                parallel_2holes_failed.append(currDir + "/" + exe_file)
                failed_first_cycle.append(counter)
            else:
                if Diff >= diffThreshold or overlap >= overlapsThreshold:
                    configureStateInputFile(f05Template_10steps_nuc, currDir, currFileName, configuration_2holes[i], jj, eigv, int(nelectrons) - 1)
            
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
                if found_cycle2:
                    i, jj, eigv = state[0]
                    
                    currDir = rootDir + "/" + directory_name + "/auger/" + shell_array_2holes[i] + "/2jj_" + str(jj) + "/eigv_" + str(eigv)
                    currFileName = shell_array_2holes[i] + "_" + str(jj) + "_" + str(eigv)
                    
                    converged, failed_orbital, overlap, higher_config, highest_percent, accuracy, Diff, welt = checkOutput(currDir, currFileName)
                    
                    calculated1holeStates[counter].append((higher_config, highest_percent, overlap, accuracy, Diff, welt))
                    
                    if not converged:
                        # Only add this state to the calculation if we reached the starting state
                        if found_cycle2:
                            parallel_2holes_failed.append(currDir + "/" + exe_file)
                        
                        failed_first_cycle.append(counter)
                    else:
                        if Diff >= diffThreshold or overlap >= overlapsThreshold:
                            # Only add this state to the calculation if we reached the starting state
                            if found_cycle2:
                                parallel_2holes_failed.append(currDir + "/" + exe_file)
                            
                            failed_first_cycle.append(counter)
                
                counter += 1
                
                # Search for the starting state
                if state[0] == starting_state:
                    found_cycle2 = True
                    start_counter = counter
                
        
        # Execute parallel batch job with logging of calculated state
        executeBatchStateCalculation(parallel_2holes_failed, file_cycle_log_2holes, calculated2holesStates[start_counter:], "Second Cycle Last Calculated:\n")
    
    
    failed_second_cycle = []
    parallel_2holes_failed = []
    
    failed_orbs = []
    
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
            
            failed_orbs = ["    " + failed_orbital + "  1 5 0 1 :"]
            
            
            calculated2holesStates[counter][-1] = (higher_config, highest_percent, overlap, accuracy, Diff, welt, failed_orbs)
            
            if not converged:
                if failed_orbital != '':
                    configureStateInputFile(f05Template_10steps_Forbs_nuc, currDir, currFileName, configuration_2holes[i], jj, eigv, int(nelectrons) - 1, failed_orbs)
                
                    parallel_2holes_failed.append(currDir + "/" + exe_file)
                
                failed_second_cycle.append(counter)
            else:
                if Diff >= diffThreshold or overlap >= overlapsThreshold:
                    if failed_orbital != '':
                        configureStateInputFile(f05Template_10steps_nuc, currDir, currFileName, configuration_2holes[i], jj, eigv, int(nelectrons) - 1, failed_orbs)
            
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
                    if found_cycle3:
                        parallel_2holes_failed.append(currDir + "/" + exe_file)
                    
                    failed_second_cycle.append(counter)
                else:
                    if Diff >= diffThreshold or overlap >= overlapsThreshold:
                        # Only add this state to the calculation if we reached the starting state
                        if found_cycle3:
                            parallel_2holes_failed.append(currDir + "/" + exe_file)
                        
                        failed_second_cycle.append(counter)
                
                counter += 1
                
                if state[0] == starting_state:
                    found_cycle3 = True
                    start_counter = counter
                
        
        # Execute parallel batch job with logging of calculated state
        executeBatchStateCalculation(parallel_2holes_failed, file_cycle_log_2holes, calculated2holesStates, "Third Cycle Last Calculated:\n")
    
    
    failed_third_cycle = []
    parallel_2holes_failed = []
    
    failed_orbs = []
    
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
            
            failed_orbs = calculated2holesStates[counter][1][5]
            
            if failed_orbital != '':
                failed_orbs.append("    " + failed_orbital + "  1 5 0 1 :")
            
            
            if not converged:
                if failed_orbs[0] != "      1 5 0 1 :" and len(failed_orbs) == 2:
                    configureStateInputFile(f05Template_10steps_nuc, currDir, currFileName, configuration_2holes[i], jj, eigv, int(nelectrons) - 1, failed_orbs)
            
                    parallel_2holes_failed.append(currDir + "/" + exe_file)
                elif len(failed_orbs) == 2:
                    del failed_orbs[0]
                    
                    configureStateInputFile(f05Template_10steps_nuc, currDir, currFileName, configuration_2holes[i], jj, eigv, int(nelectrons) - 1, failed_orbs)
            
                    parallel_2holes_failed.append(currDir + "/" + exe_file)
                
                failed_third_cycle.append(counter)
            else:
                if Diff >= diffThreshold or overlap >= overlapsThreshold:
                    if failed_orbs[0] != "      1 5 0 1 :" and len(failed_orbs) == 2:
                        configureStateInputFile(f05Template_10steps_nuc, currDir, currFileName, configuration_2holes[i], jj, eigv, int(nelectrons) - 1, failed_orbs)
            
                        parallel_2holes_failed.append(currDir + "/" + exe_file)
                    elif len(failed_orbs) == 2:
                        del failed_orbs[0]
                        
                        configureStateInputFile(f05Template_10steps_nuc, currDir, currFileName, configuration_2holes[i], jj, eigv, int(nelectrons) - 1, failed_orbs)
            
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
                if found_cycle4:
                    parallel_2holes_failed.append(currDir + "/" + exe_file)
                
                failed_third_cycle.append(counter)
            else:
                if Diff >= diffThreshold or overlap >= overlapsThreshold:
                    # Only add this state to the calculation if we reached the starting state
                    if found_cycle4:
                        parallel_2holes_failed.append(currDir + "/" + exe_file)
                    
                    failed_third_cycle.append(counter)
            
            counter += 1
            
            if state[0] == starting_state:
                found_cycle4 = True
                start_counter = counter
            
    
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
            if Diff >= diffThreshold or overlap > overlapsThreshold:
                auger_by_hand.append(counter)
    
    
    # -------------- WRITE RESULTS TO THE FILES -------------- #
    
    with open(file_results, "a") as resultDump:
        with open(file_final_results_2holes, "a") as stateResults_2holes:
            with open(file_final_results, "a") as stateResults:
                resultDump.write("Fourth Cycle 2 Hole states\nShell, Shell index, 2J, Eigv, Higher Configuration, Percentage, Overlap, Accuracy, Energy Difference, Energy Welton\n")
                stateResults_2holes.write("Calculated 2 Hole states\nShell, Shell index, 2J, Eigv, Higher Configuration, Percentage, Overlap, Accuracy, Energy Difference, Energy Welton\n")
                stateResults.write("Calculated 2 Hole states\nShell, Shell index, 2J, Eigv, Higher Configuration, Percentage, Overlap, Accuracy, Energy Difference, Energy Welton\n")
                for state in calculated2holesStates:
                    resultDump.write(shell_array_2holes[state[0][0]] + ", " + str(state[0][0]) + ", " + str(state[0][1]) + ", " + str(state[0][2]) + ", " + state[1][0] + ", " + str(state[1][1]) + ", " + str(state[1][2]) + ", " + str(state[1][3]) + ", " + str(state[1][4]) + ", " + str(state[1][5]) + "\n")
                    stateResults_2holes.write(shell_array_2holes[state[0][0]] + ", " + str(state[0][0]) + ", " + str(state[0][1]) + ", " + str(state[0][2]) + ", " + state[1][0] + ", " + str(state[1][1]) + ", " + str(state[1][2]) + ", " + str(state[1][3]) + ", " + str(state[1][4]) + ", " + str(state[1][5]) + "\n")
                    stateResults.write(shell_array_2holes[state[0][0]] + ", " + str(state[0][0]) + ", " + str(state[0][1]) + ", " + str(state[0][2]) + ", " + state[1][0] + ", " + str(state[1][1]) + ", " + str(state[1][2]) + ", " + str(state[1][3]) + ", " + str(state[1][4]) + ", " + str(state[1][5]) + "\n")
                
                stateResults_2holes.write("2 Hole by Hand\n")
                stateResults.write("2 Hole by Hand\n")
                for counter in auger_by_hand:
                    stateResults_2holes.write(shell_array_2holes[calculated2holesStates[counter][0][0]] + ", " + str(calculated2holesStates[counter][0][0]) + ", " + str(calculated2holesStates[counter][0][1]) + ", " + str(calculated2holesStates[counter][0][2]) + ", " + calculated2holesStates[counter][1][0] + ", " + str(calculated2holesStates[counter][1][1]) + ", " + str(calculated2holesStates[counter][1][2]) + ", " + str(calculated2holesStates[counter][1][3]) + ", " + str(calculated2holesStates[counter][1][4]) + "\n")
                    stateResults.write(shell_array_2holes[calculated2holesStates[counter][0][0]] + ", " + str(calculated2holesStates[counter][0][0]) + ", " + str(calculated2holesStates[counter][0][1]) + ", " + str(calculated2holesStates[counter][0][2]) + ", " + calculated2holesStates[counter][1][0] + ", " + str(calculated2holesStates[counter][1][1]) + ", " + str(calculated2holesStates[counter][1][2]) + ", " + str(calculated2holesStates[counter][1][3]) + ", " + str(calculated2holesStates[counter][1][4]) + "\n")
    

def sortCalculatedStates():
    global calculated1holeStates, calculated2holesStates
    
    
    calculated1holeStates.sort(key = lambda x: x[1][-1])
    
    with open(file_sorted_1hole, "w") as sorted_1hole:
        for state in calculated1holeStates:
            sorted_1hole.write(', '.join(state[0]) + "; " + str(state[1][0]) + ", " + str(state[1][1]) + ", " + str(state[1][2]) + ", " + str(state[1][3]) + ", " + str(state[1][4]) + ", " + str(state[1][5]) + "\n")
    
    
    calculated2holesStates.sort(key = lambda x: x[1][-1])
    
    with open(file_sorted_2holes, "w") as sorted_2holes:
        for state in calculated2holesStates:
            sorted_2holes.write(', '.join(state[0]) + "; " + str(state[1][0]) + ", " + str(state[1][1]) + ", " + str(state[1][2]) + ", " + str(state[1][3]) + ", " + str(state[1][4]) + ", " + str(state[1][5]) + "\n")



def readTransition(currDir, currFileName, radiative = True):
    energy = ''
    rate = ''
    
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
                    while True:
                        cnt = i + 3
                        
                        if outputContent[cnt] == "\n":
                            break
                        else "s-1" in outputContent[cnt]:
                            vals = outputContent[cnt].strip().split()
                            multipoles.append([vals[0], vals[1]])
            
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
    for counter, state_i in enumerate(calculated1holeStates):
        for state_f in calculated1holeStates[counter:]:
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
                
                parallel_initial_dst_paths.append(currDir_i + "/" + wfiFile + ".f09")
                parallel_final_dst_paths.append(currDir_f + "/" + wffFile + ".f09")
                
                parallel_transition_paths.append(currDir + "/" + exe_file)
            
            combCnt += 1
            
            if [state_i[0], state_f[0]] == starting_transition:
                found_starting = True
    
    
    executeBatchTransitionCalculation(parallel_transition_paths, \
                                    parallel_initial_src_paths, parallel_final_src_paths, \
                                    parallel_initial_dst_paths, parallel_final_dst_paths, \
                                    file_calculated_radiative, calculatedRadiativeTransitions, "Calculated transitions:\n")
    
    
    energies = []
    rates = []
    multipole_array = []
    
    total_rates = []
    
    combCnt = 0
    for counter, state_i in enumerate(calculated1holeStates):
        total_rates.append(0.0)
        
        for state_f in calculated1holeStates[counter:]:
            i, jj_i, eigv_i = state_i[0]
            f, jj_f, eigv_f = state_f[0]
            
            currDir = rootDir + "/" + directory_name + "/transitions/radiative/" + str(combCnt)
            currFileName = str(combCnt)
            
            energy, rate, multipoles = readTransition(currDir, currFileName)
            
            total_rates[counter] += float(rate)
            
            energies.append(energy)
            rates.append(rate)
            multipole_array.append(multipoles)
            
            combCnt += 1
    
    
    # -------------- WRITE RESULTS TO THE FILES -------------- #
    
    with open(file_rates, "a") as rad_rates:
        rad_rates.write("Calculated Radiative Transitions\nTransition register\tShell IS\tIS Configuration\tIS 2JJ\tIS eigenvalue\tIS higher configuration\tIS percentage\tShell FS\tFS Configuration\tFS 2JJ\tFS eigenvalue\tFS higher configuration\tFS percentage\ttransition energy [eV]\trate [s-1]\tnumber multipoles\ttotal rate from IS\tbranching ratio\n")
        combCnt = 0
        for counter, state_i in enumerate(calculated1holeStates):
            for state_f in calculated1holeStates[counter:]:
                i, jj_i, eigv_i = state_i[0]
                f, jj_f, eigv_f = state_f[0]
                
                calculatedRadiativeTransitions[combCnt].append((energies[combCnt], rates[combCnt], total_rates[combCnt], multipole_array[combCnt]))
                
                rad_rates.write(str(combCnt) + "\t" + \
                                shell_array[i] + "\t" + \
                                configuration_1hole[i] + "\t" + \
                                str(jj_i) + "\t" + \
                                str(eigv_i) + "\t" + \
                                state_i[1][0] + "\t" + \
                                state_i[1][1] + "\t" + \
                                shell_array[f] + "\t" + \
                                configuration_1hole[f] + "\t" + \
                                str(jj_f) + "\t" + \
                                str(eigv_f) + "\t" + \
                                state_f[1][0] + "\t" + \
                                state_f[1][1] + "\t" + \
                                energies[combCnt] + "\t" + \
                                rates[combCnt] + "\t" + \
                                str(len(multipole_array[combCnt])) + "\t" + \
                                str(total_rates[counter]) + "\t" + \
                                (str(float(rate) / total_rates[counter]) if total_rates[counter] != 0.0 else "0.0") + "\t" + \
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
                
                parallel_initial_dst_paths.append(currDir_i + "/" + wfiFile + ".f09")
                parallel_final_dst_paths.append(currDir_f + "/" + wffFile + ".f09")
                
                parallel_transition_paths.append(currDir + "/" + exe_file)
            
            combCnt += 1
            
            if [state_i[0], state_f[0]] == starting_transition:
                found_starting = True
    
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
    
    with open(file_rates_auger, "a") as aug_rates:
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
                
                calculatedAugerTransitions[combCnt].append((energies[combCnt], rates[combCnt], total_rates[combCnt]))
                
                aug_rates.write(str(combCnt) + "\t" + \
                                shell_array[i] + "\t" + \
                                configuration_1hole[i] + "\t" + \
                                str(jj_i) + "\t" + \
                                str(eigv_i) + "\t" + \
                                state_i[1][0] + "\t" + \
                                state_i[1][1] + "\t" + \
                                shell_array[f] + "\t" + \
                                configuration_2holes[f] + "\t" + \
                                str(jj_f) + "\t" + \
                                str(eigv_f) + "\t" + \
                                state_f[1][0] + "\t" + \
                                state_f[1][1] + "\t" + \
                                energies[combCnt] + "\t" + \
                                rates[combCnt] + "\t" + \
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
    for counter, state_i in enumerate(calculated2holesStates):
        for state_f in calculated2holesStates[counter:]:
            i, jj_i, eigv_i = state_i[0]
            f, jj_f, eigv_f = state_f[0]
            
            calculatedSatelliteTransitions.append([(i, jj_i, eigv_i), (f, jj_f, eigv_f)])
            
            if starting_transition == [(0, 0, 0), (0, 0, 0)] or found_starting:
                currDir = rootDir + "/" + directory_name + "/transitions/satellites/" + str(combCnt)
                currFileName = str(combCnt)
                
                currDir_i = rootDir + "/" + directory_name + "/auger/" + shell_array[i] + "/2jj_" + str(jj_i) + "/eigv_" + str(eigv_i)
                currFileName_i = shell_array[i] + "_" + str(jj_i) + "_" + str(eigv_i)
                
                currDir_f = rootDir + "/" + directory_name + "/auger/" + shell_array[f] + "/2jj_" + str(jj_f) + "/eigv_" + str(eigv_f)
                currFileName_f = shell_array[f] + "_" + str(jj_f) + "_" + str(eigv_f)
                
                wfiFile, wffFile = configureTransitionInputFile(f05RadTemplate_nuc, \
                                                                currDir, currFileName, \
                                                                currDir_i, currFileName_i, \
                                                                configuration_2holes[i], jj_i, eigv_i, str(int(nelectrons) - 1), \
                                                                currDir_f, currFileName_f, \
                                                                configuration_2holes[f], jj_f, eigv_f, str(int(nelectrons) - 1))
                
                parallel_initial_src_paths.append(currDir_i + "/" + currFileName_i + ".f09")
                parallel_final_src_paths.append(currDir_f + "/" + currFileName_f + ".f09")
                
                parallel_initial_dst_paths.append(currDir_i + "/" + wfiFile + ".f09")
                parallel_final_dst_paths.append(currDir_f + "/" + wffFile + ".f09")
                
                parallel_transition_paths.append(currDir + "/" + exe_file)
            
            combCnt += 1
            
            if [state_i[0], state_f[0]] == starting_transition:
                found_starting = True
    
    executeBatchTransitionCalculation(parallel_transition_paths, \
                                    parallel_initial_src_paths, parallel_final_src_paths, \
                                    parallel_initial_dst_paths, parallel_final_dst_paths, \
                                    file_calculated_sat, calculatedSatelliteTransitions, "Calculated transitions:\n")
    
    
    energies = []
    rates = []
    multipole_array = []
    
    total_rates = []
    
    combCnt = 0
    for counter, state_i in enumerate(calculated2holesStates):
        total_rates.append(0.0)
        
        for state_f in calculated2holesStates[counter:]:
            i, jj_i, eigv_i = state_i[0]
            f, jj_f, eigv_f = state_f[0]
            
            currDir = rootDir + "/" + directory_name + "/transitions/satellites/" + str(combCnt)
            currFileName = str(combCnt)
            
            energy, rate, multipoles = readTransition(currDir, currFileName)
            
            total_rates[counter] += float(rate)
            
            energies.append(energy)
            rates.append(rate)
            multipole_array.append(multipoles)
            
            combCnt += 1
    
    
    # -------------- WRITE RESULTS TO THE FILES -------------- #
    
    with open(file_rates_satellites, "a") as sat_rates:
        sat_rates.write("Calculated Satellite Transitions\nTransition register\tShell IS\tIS Configuration\tIS 2JJ\tIS eigenvalue\tIS higher configuration\tIS percentage\tShell FS\tFS Configuration\tFS 2JJ\tFS eigenvalue\tFS higher configuration\tFS percentage\ttransition energy [eV]\trate [s-1]\tnumber multipoles\ttotal rate from IS\tbranching ratio\n")
        combCnt = 0
        for counter, state_i in enumerate(calculated2holesStates):
            for state_f in calculated2holesStates[counter:]:
                i, jj_i, eigv_i = state_i[0]
                f, jj_f, eigv_f = state_f[0]
                
                calculatedSatelliteTransitions[combCnt].append((energies[combCnt], rates[combCnt], total_rates[combCnt], multipole_array[combCnt]))
                
                sat_rates.write(str(combCnt) + "\t" + \
                                shell_array[i] + "\t" + \
                                configuration_2holes[i] + "\t" + \
                                str(jj_i) + "\t" + \
                                str(eigv_i) + "\t" + \
                                state_i[1][0] + "\t" + \
                                state_i[1][1] + "\t" + \
                                shell_array[f] + "\t" + \
                                configuration_2holes[f] + "\t" + \
                                str(jj_f) + "\t" + \
                                str(eigv_f) + "\t" + \
                                state_f[1][0] + "\t" + \
                                state_f[1][1] + "\t" + \
                                energies[combCnt] + "\t" + \
                                rates[combCnt] + "\t" + \
                                str(len(multipole_array[combCnt])) + "\t" + \
                                str(total_rates[counter]) + "\t" + \
                                (str(float(rate) / total_rates[counter]) if total_rates[counter] != 0.0 else "0.0") + "\t" + \
                                '\t'.join(['\t'.join(pole) for pole in multipole_array[combCnt]]) + "\n")
                
                combCnt += 1



def calculateSpectra(radiative_done, auger_done, satellite_done):
    print("############ Calculating the sums ###################")
    

    print("number of vacancy configurations == " + len(shell_array) + "\n")
    print("type of vacancy == " + ', '.join(shell_array) + "\n")
	
	
    multiplicity_JJ = [0] * len(shell_array)
    
    radiative_rate_per_shell = [0.0] * len(shell_array)
    
    auger_rate_per_shell = [0.0] * len(shell_array_2holes)
    
    print("\nCalculating shell rates and multiplicities for diagram and auger...\n")
    
    for transition in calculatedRadiativeTransitions:
        state_i, state_f, pars = transition
        
        multiplicity_JJ[state_i[0]] += state_i[1] + 1
        
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
    
    
    
    print("JJ multiplicity/shell == " + ', '.join(multiplicity_JJ) + "\n")


    print("\nCalculating shell rates and multiplicities for satellites...\n")
    
    multiplicity_JJ_sat = [0] * len(shell_array_2holes)
    
    radiative_rate_per_shell_sat = [0.0] * len(shell_array_2holes)

    for transition in calculatedSatelliteTransitions:
        state_i, state_f, pars = transition
        
        multiplicity_JJ_sat[state_i[0]] += state_i[1] + 1
        
        radiative_rate_per_shell_sat[state_i[0]] += float(pars[1]) * (state_i[1] + 1)
    
    
    with open(file_rates_sums_sat, "w") as rates_sums_sat:
        for k in range(len(shell_array_2holes)):
            rates_sums_sat.write(shell_array_2holes[k] + "\n")
            rates_sums_sat.write("multiplicity of states = " + str(multiplicity_JJ_sat[k]) + "\n")
            rates_sums_sat.write("radiative * multiplicity of states = " + str(radiative_rate_per_shell_sat[k]) + "\n")
            rates_sums_sat.write("\n\n")
	
	
	print("JJ multiplicity/shell sat == " + ', '.join(multiplicity_JJ_sat) + "\n")
	

    print("\nCalculating total level widths for diagram, auger and satellite transitions...\n")
    
    rate_level_radiative = dict.fromkeys(calculated1holeStates[:][0], 0.0)
    rate_level_auger = dict.fromkeys(calculated1holeStates[:][0], 0.0)
    rate_level_radiative_sat = dict.fromkeys(calculated2holesStates[:][0], 0.0)
    
    rate_level = dict.fromkeys(calculated1holeStates[:][0], 0.0)
    rate_level_ev = dict.fromkeys(calculated1holeStates[:][0], 0.0)
    
    for transition in calculatedRadiativeTransitions:
        state_i, state_f, pars = transition
        
        rate_level_radiative[state_i] += float(pars[1])
	
    for transition in calculatedAugerTransitions:
        state_i, state_f, pars = transition
        
        rate_level_auger[state_i] += float(pars[1])
        
        
        rate_level[state_i] = rate_level_radiative[state_i] + rate_level_auger[state_i]
        rate_level_ev[state_i] = rate_level[state_i] * hbar
    
    
    fluor_sat = {}
    shell_fl_dia = {}
    rate_level_sat = {}
    rate_level_sat_ev = {}
    
    
    for transition in calculatedSatelliteTransitions:
        state_i, state_f, pars = transition
        
        rate_level_radiative_sat[state_i] += float(pars[1])
    
    for transition in calculatedSatelliteTransitions:
        state_i, state_f, pars = transition
        
        shell_sat = shell_array_2holes[state_i[0]].split("_")
        print(" shell 2 holes =  " + shell_array_2holes[state_i[0]] + "\n")
        
        print(" shell 2 holes divided 1 = " + shell_sat[0] + "     2 = " + shell_sat[1] + "\n")
    
    
        k = shell_array.index(shell_sat[0])
        fluor_sat[state_i] = fluorescenceyield[k]
        shell_fl_dia[state_i] = shell_array[k]
        
        rate_level_sat[state_i] = rate_level_radiative_sat[state_i] / fluorescenceyield[k]
        
        rate_level_sat_ev[state_i] = rate_level_sat[state_i] * hbar
    
    
    
    with open(file_level_widths, "w") as level_widths:
        level_widths.write(" Transition register \t  Shell \t Configuration \t 2JJ \t eigenvalue \t radiative width [s-1] \t  auger width [s-1] \t total width [s-1] \t total width [eV] \n")
        
        for counter, state_i in enumerate(rate_level):
            i, jj_i, eigv_i = state_i

            print("\nLevel " + str(counter) + " :  " + shell_array[i] + " " + configuration_1hole[i] + " 2J=" + str(jj_i) + " neig=" + str(eigv_i) + "\n")
            print("\tradiative width = " + str(rate_level_radiative[state_i]) + " s-1 \t auger width = " + str(rate_level_auger[state_i]) + " s-1 \t total width = " + str(rate_level[state_i]) + " s-1 \t total width (eV) = " + str(rate_level_ev[state_i]) + " eV \n")
            
            level_widths.write(str(counter) + " \t " + \
                               shell_array[i] + " \t " + \
                               configuration_1hole[i] + " \t " + \
                               str(jj_i) + " \t " + \
                               str(eigv_i) + " \t " + \
                               str(rate_level_radiative[state_i]) + " \t " + \
                               str(rate_level_auger[state_i]) + " \t " + \
                               str(rate_level[state_i]) + " \t " + \
                               str(rate_level_ev[state_i]) + "\n")



    with open(file_level_widths_sat, "w") as level_widths_sat:
        level_widths_sat.write(" Transition register \t index sorted \t  Shell \t Configuration \t 2JJ \t eigenvalue \t radiative width [s-1] \t  total width [s-1] \t total width [eV] \n")
        
        for counter, state_i in enumerate(rate_level_sat):
            i, jj_i, eigv_i = state_i
            
            print("\nLevel " + str(counter) + " :  " + shell_array_2holes[i] + " " + configuration_2holes[i] + " 2J=" + str(jj_i) + " neig=" + str(eigv_i) + "\n")
            print("\tradiative width = " + str(rate_level_radiative_sat[state_i]) + " s-1 \t total width = " + str(rate_level_sat[state_i]) + " s-1 \t total width (eV) = " + str(rate_level_sat_ev[state_i]) + " eV \n")
            
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
        for counter, state_i in enumerate(calculated1holeStates):
            for state_f in calculated1holeStates[counter:]:
                i, jj_i, eigv_i = state_i[0]
                f, jj_f, eigv_f = state_f[0]
                
                
                inten_trans.append(((jj_i + 1) / multiplicity_JJ[i]) * (float(calculatedRadiativeTransitions[combCnt][2][1]) / rate_level[state_i[0]]))
                intensity_ev.append(inten_trans[-1] * float(calculatedRadiativeTransitions[combCnt][2][0]))
                transition_width.append(rate_level_ev[state_i[0]] + rate_level_ev[state_f[0]])

                print("\ntransition " + str(combCnt) + " : from " + configuration_1hole[i] + " 2J=" + str(jj_i) + " neig=" + str(eigv_i) + " -> " + configuration_1hole[f] + " 2J=" + str(jj_f) + " neig=" + str(eigv_f) + " = " + str(calculatedRadiativeTransitions[combCnt][2][1]) + " s-1  Energy = " + str(calculatedRadiativeTransitions[combCnt][2][0]) + " eV\n")
                print(" Width = initial state (" + str(rate_level_ev[state_i[0]]) + " eV) + final state (" + str(rate_level_ev[state_f[0]]) + " eV) = " + str(transition_width[-1]) + " eV\n")

                print(" Intensity =  " + str(inten_trans[-1]) + "\n")
                print(str(jj_i) + " \t " + str(calculatedRadiativeTransitions[combCnt][2][1]) + " \t " + str(multiplicity_JJ[i]) + " \t " + str(rate_level[state_i[0]]) + "\n")
                
                spectrum_diagram.write(str(combCnt) + " \t " + \
                                       shell_array[i] + " \t " + \
                                       configuration_1hole[i] + " \t " + \
                                       str(jj_i) + " \t " + \
                                       str(eigv_i) + " \t " + \
                                       state_i[1][0] + " \t " + \
                                       state_i[1][1] + " \t " + \
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
                
                inten_auger.append(((jj_i + 1) / multiplicity_JJ[i]) * (float(calculatedAugerTransitions[combCnt][2][1]) / rate_level[state_i[0]]))
                intensity_auger_ev.append(inten_auger[-1] * float(calculatedAugerTransitions[combCnt][2][0]))
                transition_width_auger.append(rate_level_ev[state_i[0]] + rate_level_sat_ev[state_f[0]])


                print(str(combCnt) + " \t " + shell_array[i] + " \t " + configuration_1hole[i] + " \t " + str(jj_i) + " \t " + str(eigv_i) + " \t " + configuration_2holes[f] + " \t " + str(jj_f) + " \t " + str(eigv_f) + " \t " + str(calculatedAugerTransitions[combCnt][2][0]) + " \t " + str(inten_auger[-1]) + " \t " + str(intensity_auger_ev[-1]) + " \t " + str(transition_width_auger[-1]) + "\n")

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
    
    with open(file_rates_spectrum_sat, "w") as spectrum_sat:
        spectrum_sat.write("Transition register \t Shell IS \t IS Configuration \t IS 2JJ \t IS eigenvalue \t IS higher configuration \t IS percentage \t Shell FS \tFS Configuration \t FS 2JJ \t FS eigenvalue \t FS higher configuration \t FS percentage \t transition energy [eV] \t intensity \t intensity [eV] \t width [eV] \n")
	
        combCnt = 0
        for counter, state_i in enumerate(calculated2holesStates):
            for state_f in calculated2holesStates[counter:]:
                i, jj_i, eigv_i = state_i[0]
                f, jj_f, eigv_f = state_f[0]
                
                inten_trans_sat.append(((jj_i + 1) / multiplicity_JJ_sat[i]) * (float(calculatedSatelliteTransitions[combCnt][2][1]) / rate_level_sat[state_i[0]]))
                intensity_sat_ev.append(inten_trans_sat[-1] * float(calculatedSatelliteTransitions[combCnt][2][0]))
                transition_width_sat.append(rate_level_sat_ev[state_i] + rate_level_sat_ev[state_f])
                
                
                print("\ntransition " + str(combCnt) + ": from " + configuration_2holes[i] + " 2J=" + str(jj_i) + " neig=" + str(eigv_i) + " -> " + configuration_2holes[f] + " 2J=" + str(jj_f) + " neig=" + str(eigv_f) + " rate = " + str(calculatedSatelliteTransitions[combCnt][2][1]) + " s-1  Energy = " + str(calculatedSatelliteTransitions[combCnt][2][0]) + " eV\n")
                print(" Width = initial state (" + str(rate_level_sat_ev[state_i[0]]) + " eV) + final state (" + str(rate_level_sat_ev[state_f[0]]) + " eV) = " + str(transition_width_sat[-1]) + " eV\n")

                print(" Intensity =  " + str(intensity_sat_ev[-1]) + "\n")
                print(str(jj_i) + " \t " + str(calculatedSatelliteTransitions[combCnt][2][1]) + " \t " + multiplicity_JJ_sat[i] + " \t " + rate_level_sat[state_i[0]] + "\n")
                
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
    global radiative_by_hand, auger_by_hand
    
    initial_radiative = copy(radiative_by_hand)
    
    deleted_radiative = 0
    for i, counter in enumerate(initial_radiative):
        i, jj, eigv = calculated1holeStates[counter][0]
        
        currDir = rootDir + "/" + directory_name + "/radiative/" + shell_array[i] + "/2jj_" + str(jj) + "/eigv_" + str(eigv)
        currFileName = shell_array[i] + "_" + str(jj) + "_" + str(eigv)
        
        converged, failed_orbital, overlap, higher_config, highest_percent, accuracy, Diff, welt = checkOutput(currDir, currFileName)
        
        calculated1holeStates[counter][-1] = (higher_config, highest_percent, overlap, accuracy, Diff, welt)
        
        if converged and Diff >= diffThreshold or overlap > overlapsThreshold:
            del radiative_by_hand[i - deleted_radiative]
            deleted_radiative += 1
    
    
    initial_auger = copy(auger_by_hand)
    
    deleted_auger = 0
    for i, counter in enumerate(initial_auger):
        i, jj, eigv = calculated2holesStates[counter][0]
        
        currDir = rootDir + "/" + directory_name + "/auger/" + shell_array_2holes[i] + "/2jj_" + str(jj) + "/eigv_" + str(eigv)
        currFileName = shell_array_2holes[i] + "_" + str(jj) + "_" + str(eigv)
        
        converged, failed_orbital, overlap, higher_config, highest_percent, accuracy, Diff, welt = checkOutput(currDir, currFileName)
        
        calculated2holesStates[counter][-1] = (higher_config, highest_percent, overlap, accuracy, Diff, welt)
        
        if converged and Diff >= diffThreshold or overlap > overlapsThreshold:
            del auger_by_hand[i - deleted_auger]
            deleted_auger += 1
    



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
    
        while os.path.exists(inp):
            print("\n Directory name already exists!!!\n\n")
            print "Please choose another name for the calculation directory: ",
            inp = raw_input().strip()
        
        
        directory_name = inp


def setupElectronConfigs():
    global lines_conf, arr_conf, nb_lines_conf, lines_fir, arr_fir, nb_lines_fir, final_configuration, shell_array, configuration_string
    global configuration_1hole, configuration_2holes, shell_array_2holes, nelectrons
    
    count = 0
    
    if label_auto:
        with open('Conf.csv', 'r') as f:
            lines_conf = f.readlines()

        enum = int(atomic_number) - 1
        arr_conf = [int(x) for x in lines_conf[enum].strip().split(',')]
        nb_lines_conf = len(lines_conf)

        with open('Fir.csv', 'r') as f:
            lines_fir = f.readlines()

        arr_fir = [int(x) for x in lines_fir[enum].strip().split(',')]
        nb_lines_fir = len(lines_fir)

        final_configuration = []
        shell_array = []
        for i in range(len(arr_conf)):
            if arr_conf[i] != 0:
                final_configuration.append(arr_conf[i])
                shell_array.append(shells[i])
                count += 1


        count_au = 0

        configuration_string = ''
        for j in range(count):
            configuration_string += "(" + shell_array[j] + ")" + str(final_configuration[j]) + " "
        
            b = copy.deepcopy(final_configuration)
            b[j] = b[j] - 1
            
            configuration_1hole.append('')
            
            if count <= 10:
                for g in range(count):
                    configuration_1hole[j] += "(" + shell_array[g] + ")" + str(b[g]) + " "
                
            else:
                for g in range(9):
                    configuration_1hole[j] += "(" + shell_array[g] + ")" + str(b[g]) + " "
                
                configuration_1hole[j]+="\\\n    "
                for g in range(9, count):
                    configuration_1hole[j] += "(" + shell_array[g] + ")" + str(b[g]) + " "
                
            
            b = copy.deepcopy(final_configuration)
            b[j] = b[j] - 1

            if b[j] > 0:
                for k in range(j, count):
                    if b[k] > 0:
                        b = copy.deepcopy(final_configuration)
                        
                        b[j] = b[j]-1
                        b[k] = b[k]-1
                        
                        configuration_2holes.append('')
                        
                        if count <= 10:
                            for g in range(count):
                                configuration_2holes[count_au] += "(" + shell_array[g] + ")" + str(b[g]) + " "
                            
                        else:
                            for g in range(9):
                                configuration_2holes[count_au] += "(" + shell_array[g] + ")" + str(b[g]) + " "
                            
                            configuration_2holes[count_au] += "\\\n    "
                            
                            for g in range(9, count):
                                configuration_2holes[count_au] += "(" + shell_array[g] + ")" + str(b[g]) + " "
                            
                        
                        shell_array_2holes[count_au] = shell_array[k] + "_" + shell_array[j]
                        
                        count_au += 1
        
        nelectrons = str(enum)
        
        print("Element Z=" + atomic_number + "\n")
        print("Atom ground-state Neutral configuration:\n" + configuration_string + "\n")
        print("Number of occupied orbitals = " + str(count) + "\n")
    else:
        if os.path.exists(file_conf_rad) and os.path.exists(file_conf_aug):
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
            shutil.copyfile(file_conf_rad, directory_name + "/backup_" + file_conf_rad)
            shutil.copyfile(file_conf_aug, directory_name + "/backup_" + file_conf_aug)
            
            print("backup of configuration files can be found at " + directory_name + "/backup_" + file_conf_rad + " and " + directory_name + "/backup_" + file_conf_aug + " !!!\n")
            
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


def setupDirs():
    global file_cycle_log_1hole, file_cycle_log_2holes
    global file_sorted_1hole, file_sorted_2holes
    global file_calculated_radiative, file_calculated_auger, file_calculated_sat
    global file_parameters, file_results, file_final_results
    global file_final_results_1hole, file_final_results_2holes
    global file_rates, file_rates_auger, file_rates_satellites
    global file_rates_spectrum_diagram, file_rates_spectrum_auger, file_level_widths, file_rates_sums
    global file_rates_sums_sat, file_level_widths_sat, file_rates_spectrum_sat
    
    os.mkdir(directory_name)
    os.mkdir(directory_name + "/radiative")
    os.mkdir(directory_name + "/auger")
    os.mkdir(directory_name + "/transitions")
    
    file_cycle_log_1hole = rootDir + "/" + directory_name + "/" + directory_name + "_1hole_states_log.txt"
    file_cycle_log_2holes = rootDir + "/" + directory_name + "/" + directory_name + "_2holes_states_log.txt"
    
    file_sorted_1hole = rootDir + "/" + directory_name + "/" + directory_name + "_1hole_sorted.txt"
    file_sorted_2holes = rootDir + "/" + directory_name + "/" + directory_name + "_2holes_sorted.txt"
    
    file_calculated_radiative = rootDir + "/" + directory_name + "/" + directory_name + "_radiative_calculated.txt"
    file_calculated_auger = rootDir + "/" + directory_name + "/" + directory_name + "_auger_calculated.txt"
    file_calculated_sat = rootDir + "/" + directory_name + "/" + directory_name + "_sat_calculated.txt"
    
    file_parameters = rootDir + "/" + directory_name + "/calculation_parameters.txt"
    file_results = rootDir + "/" + directory_name + "/" + directory_name + "_results_all_cicles.txt"
    file_final_results = rootDir + "/" + directory_name + "/" + directory_name + "_results_energy_single_configuration.txt"

    file_final_results_1hole = rootDir + "/" + directory_name + "/" + directory_name + "_results_energy_single_configuration_1hole.txt"
    file_final_results_2holes = rootDir + "/" + directory_name + "/" + directory_name + "_results_energy_single_configuration_2holes.txt"

    file_rates = rootDir + "/" + directory_name + "/" + directory_name + "_rates_radiative.txt"
    file_rates_auger = rootDir + "/" + directory_name + "/" + directory_name + "_rates_auger.txt"
    file_rates_satellites = rootDir + "/" + directory_name + "/" + directory_name + "_rates_satellites.txt"
    
    file_rates_spectrum_diagram = rootDir + "/" + directory_name + "/" + directory_name + "_spectrum_diagram.txt"
    file_rates_spectrum_auger = rootDir + "/" + directory_name + "/" + directory_name + "_spectrum_auger.txt"
    file_level_widths = rootDir + "/" + directory_name + "/" + directory_name + "_level_widths.txt"
    file_rates_sums = rootDir + "/" + directory_name + "/" + directory_name + "_rates_sums.txt" 

    file_rates_sums_sat = rootDir + "/" + directory_name + "/" + directory_name + "_rates_sums_sat.txt" 
    file_level_widths_sat = rootDir + "/" + directory_name + "/" + directory_name + "_level_widths_sat.txt"
    file_rates_spectrum_sat = rootDir + "/" + directory_name + "/" + directory_name + "_spectrum_sat.txt"

    
    with open(file_parameters, 'w') as fp:
        fp.write("########################################## Output of the calculation parameters ##########################################################\n\n")
        fp.write("Atomic number Z= " + atomic_number + "\n")
        fp.write("Atom ground-state Neutral configuration:\n" + configuration_string + "\n")
        fp.write("Number of considered threads in the calculation= " + number_of_threads + "\n")
        fp.write("Folder with files from this calculation: " + rootDir + "/" + directory_name + "\n\n")
        fp.write("File of calculation parameters: " + file_parameters + "\n\n")


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
        setupElectronConfigs()
    else:
        flags = checkPartial()
        
        if type(flags) == type(0):
            if flags == 1:
                partial = False
            elif flags == 3:
                resort = False
        else:
            if len(flags) > 3:
                redo_energy_calc = True
                
                complete_1hole, complete_2holes, last_calculated_cycle_1hole, last_calculated_cycle_2holes, last_calculated_state_1hole, last_calculated_state_2holes = flags
            elif len(flags) == 3:
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
    
    if not partial:
        calculate1holeStates()
        calculate2holesStates()
    
    
        print("Please check for convergence of the 1 and 2 holes states.")
        print("File " + file_final_results + " contains the results for both calculations, as well as a list of flagged states.")
        print("Files " + file_final_results_1hole + " and " + file_final_results_2holes + "contain the results 1 and 2 holes respectively, as well as a list of flagged states.")
        #print("A helper script \"checkConvergence.py\" can also be used to check the convergence before continuing.")
        #print("This script will tell you which states did not reach proper convergence.\n")
        
        print("To re-check flagged states please type GetParameters.")
        print("If you would like to continue the rates calculation with the current states please type Continue.")
        inp = raw_input().strip()
        while inp != "Continue":
            if inp == "GetParameters":
                GetParameters()
                print("New flagged states parameters can be found in the files " + file_final_results + ", " + file_final_results_1hole + ", " + file_final_results_2holes + ", for both 1 and 2 holes states.\n\n")
            
            print("To recheck flagged states please type GetParameters.")
            print("If you would like to continue the rates calculation with the current states please type Continue.")
            inp = raw_input().strip()
    
    
        print("Continuing rate calculation with the current 1 and 2 holes states.\n")
        
        print(80*"-" + "\n")
    elif redo_energy_calc:
        if not complete_1hole:
            calculate1holeStates(last_calculated_cycle_1hole, last_calculated_state_1hole)
        if not complete_2holes:
            calculate2holesStates(last_calculated_cycle_2holes, last_calculated_state_2holes)
    
    
    print("Sorting lists of states...")
    if resort:
        sortCalculatedStates()
    
    
    
    
    if not partial:
        rates()
        radiative_done = True
        
        rates_auger()
        auger_done = True
        
        rates_satellite()
        satellite_done = True
    elif redo_transitions:
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
        
        if redo_sat:
            rates_satellite()
            satellite_done = True
        elif partial_sat:
            rates_satellite(last_sat_calculated)
            satellite_done = True
       
       
    
    calculateSpectra(radiative_done, auger_done, satellite_done)