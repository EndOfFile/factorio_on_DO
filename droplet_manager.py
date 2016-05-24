#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import argparse
import logging
import subprocess
from pexpect import pxssh
import sys

__version__ = '0.1'

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)-2s %(filename)s:%(lineno)s] %(message)s")

parser = argparse.ArgumentParser(description="Installs factorio headless server")

parser.add_argument(dest='command', type=str, help='install_factorio, list_mods, list_saves, download_save, factorio')
parser.add_argument('-v', '--verbose', action='store_true', dest='verbose',
					help="Print debug messages")
parser.add_argument(dest='command_command', nargs='?', type=str, help='Optional command for first command')
parser.add_argument('-ssh', '--ssh_key', dest='ssh_key',
					help="SSH key for connection to server")
parser.add_argument('-ip', '--ip_address', dest='ip_address',
					help="IP address of the VM")
parser.add_argument('-u', '--user', default='factorio:factorio', dest='username',
					help="Username factorio server should use")
parser.add_argument('-I', '--factorio-path', default='/opt/factorio', dest='factorio_path',
					help="Factorio server path")
parser.add_argument('-S', '--factorio-service-path', default='/opt/factorio-init', dest='factorio_service_path',
					help="Factorio init script path")
logging.info("Droplet manager version " + __version__)


