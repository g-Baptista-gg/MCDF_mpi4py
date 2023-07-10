import pandas as pd
orbital='5f'
df = pd.read_csv(f'spectra/to_convert/Cu_{orbital}_rates_rad.csv')[['Shell IS ', ' IS 2JJ ', ' IS eigenvalue ', ' Shell FS ', ' FS 2JJ ',
       ' FS eigenvalue ', ' transition energy [eV] ', ' rate [s-1] ']]
new_names={'Shell IS ':'Initial Config Label', ' IS 2JJ ':'Initial Config 2jj', ' IS eigenvalue ':'Initial Config eig', ' Shell FS ':'Final Config Label', ' FS 2JJ ':'Final Config 2jj',
       ' FS eigenvalue ':'Final Config eig', ' transition energy [eV] ':'Energy (eV)', ' rate [s-1] ':'Rate (s-1)'}
df=df.rename(columns=new_names)
df.to_csv(f'spectra/data/Cu_{orbital}_rates_rad.csv',index=False)


# df=pd.read_csv(f'spectra/Cu_{orbital}_spectrum_diagram.txt',sep='\t')[[ ' Shell IS ', ' IS 2JJ ',
#                                                                         ' IS eigenvalue ',
#                                                                         ' Shell FS ',  ' FS 2JJ ', ' FS eigenvalue ',
#                                                                         ' transition energy [eV] ', ' intensity ',
#                                                                         ' width [eV] ']]
# new_names={' Shell IS ':'Initial Config Label',' IS 2JJ ':'Initial Config 2jj',' IS eigenvalue ':'Initial Config eig',
#            ' Shell FS ':'Final Config Label',' FS 2JJ ':'Final Config 2jj',' FS eigenvalue ':'Final Config eig',
#            ' transition energy [eV] ':'Energy (eV)', ' intensity ':'Intensity (a.u.)',' width [eV] ':'Energy width (eV)'}

# df=df.rename(columns=new_names)
# df.to_csv(f'Cu_{orbital}_spectrum_diagram.csv',index=False)


