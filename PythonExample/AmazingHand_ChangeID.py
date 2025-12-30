import time
from rustypot import Scs0009PyController


# Configuration
SERIAL_PORT = "COM5"  # Change to your serial port
BAUDRATE = 1000000
TIMEOUT = 2.0
TARGET_NEW_ID = 2  # Desired new motor ID

# EEPROM Lock values (boolean)
EEPROM_UNLOCKED = False  # Unlock EEPROM to allow writes
EEPROM_LOCKED = True     # Lock EEPROM to protect settings

SCAN_RANGE = range(1, 11)


def main():
    print("=" * 70)
    print("Permanent Motor ID Change (EEPROM Lock/Unlock)")
    print("=" * 70)
    print(f"Target new ID: {TARGET_NEW_ID}\n")

    # Initialize controller
    print("Step 1: Initializing controller...")
    try:
        controller = Scs0009PyController(
            serial_port=SERIAL_PORT,
            baudrate=BAUDRATE,
            timeout=TIMEOUT,
        )
        print("✓ Controller initialized\n")
    except Exception as e:
        print(f"✗ Failed to initialize: {e}")
        return

    # Scan for motor
    print("Step 2: Scanning for motor...")
    current_id = None
    for motor_id in SCAN_RANGE:
        try:
            result = controller.ping(motor_id)
            if result:
                current_id = motor_id
                print(f"✓ Found motor at ID {current_id}\n")
                break
        except Exception:
            pass

    if current_id is None:
        print("✗ No motor found")
        return

    if current_id == TARGET_NEW_ID:
        print(f"Motor already has ID {TARGET_NEW_ID}")
        return

    # Change ID with EEPROM lock/unlock
    print(f"Step 3: Changing ID from {current_id} to {TARGET_NEW_ID}...")

    try:
        # Step 1: Disable torque (REQUIRED for EEPROM writes)
        print("  a) Disabling torque...")
        controller.write_torque_enable(current_id, 0)
        print("  ✓ Torque disabled")
        time.sleep(0.5)

        # Step 2: Unlock EEPROM
        print("  b) Unlocking EEPROM...")
        controller.write_lock(current_id, EEPROM_UNLOCKED)
        print("  ✓ EEPROM unlocked")
        time.sleep(0.5)

        # Step 3: Write new ID
        print(f"  c) Writing new ID {TARGET_NEW_ID} to EEPROM...")
        controller.write_id(current_id, TARGET_NEW_ID)
        print("  ✓ ID written to EEPROM")
        time.sleep(1.0)  # Wait for EEPROM write to complete

        # Step 4: Lock EEPROM to protect settings
        print("  d) Locking EEPROM to protect settings...")
        controller.write_lock(TARGET_NEW_ID, EEPROM_LOCKED)
        print("  ✓ EEPROM locked")
        time.sleep(0.5)

        # Step 5: Verify the change
        print(f"  e) Verifying new ID {TARGET_NEW_ID}...")
        time.sleep(0.5)
        result = controller.ping(TARGET_NEW_ID)

        if result:
            print(f"\n✓ SUCCESS! Motor ID permanently changed to {TARGET_NEW_ID}\n")

            # Re-enable torque
            print("  f) Re-enabling torque...")
            controller.write_torque_enable(TARGET_NEW_ID, 1)
            print("  ✓ Torque enabled")

            print("\n" + "=" * 70)
            print(f"COMPLETE: Motor ID is now {TARGET_NEW_ID}")
            print("EEPROM has been locked - settings are protected.")
            print("This ID will persist after power cycling!")
            print("=" * 70)

            print("\nVERIFICATION: Power cycle the motor to confirm")
            print("1. Disconnect power from the motor")
            print("2. Wait 5 seconds")
            print("3. Reconnect power")
            print("4. Run scanner - motor should still be at ID", TARGET_NEW_ID)

        else:
            print(f"\n✗ Failed to verify new ID {TARGET_NEW_ID}")

    except Exception as e:
        print(f"\n✗ Error during ID change: {e}")
        print("\nTrying to re-lock EEPROM for safety...")
        try:
            # Try to lock with both possible IDs
            try:
                controller.write_lock(current_id, EEPROM_LOCKED)
            except:
                pass
            try:
                controller.write_lock(TARGET_NEW_ID, EEPROM_LOCKED)
            except:
                pass
            print("EEPROM lock attempted")
        except:
            pass
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
