#!/bin/bash
#SBATCH --name=nmma_rapid_scanner
#SBATCH --time=23:59:59
#SBATCH --mail-type=ALL
#SBATCH --mail-user=ztfrest@gmail.com
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=8gb
#NOTSBATCH -p amdsmall
#SBATCH -o %X.out
#SBATCH -e %X.err

source /home/cough052/barna314/anaconda3/bin/activate nmma

python3 /home/cough052/barna314/scanner.py