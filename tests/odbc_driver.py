# Run diagnostic Tests on ODBC Drivers

import subprocess

def run_command(command):
    try:
        result = subprocess.run(command, shell=True, text=True, capture_output=True)
        return result.stdout.strip() + "\n" + result.stderr.strip()
    except Exception as e:
        return f"Error running command: {e}"

def main():
    print("🔍 Collecting ODBC Configuration Details...\n")

    # Check installed ODBC drivers
    print("📌 1️⃣ Checking available ODBC drivers:")
    print(run_command("odbcinst -q -d"))

    # Check active ODBC configuration file paths
    print("\n📌 2️⃣ Checking ODBC configuration locations:")
    print(run_command("odbcinst -j"))

    # Display the contents of the system ODBC driver config
    print("\n📌 3️⃣ Checking contents of /opt/homebrew/etc/odbcinst.ini (VS Code ODBC config):")
    print(run_command("cat /opt/homebrew/etc/odbcinst.ini"))

    print("\n📌 4️⃣ Checking contents of /etc/odbcinst.ini (Terminal ODBC config):")
    print(run_command("cat /etc/odbcinst.ini"))

    # Check if the expected driver file exists
    print("\n📌 5️⃣ Checking if libmsodbcsql.17.dylib exists:")
    print(run_command("ls -l /opt/homebrew/lib | grep msodbcsql"))

    # Check if the actual driver file exists in the Cellar directory
    print("\n📌 6️⃣ Checking if libmsodbcsql.17.dylib exists in the Cellar:")
    print(run_command("ls -l /opt/homebrew/Cellar/msodbcsql17/17.10.6.1/lib/ | grep msodbcsql"))

    # Check permissions for libmsodbcsql.17.dylib
    print("\n📌 7️⃣ Checking file permissions for libmsodbcsql.17.dylib:")
    print(run_command("ls -lah /opt/homebrew/lib/libmsodbcsql.17.dylib"))

if __name__ == "__main__":
    main()