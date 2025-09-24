#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import locale

import xmir_base
import gateway
from gateway import die


gw = gateway.Gateway(detect_device = False, detect_ssh = False)

# 语言设置 - Language settings
current_lang = 'en'

def detect_system_language():
    """检测系统语言"""
    global current_lang
    try:
        system_locale = locale.getdefaultlocale()[0]
        if system_locale and system_locale.startswith('zh'):
            current_lang = 'zh'
        elif system_locale and system_locale.startswith('ru'):
            current_lang = 'ru'
        else:
            current_lang = 'en'
    except:
        current_lang = 'en'

def set_language(lang):
    """设置当前语言"""
    global current_lang
    if lang in ['en', 'ru', 'zh']:
        current_lang = lang

# 多语言文本 - Multilingual text
texts = {
    'header': {
        'en': 'Xiaomi MiR Patcher',
        'ru': 'Патчер Xiaomi MiR',
        'zh': '小米路由器补丁工具'
    },
    'extended_functions': {
        'en': '(extended functions)',
        'ru': '(расширенные функции)',
        'zh': '(扩展功能)'
    },
    'menu1': {
        'set_ip': {
            'en': 'Set IP-address (current value: {})',
            'ru': 'Установить IP-адрес (текущее значение: {})',
            'zh': '设置IP地址 (当前值: {})'
        },
        'connect': {
            'en': 'Connect to device (install exploit)',
            'ru': 'Подключение к устройству (установка эксплойта)',
            'zh': '连接到设备 (安装漏洞利用)'
        },
        'read_info': {
            'en': 'Read full device info',
            'ru': 'Прочитать полную информацию об устройстве',
            'zh': '读取完整设备信息'
        },
        'backup': {
            'en': 'Create full backup',
            'ru': 'Создать полную резервную копию',
            'zh': '创建完整备份'
        },
        'install_lang': {
            'en': 'Install EN/RU/ZH languages',
            'ru': 'Установить языки EN/RU/ZH',
            'zh': '安装 英文/俄文/中文 语言包'
        },
        'install_ssh': {
            'en': 'Install permanent SSH',
            'ru': 'Установить постоянный SSH',
            'zh': '安装永久SSH'
        },
        'install_fw': {
            'en': 'Install firmware (from directory "firmware")',
            'ru': 'Установить прошивку (из папки "firmware")',
            'zh': '安装固件 (从"firmware"目录)'
        },
        'other_functions': {
            'en': '{{{ Other functions }}}',
            'ru': '{{{ Другие функции }}}',
            'zh': '{{{ 其他功能 }}}'
        },
        'reboot': {
            'en': '[[ Reboot device ]]',
            'ru': '[[ Перезагрузить устройство ]]',
            'zh': '[[ 重启设备 ]]'
        },
        'exit': {
            'en': 'Exit',
            'ru': 'Выход',
            'zh': '退出'
        }
    },
    'menu2': {
        'change_password': {
            'en': 'Change root password',
            'ru': 'Изменить пароль root',
            'zh': '更改root密码'
        },
        'read_logs': {
            'en': 'Read dmesg and syslog',
            'ru': 'Прочитать dmesg и syslog',
            'zh': '读取dmesg和syslog'
        },
        'backup_partition': {
            'en': 'Create a backup of the specified partition',
            'ru': 'Создать резервную копию указанного раздела',
            'zh': '创建指定分区的备份'
        },
        'uninstall_lang': {
            'en': 'Uninstall EN/RU/ZH languages',
            'ru': 'Удалить языки EN/RU/ZH',
            'zh': '卸载 英文/俄文/中文 语言包'
        },
        'set_boot': {
            'en': 'Set kernel boot address',
            'ru': 'Установить адрес загрузки ядра',
            'zh': '设置内核启动地址'
        },
        'install_breed': {
            'en': 'Install Breed bootloader',
            'ru': 'Установить загрузчик Breed',
            'zh': '安装Breed引导程序'
        },
        'test': {
            'en': '__test__',
            'ru': '__тест__',
            'zh': '__测试__'
        },
        'return_main': {
            'en': 'Return to main menu',
            'ru': 'Вернуться в главное меню',
            'zh': '返回主菜单'
        }
    },
    'prompts': {
        'select': {
            'en': 'Select: ',
            'ru': 'Выберите: ',
            'zh': '选择: '
        },
        'choice': {
            'en': 'Choice: ',
            'ru': 'Выбор: ',
            'zh': '选择: '
        },
        'enter_ip': {
            'en': 'Enter device IP-address: ',
            'ru': 'Введите IP-адрес устройства: ',
            'zh': '输入设备IP地址: '
        },
        'lang_menu': {
            'en': 'Language/Язык/语言 - 1:EN 2:RU 3:ZH 0:Continue: ',
            'ru': 'Language/Язык/语言 - 1:EN 2:RU 3:ZH 0:Продолжить: ',
            'zh': 'Language/Язык/语言 - 1:EN 2:RU 3:ZH 0:继续: '
        }
    }
}

