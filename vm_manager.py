#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import time
from time import strftime
import digitalocean
import sys
try:
	import keyring
	keychain = True
except ImportError:
	keychain = False
import logging
import argparse

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)-2s %(filename)s:%(lineno)s - %(funcName)5s()] %(message)s")

apikey = None

if keychain:
	apikey = keyring.get_password("DO_API", "DO_API")
#apikey = "myapikeyhere"


def getManager():
	global my_droplets, snapshot, manager, droplet
	logging.info("Getting manager...")
	manager = digitalocean.Manager(token=apikey)
	my_droplets = manager.get_all_droplets()

	snapshot = manager.get_my_images()[-1] # Get the latest snapshot saved
	key = manager.get_all_sshkeys()[-1] # Get the latest ssh key

	droplet = digitalocean.Droplet(token=apikey,
		name='Factorio',
		region='fra1',  # fra1 = Frankfurt 1, alternativ nyc1 = New York  (Has to be the same region where the snapshot is saved!!)
		image=manager.get_my_images()[-1].id, # Last snapshot
		size_slug='1gb', # Size of the VM
		backups=False,
		ssh_keys=[key])


# Parse arguments
parser = argparse.ArgumentParser(description='Control script for starting VM on digitalocean')
parser.add_argument('command', metavar='command', type=str, nargs=1, help='status, start, stop, set_API')
parser.add_argument('apikey', metavar='apikey', type=str, nargs='?', help='Digitalocean API key')
args = parser.parse_args()


if args.apikey is not None:
	apikey = args.apikey

if apikey is None:
	logging.error("No apikey given!!")
	sys.exit(0)

if args.command[0] == "set_API":
	if keychain:
		keyring.set_password("DO_API", "DO_API", apikey)
		logging.info("Saved API key to keychain: " + apikey)
	else:
		logging.error("Missing keyring python libary!")


if args.command[0] == "start":
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


if args.command[0] == "status":
	getManager()
	logging.info("Running droplets:" + str(my_droplets))
	for drop in my_droplets:
		logging.info(str(drop.load()))
	all_snapshots = manager.get_my_images()
	logging.info("Snapshots:" + str(all_snapshots))

	if len(all_snapshots) > 2:
		logging.info("CLEANING SNAPSHOTS")
		all_snapshots[0].destroy()
		logging.info("DONE")


if args.command[0] == "stop":

	factorio = my_droplets[0]
	snapshot_name = strftime("%d_%b_%Y_%H_%M_%S")

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
	factorio.take_snapshot(snapshot_name, power_off=True)
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

	all_snapshots = manager.get_my_images()
	logging.info("Snapshots: " + str(all_snapshots))

	if len(all_snapshots) > 2:
		logging.info("CLEANING SNAPSHOTS")
		all_snapshots[0].destroy() # Deletes oldest snapshot
	logging.info("DONE")