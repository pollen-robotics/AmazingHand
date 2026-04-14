import time
from rustypot import Scs0009PyController


# Configuration
SERIAL_PORT = "COM5"  # Change to your serial port
TIMEOUT = 0.5

# Common baudrates for Feetech servos
BAUDRATES = [1000000, 500000, 115200, 57600, 38400, 19200, 9600]

# Scan only a few IDs for faster testing (expand if needed)
QUICK_SCAN_RANGE = range(1, 11)  # IDs 1-10
FULL_SCAN_RANGE = range(0, 254)  # All possible IDs


def scan_for_motors(controller, scan_range, baudrate):
    """Scan for motors on the bus."""
    found_motors = []

    for motor_id in scan_range:
        try:
            result = controller.ping(motor_id)
            if result:
                found_motors.append(motor_id)
                print(f"  ✓ Motor found at ID {motor_id}")
        except Exception:
            pass

    return found_motors


def main():
    """Main function to scan for motors."""
    print("=" * 70)
    print("AmazingHand Motor Scanner")
    print("=" * 70)
    print(f"\nSerial Port: {SERIAL_PORT}")
    print(f"Timeout: {TIMEOUT}s")

    print("\nAttempting to detect motors at different baudrates...")
    print("This may take a moment...\n")

    all_found_motors = {}

    for baudrate in BAUDRATES:
        print(f"\n{'='*70}")
        print(f"Trying baudrate: {baudrate}")
        print(f"{'='*70}")

        try:
            controller = Scs0009PyController(
                serial_port=SERIAL_PORT,
                baudrate=baudrate,
                timeout=TIMEOUT,
            )
            print(f"Controller initialized at {baudrate} baud")

            # Quick scan first (IDs 1-10)
            print(f"Quick scan (IDs {QUICK_SCAN_RANGE.start}-{QUICK_SCAN_RANGE.stop-1})...")
            found_motors = scan_for_motors(controller, QUICK_SCAN_RANGE, baudrate)

            if found_motors:
                all_found_motors[baudrate] = found_motors
                print(f"\n✓ Found {len(found_motors)} motor(s) at {baudrate} baud: {found_motors}")

                # Get more info about the first motor
                motor_id = found_motors[0]
                try:
                    # Try to read model number
                    print(f"\nReading details for motor ID {motor_id}:")
                    position = controller.read_present_position(motor_id)
                    print(f"  - Present Position: {position:.4f} rad ({position * 180/3.14159:.1f}°)")

                    voltage = controller.read_present_voltage(motor_id)
                    print(f"  - Present Voltage: {voltage:.2f}V")

                    temperature = controller.read_present_temperature(motor_id)
                    print(f"  - Temperature: {temperature}°C")

                except Exception as e:
                    print(f"  - Could not read detailed info: {e}")
            else:
                print(f"No motors found in quick scan range")

        except Exception as e:
            print(f"✗ Error at baudrate {baudrate}: {e}")

    # Summary
    print("\n" + "=" * 70)
    print("SCAN SUMMARY")
    print("=" * 70)

    if all_found_motors:
        print("\nMotors detected:")
        for baudrate, motor_ids in all_found_motors.items():
            print(f"  Baudrate {baudrate}: Motor IDs {motor_ids}")

        # Recommend settings
        recommended_baudrate = list(all_found_motors.keys())[0]
        recommended_ids = all_found_motors[recommended_baudrate]
        print(f"\n✓ RECOMMENDED SETTINGS:")
        print(f"  Serial Port: {SERIAL_PORT}")
        print(f"  Baudrate: {recommended_baudrate}")
        print(f"  Detected Motor IDs: {recommended_ids}")
    else:
        print("\n⚠ No motors detected!")
        print("\nTroubleshooting:")
        print("  1. Check that the motor is connected to the controller")
        print("  2. Verify the motor is powered (check power LED)")
        print("  3. Ensure the USB cable is properly connected")
        print("  4. Try connecting only ONE motor at a time")
        print("  5. Check that no other program is using the serial port")

    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nScan cancelled by user.")
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
