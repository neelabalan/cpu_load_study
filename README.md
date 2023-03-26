# CPU Load Study

This repository contains a Python program to load the all CPU cores in sequence based on JSON profile. There is also a Rust program to collect CPU temperature, utilization, and clock frequency data as a CSV file.
The Jupyter Notebook in this repository provides a summary and observation of the CPU data. It includes visualizations of the data, inluding line, bar and hist plots. The notebook is located in the notebook/ directory.

In the notebook, you can see the CPU utilization, temperature, and clock frequency over time.
## Getting Started

To get started, you will need to have Python 3 and Rust installed on your computer. 

Once you have installed Rust, you can run the Rust program to collect the CPU data by navigating to the `monitor/` directory and running the following command:

`cargo run`

This will create two CSV files in `data/` directory containing the time series CPU and temperature data.

You can run  `cargo run -- --help` to know the default values and CLI args to customise the monitoring.

```
Usage: monitor [OPTIONS]

Options:
      --interval <INTERVAL>                  Data collection interval (milliseconds) [default: 1000]
      --duration <DURATION>                  Data collection duration (seconds) [default: 60]
      --cpu-path <CPU_PATH>                  [default: ../data/cpu_data.csv]
      --temperature-path <TEMPERATURE_PATH>  [default: ../data/temperature_data.csv]
  -h, --help 
```


To load the CPU, you can use the `cpu_load_generator.py` script. The JSON profile to load the CPU is available within the `cpu_load_generator` directory. 

`python cpu_load_generator.py -p profile.json`

> Refer [README](cpu_load_generator/README.md) to understand usage. Code from [this](https://github.com/sirtyman/CPULoadGenerator) repository is used here and repurposed little bit.

The load generator program uses a Proportional Integral constrol system to load the CPU on specific interval. The sleep duration is calculated based on real time CPU load on the specified core(s) while the controller has access to CPU data to calculate the sleep duration. The actuator applies the load based on results from the controller therefore maintaining the CPU load for given duration.
