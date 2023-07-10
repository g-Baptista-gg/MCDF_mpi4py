from mpi4py import MPI
import pandas as pd
import os, subprocess, shutil, sys , libtmux
import time,tqdm,re , pprint
import numpy as np
import matplotlib.pyplot as plt
from scipy.special import voigt_profile
#import scienceplots
#plt.style.use(['science'])


# For debugging: mpirun -n $(nproc) xterm -hold -e python runMCDF_MPI.py 
# For max usage of physical threads: mpirun --use-hwthread-cpus python3 runMCDF_MPI.py
# For limited usage of physical threads: mpirun --use-hwthread-cpus -n $(($(nproc)-5)) python3 runMCDF_MPI.py

# TODO: IMPORTANT- Change f05 templates in case Z>48

hbar = 6.582119569E-16

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
total_ranks = comm.Get_size()
templates = None
electron_number = None
global breakflag
breakflag = False

root_dir=None
mdfgmeFile = '	   nblipa=75 tmp_dir=./tmp/\n	   f05FileName\n	   0.\n'
mcdf_exe='mcdfgme2019.exe'



def is_digit_with_scientific_notation(string):
    try:
        float(string)
        return True
    except ValueError:
        return False


def qn_to_dir(quantum_numbers,root_dir):
    current_dir = root_dir
    current_dir += 'auger/' if ('aug' in quantum_numbers) else  'radiative/'
    appends=['','2jj_','eig_']
    quantum_numbers=quantum_numbers.split(sep=',')[1:]
    for i in range(len(quantum_numbers)):
        current_dir+=appends[i]+quantum_numbers[i]+'/'
    return current_dir

def label_to_config(label):
    return config_n_labels_dict[label].strip()


def order_orbital(strings):
    # Define the order of orbitals
    orbital_order = {'s': 0, 'p': 1, 'd': 2, 'f': 3, 'g': 4, 'h': 5, 'i': 6, 'j': 7, 'k': 8, 'l': 9, 'm': 10, 'n': 11, 'o': 12}

    # Custom sorting function
    def sort_key(string):
        # Extract the first number and orbital type using regular expressions
        match = re.search(r'(\d+)([a-z]+)', string)
        first_number = int(match.group(1))
        orbital_type = match.group(2)

        # Return a tuple for sorting
        return first_number, orbital_order[orbital_type]

    # Sort the strings based on the custom key function
    sorted_strings = sorted(strings.split(), key=sort_key)

    return sorted_strings

def check_convergence(f06_file, look_for_orb):
    #print(f06_file[-1])
    if 'Total CPU Time for this job was' in f06_file[-1]:
        overlap_flag=False
        max_overlap = 0
        
        for i in range(len(f06_file)):
            if not overlap_flag:
                if 'Overlap integrals' in f06_file[-i-1]:
                    overlap_flag=True
                    j=1
                    while ("|" in f06_file[-i-1+j] and ">" in f06_file[-i-1+j] and "<" in f06_file[-i-1+j]):
                        overlaps=f06_file[-i-1+j].split(' >')
                        for k in overlaps[1:]:
                            if '<' in k:
                                k=k.split('<')[0]
                            k=abs(float(k.strip()))
                            if k>max_overlap: max_overlap=k
                        j+=1
                    #if max_overlap>1E-5: return False
            else:
                if 'ETOT (a.u.)' in f06_file[-i-1]:
                    _,en1,en2=f06_file[-i].split()
                    en_diff=abs(float(en1)-float(en2))
                    if en_diff>1:
                        #print('Energy diff')
                        return False
                    else:
                        #print('Converged!')

                        for k in range(len(f06_file)):
                            if 'Etot_(Welt.)' in f06_file[-k-1]:
                                energy = f06_file[-k-1].split()[3].strip()
                                return True,energy,str(en_diff),str(max_overlap)
                        else:
                            return False
        else:
            for i in range(len(f06_file)):
                if 'ETOT (a.u.)' in f06_file[-i-1]:
                    _,en1,en2=f06_file[-i].split()
                    en_diff=abs(float(en1)-float(en2))
                    if en_diff>1:
                        #print('Energy diff')
                        return False
                    else:
                        #print('Converged!')

                        for k in range(len(f06_file)):
                            if 'Etot_(Welt.)' in f06_file[-k-1]:
                                energy = f06_file[-k-1].split()[3].strip()
                                return True,energy,str(en_diff),'No Overlaps'
                        else:
                            return False
            

    else:
        if look_for_orb:
            failed_orbital = None
            for i in range(len(f06_file)):
                if 'For orbital' in f06_file[-i-1] or 'for orbital' in f06_file[-i-1]:
                    failed_orbital = f06_file[-i-1].split()[2].strip()
                    break
            return False, failed_orbital
        else:
            return False
        


def check_convergence_interface(f06_file, look_for_orb):
    #print(f06_file[-1])
    if 'Total CPU Time for this job was' in f06_file[-1]:
        overlap_flag=False
        max_overlap = 0
        max_overlap_text=''
        
        for i in range(len(f06_file)):
            if not overlap_flag:
                if 'Overlap integrals' in f06_file[-i-1]:
                    overlap_flag=True
                    j=1
                    while ("|" in f06_file[-i-1+j] and ">" in f06_file[-i-1+j] and "<" in f06_file[-i-1+j]):
                        overlaps=f06_file[-i-1+j].split(' >')
                        for k in overlaps[1:]:
                            if '<' in k:
                                k=k.split('<')[0]
                                overlap= overlaps[0]+'>'
                            else:
                                if len(overlaps) ==2 :
                                    overlap = overlaps[0]+'>'
                                else:overlap ='<'+ overlaps[1].split('<')[1]+'>'
                            k=abs(float(k.strip()))
                            if k>max_overlap:
                                max_overlap=k
                                max_overlap_text=overlap
                        j+=1

            else:
                if 'ETOT (a.u.)' in f06_file[-i-1]:
                    _,en1,en2=f06_file[-i].split()
                    en_diff=abs(float(en1)-float(en2))

                    for k in range(len(f06_file)):
                        if 'Etot_(Welt.)' in f06_file[-k-1]:
                            energy = f06_file[-k-1].split()[3].strip()
                            return True,energy,str(en_diff),str(max_overlap),max_overlap_text
                    else:
                        return False
        else:
            for i in range(len(f06_file)):
                if 'ETOT (a.u.)' in f06_file[-i-1]:
                    _,en1,en2=f06_file[-i].split()
                    en_diff=abs(float(en1)-float(en2))
                    if en_diff>1:
                        #print('Energy diff')
                        return False
                    else:
                        #print('Converged!')

                        for k in range(len(f06_file)):
                            if 'Etot_(Welt.)' in f06_file[-k-1]:
                                energy = f06_file[-k-1].split()[3].strip()
                                return True,energy,str(en_diff),'No Overlaps'
                        else:
                            return False
            

    else:
        if look_for_orb:
            failed_orbital = None
            for i in range(len(f06_file)):
                if 'For orbital' in f06_file[-i-1] or 'for orbital' in f06_file[-i-1]:
                    failed_orbital = f06_file[-i-1].split()[2].strip()
                    break
            if failed_orbital == None:
                return False
            else:return False, failed_orbital
        else:
            return False
                            
