#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import argparse
import logging
import subprocess
from pexpect import pxssh


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)-2s %(filename)s:%(lineno)s] %(message)s")

parser = argparse.ArgumentParser(description="Installs factorio headless server")

parser.add_argument('-v', '--verbose', action='store_true', dest='verbose',
					help="Print debug messages")
parser.add_argument('-ssh', '--ssh_key', dest='ssh_key',
					help="SSH key for connection to server")
parser.add_argument('-ip', '--ip_address', dest='ip_address',
					help="IP address of the VM")
parser.add_argument('-u', '--user', default='factorio:factorio', dest='username',
					help="Username factorio server should use")
parser.add_argument('-I', '--install-factorio-path', default='/opt/factorio', dest='factorio_path',
					help="Factorio server install path")
parser.add_argument('-S', '--install-factorio-service-path', default='/opt/factorio-init', dest='factorio_service_path',
					help="Factorio init script path")

class droplet_manager(object):
	"""
	Class for managing factory status and setup on a droplet directly over SSH connection.
	"""
	def __init__(self, ip_address, key_file):
		self.ssh_key = key_file
		# TODO: Setup SSH Connection
		self.ip_adress = ip_address
		self.sshConnect()

	def sshConnect(self):
		self.sshConnection = pxssh.pxssh()
		self.sshConnection.login(self.ip_adress, 'root', ssh_key=self.ssh_key)

	#TODO: Capsule remote cmd inside ssh connection pxssh (no subproccess, only pxssh)
	#TODO: Keep runCommand for local commands like scp savegames/mods and ssh key generation move to extra class? Nedded here for savegames/mods and in vm_manager for ssh key generation
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
		logging.debug("Got user: " + name)
		return name


	def createUser(self, name, group=None):
		"""
		Create given UNIX user name:group
		:param name:
		:return:None
		"""
		pass

	def isRoot(self):
		if "root" in self.getUsername():
			logging.debug("User is root")
			return True
		else:
			logging.debug("User is not root")
			return False


	def mkdir(self, path):
		"""Create folder at path destination if not already exists

		:param path:str
		:return:None
		"""
		pass


	def downloadFile(self, url, destination):
		"""
		Download given file based on url and save it in destination.

		:param url:str
		:param destination:str
		:return:None
		"""
		pass


	def downloadServer(self):
		pass


	def extractArchive(self, path, destination):
		"""
		Extract archive in path to destination folder

		:param path:str
		:param destination:str
		:return:None
		"""
		pass


	def cmdFactorioService(self, cmd):
		pass

	def createFactorioService(self):
		"""
		Create factorio init script with https://github.com/Bisa/factorio-init and create a config
		:return:None
		"""
		pass


	def getFactorioStatus(self):
		pass


	def startFactorio(self):
		pass


	def stopFactorio(self):
		pass


	def loadSaveFactorio(self):
		pass


	def getLogFactorio(self):
		pass

	def pushSavegameToDroplet(self, savegame):
		"""
		Transfer given savegame from localhost to droplet

		:param path:str
		:return:None
		"""
		pass

	def getSavegameFromDroplet(self, savegame):
		"""
		Transfer given savegame from droplet to localhost

		:param savegame:str
		:return: None
		"""
		pass

	def listSavegamesOnDroplet(self):
		"""
		Print list of all available savegames on server

		:return:list of str
		"""
		pass



if __name__ == '__main__':
	args = parser.parse_args()

	if args.verbose:
		logging.getLogger().setLevel(logging.DEBUG)
		logging.debug("Verbose logging enabled")

