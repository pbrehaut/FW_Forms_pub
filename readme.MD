# Firewall Configuration Management Tool

This project is a Python-based tool for creating firewall request forms, by analysing rules requested and appropriately grouping and splitting up based on the gateways these rules need to be deployed on. It includes features for parsing network diagrams, managing configurations, creating visual representations of firewall rules, and generating Excel reports.

## Project Structure

The project consists of multiple Python modules and a configuration file:

1. `combine_diagrams.py`
2. `config.ini`
3. `configmanager.py`
4. `duplicate_rules.py`
5. `findips.py`
6. `firewalldiagram.py`
7. `generate_diagram.py`
8. `group_rules.py`
9. `generate_xl_output.py`
10. `run_gui.py`
11. `subnetfirewallmapper.py`
12. `write_excel_from_tmpl.py`

## Modules Overview

### combine_diagrams.py
Contains a function to process and combine tuple fields from input data, removing duplicates while preserving order.

### config_template.ini
The configuration file for the project, containing settings for different customers, topology information, Excel configuration, and file paths.
Customise this and rename to config.ini

### configmanager.py
A class for managing the configuration settings, providing methods to load and access various parameters from the `config.ini` file.

### duplicate_rules.py
Transforms network data, expanding device information into individual entries.

### findips.py
Extracts and validates IP addresses from text, including support for CIDR notation.

### firewalldiagram.py
Implements a `FirewallDiagram` class for parsing and analyzing network diagrams, finding paths between firewalls, and managing firewall flows.

### generate_diagram.py
Creates graphical representations of firewall flows using Graphviz.

### group_rules.py
Provides functions for grouping and collapsing firewall rules based on various criteria.

### generate_xl_output.py
The main entry point of the application, orchestrating the overall flow of the program.

### run_gui.py
Implements a graphical user interface for inputting network information and loading data from JSON files.

### subnetfirewallmapper.py
Maps subnets to firewalls using YAML configuration files and route dump information.

### write_excel_from_tmpl.py
Generates Excel reports based on firewall configuration data, with support for custom templates and image insertion.

## Key Features

- Parse and analyze firewall diagrams
- Extract and validate IP addresses from text
- Generate visual representations of firewall flows
- Group and collapse firewall rules
- GUI for user input and file loading
- Excel report generation with custom templates
- Subnet to firewall mapping
- Support for multiple customers and topologies

## Configuration

The project uses a `config.ini` file to manage settings for different customers and environments. Key configuration sections include:

- Topologies (COR, DMZ)
- Excel sheet configurations
- File paths for templates, topologies, and output

## Usage

1. Run `run_gui.py` to start the application.
2. Use the GUI to input network information or load data from a JSON file.
3. The program will process the input, analyze firewall diagrams, and generate Excel reports and visual diagrams.

## Requirements

- Python 3.x
- networkx
- graphviz
- tkinter
- openpyxl
- PyYAML

## Installation

1. Clone the repository
2. Install required dependencies: pip install -r requirements.txt
3. Rename `config_template.ini` to `config.ini`
4. Configure the `config.ini` file with appropriate settings for your environment