import pandas as pd
import numpy as np
from scipy.special import voigt_profile
import scienceplots
import matplotlib.pyplot as plt
plt.style.use(['science','nature'])

def plot_spectra(orbitals):

    en_x=np.linspace(8000,8080,10000)
    fig_all,ax_all=plt.subplots(2,1,figsize=(8,12),sharex=True,sharey=False)
    fig_all.subplots_adjust(hspace=0)
    fig_all.tight_layout()
    colors = plt.cm.tab20c.colors
    ccount=0
    for i in orbitals:
        fig,ax=plt.subplots(3,1,figsize=(8,12),sharex=True,sharey=False)
        fig.subplots_adjust(hspace=0)
        fig.tight_layout()
        df_diag=pd.read_csv('spectra/data/Cu_'+i+'_spectrum_diagram.csv')
        df_diag=df_diag[['Energy (eV)','Intensity (a.u.)','Energy width (eV)','Initial Config Label','Final Config Label','Final Config 2jj','Final Config eig']].values
        intens_y=0*en_x
        max_tot=0
        for j in df_diag:
            intens_y+=j[1]*voigt_profile(en_x-j[0],0,j[2])
            
            if j[0] > 8010 and j[0] < 8080:
                ax[1].plot(en_x,j[1]*voigt_profile(en_x-j[0],0,j[2]))
                max_y=(j[1]*voigt_profile(en_x-j[0],0,j[2])).max()
                if max_y>max_tot:max_tot=max_y
                ax[2].vlines(j[0],ymin=0,ymax=j[1])
                #ax[1].set_yscale('log')
                #print(j)
        ax[0].plot(en_x,intens_y/intens_y.max(),label=i)
        #fig.suptitle(r'4p spectator electron $K\alpha$ emission spectrum')
        #ax[1].set_ylim(0,max_tot)
        ax[2].set_xlabel('Energy (eV)',fontsize=8)
        ax[1].set_ylabel('Intensity (a.u)',fontsize=8)
        ax[0].set_ylabel('Normalized Intensity (a.u)',fontsize=8)
        ax[2].set_ylabel('Intensity (a.u)',fontsize=8)

        ax[0].text(0.05, 0.9, "Full spectrum", transform=ax[0].transAxes, fontsize=8, va='top', ha='left')
        ax[0].text(0.9, 0.9, f"{i} spectator electron", transform=ax[0].transAxes, fontsize=12, va='top', ha='right')
        ax[1].text(0.05, 0.9, "Components spectrum", transform=ax[1].transAxes, fontsize=8, va='top', ha='left')
        ax[2].text(0.05, 0.9, "Components' energy centroids", transform=ax[2].transAxes, fontsize=8, va='top', ha='left')
        for k in ax:
            k.tick_params(axis='both', which='major', labelsize=8)
        fig.savefig(f'spectra/spec_figs/{i}.pdf',dpi=300)
        ax_all[0].plot(en_x,intens_y,label=i,color=colors[ccount % len(colors)])
        ax_all[1].plot(en_x,intens_y/intens_y.max(),label=i,color=colors[ccount % len(colors)])
        ccount+=1
    ax_all[0].legend( prop={'size': 8})
    ax_all[1].legend( prop={'size': 8})
    for k in ax_all:
            k.tick_params(axis='both', which='major', labelsize=8)
    ax_all[1].set_xlabel('Energy (eV)',fontsize=8)
    ax_all[0].set_ylabel('Intensity (a.u)',fontsize=8)
    ax_all[1].set_ylabel('Normalized Intensity (a.u)',fontsize=8)
    #fig_all.savefig(f'spectra/spec_figs/all.pdf',dpi=300)


plot_spectra(['7p'])
plt.show()
