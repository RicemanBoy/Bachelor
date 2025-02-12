N=1000

for i in range(N):
    file=open('{}.py'.format(i), 'a')
    file.write('from functions import *\n')
    file.write('gen_data({})'.format(i))
    file.close()

for i in range(N):
    file=open('job{}.script'.format(i),'a')
    file.write('#!/bin/bash -l \n')
    file.write('#SBATCH --ntasks=4 \n')
    file.write('#SBATCH --time=00:15:00 \n' )
    file.write('#SBATCH --job-name=BScDustin{} \n'.format(i))
    file.write('#SBATCH --export=NONE \n')
    file.write('unset SLURM_EXPORT_ENV \n')
    file.write('module load python/3.10-anaconda \n')
    file.write('python3 {}.py'.format(i)) 
    file.close()

file=open('sc.script','a')
file.write('#! /bin/bash')
for i in range(N):
    file.write('\n sbatch.tinyfat job{}.script'.format(i))
file.close()

