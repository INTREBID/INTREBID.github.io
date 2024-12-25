#!/bin/bash
#SBATCH -p debug                     # Submit to 'debug' Partitiion. DO NOT CHANGE
#SBATCH -t 0-12:00:00                # Run for a maximum time of 0 days, 12 hours, 00 mins, 00 secs
#SBATCH --nodes=1                    # Request N nodes. DO NOT CHANGE
#SBATCH --gres=gpu:1                 # Request M GPU per node
#SBATCH --qos=normal                 # Request QOS Type. Choose in [normal, long]
#SBATCH --mail-type=FAIL,END  # 在作业失败或结束时发送邮件通知
#SBATCH --mail-user=925998740@qq.com  # 指定邮件接收地址


# Run Jupyter
source ~/.bashrc
eval "$(conda shell.bash hook)"
conda activate pmg
python ../pmg/main.py