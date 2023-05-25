from mpi4py import MPI
import pandas as pd
import os, subprocess, shutil, sys
import time,tqdm,re , pprint
import numpy as np
import matplotlib.pyplot as plt
from scipy.special import voigt_profile
import scienceplots
plt.style.use(['science'])


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
                if 'For orbital' in f06_file[-i-1]:
                    failed_orbital = f06_file[-i-1].split()[2].strip()
                    break
            return False, failed_orbital
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
                    if '(sec-1)' in f06_lines[-i-1]:
                        #print('Auger: ',f06_lines[-i-1].split()[0],flush=True)
                        rate=f06_lines[-i-1].split()[0]
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
            dir_confirmation = input('Directory already exists. Do you want to carry on with the calculation? (y/n): ')
            if dir_confirmation == 'y' or 'Y':
                dir_flag=True
        else:
            dir_flag=True

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
        electron_number = input('Number of electrons: ')
        if electron_number.isdigit():
            electron_number = int(electron_number)
            el_no_flag = True
        else:
            print('Please input a valid integer.')


    print(('-----------------------------------------------------\n|  Computation Mehtods:\t\t\t\t    |\n-----------------------------------------------------\n|  Energy and WF calculations:\t0\t\t    |\n|  Get Parameters:\t\t1\t\t    |\n|  Rates:\t\t\t2\t\t    |\n|  Sums:\t\t\t3 -> Single Thread  |\n|  Get Params + Rates + Sums:\t4 -> Single Thread  |\n|  Plot Spectra:\t\t5 -> Single Thread  |\n-----------------------------------------------------'))
    calc_step_flag=False
    while not calc_step_flag:
        calc_step = input('Please enter what computation should be performed: ')
        if calc_step.isdigit():
            calc_step=int(calc_step)
            if calc_step in [0,1,2,3,4,5]:
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

if calc_step==0:
    rad_config_n_labels = pd.read_csv('1hole_configurations.txt',header=None).values.tolist()
    for i in rad_config_n_labels:
        i[1]= 'rad,'+i[1]

    aug_config_n_labels=pd.read_csv('2holes_configurations.txt',header=None).values.tolist()
    for i in aug_config_n_labels:
        i[1]= 'aug,'+i[1]
