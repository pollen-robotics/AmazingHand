use clap::Parser;
// use dora_node_api::{dora_core::config::NodeId, DoraNode, Event};

// use dora_node_api::IntoArrow;
use dora_node_api::{self, arrow::array::Array, DoraNode, Event, Parameter};
use eyre::{eyre, Result};
use rustypot::servo;
use std::{error::Error, time::Duration};

use facet::Facet;
use facet_pretty::FacetPretty;
// use std::{collections::HashMap, path::PathBuf, sync::Arc};
// use std::error::Error;
// use arrow_convert::{
//     deserialize::TryIntoCollection, serialize::TryIntoArrow, ArrowDeserialize, ArrowField,
//     ArrowSerialize,
// };
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
    let (mut _node, mut events) =
        // DoraNode::init_from_node_id(NodeId::from("hand_controller".to_string()))?;
        DoraNode::init_from_env()?;

    while let Some(event) = events.recv() {
        match event {
            Event::Input { id, metadata, data } => match id.as_str() {
                "mj_joints_pos" => {
                    let buffer: &dora_node_api::arrow::array::Float64Array =
                        data.as_any().downcast_ref().unwrap();
                    let buffer: &[f64] = buffer.values();
                    // println!("data: {:?}", buffer);

                    let mut motors_ids: Vec<u8> = Vec::new();
                    let mut motors_goalpos: Vec<f64> = Vec::new();

                    for (_idx, finger) in motors.iter().enumerate() {
                        // println!("conf: {:?} {:?}", idx, finger.finger_name);

                        if let Some(Parameter::ListInt(finger1_idx)) =
                            metadata.parameters.get(&finger.finger_name)
                        {
                            println!(
                                "metadata: {:?} data: {:?} {:?}",
                                finger1_idx,
                                buffer[finger1_idx[0] as usize],
                                buffer[finger1_idx[1] as usize]
                            );
                            // controller.sync_write_goal_position(
                            //     &[finger.motor1.id, finger.motor2.id],
                            //     &[
                            //         buffer[finger1_idx[0] as usize] + finger.motor1.offset,
                            //         buffer[finger1_idx[1] as usize] + finger.motor2.offset,
                            //     ],
                            // )?;

                            motors_ids.push(finger.motor1.id);
                            motors_ids.push(finger.motor2.id);

                            let mut m1goal = buffer[finger1_idx[0] as usize] + finger.motor1.offset;
                            if finger.motor1.invert {
                                m1goal = -m1goal;
                            }
                            motors_goalpos.push(m1goal);
                            let mut m2goal = buffer[finger1_idx[1] as usize] + finger.motor2.offset;
                            if finger.motor2.invert {
                                m2goal = -m2goal;
                            }
                            motors_goalpos.push(m2goal);

                            // controller.write_goal_position(
                            //     finger.motor1.id,
                            //     buffer[finger1_idx[0] as usize] + finger.motor1.offset,
                            // )?;
                            // thread::sleep(Duration::from_millis(10));
                            // controller.write_goal_position(
                            //     finger.motor2.id,
                            //     buffer[finger1_idx[1] as usize] + finger.motor2.offset,
                            // )?;
                            // thread::sleep(Duration::from_millis(10));
                        }
                    }
                    controller.sync_write_goal_position(&motors_ids, &motors_goalpos)?;
                    // let parameters = MetadataParameters::default();
                    // let e: Vec<f64> = Vec::new(); //TODO return actual positions
                    // node.send_output(output.clone(), parameters, e.into_arrow())?;
                }
                other => println!("Received input `{other}`"),
            },
            Event::Stop(stop_cause) => {
                eprintln!("Received stop: {:?}", stop_cause);
                return Ok(());
            }
            _ => {}
        }
    }
    println!("Quitting");
    //torque off
    controller.sync_write_torque_enable(&motor_ids, &motors_off)?;
    thread::sleep(Duration::from_millis(1000));
    Ok(())
}
