import configparser
import os


class ConfigManager:
    def __init__(self, file_path='config.ini'):
        self.file_path = file_path
        self.config = self._load_ini()

    def _load_ini(self):
        config = configparser.ConfigParser()
        config.read(self.file_path)
        return config

    def get_customers(self):
        return [section for section in self.config.sections() if '.' not in section]

    def get_customer_subsections(self, customer):
        return [section.split('.')[-1] for section in self.config.sections()
                if section.startswith(f"{customer}.TOPOLOGIES.")]

    def get_topology(self, customer, subkey=None):
        files_config = self.get_files_config(customer)
        topology_directory = files_config.get('topology_directory', '')

        if subkey:
            section = f"{customer}.TOPOLOGIES.{subkey}"
            if section in self.config:
                return {k: os.path.join(topology_directory, v) for k, v in self.config[section].items() if v!='None'}
        else:
            result = {}
            for section in self.config.sections():
                if section.startswith(f"{customer}.TOPOLOGIES."):
                    _, _, subsection = section.split('.')
                    result[subsection] = {k: os.path.join(topology_directory, v) for k, v in self.config[section].items()}
            return result

    def get_excel_config(self, customer):
        section = f"{customer}.EXCEL"
        if section in self.config:
            return dict(self.config[section])
        return None

    def get_files_config(self, customer):
        section = f"{customer}.FILES"
        if section in self.config:
            config = dict(self.config[section])
            for key in ['topology_directory', 'template_directory', 'output_directory']:
                if key in config:
                    config[key] = os.path.abspath(config[key])
            if 'template_filename' in config:
                config['template_filename'] = os.path.join(config['template_directory'], config['template_filename'])
            return config
        return None

    def get_output_directory(self, customer):
        files_config = self.get_files_config(customer)
        if files_config and 'output_directory' in files_config:
            return files_config['output_directory']
        return None

    def get_template_file(self, customer):
        files_config = self.get_files_config(customer)
        if files_config and 'template_filename' in files_config:
            if not files_config['template_filename'].lower().endswith('none'):
                return files_config['template_filename']
        return None