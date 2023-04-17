from mpi4py import MPI
import pandas as pd

comm = MPI.COMM_WORLD
rank =comm.Get_rank()
total_ranks =comm.Get_size()


def find_jj2():
    #   Returns max jj2
    pass
def find_eig():
    #   Returns max eig
    pass
def no_cycles():
    #   Returns 0 if failed, 1 if successfull
    pass
def with_cycles():
    #   Returns 0 if failed followed by the failed orbital, 1 if successfull Ex: [0,"2p"]
    pass
def with_1orb():
    #   Returns 0 if failed followed by the failed orbitals, 1 if successfull Ex: [0,"2p_3p"]
    pass
def with_2orbs():
    #   Returns 0 if failed, 1 if successfull
    pass

def do_work(calc: str):
    quantum_numbers,calc_method=calc.split(sep=';')
    calc_method_value  = int(calc_method.split(sep=':')[0])
    calc_method_params = calc_method.split(sep=':')[1]
    if calc_method_value == -4:
        return (quantum_numbers+';'+'-3:'+str(find_jj2()))
    elif calc_method_value ==-3:
        return (quantum_numbers+';'+'-3:'+str(find_eig()))
    elif calc_method_value ==-2:
        no_cycles()
    elif calc_method_value == 1:
        with_cycles()
    elif calc_method_value == 2:
        with_1orb()
    elif calc_method_value == 3:
        with_2orbs()
    else:
        print('ERROR')
        MPI.Finalize()

def initTemplates(template,atomic_number,electron_number):
    f05=''.join(template.readlines())
    f05=f05.replace('mcdfgmeatomicnumber',str(atomic_number))
    f05=f05.replace('mcdfgmeelectronnb',str(electron_number))
    return f05

def setupTemplates(atomic_number,electron_number):
    #global f05Template_nuc, f05Template_10steps_nuc, f05Template_10steps_Forbs_nuc, f05RadTemplate_nuc, f05AugTemplate_nuc
    
    with open("f05_templates/f05_2019.f05", "r") as template:
        f05Template = initTemplates(template,atomic_number,electron_number)
    with open("f05_templates/f05_2019nstep1.f05", "r") as template:
        f05Template_10steps =  initTemplates(template,atomic_number,electron_number)
    with open("f05_templates/f05_2019nstep2.f05", "r") as template:
        f05Template_10steps_Forbs =  initTemplates(template,atomic_number,electron_number)
    return f05Template, f05Template_10steps, f05Template_10steps_Forbs



# Program starts by master asking for user inputs for atomic number and electron number, setting up f05 templates and broadcasting to slave ranks
if rank==0:
    atomic_number   =int(input('Atomic number: '))
    electron_number =int(input('Number of electrons: '))
    templates= setupTemplates(atomic_number,electron_number)
else:
    templates= None

f05Template, f05Template_10steps, f05Template_10steps_Forbs =comm.bcast(templates,root=0)

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
#
#

if rank == 0:
    #array containing idle slave processes
    idle_slaves=list(range(total_ranks))[1:]
    
    #Setup initial work pool
    config_n_labels = pd.read_csv('1hole_configurations.txt',header=None).values.tolist()+pd.read_csv('2holes_configurations.txt',header=None).values.tolist()
    work_pool=[]
    for i in config_n_labels:
        work_pool.append(i[1].strip()+';'+'-4'+':'+i[0].strip())
    print(work_pool[0])
    
    
    #by hand list
    failed_convergence = []


    while (len(idle_slaves)<total_ranks-1) or (len(work_pool)>0):


        if len(idle_slaves)==0:
            # listen for slaves to give work to and gets result
            slave_rank, calc_res = str(comm.recv(source=MPI.ANY_SOURCE)).split("|")
            quantum_numbers,calc_res_params = calc_res.split(';')
            calc_res_method = calc_res_params.split(":")[0]

            if calc_res_method==-1:
                failed_convergence.append(quantum_numbers)
            elif calc_res_method != 0 :
                #TODO create jobs for various jj2 and various eig for methods -3 and -2
                work_pool.append(calc_res)
        else:
            # give work to idle slaves
            slave_rank=idle_slaves.pop(0)

        if len(work_pool)!=0:
            comm.send(obj=work_pool.pop(0),dest=slave_rank)
        else:
            idle_slaves.append(slave_rank)
    #TODO: write output files
    MPI.Finalize()

else:
    # Slave ranks
    while True:
        do_work()