def get_text(key_path, *args):
    """获取当前语言的文本"""
    keys = key_path.split('.')
    text_dict = texts
    for key in keys:
        text_dict = text_dict.get(key, {})
    text = text_dict.get(current_lang, text_dict.get('en', key_path))
    if args:
        return text.format(*args)
    return text

def get_header(delim, suffix = ''):
  header = delim*58 + '\n'
  header += '\n'
  header_text = get_text('header') + ' ' + suffix
  header += header_text + '\n'
  header += '\n'
  return header

def show_language_menu():
  """显示语言选择菜单"""
  print('')
  print('='*58)
  print('')
  print('Choose Language / Выберите язык / 选择语言')
  print('')
  print(' 1 - English')
  print(' 2 - Русский')
  print(' 3 - 中文')
  print(' 0 - Continue with current language')
  print('')
  
def language_selection():
  """语言选择处理"""
  while True:
    show_language_menu()
    select = input(get_text('prompts.lang_menu'))
    print('')
    if not select:
      continue
    try:
      choice = int(select)
    except:
      choice = -1
    
    if choice == 1:
      set_language('en')
      break
    elif choice == 2:
      set_language('ru')
      break
    elif choice == 3:
      set_language('zh')
      break
    elif choice == 0:
      break

def menu1_show():
  gw.load_config()
  print(get_header('='))
  print(' 1 - ' + get_text('menu1.set_ip', gw.ip_addr))
  print(' 2 - ' + get_text('menu1.connect'))
  print(' 3 - ' + get_text('menu1.read_info'))
  print(' 4 - ' + get_text('menu1.backup'))
  print(' 5 - ' + get_text('menu1.install_lang'))
  print(' 6 - ' + get_text('menu1.install_ssh'))
  print(' 7 - ' + get_text('menu1.install_fw'))
  print(' 8 - ' + get_text('menu1.other_functions'))
  print(' 9 - ' + get_text('menu1.reboot'))
  print(' 0 - ' + get_text('menu1.exit'))

def menu1_process(id):
  if id == 1: 
    ip_addr = input(get_text('prompts.enter_ip'))
    return [ "gateway.py", ip_addr ]
  if id == 2: return "connect.py"
  if id == 3: return "read_info.py"
  if id == 4: return "create_backup.py"
  if id == 5: return "install_lang.py"
  if id == 6: return "install_ssh.py"
  if id == 7: return "install_fw.py"
  if id == 8: return "__menu2"
  if id == 9: return "reboot.py"
  if id == 0: sys.exit(0)
  return None

def menu2_show():
  print(get_header('-', get_text('extended_functions')))
  print(' 1 - ' + get_text('menu1.set_ip', gw.ip_addr))
  print(' 2 - ' + get_text('menu2.change_password'))
  print(' 3 - ' + get_text('menu2.read_logs'))
  print(' 4 - ' + get_text('menu2.backup_partition'))
  print(' 5 - ' + get_text('menu2.uninstall_lang'))
  print(' 6 - ' + get_text('menu2.set_boot'))
  print(' 7 - ' + get_text('menu2.install_breed'))
  print(' 8 - ' + get_text('menu2.test'))
  print(' 9 - ' + get_text('menu1.reboot'))
  print(' 0 - ' + get_text('menu2.return_main'))

def menu2_process(id):
  if id == 1:
    ip_addr = input(get_text('prompts.enter_ip'))
    return [ "gateway.py", ip_addr ]
  if id == 2: return "passw.py"
  if id == 3: return "read_dmesg.py"
  if id == 4: return [ "create_backup.py", "part" ]
  if id == 5: return [ "install_lang.py", "uninstall" ]
  if id == 6: return "activate_boot.py"
  if id == 7: return [ "install_bl.py", "breed" ]
  if id == 8: return "test.py"
  if id == 9: return "reboot.py"
  if id == 0: return "__menu1" 
  return None

def menu_show(level):
  if level == 1:
    menu1_show()
    return get_text('prompts.select')
  else:
    menu2_show()
    return get_text('prompts.choice')

def menu_process(level, id):
  if level == 1:
    return menu1_process(id)
  else:
    return menu2_process(id)

def menu():
  # 检测系统语言并显示语言选择菜单
  detect_system_language()
  language_selection()
  
  level = 1
  while True:
    print('')
    prompt = menu_show(level)
    print('')
    select = input(prompt)
    print('')
    if not select:
      continue
    try:
      id = int(select)
    except Exception:
      id = -1
    if id < 0:
      continue
    cmd = menu_process(level, id)
    if not cmd:
      continue
    if cmd == '__menu1':
      level = 1
      continue
    if cmd == '__menu2':
      level = 2
      continue
    #print("cmd2 =", cmd)
    if isinstance(cmd, str):
      result = subprocess.run([sys.executable, cmd])
    else:  
      result = subprocess.run([sys.executable] + cmd)


menu()
