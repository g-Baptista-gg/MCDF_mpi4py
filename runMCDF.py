import pandas as pd
import os
import subprocess
root_dir=os.getcwd()

global atomic_number
global electron_number

directory_name  =input('Directory name: ')
atomic_number   =int(input('Atomic number: '))
electron_number =int(input('Number of electrons: '))

curr_dir=root_dir+'/'+directory_name


# String template for the .dat file required to configure the MCDFGME calculation directory
mdfgmeFile = '	   nblipa=75 tmp_dir=./tmp/\n	   f05FileName\n	   0.\n'

mcdf_exe='mcdfgme2019.exe'


def initTemplates(template):
    f05=''.join(template.readlines())
    f05=f05.replace('mcdfgmeatomicnumber',str(atomic_number))
    f05=f05.replace('mcdfgmeelectronnb',str(electron_number))
    return f05


def setupTemplates():
    global f05Template, f05Template_10steps, f05Template_10steps_Forbs, f05RadTemplate, f05AugTemplate
    #global f05Template_nuc, f05Template_10steps_nuc, f05Template_10steps_Forbs_nuc, f05RadTemplate_nuc, f05AugTemplate_nuc
    
    with open("f05_templates/f05_2019.f05", "r") as template:
        f05Template = initTemplates(template)
    with open("f05_templates/f05_2019nstep1.f05", "r") as template:
        f05Template_10steps =  initTemplates(template)
    with open("f05_templates/f05_2019nstep2.f05", "r") as template:
        f05Template_10steps_Forbs =  initTemplates(template)
    with open("f05_templates/f05_2019_radiative.f05", "r") as template:
        f05RadTemplate =  initTemplates(template)
    with open("f05_templates/f05_2019_auger.f05", "r") as template:
        f05AugTemplate =  initTemplates(template)
    
    '''
    with open("f05_templates/f05_2019r.f05", "r") as template:
        f05Template_nuc = ''.join(template.readlines())
    with open("f05_templates/f05_2019nstep1r.f05", "r") as template:
        f05Template_10steps_nuc = ''.join(template.readlines())
    with open("f05_templates/f05_2019nstep2r.f05", "r") as template:
        f05Template_10steps_Forbs_nuc = ''.join(template.readlines())
    with open("f05_templates/f05_2019_radiativer.f05", "r") as template:
        f05RadTemplate_nuc = ''.join(template.readlines())
    with open("f05_templates/f05_2019_augerr.f05", "r") as template:
        f05AugTemplate_nuc = ''.join(template.readlines())
    '''

setupTemplates()


# Setup 1 hole configuration calculations

df_1hole=pd.read_csv('1hole_configurations.txt',header=None).to_numpy()

if not (os.path.exists(curr_dir)):
    os.makedirs(curr_dir+'/radiative')
    os.makedirs(curr_dir+'/auger')

max_jj_list=[]

for i in range (len(df_1hole)):
    df_1hole[i,0] = str(df_1hole[i,0]).strip()
    df_1hole[i,0] = df_1hole[i,0]+' '
    if not os.path.exists(curr_dir+'/radiative/'+df_1hole[i,1]):
        os.makedirs(curr_dir+'/radiative/'+str(df_1hole[i,1]))
        os.makedirs(curr_dir+'/radiative/'+str(df_1hole[i,1])+'/tmp')
        print('Created directory: '+curr_dir+'/radiative/'+df_1hole[i,1])

    with open(curr_dir+'/radiative/'+str(df_1hole[i,1])+'/jjtest.f05','w') as f05_file:
        f05_file.write(f05Template.replace('mcdfgmeconfiguration',df_1hole[i,0]).\
                                   replace('mcdfgmejj',(str(100) if electron_number%2==0 else str(101))))
        
    with open(curr_dir+'/radiative/'+str(df_1hole[i,1])+'/mdfgme.dat','w') as dat_file:
        dat_file.write(mdfgmeFile.replace('f05FileName','jjTest'))
    #subprocess.Popen(mcdf_exe,cwd=curr_dir+'/radiative/'+str(df_1hole[i,1])).wait()
    subprocess.call(mcdf_exe,cwd=curr_dir+'/radiative/'+str(df_1hole[i,1]))
    with open(curr_dir+'/radiative/'+str(df_1hole[i,1])+'/jjtest.f06','r',encoding='latin-1') as f06_file:
        for line in f06_file:
            if "highest 2Jz possible value is" in line:
                line_j = line.split("highest 2Jz possible value is")[1].strip().split()[0]
                max_jj_list.append([df_1hole[i,1],line_j])
                break

print(max_jj_list)