else:
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
        #print('Setup config files.')
        if not (os.path.exists(root_dir)):
            os.makedirs(root_dir)
        shutil.copyfile('1hole_configurations.txt',root_dir+'backup_1hole_configurations.txt')
        rad_config_n_labels = pd.read_csv('1hole_configurations.txt',header=None).values.tolist()
        for i in rad_config_n_labels:
            i[1]= 'rad,'+i[1]

        shutil.copyfile('2holes_configurations.txt',root_dir+'backup_2holes_configurations.txt')
        aug_config_n_labels=pd.read_csv('2holes_configurations.txt',header=None).values.tolist()
        for i in aug_config_n_labels:
            i[1]= 'aug,'+i[1]

        config_n_labels = rad_config_n_labels + aug_config_n_labels


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
                    print(f'Failed: {quantum_numbers}',flush=True)
                elif calc_res_method != 0 :

                    if calc_res_method == -3:
                        print
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
                                print(f'Failed: {quantum_numbers}\n',flush=True)
                                work_pool.append(quantum_numbers+',0'+';'+'1'+':')
                            else:
                                print(f'Converged: {calc_res}\n',flush=True)

                                converged_list.append(quantum_numbers.split(',')+ [0] + calc_res_params[-3:])
                    else:
                        work_pool.append(calc_res)
                else:
                    print(f'Converged: {calc_res}\n',flush=True)
                    converged_list.append((quantum_numbers+','+calc_res_params).split(','))
                    #print(f'Converged: {quantum_numbers}',flush=True)

                idle_slaves.append(slave_rank)

        pd.DataFrame(failed_convergence,columns = ['Config type','Label','2jj','eig']).sort_values(by=['Config type','Label','2jj','eig'],ascending=[False,True,True,True]).to_csv(root_dir+'byHand.csv',index=False)

        pd.DataFrame(converged_list,columns=['Config type','Label','2jj','eig','Energy','En diff','Max Overlap']).sort_values(by=['Config type','Label','2jj','eig'],ascending=[False,True,True,True]).to_csv(root_dir+'converged.csv',index=False)


        
    if calc_step==1 or calc_step==4:
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
                    trans_type = 'satellite'
                    total_sat_trans+=1
                
                if valid_trans:work_pool.append(i_qn+';'+'5:'+trans_type+','+f_qn+','+str(en_dif)+','+i_config+','+f_config)



        #pbar = tqdm.tqdm(total=len(work_pool),bar_format='{bar:10}')
        total_transitions=len(work_pool)
        print('\n\n\n')
        pbar_all = tqdm.tqdm(total=total_transitions,bar_format='{l_bar}{bar:20}{r_bar}{bar:-20b}',position=3,leave=False)
        pbar_all.set_description('All Transitions\t\t')
        pbar_rad = tqdm.tqdm(total=total_rad_trans,bar_format='{l_bar}{bar:20}| {n_fmt}/{total_fmt}{postfix}',position=0,leave=False)
        pbar_rad.set_description('Diagram Transitions\t')
        pbar_aug = tqdm.tqdm(total=total_aug_trans,bar_format='{l_bar}{bar:20}| {n_fmt}/{total_fmt}{postfix}',position=1,leave=False)
        pbar_aug.set_description('Auger Transitions\t')
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

                    rate=float(rate)*(float(i_jj2)+1)

                    if trans_type == 'diagram':
                        rad_arr.append([i_label,i_jj2,i_eig,i_config,f_label,f_jj2,f_eig,f_config,rate,en_dif,rate*hbar])
                        rad_count+=1
                        
                            
                    elif trans_type == 'auger':
                        aug_arr.append([i_label,i_jj2,i_eig,i_config,f_label,f_jj2,f_eig,f_config,rate,en_dif,rate*hbar])
                        aug_count+=1
                        
                            
                    else:
                        sat_arr.append([i_label,i_jj2,i_eig,i_config,f_label,f_jj2,f_eig,f_config,rate,en_dif,rate*hbar])
                        sat_count+=1
                        
                            

                    if tot_count>=total_transitions//1000000:
                        pbar_all.update(tot_count)
                        tot_count=0
                        pbar_rad.update(rad_count)
                        rad_count=0
                        pbar_aug.update(aug_count)
                        aug_count=0
                        pbar_sat.update(sat_count)
                        sat_count=0



                idle_slaves.append(slave_rank)

        pbar_all.close()
        pbar_rad.close()
        pbar_aug.close()
        pbar_sat.close()
        os.system('clear')

        pd.DataFrame(rad_arr,columns=['Initial Config Label','Initial Config 2jj','Initial Config eig','Initial Config','Final Config Label','Final Config 2jj','Final Config eig','Final Config','Rate (s-1)','Energy (eV)','Energy width (eV)']).sort_values('Rate (s-1)',ascending=False).to_csv(root_dir+'rates_rad.csv',index=False)
        pd.DataFrame(aug_arr,columns=['Initial Config Label','Initial Config 2jj','Initial Config eig','Initial Config','Final Config Label','Final Config 2jj','Final Config eig','Final Config','Rate (s-1)','Energy (eV)','Energy width (eV)']).sort_values('Rate (s-1)',ascending=False).to_csv(root_dir+'rates_auger.csv',index=False)
        pd.DataFrame(sat_arr,columns=['Initial Config Label','Initial Config 2jj','Initial Config eig','Initial Config','Final Config Label','Final Config 2jj','Final Config eig','Final Config','Rate (s-1)','Energy (eV)','Energy width (eV)']).sort_values('Rate (s-1)',ascending=False).to_csv(root_dir+'rates_satellite.csv',index=False)
    if calc_step == 3 or calc_step ==4:

        df_radrate=pd.read_csv(root_dir+'rates_rad.csv')
        grouped_df_radrate = df_radrate.groupby(['Initial Config Label','Initial Config 2jj','Initial Config eig'])['Rate (s-1)'].sum().reset_index()

        df_augrate=pd.read_csv(root_dir+'rates_auger.csv')
        grouped_df_augrate = df_augrate.groupby(['Initial Config Label','Initial Config 2jj','Initial Config eig'])['Rate (s-1)'].sum().reset_index()

        df_satrate=pd.read_csv(root_dir+'rates_satellite.csv')
        grouped_df_satrate = df_satrate.groupby(['Initial Config Label','Initial Config 2jj','Initial Config eig'])['Rate (s-1)'].sum().reset_index()

        radrate_sum_dict={}
        for index, row in grouped_df_radrate.iterrows():
            key = f"{row['Initial Config Label']},{row['Initial Config 2jj']},{row['Initial Config eig']}"
            sum_value = row['Rate (s-1)']
            radrate_sum_dict[key]=sum_value
        
        augrate_sum_dict={}
        for index, row in grouped_df_augrate.iterrows():
            key = f"{row['Initial Config Label']},{row['Initial Config 2jj']},{row['Initial Config eig']}"
            sum_value = row['Rate (s-1)']
            augrate_sum_dict[key]=sum_value

        satrate_sum_dict={}
        for index, row in grouped_df_satrate.iterrows():
            key = f"{row['Initial Config Label']},{row['Initial Config 2jj']},{row['Initial Config eig']}"
            sum_value = row['Rate (s-1)']
            satrate_sum_dict[key]=sum_value

        totrate_sum_dict={}
        for key in radrate_sum_dict:
            totrate_sum_dict[key]=radrate_sum_dict[key]
        for key in augrate_sum_dict:
            if totrate_sum_dict.get(key) is None:
                totrate_sum_dict[key] = augrate_sum_dict[key]
            else:
                totrate_sum_dict[key] += augrate_sum_dict[key]
        for key in satrate_sum_dict:
            if totrate_sum_dict.get(key) is None:
                totrate_sum_dict[key] = satrate_sum_dict[key]
            else:
                totrate_sum_dict[key] += satrate_sum_dict[key]
        
        


        state_multiplicy_dict = {}
        df_states = pd.read_csv(root_dir+'all_converged.csv')[['Label','2jj']]
        grouped_df_states=df_states.groupby('Label').agg(Count=('2jj', 'count'), Sum_of_2jj=('2jj', 'sum')).reset_index()

        grouped_df_states['Multiplicity'] = grouped_df_states['Sum_of_2jj'] + grouped_df_states['Count']
        print(grouped_df_states)
        
        grouped_df_states.reset_index(drop=True, inplace=True)
    
        for index, row in grouped_df_states.iterrows():
            key = row['Label']
            multiplicity = row['Multiplicity']
            state_multiplicy_dict[key]=multiplicity
        
        spectrum_header = ['Initial Config Label','Initial Config 2jj','Initial Config eig','Initial Config','Final Config Label','Final Config 2jj','Final Config eig','Final Config','Intensity (a.u.)','Energy (eV)','Energy width (eV)','Branching Ratio']


        df_radrate['Branching Ratio'] = 0
        df_radrate_np = df_radrate.values

        
        for i in range(len(df_radrate_np)):
            ini_qn = ','.join([df_radrate_np[i][0],str(df_radrate_np[i][1]),str(df_radrate_np[i][2])])
            ini_tot_rate = totrate_sum_dict[ini_qn]
    
            fin_qn = ','.join([df_radrate_np[i][4],str(df_radrate_np[i][5]),str(df_radrate_np[i][6])])
            fin_tot_rate = totrate_sum_dict.get(fin_qn)
            
            ini_jj2=df_radrate_np[i][1]

            if fin_tot_rate is None:fin_tot_rate = 0

            trans_tot_rate=ini_tot_rate+fin_tot_rate

            branching_ratio=df_radrate_np[i][8]/trans_tot_rate
            
            df_radrate_np[i][10]=hbar*trans_tot_rate # Overwrite partial energy width with total transition Energy width
            df_radrate_np[i][11]= branching_ratio    # Add Branching Ratio

            multiplicity_ratio = (df_radrate_np[i][1]+1)/state_multiplicy_dict[df_radrate_np[i][0]]
            
            df_radrate_np[i][8] = multiplicity_ratio * branching_ratio # Overwrite partial Rate with Intensity in a.u.

        df = pd.DataFrame(df_radrate_np)
        df.to_csv(root_dir+'spectrum_diagram.csv',header=spectrum_header,index=False)

        df_augrate['Branching Ratio'] = 0
        df_augrate_np = df_augrate.values

        
        for i in range(len(df_augrate_np)):
            ini_qn = ','.join([df_augrate_np[i][0],str(df_augrate_np[i][1]),str(df_augrate_np[i][2])])
            ini_tot_rate = totrate_sum_dict[ini_qn]
    
            fin_qn = ','.join([df_augrate_np[i][4],str(df_augrate_np[i][5]),str(df_augrate_np[i][6])])
            fin_tot_rate = totrate_sum_dict.get(fin_qn)
            
            ini_jj2=df_augrate_np[i][1]

            if fin_tot_rate is None:fin_tot_rate = 0

            trans_tot_rate=ini_tot_rate+fin_tot_rate

            branching_ratio=df_augrate_np[i][8]/trans_tot_rate
            
            df_augrate_np[i][10]=hbar*trans_tot_rate # Overwrite partial energy width with total transition Energy width
            df_augrate_np[i][11]= branching_ratio    # Add Branching Ratio

            multiplicity_ratio = (df_augrate_np[i][1]+1)/state_multiplicy_dict[df_augrate_np[i][0]]
            
            df_augrate_np[i][8] = multiplicity_ratio * branching_ratio # Overwrite partial Rate with Intensity in a.u.

        df = pd.DataFrame(df_augrate_np)
        df.to_csv(root_dir+'spectrum_auger.csv',header=spectrum_header,index=False)

        df_satrate['Branching Ratio'] = 0
        df_satrate_np = df_satrate.values

        
        for i in range(len(df_satrate_np)):
            ini_qn = ','.join([df_satrate_np[i][0],str(df_satrate_np[i][1]),str(df_satrate_np[i][2])])
            ini_tot_rate = totrate_sum_dict[ini_qn]
    
            fin_qn = ','.join([df_satrate_np[i][4],str(df_satrate_np[i][5]),str(df_satrate_np[i][6])])
            fin_tot_rate = totrate_sum_dict.get(fin_qn)
            
            ini_jj2=df_satrate_np[i][1]

            if fin_tot_rate is None:fin_tot_rate = 0

            trans_tot_rate=ini_tot_rate+fin_tot_rate

            branching_ratio=df_satrate_np[i][8]/trans_tot_rate
            
            df_satrate_np[i][10]=hbar*trans_tot_rate # Overwrite partial energy width with total transition Energy width
            df_satrate_np[i][11]= branching_ratio    # Add Branching Ratio

            multiplicity_ratio = (df_satrate_np[i][1]+1)/state_multiplicy_dict[df_satrate_np[i][0]]
            
            df_satrate_np[i][8] = multiplicity_ratio * branching_ratio # Overwrite partial Rate with Intensity in a.u.

        df = pd.DataFrame(df_satrate_np)
        df.to_csv(root_dir+'spectrum_satellite.csv',header=spectrum_header,index=False)
        
        
        
        
    if calc_step == 5:
        fig,ax=plt.subplots(1,1,figsize=(5,4))
        df=pd.read_csv(root_dir+'spectrum_diagram.csv')
        df=df[['Energy (eV)','Intensity (a.u.)','Energy width (eV)']]
        df_np=df.to_numpy()
        pprint.pprint(df_np)
        en_x=np.linspace(7900,8100,10000)
        en_y=en_x*0
        for i in df_np:
            en_y+=i[1]*voigt_profile(en_x-i[0],0,i[2])
            if i[0]>en_x[0] and i[0]<en_x[-1]:
                plt.plot(en_x,i[1]*voigt_profile(en_x-i[0],0,i[2]),':')
        plt.plot(en_x,en_y)
        plt.show()
         
    if calc_step not in [0,1,2,3,4,5]:
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