class droplet_manager(object):
	"""
	Class for managing factory status and setup on a droplet directly over SSH connection.
	"""
	def __init__(self, ip_address, key_file, factorio_directory='/opt/factorio', factorio_user='factorio'):
		self.factorio_directory = factorio_directory
		self.factorio_user = factorio_user
		self.ssh_key = key_file
		self.ip_adress = ip_address
		self.mods_droplet = [] # Mods on droplet
		self.saveGames_droplet = [] # Savegames on droplet
		self.sshConnect()
		if not self.isRoot():
			logging.error("I am not ROOT")
			self.sshExit()
			sys.exit(0)

	def sshConnect(self):
		self.sshConnection = pxssh.pxssh()
		try:
			self.sshConnection.login(self.ip_adress, 'root', ssh_key=self.ssh_key)
		except pxssh.ExceptionPxssh, e:
			print e
			sys.exit(0)

	def sshExit(self):
		self.sshConnection.logout()

	def runCommand(self, cmd):
		"""
		Run given command over ssh connection and return result

		:param cmd:str
		:return:str
		"""
		logging.debug("Running command: " + cmd)
		proccess = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) #, stderr=subprocess.STDOUT )

		(out, err) = proccess.communicate()
		out = out.strip() # Remove lineend
		if len(err) > 0:
			logging.error("Got an error: " + err)

		logging.debug("Output: " + out)
		return out

	def getUsername(self):
		self.sshConnection.sendline('whoami')
		self.sshConnection.prompt()
		name = self.sshConnection.before
		name = name.split('\n')[1].strip()
		logging.debug("Got user: " + name)
		return name


	def createUser(self, name, group=None):
		"""
		Create given UNIX user name:group

		Args:
			name (str): Username
			group (str): Group of user
		"""
		if group is not None:
			name = name + ':' + group
		else:
			name = name + ':' + name

		self.sshConnection.sendline('useradd ' + name)
		self.sshConnection.prompt()


	def isRoot(self):
		"""
		Check if ssh connection is root

		Returns:
			True if root
		"""
		if 'root' in self.getUsername():
			logging.debug("User is root")
			return True
		else:
			logging.debug("User is not root")
			return False


	def changeFolder(self, path):
		"""
		Change current folder to path

		Args:
			path (str): New current folder

		Returns:
			None
		"""
		self.sshConnection.sendline('cd ' + path)
		self.sshConnection.prompt()
		if 'No such file or directory' in self.sshConnection.before:
			logging.warning("Path does not exist: " + path)

	def mkdir(self, path):
		"""
		Create folder at path destination if not already exists

		Args:
			path (str): Folder to be created
		"""
		pass

	def getFileList(self, path):
		"""
		Returns a list of all files in path

		Args:
			path (str): Path to folder

		Returns:
			list of strings
		"""
		logging.debug("Getting file list for: " + path)
		self.changeFolder(path)
		self.sshConnection.sendline('ls')
		self.sshConnection.prompt()
		file_list = self.sshConnection.before.split()
		del file_list[0]  # Removes ls command
		return file_list

	def chown(self, path, user):
		"""
		Do chown -R for path

		Args:
			path (str): Path to chown
			user (str): User to change to

		Returns:
			None
		"""
		logging.debug("Chown: " + path + " to " + user)
		self.sshConnection.sendline('chown -R ' + user + ':' + user + " " + path)
		self.sshConnection.prompt()
		if 'No such' or 'illegal' in self.sshConnection.before:
			logging.error("Error while chown: " + self.sshConnection.before)


	def downloadFileOnDroplet(self, url, destination):
		"""
		Download given file based on url and save it in destination.

		Args:
			url (str): Download URL
			destination (str): Download destination on Droplet
		"""
		logging.debug("Downloading " + url + " to " + destination)
		self.sshConnection.sendline('wget --no-check-certificate ' + url + ' -P ' + destination)
		#FIXME: --no-check-certificate shouldn't be needed
		self.sshConnection.prompt()
		if 'ERROR' in self.sshConnection.before:
			logging.error("Could not download file: " + url)
			logging.debug(self.sshConnection.before)
		logging.debug(self.sshConnection.before)

	def downloadFileFromDroplet(self, remote_path):
		"""
		Download a file from droplet to local machine

		Args:
			remote_path (str): Remote path to file

		Returns:
			None
		"""
		logging.debug("Scp from Droplet: " + remote_path)
		# TODO: Add progress bar + for upload
		out = self.runCommand('scp -i ' + self.ssh_key + ' root@' + self.ip_adress + ':' + remote_path)

		if 'No such file' in out:
			logging.error("Wrong path: " + out)
			return False

		return True

	def uploadFileToDroplet(self, local_path, remote_path):
		"""
		Upload a file from local machine to droplet

		Args:
			local_path (str): Local path to file
			remote_path (str): Remote path to file

		Returns:
			None
		"""
		logging.debug("Scp to Droplet: " + local_path + ' ' + remote_path)

		out = self.runCommand('scp -i ' + self.ssh_key + ' ' + local_path + ' root@' + self.ip_adress + ':' + remote_path)

		if 'No such file' in out:
			logging.error("Wrong path: " + out)
			return False

		return True

	def downloadFactorioServer(self, destination='/tmp'):
		"""
		Download and extract latest headless server

		Args:
			destination (str): Destination fo download

		Returns:
			None
		"""
		logging.info("Downloading factorio server")
		# TODO: Get link to latest version
		self.downloadFileOnDroplet('https://www.factorio.com/get-download/0.12.33/headless/linux64', destination)


	def installFactorio(self, destination='/opt'):#TODO: Use self.factorio_directory for that
		"""
		Install latest factorio headless server

		Returns:
			None
		"""
		# Download and extract headless factorio server
		logging.info("Installing factorio headless server to " + destination)
		self.downloadFactorioServer()

		logging.info("Extracting factorio server")
		#TODO: Check archive name
		self.extractArchive('/tmp/factorio.tar.gz', destination)

		# Create user and chown directory
		self.createUser(self.factorio_user)
		self.chown(self.factorio_directory, self.factorio_user)



	def extractArchive(self, path, destination):
		"""
		Extract archive in path to destination folder

		Args:
			path (str): Path to zip file
			destination (str): Extraction destination
		"""
		self.changeFolder(destination)
		self.sshConnection.sendline('tar -xzf ' + path)
		self.sshConnection.prompt()

		if 'Error' in self.sshConnection.before:
			logging.error("Error while extracting: " + path)
			logging.debug(self.sshConnection.before)


	def cmdFactorioService(self, cmd):
		"""
		Pass this command to factirio service and return responds

		Args:
			cmd (str): Command to execute

		Returns:
			responds (str)

		"""
		self.sshConnection.sendline('service factorio ' + cmd)
		self.sshConnection.prompt()
		return self.sshConnection.before

	def installFactorioService(self):
		"""
		Create factorio init script with https://github.com/Bisa/factorio-init and create a config
		"""
		# TODO: Create config file based on name/user for this factorio installation
		self.changeFolder('/opt')
		self.sshConnection.sendline('git clone https://github.com/Bisa/factorio-init.git')
		self.sshConnection.prompt()
		self.sshConnection.sendline('ln -s /opt/factorio-init/factorio /etc/init.d/factorio')
		self.sshConnection.prompt()
		self.sshConnection.sendline('chmod +x /opt/factorio-init/factorio')
		self.sshConnection.prompt()
		# TODO: Use systemd if possible



	def getFactorioStatus(self):
		logging.debug("Getting factorio status")
		return self.cmdFactorioService('status')

	def startFactorio(self):
		logging.debug("Starting factorio server")
		return self.cmdFactorioService('start')

	def stopFactorio(self):
		logging.debug("Stopping factorio server")
		return self.cmdFactorioService('stop')

	def loadSaveFactorio(self, savegame):
		logging.debug("Loading factorio savegame")
		return self.cmdFactorioService('load-save ' + savegame)

	def getLogFactorio(self):
		logging.debug("Getting factorio log")
		self.sshConnection.sendline('cat ' + self.factorio_directory + '/factorio-current.log')
		self.sshConnection.prompt()
		return self.sshConnection.before

	def uploadSavegameToDroplet(self, savegame):
		"""
		Transfer given savegame from localhost to droplet

		Args:
			savegame (str): Path to local savegame

		Returns:
			None
		"""
		logging.info("Uploading Savegame to droplet: " + savegame)
		self.uploadFileToDroplet(savegame, self.factorio_directory + '/saves')

	def downloadSavegameFromDroplet(self, savegame):
		"""
		Transfer given savegame from droplet to localhost

		Args:
			savegame (str): Path to remote savegame

		Returns:
			None
		"""
		logging.info("Downloading savegame: " + savegame)

		self.downloadFileFromDroplet(self.factorio_directory + '/saves/' + savegame)

	def getSavegamesFromDroplet(self):
		"""
		Print list of all available savegames on server

		Returns:
			list of strings
		"""
		logging.info("Get list of all saves on droplet")
		saves = self.getFileList(self.factorio_directory + '/saves')

		for save in saves:
			logging.info(save)
		# TODO: Get last modifed date for each savegame

	def uploadModToDroplet(self, mod):
		"""
		Push a local mod to droplet

		Args:
			mod(str): Path to mod zip file

		Returns:
			None
		"""
		logging.info("Uploading mod: " + mod)
		self.uploadFileToDroplet(mod, self.factorio_directory + '/mods')


	def uploadModFromUrlToDroplet(self, url):
		"""
		Install a mod from URL directly on the droplet

		Args:
			url (str): Mod zipfile URL
		"""
		logging.info("Installing mod from url: " + url)
		self.downloadFileOnDroplet(url, self.factorio_directory + '/mods')

	def getModListFromDroplet(self):
		"""
		Returns all installed mods of the server

		Returns:
			list of strings
		"""
		logging.info("Get list of all mods on droplet")
		mods = self.getFileList(self.factorio_directory + '/mods')

		for mod in mods:
			logging.info(mod)




