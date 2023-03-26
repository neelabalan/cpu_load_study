use chrono::prelude::*;
use csv::Writer;
use env_logger::Env;
use serde::Serialize;
use std::error::Error;
use std::thread;

use clap::Parser;
use std::time::Duration;
use sysinfo::{ComponentExt, CpuExt, CpuRefreshKind, System, SystemExt};

#[macro_use]
extern crate log;

pub fn dump_csv<T: Serialize>(list: &Vec<T>, file_path: &str) -> Result<(), Box<dyn Error>> {
    let mut writer = Writer::from_path(file_path).unwrap();
    for record in list {
        writer.serialize(record)?;
    }
    writer.flush()?;
    Ok(())
}
#[derive(Debug, PartialEq, Serialize)]
struct CPUMetric {
    timestamp: String,
    thread_label: String,
    utilization: f32,
    frequency: u64,
}

#[derive(Debug, PartialEq, Serialize)]
struct Temperature {
    timestamp: String,
    label: String,
    temperature: f32,
}
struct Monitor {
    sys: System,
    cpu_data: Vec<CPUMetric>,
    temperature_data: Vec<Temperature>,
}

impl Monitor {
    fn new() -> Self {
        let mut sys: System = System::new_all();
        // Refreshing CPU and Component information.
        sys.refresh_cpu();
        sys.refresh_components();
        Monitor {
            sys: sys,
            cpu_data: vec![],
            temperature_data: vec![],
        }
    }
    fn collect_cpu(&mut self) {
        self.sys
            .refresh_cpu_specifics(CpuRefreshKind::new().with_cpu_usage());
        self.sys
            .refresh_cpu_specifics(CpuRefreshKind::new().with_frequency());
        for processor in self.sys.cpus() {
            self.cpu_data.push(CPUMetric {
                timestamp: Local::now().to_string(),
                thread_label: processor.name().to_string(),
                utilization: processor.cpu_usage(),
                frequency: processor.frequency(),
            });

            debug!("{:?}", processor);
        }
    }
    fn collect_temperature(&mut self) {
        self.sys.refresh_components();
        for component in self.sys.components() {
            // We don't want harddisk wifi temp
            if component.label().starts_with("coretemp") {
                self.temperature_data.push(Temperature {
                    timestamp: Local::now().to_string(),
                    label: component.label().to_string(),
                    temperature: component.temperature(),
                });
            }
            debug!("{:?}", component);
        }
    }
}

#[derive(Parser, Debug)]
#[command(author, about, long_about = None)]
struct Args {
    #[arg(
        long,
        default_value_t = 1000,
        help = "Data collection interval (milliseconds)"
    )]
    interval: u64,

    #[arg(
        long,
        default_value_t = 60,
        help = "Data collection duration (seconds)"
    )]
    duration: u64,

    // filepath
    #[arg(long, default_value_t=format!("../data/cpu_data.csv"))]
    cpu_path: String,

    // filepath
    #[arg(long, default_value_t=format!("../data/temperature_data.csv"))]
    temperature_path: String,
}

fn main() {
    let env = Env::default()
        .filter_or("MY_LOG_LEVEL", "trace")
        .write_style_or("MY_LOG_STYLE", "always");

    env_logger::init_from_env(env);
    let args = Args::parse();

    let mut cpu_monitor = Monitor::new();
    let mut temp_monitor = Monitor::new();
    let max_duration = Duration::new(args.duration, 0); // Exit after 60 seconds
    let interval = Duration::from_millis(args.interval);

    let t1 = thread::spawn(move || {
        let mut elapsed_time = Duration::new(0, 0);
        while elapsed_time < max_duration {
            thread::sleep(interval);
            cpu_monitor.collect_cpu();
            dump_csv(&cpu_monitor.cpu_data, &args.cpu_path);
            elapsed_time += interval;
        }
    });
    let t2 = thread::spawn(move || {
        let mut elapsed_time = Duration::new(0, 0);
        while elapsed_time < max_duration {
            thread::sleep(Duration::from_millis(1000));
            temp_monitor.collect_temperature();
            dump_csv(&temp_monitor.temperature_data, &args.temperature_path);
            elapsed_time += interval;
        }
    });
    t1.join().unwrap();
    t2.join().unwrap();
}
