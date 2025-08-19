use clap::Parser;

use eyre::{eyre, Result};
use rustypot::servo;
use std::{error::Error, time::Duration};

use facet::Facet;
use facet_pretty::FacetPretty;

use std::{fs, thread};

// use std::io::Read;
#[derive(Debug, Facet)]
struct Fingers {
    #[allow(dead_code)] // Disable dead code warning for the entire struct
    motors: Vec<Motors>,
}

#[derive(Debug, Facet)]
struct Motors {
    #[allow(dead_code)] // Disable dead code warning for the entire struct
    finger_name: String,
    #[allow(dead_code)] // Disable dead code warning for the entire struct
    motor1: Motor,
    #[allow(dead_code)] // Disable dead code warning for the entire struct
    motor2: Motor,
}

#[derive(Debug, Facet)]
struct Motor {
    #[allow(dead_code)]
    id: u8,
    #[allow(dead_code)]
    offset: f64,
    #[allow(dead_code)]
    invert: bool,
    #[allow(dead_code)]
    model: String,
}

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Serialport
    #[arg(short, long, default_value = "/dev/ttyACM0")]
    serialport: String,
    /// baudrate
    #[arg(short, long, default_value_t = 1_000_000)]
    baudrate: u32,
    /// TOML config file
    #[arg(short, long, default_value = "config/r_hand.toml")]
    config: String,
}

fn main() -> Result<(), Box<dyn Error>> {
    let args = Args::parse();
    let serialport: String = args.serialport;
    let baudrate: u32 = args.baudrate;
    let configfile: String = args.config;
    println!("Opening {:?}", configfile);
    let toml_str = fs::read_to_string(configfile).expect("Failed to read config file");

    let motors_conf: Fingers =
        facet_toml::from_str(&toml_str).expect("Failed to deserialize config file");

    println!("{}", motors_conf.pretty());
    let serial_port = serialport::new(serialport, baudrate)
        .timeout(Duration::from_millis(10))
        .open()?;

    let mut controller = servo::feetech::scs0009::Scs0009Controller::new()
        .with_protocol_v1()
        .with_serial_port(serial_port);

    if motors_conf.motors[0].motor1.model != *"SCS0009" {
        return Err(eyre!("Only SCS0009 motors are supported for now...").into());
    };

    // let output = DataId::from("pull_position".to_owned());
    let mut finger_names: Vec<String> = vec![];
    let mut motor_ids: Vec<u8> = vec![];
    let mut motor_offsets: Vec<f64> = vec![];
    let motors = &motors_conf.motors;
    for motors in motors {
        finger_names.push(motors.finger_name.clone());
        motor_ids.push(motors.motor1.id);
        motor_ids.push(motors.motor2.id);
        motor_offsets.push(motors.motor1.offset);
        motor_offsets.push(motors.motor2.offset);
    }
    let motors_on: Vec<u8> = vec![1; motor_ids.len()];
    let motors_off: Vec<u8> = vec![0; motor_ids.len()];

    //torque enable
    controller.sync_write_torque_enable(&motor_ids, &motors_on)?;
    thread::sleep(Duration::from_millis(1000));
    controller.sync_write_goal_position(&motor_ids, &motor_offsets)?;
    thread::sleep(Duration::from_millis(1000));
    println!("Quitting");
    //torque off
    controller.sync_write_torque_enable(&motor_ids, &motors_off)?;
    thread::sleep(Duration::from_millis(1000));
    Ok(())
}
