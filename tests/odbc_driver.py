# Run diagnostic Tests on ODBC Drivers

import subprocess

def run_command(command):
    try:
        result = subprocess.run(command, shell=True, text=True, capture_output=True)
        return result.stdout.strip() + "\n" + result.stderr.strip()
    except Exception as e:
        return f"Error running command: {e}"

def main():
    # Check installed ODBC drivers
    print("Check available ODBC drivers:")
    print(run_command("odbcinst -q -d"))

    # Check active ODBC configuration file paths
    print("\nCheck ODBC configuration locations:")
    print(run_command("odbcinst -j"))

    # Display the contents of the system ODBC driver config
    print("\nCheck contents of /opt/homebrew/etc/odbcinst.ini (VS Code ODBC config):")
    print(run_command("cat /opt/homebrew/etc/odbcinst.ini"))

    print("\nCheck contents of /etc/odbcinst.ini (Terminal ODBC config):")
    print(run_command("cat /etc/odbcinst.ini"))

    # Check if the expected driver file exists
    print("\nCheck if libmsodbcsql.17.dylib exists:")
    print(run_command("ls -l /opt/homebrew/lib | grep msodbcsql"))

    # Check if the actual driver file exists in the Cellar directory
    print("\nCheck if libmsodbcsql.17.dylib exists in the Cellar:")
    print(run_command("ls -l /opt/homebrew/Cellar/msodbcsql17/17.10.6.1/lib/ | grep msodbcsql"))

    # Check permissions for libmsodbcsql.17.dylib
    print("\nCheck file permissions for libmsodbcsql.17.dylib:")
    print(run_command("ls -lah /opt/homebrew/lib/libmsodbcsql.17.dylib"))

if __name__ == "__main__":
    main()