def check_convergence_gp(f06_file):
    #print(f06_file[-1])
    if 'Total CPU Time for this job was' in f06_file[-1]:
        overlap_flag=False
        enTot_flag=False
        en_flag = False
        config_flag=False
        common_flag=False
        config_count=0
        max_overlap = 0
        max_config = ''
        max_config_val = 0
        config=''
        
        for i in range(len(f06_file)):
            if not config_flag:
                if 'Configuration(s)' in f06_file[i]:
                    config_count+=1
                    if config_count==1:config=f06_file[i+1].strip()
                    if 'Configuration(s)' not in f06_file[i+2]:config_flag=True
            else:
                if not common_flag and config_count>1:
                    
                    if 'Common to all configurations' in f06_file[i]:
                        config=f06_file[i].split('Common to all configurations')[-1].strip()
                        common_flag=True
                

            if not enTot_flag:
                if 'Etot_(Welt.)' in f06_file[-i-1]:
                    energy = f06_file[-i-1].split()[3].strip()
                    enTot_flag=True
            else:
                if not overlap_flag:
                    if 'Overlap integrals' in f06_file[-i-1]:
                        overlap_flag=True
                        j=1
                        while ("|" in f06_file[-i-1+j] and ">" in f06_file[-i-1+j] and "<" in f06_file[-i-1+j]):
                            overlaps=f06_file[-i-1+j].split(' >')
                            for k in overlaps[1:]:
                                if '<' in k:
                                    k=k.split('<')[0]
                                k=abs(float(k.strip()))
                            if k>max_overlap: max_overlap=k
                            j+=1
                else:
                    if not en_flag:
                        if 'ETOT (a.u.)' in f06_file[-i-1]:
                            _,en1,en2=f06_file[-i].split()
                            en_diff=abs(float(en1)-float(en2))
                            if config_count==1:
                                config=order_orbital(config)
                                return True,' '.join(config),energy,str(en_diff),str(max_overlap)
                            else: en_flag=True
                    else:
                        if 'List of jj configurations with a weight >= 0.01%' in f06_file[-i-1]:
                            k=0
                            while '%' in f06_file[-i+k]:
                                if float(f06_file[-i+k].split()[-2])>max_config_val:
                                    max_config_val = float(f06_file[-i+k].split()[-2])
                                    max_config=' '.join(f06_file[-i+k].split()[:-2])
                                k+=1
                            config=config+' '+max_config
                            config=order_orbital(config)
                            return True,' '.join(config),energy,str(en_diff),str(max_overlap)




# TODO: same for this case
        else:
            for i in range(len(f06_file)):
                if 'ETOT (a.u.)' in f06_file[-i-1]:
                    _,en1,en2=f06_file[-i].split()
                    en_diff=abs(float(en1)-float(en2))
                    if en_diff>1:
                        #print('Energy diff')
                        return False
                    else:
                        #print('Converged!')

                        for k in range(len(f06_file)):
                            if 'Etot_(Welt.)' in f06_file[-k-1]:
                                energy = f06_file[-k-1].split()[3].strip()
                                return True,energy,str(en_diff),'No Overlaps'
                        else:
                            return False
    else: return False



