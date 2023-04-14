from mpi4py import MPI

comm = MPI.COMM_WORLD
rank =comm.Get_rank()
total_ranks =comm.Get_size()


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
#       
#       For calc_method values>0, the value is accompanied by the failed orbitals (i.e. "1,4s,2s")
#
#   Examples:
#       "4s,2,1:2,4s,2s"


if rank == 0:
    #array containing idle slave processes
    idle_slaves=list(range(total_ranks))[1:]
    
    #dummy initial work pool
    work_pool = list(range(0,1000))

    #by hand list
    failed_convergence = []

    while (len(idle_slaves)<total_ranks-1) or (len(work_pool)>0):


        if len(idle_slaves)==0:
            # listen for slaves to give work to and gets result
            slave_rank, calc_res = str(comm.recv(source=MPI.ANY_SOURCE)).split(";")
            quantum_numbers,calc_res_params = calc_res.split(':')
            calc_res_method = calc_res_params.split(",")[0]

            if calc_res_method==-1:
                label,jj2,eig=calc_res.split(',')[:2]
                failed_convergence.append(quantum_numbers)
            elif calc_res_method != 0 :
                work_pool.append(calc_res)
        else:
            # give work to idle slaves
            slave_rank=idle_slaves.pop(0)

        if len(work_pool)!=0:
            comm.send(obj=work_pool.pop(0),dest=slave_rank)
        else:
            idle_slaves.append(slave_rank)

        
            

