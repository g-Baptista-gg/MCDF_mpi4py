# MCDF_mpi4py
A repository containing a *Python3* script for spawning parallelized atomic structure calculations using the MPI communication protocol.

The executable, *mcdfgme2019.exe* is not available in this repository.

The script has only been tested in *UNIX* Operating Systems.

## Capabilities

- Level calculations for given 1-hole and 2-holes configurations
- Transition Calculations
  - Diagram Transitions
  - Auger Transitions
  - Satelite Transitions

- Spectral intensities calculations
- Interface for aiding in manual level convergence

## Dependencies:
The user should have Open MPI installed in order to run the script.

The *mcdfgme2019.exe* should either be in the user's bin or exported in the ```.bashrc``` file.
As an example:
```bash
export PATH=<path_to_MCDF_directory>:$PATH
```


To install the project dependencies, run:

```bash
pip install -r requirements.txt
```
## Running the script

In order to run the script, the user should indicate the number o ranks to be used:

```bash
mpirun -n <number_of_desired_ranks> python3 runMCDF_MPI.py
```

**For most uses, this number should be equal or greater than 2, since one of the ranks works as master.**

The number of ranks is usually capped by the number of CPUs available. However, should the user desire to use a rank number bigger than the CPU number, they can use the machine's physical threads:


```bash
mpirun --use-hwthread-cpus -n <number_of_desired_ranks> python3 runMCDF_MPI.py
```
In this case, if ```-n <number_of_desired_ranks>``` is ommited, the maximum number of processes available will be used.


## Todo

- 3+ holes calculations
- Auto configuration generator
- Exotic systems
- Change nuclear model
- Code refactoring