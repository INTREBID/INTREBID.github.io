#!/bin/bash
#SBATCH -p debug                     # Submit to 'debug' Partitiion. DO NOT CHANGE
#SBATCH -t 0-12:00:00                # Run for a maximum time of 0 days, 12 hours, 00 mins, 00 secs
#SBATCH --nodes=1                    # Request N nodes. DO NOT CHANGE
#SBATCH --gres=gpu:1                 # Request M GPU per node
#SBATCH --qos=normal                 # Request QOS Type. Choose in [normal, long]
#SBATCH --mail-type=FAIL,END  # 在作业失败或结束时发送邮件通知
#SBATCH --mail-user=925998740@qq.com  # 指定邮件接收地址

# 获取隧道信息
XDG_RUNTIME_DIR=""  # 清空 XDG 运行时目录环境变量
port=$(shuf -i8000-9999 -n1)  # 生成一个随机端口号用于 Jupyter
node=$(hostname -s)  # 获取当前节点名称
user=$(whoami)  # 获取当前用户名
cluster=$(hostname -f | awk -F"." '{print $2}')  # 获取集群名称

# 设置 SSH 连接信息
clusterurl="222.20.98.89"  # 远程服务器地址
export PATH=$PATH:~/.local/bin  # 将本地 bin 目录添加到 PATH

# 打印 SSH 隧道连接指令
echo -e "
To connect to the compute node ${node} on sribd running your jupyter notebook server,
you need to run following two commands in a terminal
1. Command to create ssh tunnel from you workstation/laptop to cs-login:
ssh -N -f -L ${port}:${node}:${port} ${user}@${clusterurl}
2. Copy the link provided below by jupyter-server and paste it in your browser on your workstation/laptop, eg:
[I 2024-10-23 15:10:41.980 ServerApp] http://127.0.0.1:[PORT]/lab?token=[TOKEN]
3. Enter command in cmd to connect to the server, and enter link in vscode to connect to the existing jupyter server.
"

# Run Jupyter
source ~/.bashrc
eval "$(conda shell.bash hook)"
conda activate ml_base
jupyter lab --no-browser --port=${port} --ip=${node}