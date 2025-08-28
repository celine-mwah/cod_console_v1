import configparser
import os

##configs
CONFIG_DIR = "configs"


def save_config(ui_vars_dict, hotkeys_dict, filename):
    config = configparser.ConfigParser()

    ## save the ui vars
    for section, values in ui_vars_dict.items():
        config[section] = {k: str(v) for k, v in values.items()}

    ## save hotkeys
    config['Hotkeys'] = hotkeys_dict

    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(os.path.join(CONFIG_DIR, f"{filename}.ini"), 'w') as f:
        config.write(f)


def load_config(filename):
    config = configparser.ConfigParser()
    config.read(os.path.join(CONFIG_DIR, filename))

    ## loading ui vars
    loaded_ui_data = {"doubles": {}, "booleans": {}, "colors": {}, "integers": {}}

    def convert(v):
        if v.lower() in ['true', 'false']: return v.lower() == 'true'
        try:
            return int(v) if '.' not in v else float(v)
        except ValueError:
            return v

    for section in config.sections():
        if section in loaded_ui_data:
            for key, val in config.items(section):
                if section == "colors" and val.startswith('[') and val.endswith(']'):
                    loaded_ui_data[section][key] = [float(f) for f in val.strip('[]').split(',')]
                else:
                    loaded_ui_data[section][key] = convert(val)

    ## load hotkeys
    loaded_hotkeys = {}
    if 'Hotkeys' in config:
        loaded_hotkeys = dict(config.items('Hotkeys'))

    return {"ui": loaded_ui_data, "hotkeys": loaded_hotkeys}


def list_config_files():
    if not os.path.exists(CONFIG_DIR): return []
    return [f for f in os.listdir(CONFIG_DIR) if f.endswith('.ini')]