"""Windows memory counters for the actual running Python process."""
import ctypes
from ctypes import wintypes as w

class Counters(ctypes.Structure):
    _fields_ = [('cb', w.DWORD), ('PageFaultCount', w.DWORD)] + [
        (name, ctypes.c_size_t) for name in (
            'PeakWorkingSetSize', 'WorkingSetSize', 'QuotaPeakPagedPoolUsage',
            'QuotaPagedPoolUsage', 'QuotaPeakNonPagedPoolUsage', 'QuotaNonPagedPoolUsage',
            'PagefileUsage', 'PeakPagefileUsage', 'PrivateUsage')]

class SystemMemory(ctypes.Structure):
    _fields_ = [('length', w.DWORD), ('load', w.DWORD)] + [
        (name, ctypes.c_ulonglong) for name in (
            'total_physical', 'available_physical', 'total_pagefile', 'available_pagefile',
            'total_virtual', 'available_virtual', 'available_extended_virtual')]

kernel = ctypes.WinDLL('kernel32', use_last_error=True)
psapi = ctypes.WinDLL('psapi', use_last_error=True)
kernel.GetCurrentProcess.restype = w.HANDLE
psapi.GetProcessMemoryInfo.argtypes = [w.HANDLE, ctypes.POINTER(Counters), w.DWORD]
kernel.GlobalMemoryStatusEx.argtypes = [ctypes.POINTER(SystemMemory)]

def snapshot():
    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
        raise ctypes.WinError(ctypes.get_last_error())
    system = SystemMemory()
    system.length = ctypes.sizeof(system)
    if not kernel.GlobalMemoryStatusEx(ctypes.byref(system)):
        raise ctypes.WinError(ctypes.get_last_error())
    return {key: round(value / 1048576, 1) for key, value in {
        'ram_mb': counters.WorkingSetSize, 'private_commit_mb': counters.PrivateUsage,
        'peak_ram_mb': counters.PeakWorkingSetSize,
        'system_available_mb': system.available_physical}.items()}