if __name__ == '__main__':
	args = parser.parse_args()

	if args.verbose:
		logging.getLogger().setLevel(logging.DEBUG)
		logging.debug("Verbose logging enabled")

	if args.factorio_path:
		factorio_directory = args.factorio_path

	drop = droplet_manager(args.ip_address, args.ssh_key)

	if args.command == 'install_factorio':
		drop.installFactorio()

	if args.command == 'list_mods':
		drop.getModListFromDroplet()

	if args.command == 'get_mod':
		if not args.command_command:
			logging.error("Need url to mod")
			sys.exit(0)
		drop.uploadModFromUrlToDroplet(args.command_command)

	if args.command == 'list_saves':
		drop.getSavegamesFromDroplet()

	if args.command == 'download_save':
		name = 'factorio-init-save.zip'
		if not args.command_command:
			logging.info("No savegame name giving guessing factorio-init-save.zip")
		else:
			name = args.command_command
		drop.downloadSavegameFromDroplet(name)

	if args.command == 'uploadSave':
		if not args.command_command:
			logging.error("Need path to a savegame")
			sys.exit(0)

		drop.uploadSavegameToDroplet(args.command_command)


	if args.command == 'factorio':
		if not args.command_command:
			logging.error("Need a command to send to factorio service (status, start, stop, getLog, loadSave)")
			sys.exit(0)

		if args.command_command == 'status':
			logging.info(drop.getFactorioStatus())

		if args.command_command == 'start':
			logging.info(drop.startFactorio())

		if args.command_command == 'stop':
			logging.info(drop.stopFactorio())

		if args.command_command == 'getLog':
			logging.info(drop.getLogFactorio())

		if args.command_command == 'loadSave':
			logging.info(drop.loadSaveFactorio())

	logging.info("DONE")
	drop.sshExit()

