# Sork_Lab

Plotly Dash Dashboard for Sork Lab in UCLA's Department of Ecology and Evolutionary Biology

Step 0: Clone the Repo

- On the repo, click the green button that says "<> Code"
- Copy the HTTPS link that shows up
- Open a new terminal and cd into whatever folder you want to clone the repo into
- i.e. "cd Desktop" will move you to your computer's desktop
- i.e. "cd .." will go backwards if you change your mind
- Clone the repo by running the following command:
- git clone https://github.com/jkim1626/sork.git

Step 1: Create a virtual environment

- In the terminal of your IDE (RStudio, VScode, etc), run the following command to create a virtual environment:
- python -m venv <name_of_virtual_environment>
- i.e. python -m venv hello
- Then run the following command to activate the virtual environment you created:
- source <name_of_virtual_environment>/bin/activate
- i.e. source hello/bin/activate

Step 2: Install all modules/dependencies

- In the terminal, run the following command:
- pip install -r requirements.txt

Step 3: Start the app on a local server

- In the terminal, run the following command:
- python app.py
- It should produce the following output:
- Dash is running on http://127.0.0.1:8050/

  - Serving Flask app 'Sork Lab Dashboard'
  - Debug mode: on

Step 4: Open the app on a local server

- Copy the link into a web browser of your choice:
- http://127.0.0.1:8050/

Version of Python:
3.11.11
