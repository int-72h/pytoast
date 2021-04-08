# ofatomic (oflauncher-atomic)

## This is an alternate launcher for Open Fortress, a free and open-source mod for Team Fortress 2.

* This launcher doesn't have a GUI like stainless, however it's written (as you can see) in Python, which makes this ideal for server operators.

* It is designed to be used by server operators and more advanced users as well as those platforms which don't have official binaries provided for.

* It's also a lot more simpler due to the lack of a GUI.

PRs are welcome.

## "Basic" Install instructions

Install instructions are like any other local pip package using `setup.py`:

* Download this repo.
* run `python setup.py install`.
* Now, if pip scripts are in your path, simply running `ofatomic` will invoke the script.

> Note: on Windows, trying to Ctrl-C out of it whilst it's running appears to not play well with multiprocessing, unlike on Unix-like systems.

Note that these instructions just download the OF files - you will need to still follow the official guide for the rest of the steps prior and after you would normally use SVN for.


Here's the usage from the file for those wanting to customise/automate the install.
```
Usage: ofatomic -k file [-p (ofpublic.pem)] [-u (default server url)] [-n 4] [--disable-hashing] [--disable-signing]
Command line launcher/installer for Open Fortress.
  -p: Choose desired path for installation. Default is the directory this script is located in.
  -k: Specify public key file to verify signatures against. Default is the current OF public key (ofpublic.pem).
  -n: Amount of threads to be used - choose 1 to disable multithreading. Default is the number of threads in the system.
  -u: Specifies URL to download from. Specify the protocol (https:// or http://) as well. Default is the OF repository.
  --disable-hashing: Disables hash checking when downloading.
  --disable-signing: Disables signature checking when downloading.
  ```
