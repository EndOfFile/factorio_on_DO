#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import time
from time import strftime
from datetime import datetime
import digitalocean
import sys
try:
	import keyring
	keychain = True
except ImportError:
	keychain = False
import logging
import argparse

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)-2s %(filename)s:%(lineno)s] %(message)s")
logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('digitalocean').setLevel(logging.WARNING)

####################################################################################################
##### Config here
####################################################################################################
apikey = None
#apikey = "myapikeyhere"

vm_name = "Factorio"
snapshot_name = "%d_%b_%Y_%H_%M_%S-" + vm_name
max_factorio_snapshots = 2

####################################################################################################
####################################################################################################

if keychain:
	apikey = keyring.get_password("DO_API", "DO_API")


def getManager():
	global my_droplets, snapshot, manager, droplet
	logging.info("Getting manager...")

	manager = digitalocean.Manager(token=apikey)
	my_droplets = manager.get_all_droplets()

	# Get ssh key
	# Note: ssh key names are NOT unique, just take the first one
	key = None
	for k in manager.get_all_sshkeys():
		if k.name == 'DO_' + vm_name:
			if key is None:
				key = k
			else:
				logging.error("There are multiple ssh keys with name: " + 'DO_' + vm_name + " on DO, using first found!")
				break

	if key is None:
		logging.error("Got no SSH key!")
		sys.exit(0)
	#TODO: For new Droplet create and upload new key if key doesnt exist on DO

	image = getLatestFactorioImage()

	if image is None:
		logging.error("Could not find latest image of " + vm_name)
		sys.exit(0)

	droplet = digitalocean.Droplet(token=apikey,
		name=vm_name,
		region='fra1',  # fra1 = Frankfurt 1, alternativ nyc1 = New York  (Has to be the same region where the snapshot is saved!!)
		image=image.id, # Latest matching snapshot
		size_slug='1gb', # Size of the VM
		backups=False,
		ssh_keys=[key])


def getLatestFactorioImage():
	factorio_images = []

	for image in manager.get_my_images():
		try:
			time = datetime.strptime(image.name, snapshot_name)
			factorio_images.append(image)
		except ValueError:
			pass
	if len(factorio_images) > 0:
		logging.info("Latest " + vm_name + " image: " + factorio_images[-1].name)
		return factorio_images[-1]
	else:
		return None


def getFactorioSnapshots():
	all_snapshots = manager.get_my_images()

	factorio_snapshots = []

	for snapshot in all_snapshots:
		try:
			time = datetime.strptime(snapshot.name, snapshot_name)
			factorio_snapshots.append(snapshot)
		except ValueError:
			pass
	return factorio_snapshots

def cleanUpSnapshots():
	all_snapshots = manager.get_my_images()

	factorio_snapshots = getFactorioSnapshots()

	logging.info("Out of " + str(len(all_snapshots)) + " found " + str(len(factorio_snapshots)) + " factorio snapshots")

	if len(factorio_snapshots) > max_factorio_snapshots:
		logging.info("CLEANING FACTORIO SNAPSHOTS")
		factorio_snapshots[0].destroy()  # Deletes oldest snapshot
	logging.info("DONE")


def getFactorioVM():
	# Find factorio VM
	vm = None
	for drop in my_droplets:
		if drop.name == vm_name:
			vm = drop
			break
	return vm



# Parse arguments
parser = argparse.ArgumentParser(description='Control script for starting VM on digitalocean')
parser.add_argument(dest='command', type=str, help='status, start, stop, setAPIKEY')
parser.add_argument(dest='apikey', type=str, nargs='?', help='Digitalocean API key')
parser.add_argument('-v', '--verbose', action='store_true', dest='verbose',
					help="Print debug messages")

args = parser.parse_args()

if args.verbose:
	logging.getLogger().setLevel(logging.DEBUG)
	logging.debug("Verbose logging enabled")

if args.apikey is not None:
	apikey = args.apikey

if apikey is None:
	logging.error("No apikey given!!")
	sys.exit(0)

if args.command == "setAPIKEY":
	if keychain:
		keyring.set_password("DO_API", "DO_API", apikey)
		logging.info("Saved API key to keychain: " + apikey)
	else:
		logging.error("Missing keyring python libary!")


if args.command == "start":
	getManager()
	logging.info(str(droplet))
	droplet.create()

	actions = droplet.get_actions()
	for action in actions:
		action.load()
		# Once it shows complete, droplet is up and running
		while "progress" in action.status:
			time.sleep(5)
			action.load()
			logging.info(str(action.status))
	droplet.load()
	logging.info("Droplet ip adress:" + str(droplet.ip_address))


if args.command == "status":
	getManager()
	logging.debug("Running droplets: " + str(my_droplets))
	logging.info("Factorio droplet: " + str(getFactorioVM()))
	#for drop in my_droplets:
	#	logging.info(str(drop.load()))
	all_snapshots = manager.get_my_images()
	logging.debug("Snapshots:" + str(all_snapshots))
	logging.info("Snapshots of " + vm_name + ": " + str(getFactorioSnapshots()))


if args.command == "stop":
	getManager()

	# Find factorio VM
	factorio = getFactorioVM()

	if factorio is None:
		logging.error("Could not find VM: " + vm_name)
		sys.exit(0)

	if factorio.status != "off":
		logging.info("SHUTDOWN")
		factorio.shutdown()
		actions = factorio.get_actions()
		for action in actions:
			action.load()
			# Once it shows complete, droplet is up and running
			while "progress" in action.status:
				time.sleep(5)
				action.load()
				logging.info(str(action.status))

	logging.info("TAKE SNAPSHOT")
	factorio.take_snapshot(strftime(snapshot_name), power_off=True)
	actions = factorio.get_actions()
	for action in actions:
		action.load()
		# Once it shows complete, droplet is up and running
		while "progress" in action.status:
			time.sleep(5)
			action.load()
			logging.info(action.status)

	logging.info("DESTROY")
	factorio.destroy()
	actions = factorio.get_actions()
	for action in actions:
		action.load()
		# Once it shows complete, droplet is up and running
		while "progress" in action.status:
			time.sleep(5)
			action.load()
			logging.info(str(action.status))

	cleanUpSnapshots()