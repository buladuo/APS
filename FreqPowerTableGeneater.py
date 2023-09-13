import subprocess
import pynvml

all_devices_in_the_system = ["CPU0", "CPU1", "GPU0"]
password = 'JQX_ard_1234'   #账户密码
sleeptime = 0.1             # perf 的测量时间（秒）

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

def applyfrequencies(freq):
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
