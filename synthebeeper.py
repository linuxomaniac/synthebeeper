#!/usr/bin/python3

from rtmidi import MidiIn
from socket import socket, AF_INET, SOCK_STREAM
from random import choice, shuffle, seed
from math import pow
from struct import pack
from sys import argv

seed()# Initialise l'aléatoire

DEFAULT_PORT = 4243

note_to_freq = []
for i in range(128): note_to_freq.append((440/32.0)*pow(2,(len(note_to_freq)-9)/12.0))

hosts = {}# host[0] le socket et host[1] la note jouée (0 quand libre)
notes = {}# Correspondance entre les notes et les hôtes en utilisation. Contient toutes les notes en cours

def note_off(note, send = True):
	if note != 0 and note in notes:# Il est possible de recevoir un note_off, même si l'élément a été enlevé
		if send: hosts[notes[note]][0].send(pack("I", 0))
		hosts[notes[note]][1] = 0
		del notes[note]

def find_host():
	hosts_list = list(hosts)# On veut itérer hosts aléatoirement, donc on copie les indexes dans une liste
	shuffle(hosts_list)# Un petit coup d'aléatoire
	found = False
	for host in hosts_list:
		if hosts[host][1] == 0:# Si un host n'est pas en cours d'utilisation
			found = True
			break
	if found != True:# On n'a pas trouvé d'hôte libre, alors on en choisit un aléatoirement
		host = choice(list(hosts.keys()))
		note_off(hosts[host][1], False)# On désactive l'hôte et on le rend disponible. False : on n'envoie pas le signal d'arrêt ; on va enchaîner directement avec une nouvelle note
	return host

def note_on(note):
	host = find_host()
	hosts[host][0].send(pack("I", int(note_to_freq[note])))
	hosts[host][1] = note
	notes[note] = host

def callback_event(message, time):
	if message[0][0] & 0xF0 == 0x90:# Si ça correspond à NOTE_ON (Ox9X correspond à NOTE_ON, X peut aller de 0 à F en fonction des channels)
		note_on(message[0][1])
	elif message[0][0] & 0xF0 == 0x80:# NOTE_OFF, pareil que précédemment
		note_off(message[0][1])

if len(argv) < 3:
	print("%s <Numéro de port MIDI d'entrée> <IP[:Port]> <IP[:Port]> [...]" % (argv[0]))
	print("Liste des ports MIDI :\nNuméro\tNom")
	x = 0
	for i in MidiIn.get_ports():
		print('%d\t%s' % (x, i))
		x += 1
	exit()

for i in argv[2:]:# On lit tous les arguments pour les traiter
	i = i.split(':')
	if len(i) == 1: i.append(DEFAULT_PORT)# S'il n'y a pas de port, on ajoute le port par défaut
	hosts[i[0]] = [socket(AF_INET, SOCK_STREAM), 0]
	hosts[i[0]][0].connect((i[0], int(i[1])))

MidiIn = MidiIn()
MidiIn.open_port(int(argv[1]))
MidiIn.ignore_types(True, True, True)# Ignorer sysex, timing et active sensing
MidiIn.set_callback(callback_event)

input("En cours, <Entrée> pour quitter...")

del MidiIn

for host in hosts:
	hosts[host][0].close()
