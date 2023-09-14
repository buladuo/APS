import subprocess
import pynvml
import csv

all_devices_in_the_system = ["CPU0", "CPU1", "GPU0"]
password = 'JQX_ard_1234'   #账户密码
sleeptime = 0.1             # perf 的测量时间（秒）

cpu_freq_list = [2201000, 2200000, 2100000, 2000000, 1900000, 1800000, 1700000, 
                 1600000, 1500000, 1400000, 1300000, 1200000, 1100000, 1000000]          # cpu 测试频率表KHz
gpu_min_freq = 135          # Mhz 
gpu_max_freq = 1107         # Mhz

N = 100                     # 每个频率测量的次数

def caculate_cpu_power(password , sleeptime):
    """
    计算CPU功耗。

    参数:
    - password: str，访问权限密码。
    - sleeptime: float，指令运行时间（秒）。

    返回值:
    - power: dict,CPU的功耗（W）,键为设备名，值为设备功耗。

    功能:
    根据给定的访问权限密码和睡眠时间，计算CPU的功耗并返回。
    """
    # 函数实现...
    command = f"echo {password} | sudo -S perf stat -e power/energy-pkg/ --per-socket sleep {sleeptime}"

    result = subprocess.run(command,shell=True,capture_output=True, text=True)
    
    info = result.stderr
    energy_values = []
    time_elapsed = None
    for line in info.split('\n'):
        if 'Joules power/energy-pkg/' in line:
            energy_value = float(line.split()[2])
            energy_values.append(energy_value)
        elif 'seconds time elapsed' in line:
                time_elapsed = float(line.split()[0])
    if energy_values is None or time_elapsed is None:
        print("Failed to extract CPU stats from the output.")
        return None
    
    # 计算功耗
    power = {
        "CPU0":float(energy_values[0] / time_elapsed),
        "CPU1":float(energy_values[1] / time_elapsed)
    }
    return power

def apply_frequencies_to_CPUs(freq):
    """
    各个设备的频率设置。

    参数:
    - freq: dict，设备频率的字典，键为设备名，值为将被设置的设备频率。

    返回值:
    无返回值。

    功能:
    根据参数中的频率字典（表）设置各个设备的频率。
    """
    # 函数实现...
    cores_to_set_0 = list(range(0, 10)) + list(range(20, 30))
    for core in cores_to_set_0:
        subprocess.run(f'echo {password} | sudo -S cpufreq-set -c {core} -u {freq["CPU0"]}', shell=True)
    cores_to_set_1 = list(range(10, 20)) + list(range(30, 40))
    for core in cores_to_set_1:
        subprocess.run(f'echo {password} | sudo -S cpufreq-set -c {core} -u {freq["CPU1"]}', shell=True)

    return


def caculate_gpu_power():
    """
    计算GPU的功耗

    参数:
    无参数。

    返回值:
    - int: 返回GPU的功耗

    功能:
    查询当前GPU的功耗。
    """
    # 函数实现...
    pynvml.nvmlInit()
    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
    
    # 获取功耗
    utilization_info = pynvml.nvmlDeviceGetUtilizationRates(handle)
    pynvml.nvmlShutdown()
    return utilization_info


def apply_frequencies_to_GPU(freq):
    """
    各个设备的频率设置。

    参数:
    - freq: dict，设备频率的字典，键为设备名，值为将被设置的设备频率。

    返回值:
    无返回值。

    功能:
    根据参数中的频率字典（表）设置各个设备的频率。
    """
    # 初始化NVML
    pynvml.nvmlInit()
    # 获取设备句柄
    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
    # 设置频率
    # 
    pynvml.nvmlDeviceSetApplicationsClocks(handle, freq["GPU0"], 0) #最后面的0表示不对显存进行处理
    
    # 清理NVML
    pynvml.nvmlShutdown()

    return


def generate_freq_power_table_for_cpu():
    with open('cpu_freq_power.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        
        for freq in cpu_freq_list:
            apply_frequencies_to_CPUs({'CPU0':freq,'CPU1':freq})
            cpu0 = []
            cpu1 = []
            for i in range(N):
                power = caculate_cpu_power(password , sleeptime)
                cpu0.append(power['CPU0'])
                cpu1.append(power['CPU1'])
            writer.writerow([freq] + ['CPU0'] + cpu0)
            writer.writerow([freq] + ['CPU1'] + cpu0)
    print('CPU测量完毕')
    return

def generate_freq_power_table_for_gpu():
    with open('gpu_freq_power.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
    for freq in range(gpu_min_freq,gpu_max_freq+1):
        apply_frequencies_to_GPU({'GPU0':freq})
        gpu = []
        for i in range(N):
            power = caculate_gpu_power()
            gpu.append(power['GPU0'])
        writer.writerow([freq] + gpu)
    
    print('GPU测量完毕')
    return

generate_freq_power_table_for_cpu()
# generate_freq_power_table_for_gpu()