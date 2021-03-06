# factorio_on_DO
Simple python script for managing a VM on digitalocean.com for running a headless factorio server.

# WARNING
This script deletes VMs and snapshots so please use with caution and check the source first!!

1. If there are more than 2 snapshots that match the naming scheme for factorio vm snapshots the oldest one gets deleted (If you have more than 5 Snapshots you have to pay for them)
2. The VM gets created based on the newest snapshot that matches the snapshot naming scheme
3. Standard name for the VM is Factorio, if you have already one VM with this name change vm_name inside the script!!
4. Snapshots standard name are date_time-vm_name

## Requirements
1. [digitalocean.com](digitalocean.com) account and [apikey (Personal Access Token)](https://www.digitalocean.com/community/tutorials/how-to-use-the-digitalocean-api-v2) 
2. A running VM on DO or a Snapshot of a VM
3. Python 2.7
4. Python libraries 
  * [digitalocean](https://github.com/koalalorenzo/python-digitalocean) (For API calls to DO)
  * [keyring](https://github.com/jaraco/keyring) (Optional, for saving the API key inside the mac keychain or other keyrings)
5. Set a region near to you (See config here inside the script), default is Frankfurt germany

## Installation
1. `pip install python-digitalocean`
2. `pip install keyring` (Optional)
  * Save apikey with keyring: `python vm_manager.py setAPIKEY yourkeygoeshere`

2. Save your apikey inside script or always call the script with the apikey as second argument

## Usage
- `python vm_manager.py status (apikey)`   prints all running VMs and all saved snapshots. 
- `python vm_manager.py start (apikey)`      starts the factorio VM based on the oldes snapshot.
- `python vm_manager.py stop (apikey)`       stops the VM takes a snapshot and destroys VM. Deletes oldest snapshot if there are more than two.


```
$ python vm_manager.py status
2016-05-13 11:00:46,152 [INFO vm_manager.py:27 - getManager()] Getting manager...
2016-05-13 11:00:48,031 [INFO vm_manager.py:84 - <module>()] Running droplets:[]
2016-05-13 11:00:48,505 [INFO vm_manager.py:88 - <module>()] Snapshots:[< 17280127 Ubuntu 12_May_2016_00_34_19 >, < 17297312 Ubuntu 12_May_2016_23_42_28 >]
```

## LICENSE
MIT License

Copyright (c) [2016] [EndOfFile]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.