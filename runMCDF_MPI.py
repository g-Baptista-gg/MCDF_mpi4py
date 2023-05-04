from mpi4py import MPI
import pandas as pd
import os, subprocess, shutil, csv
import time

# For debugging: mpirun -n 4 xterm -hold -e python runMCDF_MPI.py 
# TODO: IMPORTANT- Change f05 templates in case Z>48

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

rad_config_n_labels = pd.read_csv('1hole_configurations.txt',header=None).values.tolist()
for i in rad_config_n_labels:
    i[1]= 'rad,'+i[1]

aug_config_n_labels=pd.read_csv('2holes_configurations.txt',header=None).values.tolist()
for i in aug_config_n_labels:
    i[1]= 'aug,'+i[1]

config_n_labels = rad_config_n_labels + aug_config_n_labels
#config_n_labels = pd.read_csv('1hole_configurations.txt',header=None).values.tolist()+pd.read_csv('2holes_configurations.txt',header=None).values.tolist()
config_n_labels_dict={config_n_labels[i][1]:config_n_labels[i][0] for i in range(len(config_n_labels))}



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
            print('???????')
            comm.Abort()
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
                            


def find_jj2(quantum_numbers):
    print(quantum_numbers,flush=True)
    cwd = qn_to_dir(quantum_numbers=quantum_numbers,root_dir=root_dir)
    config=label_to_config(quantum_numbers)
    if not (os.path.exists(cwd)):
        os.makedirs(cwd)
    if not (os.path.exists(cwd+'tmp/')):
        os.makedirs(cwd+'tmp/')

    electron_number_=(electron_number-1 if ('_' in quantum_numbers) else electron_number)

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
                                  .replace('mcdfgmeelectronnb', (str(electron_number-1) if ('_' in quantum_numbers) else str(electron_number)))\
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
            return quantum_numbers+';'+'-2'+':'+str(max_eig)+','+'1,'+res[1]+','+res[2]+','+res[3]
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
                                  .replace('mcdfgmeelectronnb', (str(electron_number-1) if ('_' in quantum_numbers) else str(electron_number)))\
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
                                  .replace('mcdfgmeelectronnb', (str(electron_number-1) if ('_' in quantum_numbers) else str(electron_number)))\
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
                                  .replace('mcdfgmeelectronnb', (str(electron_number-1) if ('_' in quantum_numbers) else str(electron_number)))\
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
                                  .replace('mcdfgmeelectronnb', (str(electron_number-1) if ('_' in quantum_numbers) else str(electron_number)))\
                                  .replace('mcdfgmeneigv',str(int(eig)+1))\
                                  .replace('mcdfgmefailledorbital',failed_orbs[0]+'  1 5 0 1 :\n    '+failed_orbs[1]+'  1 5 0 1 :'))
    with open(cwd +'mdfgme.dat','w') as dat_file:
        dat_file.write(mdfgmeFile.replace('f05FileName',label+'_'+jj2+'_'+eig))
    subprocess.call(mcdf_exe,cwd=cwd,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
    with open(cwd+label+'_'+jj2+'_'+eig+'.f06','r',encoding='latin-1') as f06_file:
        return check_convergence(f06_file.readlines(),False)
    
def get_parameters(quantum_numbers):
    cwd = qn_to_dir(quantum_numbers=quantum_numbers,root_dir=root_dir)
    label,jj2,eig=quantum_numbers.split(',')


def do_work(calc: str):
    global breakflag
    quantum_numbers,calc_method=calc.split(sep=';')
    #print(calc_method,flush=True)
    # current_dir = root_dir
    # if quantum_numbers!= '':
    #     current_dir += 'auger/' if ('aug' in quantum_numbers) else  'radiative/'
    #     for i in quantum_numbers.split(sep=','): current_dir+=i+'/'

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
            return (quantum_numbers+';0:'+res[1]+','+res[2]+','+res[3])

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
                return (quantum_numbers+';0:'+conv_n_orbs[1]+','+conv_n_orbs[2]+','+conv_n_orbs[3])
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
            return quantum_numbers+';0:'+res[1]+','+res[2]+','+res[3]
        
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
    return f05Template, f05Template_10steps, f05Template_10steps_Forbs



# Program starts by master asking for user inputs for atomic number and electron number, setting up f05 templates and broadcasting to slave ranks
if rank==0:
    os.system('clear')
    directory_name = 'Cu_4p'
    # directory_name = input('Directory name: ')
    atomic_number   = int(29)
    # atomic_number   = int(input('Atomic number: '))
    electron_number = int(29)
    # electron_number = int(input('Number of electrons: '))

    calc_step = int(input('----------------------------------------------------\nComputation Mehtods:\n----------------------------------------------------\nEnergy and WF calculations:\t0\nGet Parameters:\t\t\t1 \nRates:\t\t\t\t2\nSums:\t\t\t\t3\nGet Parameters + Rates + Sums:\t4\n----------------------------------------------------\nPlease enter what computation should be performed: '))

    start_time = time.time()
    
    templates = setupTemplates(atomic_number,electron_number)
    #print('Done setup templates')
    root_dir = os.getcwd()+'/'+directory_name+'/'

f05Template, f05Template_10steps, f05Template_10steps_Forbs = comm.bcast(templates,root=0)
root_dir = comm.bcast(root_dir,root=0)
electron_number = comm.bcast(electron_number,root=0)

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
                                converged_list.append(calc_res.split(','))
                    else:
                        work_pool.append(calc_res)
                else:
                    print(f'Converged: {calc_res}\n',flush=True)

                    converged_list.append(calc_res.split(','))
                    #print(f'Converged: {quantum_numbers}',flush=True)

                idle_slaves.append(slave_rank)

        for i in idle_slaves:
            comm.send(';-5:',dest=int(i))

        MPI.Finalize()

        # with open(root_dir+'byHand.csv','w') as file:
            # writer = csv.writer(file)
            # writer.writerow(['Config type','Label','2jj','eig'])
            # writer.writerows(failed_convergence)
        
        df= pd.DataFrame(failed_convergence,columns = ['Config type','Label','2jj','eig']).sort_values(by=['Config type','Label','2jj','eig'],ascending=[False,True,True,True]).to_csv(root_dir+'byHand.csv',index=False)

        # with open(root_dir+'converged.csv','w') as file:
        #     writer = csv.writer(file)
        #     writer.writerow(['Config type','Label','2jj','eig','Energy','Max Overlap'])
        #     writer.writerows(converged_list)

        df= pd.DataFrame(converged_list,columns=['Config type','Label','2jj','eig','Energy','En diff','Max Overlap']).sort_values(by=['Config type','Label','2jj','eig'],ascending=[False,True,True,True]).to_csv(root_dir+'converged.csv',index=False)


        print("--- %s seconds ---" % (time.time() - start_time))
    else:
        comm.Abort()





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

