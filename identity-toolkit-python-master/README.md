# identity-toolkit-python
Demonstrates how to access the Identity Toolkit API with Python

## Command Line Tool
The script `gitkit_command_tool.py` is a useful CLI for interacting with 
Identity Toolkit while debugging your application.  You can easily get 
information on registered users and delete users so that you can test
onboarding flows repeatedly.

## Setup
First, install the python dependencies by running:

    pip install -r requirements.txt

Next, you will need to configure the following fields in the file
`gitkit-server-config.json` with values from your Google Developers Console
project:

  * `clientId` - the client ID for your web application.
  * `serviceAccountEmail` - the email address listed for your service account.
  If your project does not have a service account, you will need to create one.

Next, you will need to download a p12 key for your service account by clicking
the **Generate new P12 key** in the Developers Console.  Once downloaded,
move it to this folder and rename it `private-key.p12`. 

## Usage
Run the script by invoking `python gitkit_command_tool.py`:

    usage: gitkit_command_tool.py [-h] [--id [ID]] [--email [EMAIL]] command

    positional arguments:
      command          one of: get, list, insert, delete

    optional arguments:
      -h, --help       show this help message and exit
      --id [ID]        id of the user
      --email [EMAIL]  email of the user
