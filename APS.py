import subprocess
import psutil
import pynvml


all_devices_in_the_system = ["CPU0", "CPU1", "GPU0"]
all_devices_in_the_system_maxfreq = {   #每个设备的最大运行频率
    "CPU0":2201,
    "CPU1":2201,
    "GPU0":1579             #！不是正确的，没有进行测量
}

password = 'JQX_ard_1234'   #账户密码
sleeptime = 0.1             # perf 的测量时间（秒）
cpumaxfreq = 2201           # cpu的最高频率
device_counts = 3           # 2个cpu一个GPU

PowerCap = 250              # 功耗上限（W）

minPowerStep = 5            # 最小功耗步长

def caculate_cpu_freq():
    """
    计算CPU频率。

    参数:
    无参数。

    返回值:
    - freq: dict, 每个CPU的频率,键为设备名，值为设备利用率。

    功能:
    根据当前CPU的相关信息，计算并返回CPU的频率。
    """
    # 函数实现...
    cpu_freq = psutil.cpu_freq(percpu=True)
    cpu_freq_curs =[]
    for i, cpu_freq in enumerate(cpu_freq):
        cpu_freq_cur = cpu_freq.current
        cpu_freq_curs.append(cpu_freq_cur)
        fre_0=(sum(cpu_freq_curs[0:10])+sum(cpu_freq_curs[20:30]))/20
        fre_1=(sum(cpu_freq_curs[10:20])+sum(cpu_freq_curs[30:40]))/20
    freq = {
        "CPU0":fre_0,
        "CPU1":fre_1
    }
    return freq

def caculate_cpu_util():
    """
    计算CPU利用率。

    参数:
    无参数。

    返回值:
    - utils: dict, CPU的利用率(%)，键为设备名，值为设备频率。

    功能:
    根据当前CPU的相关信息，计算返回CPU的利用率。
    """
    # 函数实现...
    cpu_utilization = psutil.cpu_percent(percpu=True)
    cpu_utils=[]
    for i, cpu_util in enumerate(cpu_utilization):
        cpu_utils.append(cpu_util)
    cpu_util_0 = (sum(cpu_utils[0:10])+sum(cpu_utils[20:30]))/20
    cpu_util_1 = (sum(cpu_utils[10:20])+sum(cpu_utils[30:40]))/20
    utils = {
        "CPU0":cpu_util_0,
        "CPU1":cpu_util_1
    }
    return utils


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

def caculate_gpu_status():
    """
    计算GPU状态。

    参数:
    无参数。

    返回值:
    - list: 包含频率、利用率、功耗的列表

    功能:
    查询当前GPU的状态，并返回相关信息。
    """
    # 函数实现...
    pynvml.nvmlInit()
    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
    
    # 获取频率
    clock_info = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_GRAPHICS)
    
    # 获取利用率
    power_info = pynvml.nvmlDeviceGetPowerUsage(handle)/1000

    # 获取功耗
    utilization_info = pynvml.nvmlDeviceGetUtilizationRates(handle)
    pynvml.nvmlShutdown()
    return [clock_info,utilization_info,power_info]


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

def ForcePowerCap(freq, power, CurrentPower):
    """
    通过强制功率上限来调整频率字典。

    参数：
    - freq：设备频率字典，键为设备标识符，值为频率值。
    - power：设备功率字典，键为设备标识符，值为功率值。
    - CurrentPower：当前总功率，整数类型。

    返回值：
    无返回值

    """
    # 函数实现代码
    # ...
    while CurrentPower > PowerCap:
        NonMinFreqDevices = [device for device in all_devices_in_the_system if freq[device] > minPowerStep]
        N = len(NonMinFreqDevices)
        if N == 0:
            break
        PowerToReduce = CurrentPower - PowerCap
        DevicePowerToReduce = PowerToReduce / N
        CurrentPower = 0
        for device in NonMinFreqDevices:
            PowerBudget = power[device] - DevicePowerToReduce
            freq[device] = freqpowertable[PowerBudget]
            CurrentPower += PowerBudget
        MinFreqDevices = [device for device in all_devices_in_the_system if freq[device] == minPowerStep]
        CurrentPower += len(MinFreqDevices)*minPowerStep

    applyfrequencies(freq)
    return


def PowerDistribution(freq, util, power, TotalUtil):
    """
    计算功耗分布。

    参数:
    - freq: dict，设备频率的字典，键为设备名，值为设备频率。
    - util: dict，设备利用率的字典，键为设备名，值为设备利用率。
    - power: dict，设备功耗的字典，键为设备名，值为设备功耗。
    - TotalUtil: float，总利用率。

    返回值:
    无返回值。

    功能:
    根据给定的设备频率、利用率和功耗，以及总利用率，计算功耗分布并进行相应处理。
    """
    # 函数实现...
    RelativeUtil = {}  # 存储相对利用率
    PowerHeadroom = PowerCap  # 初始功耗余量
    

    for device in all_devices_in_the_system:
        RelativeUtil[device] = util[device] / TotalUtil

    while PowerHeadroom > 0 and PowerHeadroom > minPowerStep:
        CurrentPower = 0
        MaxFreqDevices = [device for device in all_devices_in_the_system if freq[device] == all_devices_in_the_system_maxfreq[freq]]

        N = len(MaxFreqDevices)
        if N == len(all_devices_in_the_system):
            break

        for device in all_devices_in_the_system:
            TargetPower = RelativeUtil[device] * PowerCap
            StressmarkPower = freqpowertable[freq[device]]
            RatioDevice = StressmarkPower / power[device]
            PowerBudget = TargetPower * RatioDevice
            freq[device] = freqpowertable[PowerBudget]
            CurrentPower += TargetPower
            PowerHeadroom = PowerCap - CurrentPower

    applyfrequencies(freq)
    
    return


def MonitoringDeviceActivityPower():
    avgSamples = 5
    numSamples = 0

    while True:
        TotalUtil = 0.0
        TotalPower = 0.0

        power = {}
        freq = {}
        util = {}

        power = caculate_cpu_power(password,sleeptime)
        freq = caculate_cpu_freq()
        util = caculate_cpu_util()
        gpu_status = caculate_gpu_status()
        freq["GPU0"] = gpu_status[0]
        util["GPU0"] = gpu_status[1]
        power["GPU0"] = gpu_status[2]

        
        for device in all_devices_in_the_system:
            TotalUtil += util[device]
            TotalPower += power[device]
        numSamples += 1

        if numSamples == (avgSamples - 1):
            PowerDistribution(freq, util, power, TotalUtil)
            numSamples = 0
        elif TotalPower > PowerCap:
            ForcePowerCap(freq, power, TotalPower)
            
    return






