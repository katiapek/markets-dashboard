import subprocess
import datetime

# Check if today is Friday in UTC
if datetime.datetime.now(datetime.timezone.utc).weekday() != 4:  # 4 is Friday
    print("Today is not Friday. Exiting script.")
    exit()

# List of scripts to run in order
scripts_to_run = [
    'Fetch_COT_Legacy_Combined.py',
    'Fetch_COT_Legacy_Futures_Only.py',
    'Fetch_COT_Disaggregated_Combined.py',
    'Fetch_COT_Disaggregated_Futures_Only.py',
    'Fetch_COT_TFF_Combined.py',
    'Fetch_COT_TFF_Futures_Only.py',
    'Calc_COT_Legacy.py',
    'Calc_COT_Disaggregated.py',
    'Calc_COT_TFF.py'
]


def run_scripts():
    for script in scripts_to_run:
        print(f"Running {script}...")
        subprocess.run(['python', script], check=True)


if __name__ == '__main__':
    run_scripts()
