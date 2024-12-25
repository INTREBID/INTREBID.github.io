import torch
import torchvision


print("PyTorch版本: ", torch.__version__)  # 打印PyTorch版本
print("torchvision版本 ", torchvision.__version__)  # 打印torchvision版本
print("CUDA是否可用: ", torch.cuda.is_available())  # 检查CUDA是否可用

if torch.cuda.is_available():
    num_cuda_devices = torch.cuda.device_count()
    print(f"Number of CUDA devices: {num_cuda_devices}")
    for i in range(num_cuda_devices):
        print(f"CUDA Device {i}: {torch.cuda.get_device_name(i)}")
else:
    print("No CUDA devices available.")