def find_jj2(quantum_numbers):
    #print(quantum_numbers,flush=True)
    cwd = qn_to_dir(quantum_numbers=quantum_numbers,root_dir=root_dir)
    config=label_to_config(quantum_numbers)
    if not (os.path.exists(cwd)):
        os.makedirs(cwd)
    if not (os.path.exists(cwd+'tmp/')):
        os.makedirs(cwd+'tmp/')

    electron_number_=(electron_number-1 if ('aug' in quantum_numbers) else electron_number)

    with open(cwd+'jjtest.f05','w') as f05_file:
        f05_file.write(f05Template.replace('mcdfgmeconfiguration',config+' ')\
                                  .replace('mcdfgmejj',(str(100) if electron_number_%2==0 else str(101)))\
                                  .replace('mcdfgmeelectronnb', str(electron_number_)))
        
    with open(cwd +'mdfgme.dat','w') as dat_file:
        dat_file.write(mdfgmeFile.replace('f05FileName','jjTest'))
    subprocess.call(mcdf_exe,cwd=cwd,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
    with open(cwd+'jjtest.f06','r',encoding='latin-1') as f06_file:
        for line in f06_file:
            if "highest 2Jz possible value is" in line:
                max_j = line.split("highest 2Jz possible value is")[1].strip().split()[0]
                break
    #print(f'{quantum_numbers}-> Max jj2 = {max_j}',flush=True)
    #print(max_j)
    return max_j

def find_eig(quantum_numbers): # performs calculation for 1st eigen in order to find max
    #print(f'{quantum_numbers}-> Find eig')
    cwd = qn_to_dir(quantum_numbers=quantum_numbers,root_dir=root_dir)
    if not (os.path.exists(cwd)):
        os.makedirs(cwd)
        os.makedirs(cwd+'eig_0/')
    if not (os.path.exists(cwd+'eig_0/'+'tmp/')):
        os.makedirs(cwd+'eig_0/'+'tmp/')
    hole_type,label,jj2=quantum_numbers.split(',')
    with open(cwd+'eig_0/'+label+'_'+jj2+'_0'+'.f05','w') as f05_file:
        f05_file.write(f05Template.replace('mcdfgmeconfiguration',label_to_config(hole_type+','+label)+' ')\
                                  .replace('mcdfgmejj',jj2)\
                                  .replace('mcdfgmeelectronnb', (str(electron_number-1) if ('aug' in quantum_numbers) else str(electron_number)))\
                                  .replace('mcdfgmeneigv',str(1)))
    with open(cwd+'eig_0/' +'mdfgme.dat','w') as dat_file:
        dat_file.write(mdfgmeFile.replace('f05FileName',label+'_'+jj2+'_0'))
    subprocess.call(mcdf_exe,cwd=cwd+'eig_0/',stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
    with open(cwd+'eig_0/'+label+'_'+jj2+'_0'+'.f06','r',encoding='latin-1') as f06_file:
        for line in f06_file:
            if '---- Current subspace include jj configurations from' in line:
                max_eig=line.split('to')[1].strip()
                #print(f'Max eig: {max_eig}',flush=True)
                break
        else:
            #print(f'Couldnt find Eigenvalues: {quantum_numbers}',flush=True)
            shutil.rmtree(cwd)
            return quantum_numbers+';'+'-2'+':'+'-1'
        f06_lines=f06_file.readlines()
        #print(f'{quantum_numbers}     {check_convergence(f06_lines,False)}\n {f06_lines[-1]}',flush=True)
        res=check_convergence(f06_lines,False)
        if type(res)!=bool:
            return quantum_numbers+';'+'-2'+':'+str(max_eig)+','+'1,'+','.join(res[1:])
        else:
            return quantum_numbers+';'+'-2'+':'+str(max_eig)+','+'0'

def no_cycles(quantum_numbers):
    #print(f'{quantum_numbers}-> no cycles')
    cwd = qn_to_dir(quantum_numbers=quantum_numbers,root_dir=root_dir)
    if not (os.path.exists(cwd)):
        os.makedirs(cwd)
    if not (os.path.exists(cwd+'tmp/')):
        os.makedirs(cwd+'tmp/')
    hole_type,label,jj2,eig=quantum_numbers.split(',')
    with open(cwd+label+'_'+jj2+'_'+eig+'.f05','w') as f05_file:
        f05_file.write(f05Template.replace('mcdfgmeconfiguration',label_to_config(hole_type+','+label)+' ')\
                                  .replace('mcdfgmejj',jj2)\
                                  .replace('mcdfgmeelectronnb', (str(electron_number-1) if ('aug' in quantum_numbers) else str(electron_number)))\
                                  .replace('mcdfgmeneigv',str(int(eig)+1)))
    with open(cwd +'mdfgme.dat','w') as dat_file:
        dat_file.write(mdfgmeFile.replace('f05FileName',label+'_'+jj2+'_'+eig))
    subprocess.call(mcdf_exe,cwd=cwd,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
    with open(cwd+label+'_'+jj2+'_'+eig+'.f06','r',encoding='latin-1') as f06_file:
        return check_convergence(f06_file.readlines(),False)
    




def with_cycles(quantum_numbers):
    #   Returns 0 if failed followed by the failed orbital, 1 if successfull Ex: [0,"2p"]
    cwd = qn_to_dir(quantum_numbers=quantum_numbers,root_dir=root_dir)
    if not (os.path.exists(cwd)):
        os.makedirs(cwd)
    if not (os.path.exists(cwd+'tmp/')):
        os.makedirs(cwd+'tmp/')
    hole_type,label,jj2,eig=quantum_numbers.split(',')
    with open(cwd+label+'_'+jj2+'_'+eig+'.f05','w') as f05_file:
        f05_file.write(f05Template_10steps.replace('mcdfgmeconfiguration',label_to_config(hole_type+','+label)+' ')\
                                  .replace('mcdfgmejj',jj2)\
                                  .replace('mcdfgmeelectronnb', (str(electron_number-1) if ('aug' in quantum_numbers) else str(electron_number)))\
                                  .replace('mcdfgmeneigv',str(int(eig)+1)))
    with open(cwd +'mdfgme.dat','w') as dat_file:
        dat_file.write(mdfgmeFile.replace('f05FileName',label+'_'+jj2+'_'+eig))
    subprocess.call(mcdf_exe,cwd=cwd,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
    with open(cwd+label+'_'+jj2+'_'+eig+'.f06','r',encoding='latin-1') as f06_file:
        return check_convergence(f06_file.readlines(),True)
    

def with_1orb(quantum_numbers,failed_orbs):
    #   Returns 0 if failed followed by the failed orbitals, 1 if successfull Ex: [0,"2p_3p"]
    cwd = qn_to_dir(quantum_numbers=quantum_numbers,root_dir=root_dir)
    if not (os.path.exists(cwd)):
        os.makedirs(cwd)
    if not (os.path.exists(cwd+'tmp/')):
        os.makedirs(cwd+'tmp/')
    hole_type,label,jj2,eig=quantum_numbers.split(',')
    with open(cwd+label+'_'+jj2+'_'+eig+'.f05','w') as f05_file:
        f05_file.write(f05Template_10steps_Forbs.replace('mcdfgmeconfiguration',label_to_config(hole_type+','+label)+' ')\
                                  .replace('mcdfgmejj',jj2)\
                                  .replace('mcdfgmeelectronnb', (str(electron_number-1) if ('aug' in quantum_numbers) else str(electron_number)))\
                                  .replace('mcdfgmeneigv',str(int(eig)+1))\
                                  .replace('mcdfgmefailledorbital',failed_orbs+'  1 5 0 1 :'))
    with open(cwd +'mdfgme.dat','w') as dat_file:
        dat_file.write(mdfgmeFile.replace('f05FileName',label+'_'+jj2+'_'+eig))
    subprocess.call(mcdf_exe,cwd=cwd,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
    with open(cwd+label+'_'+jj2+'_'+eig+'.f06','r',encoding='latin-1') as f06_file:
        return check_convergence(f06_file.readlines(),True)


def with_2orbs(quantum_numbers,failed_orbs):
    #   Returns 0 if failed, 1 if successfull
    cwd = qn_to_dir(quantum_numbers=quantum_numbers,root_dir=root_dir)

    failed_orbs = failed_orbs.split(',')
    #print(failed_orbs,flush=True)

    if not (os.path.exists(cwd)):
        os.makedirs(cwd)
    if not (os.path.exists(cwd+'tmp/')):
        os.makedirs(cwd+'tmp/')
    hole_type,label,jj2,eig=quantum_numbers.split(',')
    with open(cwd+label+'_'+jj2+'_'+eig+'.f05','w') as f05_file:
        f05_file.write(f05Template_10steps_Forbs.replace('mcdfgmeconfiguration',label_to_config(hole_type+','+label)+' ')\
                                  .replace('mcdfgmejj',jj2)\
                                  .replace('mcdfgmeelectronnb', (str(electron_number-1) if ('aug' in quantum_numbers) else str(electron_number)))\
                                  .replace('mcdfgmeneigv',str(int(eig)+1))\
                                  .replace('mcdfgmefailledorbital',failed_orbs[0]+'  1 5 0 1 :\n    '+failed_orbs[1]+'  1 5 0 1 :'))
    with open(cwd +'mdfgme.dat','w') as dat_file:
        dat_file.write(mdfgmeFile.replace('f05FileName',label+'_'+jj2+'_'+eig))
    subprocess.call(mcdf_exe,cwd=cwd,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
    with open(cwd+label+'_'+jj2+'_'+eig+'.f06','r',encoding='latin-1') as f06_file:
        return check_convergence(f06_file.readlines(),False)
    
def get_parameters(quantum_numbers):
    cwd = qn_to_dir(quantum_numbers=quantum_numbers,root_dir=root_dir)
    hole_type,label,jj2,eig=quantum_numbers.split(',')
    with open(cwd+label+'_'+jj2+'_'+eig+'.f06','r',encoding='latin-1') as f06_file:
        return check_convergence_gp(f06_file.readlines())

def get_rate(i_qn,f_qn,trans_type,en_dif):
    #print(i_qn,f_qn,trans_type,en_dif)
    i_cwd=qn_to_dir(i_qn,root_dir)
    i_hole_type,i_label,i_jj2,i_eig = i_qn.split(',')

    f_cwd=qn_to_dir(f_qn,root_dir)
    f_hole_type,f_label,f_jj2,f_eig = f_qn.split(',')

    cwd = root_dir+'/'.join(['transitions',trans_type,'_'.join(i_qn.split(',')[1:]),'_'.join(f_qn.split(',')[1:])])+'/'

    if not (os.path.exists(cwd)):
        os.makedirs(cwd)
        os.makedirs(cwd+'/tmp')

    shutil.copyfile(i_cwd+'_'.join(i_qn.split(',')[1:])+'.f09',cwd+'i_wf.f09')
    shutil.copyfile(f_cwd+'_'.join(f_qn.split(',')[1:])+'.f09',cwd+'f_wf.f09')

    with open(cwd+'transition.f05','w') as f05_file:
        if trans_type == 'auger':
            f05_file.write(f05Template_aug.replace('energylabel',en_dif)\
                                        .replace('mcdfgmeelectronnbi',str(electron_number))\
                                        .replace('mcdfgmejji',i_jj2)\
                                        .replace('mcdfgmeelectronnbf',str(electron_number-1))\
                                        .replace('mcdfgmejjf',f_jj2)\
                                        .replace('mcdfgmeconfigurationi',label_to_config(i_hole_type+','+i_label)+' ')\
                                        .replace('mcdfgmeconfigurationf',label_to_config(f_hole_type+','+f_label)+' ')\
                                        .replace('mcdfgmeneigvi',str(int(i_eig)+1))\
                                        .replace('mcdfgmeneigvf',str(int(f_eig)+1))\
                                        .replace('mcdfgmewffilei','i_wf')\
                                        .replace('mcdfgmewffilef','f_wf'))
            
        else:
            f05_file.write(f05Template_rad\
                                        .replace('mcdfgmeelectronnbi',(str(electron_number-1) if ('aug' in i_qn) else str(electron_number)))\
                                        .replace('mcdfgmejji',i_jj2)\
                                        .replace('mcdfgmeelectronnbf',(str(electron_number-1) if ('aug' in f_qn) else str(electron_number)))\
                                        .replace('mcdfgmejjf',f_jj2)\
                                        .replace('mcdfgmeconfigurationi',label_to_config(i_hole_type+','+i_label)+' ')\
                                        .replace('mcdfgmeconfigurationf',label_to_config(f_hole_type+','+f_label)+' ')\
                                        .replace('mcdfgmeneigvi',str(int(i_eig)+1))\
                                        .replace('mcdfgmeneigvf',str(int(f_eig)+1))\
                                        .replace('mcdfgmewffilei','i_wf')\
                                        .replace('mcdfgmewffilef','f_wf'))
            
    with open(cwd +'mdfgme.dat','w') as dat_file:
        dat_file.write(mdfgmeFile.replace('f05FileName','transition'))

    subprocess.call(mcdf_exe,cwd=cwd,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
    
    with open(cwd+'transition.f06','r',encoding='latin-1') as f06_file:
        f06_lines = f06_file.readlines()

        if trans_type == 'auger':
            for i in range(len(f06_lines)):
                    if 'For Auger transition of energy' in f06_lines[-i-1] and 'Total rate is' in f06_lines[-i-1]:
                        #print('Auger: ',f06_lines[-i-1].split()[0],flush=True)
                        rate=f06_lines[-i].split()[0].strip()
                        #shutil.rmtree(cwd)
                        return rate
        else:
            for i in range(len(f06_lines)):
                if 'and total transition rate is:' in f06_lines[-i-1]:
                    #print('RAD: ',f06_lines[-i-1].split(':')[1].split()[0],flush=True)
                    rate=f06_lines[-i-1].split(':')[1].split()[0]
                    #shutil.rmtree(cwd)
                    return rate
        
        shutil.rmtree(cwd)
        return -1

def do_work(calc: str):
    global breakflag
    quantum_numbers,calc_method=calc.split(sep=';')


    calc_method_value  = int(calc_method.split(sep=':')[0])
    calc_method_params = calc_method.split(sep=':')[1]
    
    if calc_method_value == -4:
        #print(f'Finding max 2jj: {quantum_numbers}',flush=True)
        return (quantum_numbers+';'+'-3:'+str(find_jj2(quantum_numbers=quantum_numbers)))
    
    elif calc_method_value ==-3:
        #print(f'Finding max eig: {quantum_numbers}',flush=True)
        return find_eig(quantum_numbers)
    
    elif calc_method_value ==-2:
        #print(f'No Cycles: {quantum_numbers}',flush=True)
        res= no_cycles(quantum_numbers)
        #print(res,flush=True)
        if type(res)==bool:
            return (quantum_numbers+';1:')
        else:
            return (quantum_numbers+';0:'+','.join(res[1:]))

    elif calc_method_value == 1:
        #print(f'10 Cycles: {quantum_numbers}',flush=True)
        conv_n_orbs=with_cycles(quantum_numbers)
        if type(conv_n_orbs)!=bool:
            if conv_n_orbs[0]:
                return (quantum_numbers+';0:'+','.join(conv_n_orbs[1:]))
            else:
                if conv_n_orbs[1]!=None:
                    return (quantum_numbers+';2:'+conv_n_orbs[1])
                else:
                    return quantum_numbers+';-1:'
        else:
            return quantum_numbers+';-1:'
        # if type(conv_n_orbs)!=bool:
        #     if conv_n_orbs[1]!=None:
        #         return (quantum_numbers+';2:'+conv_n_orbs[1])
        #     else:
        #         return quantum_numbers+';-1:'
        # else:
        #     if conv_n_orbs:
        #         return quantum_numbers+';0:'
        #     else:
        #         return quantum_numbers+';-1:'
            
    elif calc_method_value == 2:
        conv_n_orbs=with_1orb(quantum_numbers,calc_method_params)
        #print(f'1 Failed Orbital: {quantum_numbers}',flush=True)
        if type(conv_n_orbs)!=bool:
            if conv_n_orbs[0]:
                return (quantum_numbers+';0:'+','.join(conv_n_orbs[1:]))
            else:
                if conv_n_orbs[1]!=None:
                    return (quantum_numbers+';3:'+calc_method_params+','+conv_n_orbs[1])
                else:
                    return quantum_numbers+';-1:'
        else:
            return quantum_numbers+';-1:'


    elif calc_method_value == 3:
        #print(f'2 Failed Orbitals: {quantum_numbers}',flush=True)
        res=with_2orbs(quantum_numbers,calc_method_params)
        if type(res)==bool:
            return quantum_numbers+';-1:'
        else:
            return quantum_numbers+';0:'+','.join(res[1:])
    
    elif calc_method_value == 4:
        return quantum_numbers+';0:'+ ','.join(get_parameters(quantum_numbers)[1:])
    
    elif calc_method_value == 5:
        i_qn = quantum_numbers
        _=calc_method_params.split(',')
        trans_type=_[0]
        en_dif = _[-3]
        i_config = _[-2]
        f_config = _[-1]
        
        f_qn = ','.join(_[1:5])
        rate=get_rate(i_qn,f_qn,trans_type,en_dif)
        if rate!=-1:
        #print('AHH ',i_qn+';0:'+trans_type+','+f_qn+','+rate+','+en_dif,flush=True)
            return i_qn+';0:'+trans_type+','+f_qn+','+rate+','+en_dif+','+i_config+','+f_config
        else:

            return i_qn+';-1:'
        
        
    elif calc_method_value == -5:
        breakflag=True
    else:
        print('ERROR: Got undefined job')
        comm.Abort()

def initTemplates(template,atomic_number):
    f05=''.join(template.readlines())
    f05=f05.replace('mcdfgmeatomicnumber',str(atomic_number))
    #f05=f05.replace('mcdfgmeelectronnb',str(electron_number))
    return f05

def setupTemplates(atomic_number,electron_number):
    #global f05Template_nuc, f05Template_10steps_nuc, f05Template_10steps_Forbs_nuc, f05RadTemplate_nuc, f05AugTemplate_nuc
    
    with open("f05_templates/f05_2019.f05", "r") as template:
        f05Template = initTemplates(template,atomic_number)
    with open("f05_templates/f05_2019nstep1.f05", "r") as template:
        f05Template_10steps =  initTemplates(template,atomic_number)
    with open("f05_templates/f05_2019nstep2.f05", "r") as template:
        f05Template_10steps_Forbs =  initTemplates(template,atomic_number)
    with open("f05_templates/f05_2019_radiative.f05","r") as template:
        f05Template_rad = initTemplates(template,atomic_number)
    with open("f05_templates/f05_2019_auger.f05","r") as template:
        f05Template_aug = initTemplates(template,atomic_number)
    return f05Template, f05Template_10steps, f05Template_10steps_Forbs,f05Template_rad,f05Template_aug



# Program starts by master asking for user inputs for atomic number and electron number, setting up f05 templates and broadcasting to slave ranks
calc_step=None
if rank==0:
    os.system('clear')

    dir_flag=False
    while not dir_flag:
        #directory_name = 'Cu_4s'
        directory_name = input('Directory name: ')
        root_dir = os.getcwd()+'/'+directory_name+'/'
        if os.path.exists(root_dir):
            dir_conf_flag=False
            while not dir_conf_flag:
                dir_confirmation = input('Directory already exists. Do you want to carry on with the calculation? (y/n): ')
                if dir_confirmation == 'y' or dir_confirmation == 'Y':
                    dir_flag=True
                    dir_conf_flag=True
                    if os.path.exists(root_dir+'backup_1hole_configurations.txt') and os.path.exists(root_dir+'backup_2holes_configurations.txt'):
                        copy_configs_flag=False
                        while not copy_configs_flag:
                            copy_config_confirmation = input('Config files already exists. Replace with new configs? (y/n): ')
                            if copy_config_confirmation == 'y' or copy_config_confirmation == 'Y':
                                copy_configs_flag = True
                                shutil.copyfile('1hole_configurations.txt',root_dir+'backup_1hole_configurations.txt')
                                shutil.copyfile('2holes_configurations.txt',root_dir+'backup_2holes_configurations.txt')
                                print('Backup files replaced.')
                            elif copy_config_confirmation == 'n' or copy_config_confirmation == 'N':
                                copy_configs_flag = True
                                print('Backup files kept.')
                            else:
                                print('Please input a valid option...')

                elif dir_confirmation == 'n' or dir_confirmation == 'N':
                    os.system('clear')
                    print('Please select another name for the directory.')
                    dir_conf_flag=True


                else:
                    print('Please input a valid option...')
        else:
            dir_flag=True
            os.makedirs(root_dir)
            shutil.copyfile('1hole_configurations.txt',root_dir+'backup_1hole_configurations.txt')
            shutil.copyfile('2holes_configurations.txt',root_dir+'backup_2holes_configurations.txt')

    at_no_flag = False
    while not at_no_flag:
        atomic_number   = input('Atomic number: ')
        if atomic_number.isdigit():
            atomic_number=int(atomic_number)
            at_no_flag = True
        else:
            print('Please input a valid integer.')
    
    el_no_flag = False
    while not el_no_flag:
        electron_number = input('Number of electrons: ') # TODO: calculate from 1hole and 2holes
        if electron_number.isdigit():
            electron_number = int(electron_number)
            el_no_flag = True
        else:
            print('Please input a valid integer.')


    #print(('-----------------------------------------------------\n|  Computation Mehtods:\t\t\t\t    |\n-----------------------------------------------------\n|  Energy and WF calculations:\t0\t\t    |\n|  Get Parameters:\t\t1\t\t    |\n|  Rates:\t\t\t2\t\t    |\n|  Sums:\t\t\t3 -> Single Thread  |\n|  Get Params + Rates + Sums:\t4 -> Single Thread  |\n|  Plot Spectra:\t\t5 -> Single Thread  |\n-----------------------------------------------------'))
    print('-----------------------------------------------------\n|  Computation Mehtods:\t\t\t\t    |\n-----------------------------------------------------\n|  Energy and WF calculations:\t0\t\t    |')
    if os.path.exists(root_dir+'byHand.csv') and os.path.exists(root_dir+'converged.csv'):
        print('|  Get Parameters:\t\t1\t\t    |')
        if os.path.exists(root_dir+'all_converged.csv'):
            print('|  Rates:\t\t\t2\t\t    |')
            if os.path.exists(root_dir+'rates_auger.csv') and os.path.exists(root_dir+'rates_rad.csv') and os.path.exists(root_dir+'rates_satellite.csv'):
                print('|  Sums:\t\t\t3 -> Single Thread  |')
                if os.path.exists(root_dir+'spectrum_diagram.csv') and os.path.exists(root_dir+'spectrum_satellite.csv'):
                    print('|  Plot Spectra:\t\t5 -> Single Thread  |')
                    allowed_calc=[0,1,2,3,4,5,6]
                else:allowed_calc=[0,1,2,3,4,6]

            else:allowed_calc=[0,1,2,4,6]
        
        else:allowed_calc=[0,1,4,6]
        print('|  Get Params + Rates + Sums:\t4\t\t    |')
        print('|  State convergence util:\t6\t\t    |')

    else:
        allowed_calc=[0]
    print('-----------------------------------------------------')
    
    calc_step_flag=False
    while not calc_step_flag:
        calc_step = input('Please enter what computation should be performed: ')
        if calc_step.isdigit():
            calc_step=int(calc_step)
            if calc_step in allowed_calc:
                calc_step_flag = True
            else:print('Please input a valid option')
        else:print('Please input a valid option')

    start_time = time.time()
    
    templates = setupTemplates(atomic_number,electron_number)
    #print('Done setup templates')
    root_dir = os.getcwd()+'/'+directory_name+'/'




f05Template, f05Template_10steps, f05Template_10steps_Forbs,f05Template_rad,f05Template_aug = comm.bcast(templates,root=0)
root_dir = comm.bcast(root_dir,root=0)
electron_number = comm.bcast(electron_number,root=0)

calc_step=comm.bcast(calc_step,root=0)


rad_config_n_labels = pd.read_csv(root_dir+'backup_1hole_configurations.txt',header=None).values.tolist()
for i in rad_config_n_labels:
    i[1]= 'rad,'+i[1]

aug_config_n_labels=pd.read_csv(root_dir+'backup_2holes_configurations.txt',header=None).values.tolist()
for i in aug_config_n_labels:
    i[1]= 'aug,'+i[1]


config_n_labels = rad_config_n_labels + aug_config_n_labels
config_n_labels_dict={config_n_labels[i][1]:config_n_labels[i][0] for i in range(len(config_n_labels))}


# calc_res structure: "quantum_numbers;calc_method"
#
#   quantum_numbers structure: "orb,jj2,eig"
#       orb: configuration label
#       jj2: 2x total angular momentum
#       eig: eigenvalue
#       
#   calc_method values (cv):
#       0: Converged successfully. Exits pool.
#       1: Failed first try. Implement the 10 cycles method
#       2: Failed second try. Use B-splines (method 5) for failed orbital.
#       3: Failed third try. Add B-splines for the new failed orbital.
#      -1: Failed automatic convergence. Exits pool and should be done by hand
#      -2: Calculation of max eigenvalue
#      -3: Calculation of max jj2
#      -4: Initial job. Always sent by master, never received.
#       
#       For calc_method values>0, the value is accompanied by the failed orbitals (i.e. "1:4s,2s")
#       For calc_method values=-4, the value is accompanied by the configuration (i.e. "4s;-4:(1s)2 (2s)2 (2p)6 (3s)2 (3p)6 (3d)10 (5s)1")
#       For calc_method values=-3, the q.n. are composed of only the label and the calc_method is accompanied by the max jj2. (i.e. "4s;-3:3")
#       For calculation values=-2, the q.n. are composed of only the label and jj2, and the calc_method is acoompanied by the max eig (i.e. "4s,3;-2:3")
#       7|4s,3,1;2:2p
#
if rank == 0:
    #array containing idle slave processes
    idle_slaves=list(range(total_ranks))[1:]
    work_pool=[]
    if calc_step == 0:
        #Setup initial work pool


        for i in config_n_labels:
            work_pool.append(i[1].strip()+';'+'-4'+':')
        #print('Done...')


        #by hand list
        failed_convergence = []
        #Successfully converged list
        converged_list = []


        while (len(idle_slaves)<total_ranks-1) or (len(work_pool)>0):
            print(f'Idle Slaves: {idle_slaves}',flush=True) if len(idle_slaves)>0 else print('',flush=True)

            #pprint.pprint(work_pool)
            if len(work_pool)!=0 and len(idle_slaves)!=0:
                print(f'Work: {work_pool[0]}\n',flush=True)
                # Gives a job from pool to slave.
                slave_rank = idle_slaves.pop(0)

                comm.send(obj=work_pool.pop(0),dest=int(slave_rank))
            else:
                print(f'Idle Slaves: {idle_slaves}',flush=True) if len(idle_slaves)>0 else print('',flush=True)
                slave_rank, calc_res = str(comm.recv(source=MPI.ANY_SOURCE)).split("|")
                #print(calc_res)
                quantum_numbers,calc_res_vals = calc_res.split(';')
                calc_res_method , calc_res_params = calc_res_vals.split(":")
                calc_res_method= int(calc_res_method)
                if calc_res_method==-1:
                    failed_convergence.append(quantum_numbers.split(','))
                    #print(f'Failed: {quantum_numbers}',flush=True)
                elif calc_res_method != 0 :

                    if calc_res_method == -3:
                        max_jj2=int(calc_res_params)
                        while max_jj2>=0:
                            work_pool.append(quantum_numbers+','+str(max_jj2)+';'+str(calc_res_method)+':')
                            max_jj2-=2

                    elif calc_res_method == -2:
                        calc_res_params = calc_res_params.split(',')
                        if len(calc_res_params)>=2:
                            max_eig=int(calc_res_params[0])
                            eig_test_converged=calc_res_params[1]
                            for i in range(max_eig):
                                if i!=0: work_pool.append(quantum_numbers+','+str(i)+';'+'-2'+':')
                            if eig_test_converged=='0':
                                #print(f'Failed: {quantum_numbers}\n',flush=True)
                                work_pool.append(quantum_numbers+',0'+';'+'1'+':')
                            else:
                                #print(f'Converged: {calc_res}\n',flush=True)

                                converged_list.append(quantum_numbers.split(',')+ [0] + calc_res_params[-3:])
                    else:
                        work_pool.append(calc_res)
                else:
                    #print(f'Converged: {calc_res}\n',flush=True)
                    converged_list.append((quantum_numbers+','+calc_res_params).split(','))
                    #print(f'Converged: {quantum_numbers}',flush=True)

                idle_slaves.append(slave_rank)

        pd.DataFrame(failed_convergence,columns = ['Config type','Label','2jj','eig']).sort_values(by=['Config type','Label','2jj','eig'],ascending=[False,True,True,True]).to_csv(root_dir+'byHand.csv',index=False)

        pd.DataFrame(converged_list,columns=['Config type','Label','2jj','eig','Energy','En diff','Max Overlap']).sort_values(by=['Config type','Label','2jj','eig'],ascending=[False,True,True,True]).to_csv(root_dir+'converged.csv',index=False)


    calc_sat_opt=None
    if calc_step==1 or calc_step==4:
        if calc_step ==4:
            while calc_sat_opt is None:
                sat_opt=input('Calculate satellite transitions?(y/n): ')
                if sat_opt=='y' or sat_opt=='Y':
                    calc_sat_opt = True
                elif sat_opt=='n' or sat_opt=='N':
                    calc_sat_opt = False
                else:
                    print('Please input a valid option...')

        final_state_res=[]
        df = pd.read_csv(root_dir+'byHand.csv',dtype=str).values.tolist()+pd.read_csv(root_dir+'converged.csv',dtype=str)[['Config type','Label','2jj','eig']].values.tolist()
        for i in df:
            work_pool.append(','.join(i)+';4:')

        while (len(idle_slaves)<total_ranks-1) or (len(work_pool)>0):
            print(f'Idle Slaves: {idle_slaves}',flush=True) if len(idle_slaves)>0 else print('',flush=True)

            #pprint.pprint(work_pool)
            if len(work_pool)!=0 and len(idle_slaves)!=0:
                print(f'Work: {work_pool[0]}\n',flush=True)
                # Gives a job from pool to slave.
                slave_rank = idle_slaves.pop(0)
                
                comm.send(obj=work_pool.pop(0),dest=int(slave_rank))
            else:
                print(f'Idle Slaves: {idle_slaves}',flush=True) if len(idle_slaves)>0 else print('',flush=True)
                slave_rank, calc_res = str(comm.recv(source=MPI.ANY_SOURCE)).split("|")

                quantum_numbers,calc_res_vals = calc_res.split(';')
                _ , calc_res_params = calc_res_vals.split(":")

                final_state_res.append((quantum_numbers+','+calc_res_params).split(','))

                idle_slaves.append(slave_rank)
                


        pd.DataFrame(final_state_res,columns=['Config type','Label','2jj','eig','Configuration','Energy','En diff','Max Overlap']).sort_values(by=['Config type','Label','2jj','eig'],ascending=[False,True,True,True]).to_csv(root_dir+'all_converged.csv',index=False)
    
    
    if calc_step == 2 or calc_step==4:
        while calc_sat_opt is None:
            sat_opt=input('Calculate satellite transitions?(y/n): ')
            if sat_opt=='y' or sat_opt=='Y':
                calc_sat_opt = True
            elif sat_opt=='n' or sat_opt=='N':
                calc_sat_opt = False
            else:
                print('Please input a valid option...')
        

        total_rad_trans,total_aug_trans,total_sat_trans=0,0,0
        df = pd.read_csv(root_dir + 'all_converged.csv').sort_values('Energy',ascending=True)[['Config type','Label','2jj','eig','Energy','Configuration']].to_numpy(dtype=str)

        if os.path.exists(root_dir+'/transitions'):
            shutil.rmtree(root_dir+'/transitions')

        for i in range(len(df)):
            f_config_type,f_label,f_jj2,f_eig,f_en,f_config=df[i]
            f_qn = ','.join([f_config_type,f_label,f_jj2,f_eig])

            for j in df[i+1:]:
                i_config_type,i_label,i_jj2,i_eig,i_en,i_config=j

                i_qn = ','.join([i_config_type,i_label,i_jj2,i_eig])
                en_dif = float(i_en) - float(f_en)
                
                valid_trans=True
                if   i_config_type == 'aug' and f_config_type == 'rad':
                    valid_trans=False
                elif i_config_type == 'rad' and f_config_type == 'rad':
                    trans_type = 'diagram'
                    total_rad_trans+=1
                elif i_config_type == 'rad' and f_config_type == 'aug':
                    trans_type = 'auger'
                    total_aug_trans+=1
                else:
                    if calc_sat_opt:
                        trans_type = 'satellite'
                        total_sat_trans+=1
                    else:
                        valid_trans=False
                
                if valid_trans:work_pool.append(i_qn+';'+'5:'+trans_type+','+f_qn+','+str(en_dif)+','+i_config+','+f_config)


        #print(work_pool[0])
        #pbar = tqdm.tqdm(total=len(work_pool),bar_format='{bar:10}')
        total_transitions=len(work_pool)
        print('\n\n\n')
        pbar_all = tqdm.tqdm(total=total_transitions,bar_format='{l_bar}{bar:20}{r_bar}{bar:-20b}',position=3,leave=False)
        pbar_all.set_description('All Transitions\t\t')
        pbar_rad = tqdm.tqdm(total=total_rad_trans,bar_format='{l_bar}{bar:20}| {n_fmt}/{total_fmt}{postfix}',position=0,leave=False)
        pbar_rad.set_description('Diagram Transitions\t')
        pbar_aug = tqdm.tqdm(total=total_aug_trans,bar_format='{l_bar}{bar:20}| {n_fmt}/{total_fmt}{postfix}',position=1,leave=False)
        pbar_aug.set_description('Auger Transitions\t')
        if calc_sat_opt:
            pbar_sat = tqdm.tqdm(total=total_sat_trans,bar_format='{l_bar}{bar:20}| {n_fmt}/{total_fmt}{postfix}',position=2,leave=False)
            pbar_sat.set_description('Satellite Transitions\t')

        rad_arr=[]
        aug_arr=[]
        sat_arr=[]

        tot_count=0
        rad_count=0
        aug_count=0
        sat_count=0
        while (len(idle_slaves)<total_ranks-1) or (len(work_pool)>0):
            
            #print(f'Idle Slaves: {idle_slaves}',flush=True) if len(idle_slaves)>0 else print('',flush=True)

            #pprint.pprint(work_pool)



            if len(work_pool)!=0 and len(idle_slaves)!=0:
		#os.sys('clear')
                #print(f'Work: {work_pool[0]}\n',flush=True)
                # Gives a job from pool to slave.
                slave_rank = idle_slaves.pop(0)
                
                comm.send(obj=work_pool.pop(0),dest=int(slave_rank))
            else:
                tot_count+=1
                slave_rank, calc_res = str(comm.recv(source=MPI.ANY_SOURCE)).split("|")
                

                

                i_qn,calc_res_vals = calc_res.split(';')
                i_config_type,i_label,i_jj2,i_eig=i_qn.split(',')
                
                _ , calc_res_params = calc_res_vals.split(":")

                if _!='-1':
                    trans_type,f_config_type,f_label,f_jj2,f_eig,rate,en_dif,i_config,f_config=calc_res_params.split(',')
                    f_qn=','.join([f_config_type,f_label,f_jj2,f_eig])

                    #rate=float(rate)*(float(i_jj2)+1)
                    

                    if trans_type == 'diagram':
                        rad_arr.append([i_label,i_jj2,i_eig,i_config,f_label,f_jj2,f_eig,f_config,rate,en_dif])
                        rad_count+=1
                        
                            
                    elif trans_type == 'auger':
                        aug_arr.append([i_label,i_jj2,i_eig,i_config,f_label,f_jj2,f_eig,f_config,rate,en_dif])
                        aug_count+=1
                        
                            
                    else:
                        sat_arr.append([i_label,i_jj2,i_eig,i_config,f_label,f_jj2,f_eig,f_config,rate,en_dif])
                        sat_count+=1
                        
                            

                    if tot_count>=total_transitions//1000000:
                        pbar_all.update(tot_count)
                        tot_count=0
                        pbar_rad.update(rad_count)
                        rad_count=0
                        pbar_aug.update(aug_count)
                        aug_count=0
                        if calc_sat_opt:
                            pbar_sat.update(sat_count)
                            sat_count=0



                idle_slaves.append(slave_rank)

        pbar_all.close()
        pbar_rad.close()
        pbar_aug.close()
        if calc_sat_opt:pbar_sat.close()
        os.system('clear')

        pd.DataFrame(rad_arr,columns=['Initial Config Label','Initial Config 2jj','Initial Config eig','Initial Config','Final Config Label','Final Config 2jj','Final Config eig','Final Config','Rate (s-1)','Energy (eV)']).sort_values(['Initial Config Label','Initial Config 2jj','Initial Config eig','Final Config Label','Final Config 2jj','Final Config eig']).to_csv(root_dir+'rates_rad.csv',index=False)
        pd.DataFrame(aug_arr,columns=['Initial Config Label','Initial Config 2jj','Initial Config eig','Initial Config','Final Config Label','Final Config 2jj','Final Config eig','Final Config','Rate (s-1)','Energy (eV)']).sort_values(['Initial Config Label','Initial Config 2jj','Initial Config eig','Final Config Label','Final Config 2jj','Final Config eig']).to_csv(root_dir+'rates_auger.csv',index=False)
        if calc_sat_opt:pd.DataFrame(sat_arr,columns=['Initial Config Label','Initial Config 2jj','Initial Config eig','Initial Config','Final Config Label','Final Config 2jj','Final Config eig','Final Config','Rate (s-1)','Energy (eV)'],).sort_values(['Initial Config Label','Initial Config 2jj','Initial Config eig','Final Config Label','Final Config 2jj','Final Config eig']).to_csv(root_dir+'rates_satellite.csv',index=False)
    if calc_step == 3 or calc_step ==4:
        if calc_step ==4:
            while calc_sat_opt is None:
                sat_opt=input('Calculate satellite transitions?(y/n): ')
                if sat_opt=='y' or sat_opt=='Y':
                    calc_sat_opt = True
                elif sat_opt=='n' or sat_opt=='N':
                    calc_sat_opt = False
                else:
                    print('Please input a valid option...')

        df_radrate=pd.read_csv(root_dir+'rates_rad.csv')
        df_radrate['Rate (s-1)'] = pd.to_numeric(df_radrate['Rate (s-1)'],errors='coerce').fillna(0)
        df_radrate['Partial width']=df_radrate['Rate (s-1)']*(df_radrate['Initial Config 2jj']+1)*hbar
        grouped_df_radrate_level = df_radrate.groupby(['Initial Config Label','Initial Config 2jj','Initial Config eig'])['Rate (s-1)'].sum().reset_index()
        grouped_df_radrate_subshell = grouped_df_radrate_level.groupby(['Initial Config Label'])['Rate (s-1)'].sum().reset_index()


        df_augrate=pd.read_csv(root_dir+'rates_auger.csv')
        df_augrate['Rate (s-1)'] = pd.to_numeric(df_augrate['Rate (s-1)'],errors='coerce').fillna(0)
        df_augrate['Partial width']=df_augrate['Rate (s-1)']*(df_augrate['Initial Config 2jj']+1)*hbar
        grouped_df_augrate_level = df_augrate.groupby(['Initial Config Label','Initial Config 2jj','Initial Config eig'])['Rate (s-1)'].sum().reset_index()
        grouped_df_augrate_subshell = grouped_df_augrate_level.groupby(['Initial Config Label'])['Rate (s-1)'].sum().reset_index()

        if calc_sat_opt:
            df_satrate=pd.read_csv(root_dir+'rates_satellite.csv')
            df_satrate['Rate (s-1)'] = pd.to_numeric(df_satrate['Rate (s-1)'],errors='coerce').fillna(0)
            df_satrate['Partial width']=df_satrate['Rate (s-1)']*(df_satrate['Initial Config 2jj']+1)*hbar
            grouped_df_satrate_level = df_satrate.groupby(['Initial Config Label','Initial Config 2jj','Initial Config eig'])['Rate (s-1)'].sum().reset_index()
            grouped_df_satrate_subshell = grouped_df_satrate_level.groupby(['Initial Config Label'])['Rate (s-1)'].sum().reset_index()

        level_multiplicity_dict = {}
        df_states = pd.read_csv(root_dir+'all_converged.csv')[['Label','2jj']]
        grouped_df_states=df_states.groupby('Label').agg(Count=('2jj', 'count'), Sum_of_2jj=('2jj', 'sum')).reset_index()

        grouped_df_states['Multiplicity'] = grouped_df_states['Sum_of_2jj'] + grouped_df_states['Count']
        grouped_df_states.reset_index(drop=True, inplace=True)

        level_multiplicity_dict={}
        for index, row in grouped_df_states.iterrows():
            key = row['Label']
            multiplicity = row['Multiplicity']
            level_multiplicity_dict[key]=multiplicity
        
        #print(grouped_df_radrate_level)
        tot_rad_rate_level_dict={}
        for index, row in grouped_df_radrate_level.iterrows():
            key = f"{row['Initial Config Label']},{row['Initial Config 2jj']},{row['Initial Config eig']}"
            value = row['Rate (s-1)']
            tot_rad_rate_level_dict[key]=value
        

        tot_rad_rate_subshell_dict={}
        for index, row in grouped_df_radrate_subshell.iterrows():
            key = f"{row['Initial Config Label']}"
            value = row['Rate (s-1)']
            tot_rad_rate_subshell_dict[key]=value
        
        
        
        tot_aug_rate_level_dict={}
        for index, row in grouped_df_augrate_level.iterrows():
            key = f"{row['Initial Config Label']},{row['Initial Config 2jj']},{row['Initial Config eig']}"
            value = row['Rate (s-1)']
            tot_aug_rate_level_dict[key]=value
        
        tot_aug_rate_subshell_dict={}
        for index, row in grouped_df_augrate_subshell.iterrows():
            key = f"{row['Initial Config Label']}"
            value = row['Rate (s-1)']
            tot_aug_rate_subshell_dict[key]=value
            
        if calc_sat_opt:
            tot_sat_rate_level_dict={}
            for index, row in grouped_df_satrate_level.iterrows():
                key = f"{row['Initial Config Label']},{row['Initial Config 2jj']},{row['Initial Config eig']}"
                value = row['Rate (s-1)']
                tot_sat_rate_level_dict[key]=value

            tot_sat_rate_subshell_dict={}
            for index, row in grouped_df_satrate_subshell.iterrows():
                key = f"{row['Initial Config Label']}"
                value = row['Rate (s-1)']
                tot_sat_rate_subshell_dict[key]=value
            

        tot_rate_level_dict={}
        for key in tot_rad_rate_level_dict:
            tot_rate_level_dict[key]=tot_rad_rate_level_dict[key]
        for key in tot_aug_rate_level_dict:
            value_rad=tot_rate_level_dict.get(key)
            if value_rad is None:value_rad=0
            tot_rate_level_dict[key]=value_rad+tot_aug_rate_level_dict[key]
        if calc_sat_opt:
            for key in tot_sat_rate_level_dict:
                value_aug_rad=tot_rate_level_dict.get(key)
                if value_aug_rad is None:value_aug_rad=0
                tot_rate_level_dict[key]=value_aug_rad+tot_sat_rate_level_dict[key]
        
        tot_rate_subshell_dict={}
        for key in tot_rad_rate_subshell_dict:
            tot_rate_subshell_dict[key]=tot_rad_rate_subshell_dict[key]
        for key in tot_aug_rate_subshell_dict:
            value_rad=tot_rate_subshell_dict.get(key)
            if value_rad is None:value_rad=0
            tot_rate_subshell_dict[key]=value_rad+tot_aug_rate_subshell_dict[key]
        if calc_sat_opt:
            for key in tot_sat_rate_subshell_dict:
                value_aug_rad=tot_rate_subshell_dict.get(key)
                if value_aug_rad is None:value_aug_rad=0
                tot_rate_subshell_dict[key]=value_aug_rad+tot_sat_rate_subshell_dict[key]




        #pprint.pprint(tot_rad_rate_level_dict)
        #print('--------------------------------------------')
        #pprint.pprint(tot_aug_rate_level_dict)
        #print('--------------------------------------------')
        #pprint.pprint(tot_rate_level_dict)
        spectrum_header=['Initial Config Label','Initial Config 2jj','Initial Config eig','Initial Config','Final Config Label','Final Config 2jj','Final Config eig','Final Config','Intensity (a.u.)','Energy (eV)','Energy width (eV)']

        df_radrate = df_radrate.sort_values(by=['Initial Config Label','Initial Config 2jj','Initial Config eig','Final Config Label','Final Config 2jj','Final Config eig'])
        df_radrate_np = df_radrate.values
        for i in range(len(df_radrate_np)):
            ini_qn = ','.join([df_radrate_np[i][0],str(df_radrate_np[i][1]),str(df_radrate_np[i][2])])
            ini_jj2= df_radrate_np[i][1]

            fin_qn = ','.join([df_radrate_np[i][4],str(df_radrate_np[i][5]),str(df_radrate_np[i][6])])
            fin_jj2= df_radrate_np[i][5]

            branching_ratio=df_radrate_np[i][-3]/tot_rad_rate_level_dict[ini_qn]
            fluorescence_yield = tot_rad_rate_level_dict[ini_qn]/tot_rate_level_dict[ini_qn]
            df_radrate_np[i][-3]=(ini_jj2+1)/level_multiplicity_dict[df_radrate_np[i][0]] * branching_ratio * fluorescence_yield

            #print(f'{ini_qn} {fin_qn}     {branching_ratio}')
            ini_tot_rate = tot_rate_level_dict[ini_qn]
            fin_tot_rate = tot_rate_level_dict.get(fin_qn)
            if fin_tot_rate is None: fin_tot_rate = 0

            df_radrate_np[i][-1] = hbar*(ini_tot_rate + fin_tot_rate)  # Calculates transition width

        df = pd.DataFrame(df_radrate_np)
        df.to_csv(root_dir+'spectrum_diagram.csv',header=spectrum_header,index=False)   
        if calc_sat_opt:
            df_satrate = df_satrate.sort_values(by=['Initial Config Label','Initial Config 2jj','Initial Config eig','Final Config Label','Final Config 2jj','Final Config eig'])
            df_satrate_np=df_satrate.values
            for i in range(len(df_satrate_np)):
                #print(i)
                ini_qn = ','.join([df_satrate_np[i][0],str(df_satrate_np[i][1]),str(df_satrate_np[i][2])])
                ini_jj2= df_satrate_np[i][1]

                fin_qn = ','.join([df_satrate_np[i][4],str(df_satrate_np[i][5]),str(df_satrate_np[i][6])])
                fin_jj2= df_satrate_np[i][5]

                branching_ratio=df_satrate_np[i][-3]/tot_sat_rate_level_dict[ini_qn]
                fluorescence_yield = tot_rad_rate_subshell_dict[df_satrate_np[i][0].split('_')[0]]/tot_rate_subshell_dict[df_satrate_np[i][0].split('_')[0]]
                df_satrate_np[i][-3]=(ini_jj2+1)/level_multiplicity_dict[df_satrate_np[i][0]] * branching_ratio * fluorescence_yield

                ini_tot_rate = tot_rate_level_dict[ini_qn]
                fin_tot_rate = tot_rate_level_dict.get(fin_qn)
                if fin_tot_rate is None: fin_tot_rate = 0
                if ini_tot_rate + fin_tot_rate ==0:print(ini_tot_rate + fin_tot_rate)
                df_satrate_np[i][-1] = hbar*(ini_tot_rate + fin_tot_rate)/fluorescence_yield

            df = pd.DataFrame(df_satrate_np)
            df.to_csv(root_dir+'spectrum_satellite.csv',header=spectrum_header,index=False)   


        
        
        
        
        
        
    if calc_step == 5:
        fig,ax=plt.subplots(1,1,figsize=(5,4))

        df_diag=pd.read_csv(root_dir+'spectrum_diagram.csv')
        df_diag=df_diag[['Energy (eV)','Intensity (a.u.)','Energy width (eV)','Initial Config Label','Final Config Label']]

        df_sat=pd.read_csv(root_dir+'spectrum_satellite.csv')
        df_sat=df_sat[['Energy (eV)','Intensity (a.u.)','Energy width (eV)','Initial Config Label','Final Config Label']]

        df_np=np.concatenate((df_diag.to_numpy(),df_sat.to_numpy()),axis=0)
        pprint.pprint(df_np)
        en_x=np.linspace(7950,8200,10000)
        en_y=en_x*0
        for i in df_diag.to_numpy():
            en_y+=i[1]*voigt_profile(en_x-i[0],0,i[2])
            if i[0]>en_x[0] and i[0]<en_x[-1]:
                plt.plot(en_x,i[1]*voigt_profile(en_x-i[0],0,i[2]),':')
        plt.plot(en_x,en_y)
        plt.legend()
        plt.show()

    if calc_step == 6:
        overlap_thresh_flag=False
        while not overlap_thresh_flag:
            overlap_thresh=input('Please set the overlap threshold: ')
            if is_digit_with_scientific_notation(overlap_thresh):
                overlap_thresh_flag = True
                overlap_thresh = float(overlap_thresh)
            else: print('Please input a valid value:')

        en_thresh_flag=False
        while not en_thresh_flag:
            en_thresh=input('Please set the energy threshold: ')
            if is_digit_with_scientific_notation(en_thresh):
                en_thresh_flag = True
                en_thresh = float(en_thresh)
            else: print('Please input a valid value.')
        

        what_states_flag=False
        while not what_states_flag:
            what_states=input('What states should be included? (1 -Failed; 2 -All): ')
            if what_states=='1':
                states_array=byHand_array=pd.read_csv(root_dir+'byHand.csv').values
                what_states_flag=True
            elif what_states=='2':
                byHand_array=pd.read_csv(root_dir+'byHand.csv')
                converged_array = pd.read_csv(root_dir+'converged.csv')[['Config type','Label','2jj','eig']]
                states_array=pd.concat([byHand_array,converged_array]).values
                what_states_flag=True
            else:print('Please input a valid option.')
        def is_in_tmux():
            return 'TMUX' in os.environ

        server = libtmux.Server()
        if is_in_tmux():
            session = server.attached_sessions[0]
            window = session.attached_window
            pane_tail=window.split_window(attach=False,vertical=False)
        for i in states_array:
            print(i)
            hole_type,label,jj2,eig=i.astype(str)
            cwd=qn_to_dir(','.join([hole_type,label,jj2,eig]),root_dir)
            os.system('clear')
            if is_in_tmux():pane_tail.send_keys('less '+cwd+label+'_'+jj2+'_'+eig+'.f06')
            with open(cwd+label+'_'+jj2+'_'+eig+'.f06','r',encoding='latin-1') as f06_file:
                result = check_convergence_interface(f06_file.readlines(),True)
                if type(result)==bool:
                    result_bool=False
                else: result_bool=result[0]
                if not result_bool:
                    print(f'------------------------------------------------------\nHole Type: {hole_type}    Label: {label}    2jj: {jj2}   Eig: {eig}\n------------------------------------------------------')
                    conv_flag=False
                    if type(result)==bool:
                        print('Failed Convergence.')
                    else:
                        print(f'Orbital {result[1]} failed.')
                else:
                    en_dif=float(result[2])
                    max_overlap=float(result[3])
                    overlap=result[4].replace(' ','')
                    conv_flag=True
                    if en_dif>en_thresh or max_overlap>overlap_thresh:
                        print(f'------------------------------------------------------\nHole Type: {hole_type}    Label: {label}    2jj: {jj2}   Eig: {eig}\n------------------------------------------------------')
                        print(f'Energy: {result[1]}\tEn.Dif: {result[2]}\nMax Overlap: {result[3]}\t\t{overlap}')
                        conv_flag=False
            if not conv_flag:
                print('\n\nOptions:\n- e : Edit f05 file\n- l : Read f06 file\n- r : Run MCDF\n- n : Next state\n- x : Exit Interface')
                while True:
                    option = input('Insert chosen option: ')
                    if option == 'e':
                        os.system('nano '+cwd+label+'_'+jj2+'_'+eig+'.f05')
                    if option == 'l':
                        os.system('less '+cwd+label+'_'+jj2+'_'+eig+'.f06')
                    if option == 'r':
                        if is_in_tmux():
                            pane_tail.send_keys('q')
                            pane_tail.send_keys('tail -F '+cwd+label+'_'+jj2+'_'+eig+'.f06')
                        subprocess.call(mcdf_exe,cwd=cwd)
                        if is_in_tmux():
                            pane_tail.send_keys('\x03')
                            pane_tail.send_keys('less '+cwd+label+'_'+jj2+'_'+eig+'.f06')
                    if option == 'n':
                        pane_tail.send_keys('q')
                        break
                    if option == 'x':
                        for i in idle_slaves:
                            comm.send(';-5:',dest=int(i))
                        if is_in_tmux():pane_tail.cmd('kill-pane')
                        MPI.Finalize()
                        exit()
                    os.system('clear')
                    if option in ['e','l','r'] or option not in ['n','x']:
                            print(f'------------------------------------------------------\nHole Type: {hole_type}    Label: {label}    2jj: {jj2}   Eig: {eig}\n------------------------------------------------------')
                            with open(cwd+label+'_'+jj2+'_'+eig+'.f06','r',encoding='latin-1') as f06_file:
                                result = check_convergence_interface(f06_file.readlines(),True)
                                if type(result)==bool:
                                    result_bool=False
                                else: result_bool=result[0]
                            if not result_bool:
                                if type(result)==bool:
                                    print('Failed Convergence.')
                                else:
                                    print(f'Orbital {result[1]} failed.')
                            else:
                                overlap=result[4].replace(' ','')
                                print(f'Energy: {result[1]}\tEn.Dif: {result[2]}\nMax Overlap: {result[3]}\t\t{overlap}')
                            print('\n\nOptions:\n- e : Edit f05 file\n- l : Read f06 file\n- r : Run MCDF\n- n : Next state\n- x : Exit Interface')
        if is_in_tmux():pane_tail.cmd('kill-pane')
         
    if calc_step not in allowed_calc:
        comm.Abort()


    print('\n\nJob has finished')
    for i in idle_slaves:
        comm.send(';-5:',dest=int(i))
    MPI.Finalize()

    print("--- %s seconds ---" % (time.time() - start_time))



else:
    # Slave ranks
    while True:
        #print(f'Waiting for job -> {rank}', flush=True)
        work = comm.recv(source=0)
        #print(f'Starting job -> {rank}', flush=True)
        result = do_work(work)
        if breakflag:
            break
        comm.send(f'{rank}|{result}', 0)

