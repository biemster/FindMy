# FindMy

Query Apple's Find My network, allowing none Apple devices to retrieve the location reports.

This project based on all the hard work of, and is a combination of the following projects:

1. https://github.com/seemoo-lab/openhaystack/
2. https://github.com/biemster/FindMy
3. https://github.com/Dadoum/anisette-v3-server

## Schematic and Usage

### generate_keys.py
Use the `generate_keys.py` script to generate the required keys. The script will generate a `.keys`
or mutiple files for each device you want to use. Each `.keys` file will contain the private key, the public key
(also called advertisement key) and the hashed advertisement key. As the name suggests, the private key is a secret
and should not be shared. The public key (advertisement key) is used for broadcasting the BLE message, this is also
being asked by the `hci.py` script in openhaystack project. The hashed advertisement key is for requesting location
reports from Apple.

### request_reports.py
Use the `request_reports.py` script to request location reports from Apple. The script will read the `.keys` files and
request location reports for each device. The script will also attempt to log in and provided Apple acount and save
the session cookies in `auth.json` file. The reports are stored in the `reports` database.

### web_service.py
Use the `web_service.py` script to start a web service that will serve the location reports via its API.

### anisette-v3-server

Q: What does this external project do? The SMS code is only asked once, where and how is the information stored?

A: Anisette is similar to a device fingerprint. It is intended to be stored on an Apple device once it becomes trusted. 
Subsequent requests made by this "device" using this fingerprint and same Apple account will not trigger the 2FA again. 
The first call (icloud_login_mobileme) is used to obtain the search party token. The subsequent calls 
(generate_anisette_headers) use the cached search party token from the first call as the password and the dsid as the 
username. I (@biemster) have observed that the search party tokens change when using different sources for anisette data,
possibly due to various reasons. If it's deployed as a docker container, the storage location is $HOME/.config/anisette-v3/
adi.pb and device.json. These numbers together generate a validation code like OTP, which then undergoes a process of 
Mixed Boolean Arithmetic to produce two anisette headers for the request. One header represents a relatively static 
machine serial, while the other header contains a frequently changing OTP. 
If you switch to https://github.com/Dadoum/pyprovision, you will obtain the ADI data in the anisette folder. 
(Answer revised and organized from https://github.com/biemster/FindMy/issues/37#issuecomment-1840277808)

## Installation and initial setup
This project only need a free Apple ID with SMS 2FA properly setup. If you don't have any, follow one of the many 
guides found on the internet. 

**Using your personal Apple ID is strongly discouraged, I recommended to create a blank 
Apple ID for experimental purpose.**  

1. Clone this repository and anisette-v3-server:

```bash
git clone https://github.com/Chapoly1305/FindMy.git
git clone https://github.com/Dadoum/anisette-v3-server
```

2. Navigate to `anisette-v3-server` directory. Follow the installation instructions for `anisette-v3-server`. 
Deploy with docker is recommended. 

```
docker run -d --restart always --name anisette-v3 -p 6969:6969 --volume anisette-v3_data:/home/Alcoholic/.config/anisette-v3/lib/ dadoum/anisette-v3-server
```

5. After deployed `anisette-v3-server`, you may validate the server is running by,

``` commandline
curl http://localhost:6969
``` 

3. Navigate to `FindMy` directory, install the required python packages:

```commandline
pip3 install -r requirements.txt
```

## Run

1. `cd` into the `FindMy` directory and generate keys using `./generate_keys.py`.
2. Deploy your advertisement keys on devices supported by OpenHaystack. The ESP32 firmware is a mirror of the
   OpenHaystack binary, the Lenze 17H66 is found in many 1$ tags obtained from Ali.
   An nRF51 firmware can be found here: https://github.com/dakhnod/FakeTag
3. If the anisetter runs within a docker and up, then run :

```bash
./request_reports.py
```

Otherwise, in the same directory as your `.keys` files, run :

```bash
../anisette-v3-server/anisette-v3-server & ./request_reports.py ; killall anisette-v3-server
```

## Untested Section
Alternatively to step 3 you could install `https://github.com/Dadoum/pyprovision` (first install `anisette-v3-server`
though to get a nice D environment and the required android libs),
make a folder `anisette` in your working directory and just run

```bash
./request_reports.py
```

The script should pick up the python bindings to provision and use that instead.

This current non-Mac workflow is not optimal yet, mainly because the anisette server is a bit of a workaround. A python
solution for retrieving this is being developed in the pypush discord, please join there if you want to contribute!
