import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.gridspec as gridspec
import scienceplots
plt.style.use(['science'])

orbital='4p'

df= pd.read_csv('Cu_'+orbital+'/all_converged.csv')[['Label','2jj','eig','Configuration','Energy']].values




labels_1s=[]
energies_1s=[]
labels_2p=[]
energies_2p=[]

for i in df:
    if i[0]=='1s':
        labels_1s.append((','.join([str(i[1]),str(i[2])]),i[3]))
        energies_1s.append(i[-1])
    elif i[0]=='2p':
        labels_2p.append((','.join([str(i[1]),str(i[2])]),i[3]))
        energies_2p.append(i[-1])

# fig,ax=plt.subplots(1,2,figsize=(10,10))
# fig.tight_layout()
    
# ax[0].scatter(np.ones(len(labels_1s)),energies_1s,s=900, marker="_", linewidth=2, zorder=3)
# ax[1].scatter(np.ones(len(labels_2p)),energies_2p,s=900, marker="_", linewidth=2, zorder=3)
# ax[1].yaxis.tick_right()
# for i in range(len(energies_1s)):
    # ax[0].annotate(labels_1s[i][0],xy=(1,energies_1s[i]),xytext=(1-0.01, energies_1s[i]),ha="right",va='center')
    # ax[0].annotate(labels_1s[i][1],xy=(1,energies_1s[i]),xytext=(1+0.01, energies_1s[i]),ha="left",va='center')
# 
# for i in range(len(energies_2p)):
    # ax[1].annotate(labels_2p[i][0],xy=(1,energies_2p[i]),xytext=(1-0.01, energies_2p[i]),ha="right",va='center')
    # ax[1].annotate(labels_2p[i][1],xy=(1,energies_2p[i]),xytext=(1+0.01, energies_2p[i]),ha="left",va='center')
# 
# 
# 
# ax[0].set_xlim(0.98,1.07)
# ax[1].set_xlim(0.98,1.07)
# 
# fig.savefig('Cu_4p_levels.pdf',dpi=300)
# plt.show()
# 


#fig,ax=plt.subplots(2,2,figsize=(10,10),sharex='col')
fig = plt.figure(constrained_layout=True,figsize=(8,10))
gspec = gridspec.GridSpec(ncols=2, nrows=2, figure=fig)
ax0=fig.add_subplot(gspec[:,0])
ax1=fig.add_subplot(gspec[0,1])
ax2=fig.add_subplot(gspec[1,1],sharex=ax1)

ax0.tick_params(which='major',labeltop = False,top = False)
ax1.tick_params(which='major',labeltop = False,top = False)
ax2.tick_params(which='major',labeltop = False,top = False)


ax0.set_title('Hole in 1s')
ax1.set_title('Hole in 2p 1/2')
ax2.set_title('Hole in 2p 3/2')
fig.tight_layout()

for i in range(len(labels_1s)):
    if orbital+'*' in labels_1s[i][1]:
        ax0.scatter(1,energies_1s[i],s=900, marker="_", linewidth=2, zorder=3,c='r')
        ax0.annotate(labels_1s[i][0],xy=(1,energies_1s[i]),xytext=(1+0.01, energies_1s[i]),ha="left",va='center')
    else:
        ax0.scatter(1.07,energies_1s[i],s=900, marker="_", linewidth=2, zorder=3,c='r')
        ax0.annotate(labels_1s[i][0],xy=(1,energies_1s[i]),xytext=(1.07-0.01, energies_1s[i]),ha="right",va='center')



for i in range(len(labels_2p)):
    if '2p*2' in labels_2p[i][1]:
        ax = ax2
        c='b'
    else:
        ax = ax1
        c='g'
    if orbital+'*' in labels_2p[i][1]:
        ax.scatter(1,energies_2p[i],s=900, marker="_", linewidth=2, zorder=3,c=c)
        ax.annotate(labels_2p[i][0],xy=(1,energies_2p[i]),xytext=(1+0.01, energies_2p[i]),ha="left",va='center')
    else:
        ax.scatter(1.07,energies_2p[i],s=900, marker="_", linewidth=2, zorder=3,c=c)
        ax.annotate(labels_2p[i][0],xy=(1,energies_2p[i]),xytext=(1.07-0.01, energies_2p[i]),ha="right",va='center')


ax2.yaxis.tick_right()
ax1.yaxis.tick_right()


ax0.set_xlim(0.98,1.09)
ax1.set_xlim(0.98,1.09)
ax2.set_xlim(0.98,1.09)
#
ax0.set_ylabel('Level Energy (eV)')
ax1.set_ylabel('Level Energy (eV)')
ax2.set_ylabel('Level Energy (eV)')

x_ticks=[1,1.07]
x_ticks_labels=[orbital+'*',orbital]

ax0.set_xticks(x_ticks)
ax0.set_xticklabels(x_ticks_labels)

ax1.set_xticks(x_ticks)
ax1.set_xticklabels(x_ticks_labels)

ax2.set_xticks(x_ticks)
ax2.set_xticklabels(x_ticks_labels)



fig.tight_layout()
plt.show()


