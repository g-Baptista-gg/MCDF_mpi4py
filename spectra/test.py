import pandas as pd
import numpy as np
from scipy.special import voigt_profile
import matplotlib.pyplot as plt

def plot_spectra(orbitals):
    fig,ax=plt.subplots(1,1)
    en_x=np.linspace(8000,8100,10000)
    for i in orbitals:
        df_diag=pd.read_csv('spectra/Cu_'+i+'_spectrum_diagram.csv')
        df_diag=df_diag[['Energy (eV)','Intensity (a.u.)','Energy width (eV)','Initial Config Label','Final Config Label','Final Config 2jj','Final Config eig']].values
        intens_y=0*en_x
        for j in df_diag:
            intens_y+=j[1]*voigt_profile(en_x-j[0],0,j[2])
            if j[0] > en_x[0] and j[0] < en_x[-1]:
                ax.plot(en_x,j[1]*voigt_profile(en_x-j[0],0,j[2]))
                print(j)
        #ax.plot(en_x,intens_y,label=i)
            
    ax.legend()


plot_spectra(['4p'])
plt.savefig('spectra/test.pdf',dpi=300)
