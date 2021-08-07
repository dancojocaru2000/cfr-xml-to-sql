#! /usr/bin/env python3

import xml.etree.ElementTree as ET
from itertools import takewhile
try:
	from tqdm import tqdm
except ImportError:
	def tqdm(iter, *args, **kargs):
		return iter

def get_database_connection():
	import sqlite3
	return sqlite3.connect('trains.sqlite')

def create_tables(con):
	cursor = con.cursor()
	
	cursor.execute("select name from sqlite_master where type='table' order by name;")
	tables = [item[0] for item in cursor.fetchall()]

	if 'Meta' not in tables:
		cursor.execute('create table Meta (Versiune int)')
	if 'Companii' not in tables:
		cursor.execute('create table Companii (Id integer primary key, NumeLegal text, NumeComun text)')
	if 'Trenuri' not in tables:
		cursor.execute('create table Trenuri (Number integer primary key, IdCompanie int, CategorieTren, KmCum int, Lungime int, Numar, Operator, Proprietar, Putere, Rang, Servicii, Tonaj)')
	if 'Trase' not in tables:
		cursor.execute('create table Trase (NumarTren int, Id int, Tip, CodStatieInitiala int, CodStatieFinala int)')
	if 'ElementeTrasa' not in tables:
		cursor.execute('create table ElementeTrasa (NumarTren int, IdTrasa int, Secventa int, Ajustari, CodStaDest, CodStaOrigine, DenStaDestinatie, DenStaOrigine, Km int, Lungime int, OraP int, OraS int, Rci, Rco, Restrictie, StationareSecunde int, TipOprire, Tonaj, VitezaLivret int)')
	if 'Statii' not in tables:
		cursor.execute('create table Statii (CodStatie integer primary key, Denumire text)')
	con.commit()

def insert(con, table, *args, _commit=True, **kargs):
	cursor = con.cursor()

	if args and not kargs:
		arg_str = '(' + ', '.join((['?'] * len(args))) + ')'
		cursor.execute(f"insert into {table} values {arg_str}", args)
	elif not args and kargs:
		arg_str = '(' + ', '.join((['?'] * len(kargs))) + ')'
		apair = list(kargs.items())
		keys = [k for (k, _) in apair]
		values = [v for (_, v) in apair]
		columns = '(' + ','.join(keys) + ')'
		cursor.execute(f"insert into {table} {columns} values {arg_str}", values)
	else:
		raise Exception('Provide args XOR kargs')

	if _commit:
		con.commit()

def get_data_folder():
	import os
	data_folder = os.path.join('.', 'datafiles')
	return data_folder

def get_xml_files():
	import os
	data_folder = get_data_folder()
	for entry in os.listdir(data_folder):
		entry = os.path.join(data_folder, entry)
		if os.path.isfile(entry):
			if os.path.splitext(entry)[1] == '.xml':
				yield entry

def get_mappings():
	from os.path import join
	import json
	data_folder = get_data_folder()
	mappings_file = join(data_folder, 'mapping.json')
	try:
		with open(mappings_file) as f:
			fj = json.load(f)
			return fj['mappings']
	except:
		return []
			
def train_number_stoi(s):
	return int(''.join(takewhile(lambda c: c.isnumeric(), s)))

def find_trains(con):
	cursor = con.cursor()

	cursor.execute('select Number from Trenuri;')

	return set((item[0] for item in cursor.fetchall()))

def find_trase(con, train_number=None):
	cursor = con.cursor()

	if train_number is None:
		cursor.execute('select NumarTren, Id from Trase')
	else:
		cursor.execute('select NumarTren, Id from Trase where NumarTren = ?', (train_number,))

	return [(nt, i) for nt, i in cursor.fetchall()]

def find_secvente(con, train_number=None, id_trasa=None):
	cursor = con.cursor()

	if train_number is None:
		cursor.execute('select NumarTren, IdTrasa, Secventa from ElementeTrasa')
	elif id_trasa is None:
		cursor.execute('select NumarTren, IdTrasa, Secventa from ElementeTrasa where NumarTren = ?', (train_number,))
	else:
		cursor.execute('select NumarTren, IdTrasa, Secventa from ElementeTrasa where NumarTren = ? and IdTrasa = ?', (train_number, id_trasa))

	return [(nt, it, s) for nt, it, s in cursor.fetchall()]

def find_station_ids(con):
	cursor = con.cursor()

	cursor.execute('select CodStatie from Statii;')

	return set((item[0] for item in cursor.fetchall()))

def find_companies(con):
	cursor = con.cursor()
	
	cursor.execute('select Id, NumeLegal, NumeComun from Companii')

	return list(cursor.fetchall())
		

def main():
	con = get_database_connection()
	create_tables(con)
	insert(con, 'Meta', 2)

	station_ids = find_station_ids(con)
	companies = find_companies(con)

	mappings = get_mappings()

	def get_company_name(path):
		try:
			from os.path import basename
			bn = basename(path)
			for mapping in mappings:
				if mapping['filename'] == bn:
					return mapping['legalName'], mapping['commonName']
		except:
			pass
		return None, None


	for f in get_xml_files():
		company_legal_name, company_common_name = get_company_name(f)
		if len([cln for (_, cln, ccn) in companies if cln == company_legal_name and ccn == company_common_name]) == 0:
			insert(con, 'Companii', NumeLegal=company_legal_name, NumeComun=company_common_name)
			companies = find_companies(con)
		company_id = [i for (i, cln, ccn) in companies if cln == company_legal_name and ccn == company_common_name][0]

		tree = ET.parse(f)
		el_trenuri = tree.find("/XmlMts/Mt/Trenuri")
		
		trains = find_trains(con)

		print(f'Adding {company_common_name or f}...')
		for el_tren in tqdm(el_trenuri.findall("./Tren")):
			train_number_str = el_tren.attrib['Numar']
			train_number = train_number_stoi(train_number_str)

			if train_number in trains:
				continue

			trase = find_trase(con, train_number)

			insert(
				con, 
				'Trenuri',
				train_number,
				company_id,
				el_tren.attrib['CategorieTren'],
				el_tren.attrib['KmCum'],
				el_tren.attrib['Lungime'],
				train_number_str,
				el_tren.attrib['Operator'],
				el_tren.attrib['Proprietar'],
				el_tren.attrib['Putere'],
				el_tren.attrib['Rang'],
				el_tren.attrib['Servicii'],
				el_tren.attrib['Tonaj'],
				_commit=False,
			)

			for el_trasa in el_tren.findall('./Trase/Trasa'):
				id_trasa = int(el_trasa.attrib['Id'])

				if (train_number, id_trasa) in trase:
					continue

				secvente = find_secvente(con, train_number, id_trasa)

				insert(
					con,
					'Trase',
					train_number,
					id_trasa,
					el_trasa.attrib['Tip'],
					el_trasa.attrib['CodStatieInitiala'],
					el_trasa.attrib['CodStatieFinala'],
					_commit=False,
				)

				for el_elementtrasa in el_trasa.findall('./ElementTrasa'):
					secventa = int(el_elementtrasa.attrib['Secventa'])

					if (train_number, id_trasa, secventa) in secvente:
						continue
				
					insert(
						con,
						'ElementeTrasa',
						train_number,
						id_trasa,
						secventa,
						el_elementtrasa.attrib['Ajustari'],
						el_elementtrasa.attrib['CodStaDest'],
						el_elementtrasa.attrib['CodStaOrigine'],
						el_elementtrasa.attrib['DenStaDestinatie'],
						el_elementtrasa.attrib['DenStaOrigine'],
						el_elementtrasa.attrib['Km'],
						el_elementtrasa.attrib['Lungime'],
						el_elementtrasa.attrib['OraP'],
						el_elementtrasa.attrib['OraS'],
						el_elementtrasa.attrib['Rci'],
						el_elementtrasa.attrib['Rco'],
						el_elementtrasa.attrib['Restrictie'],
						el_elementtrasa.attrib['StationareSecunde'],
						el_elementtrasa.attrib['TipOprire'],
						el_elementtrasa.attrib['Tonaj'],
						el_elementtrasa.attrib['VitezaLivret'],
						_commit=False,
					)

					if el_elementtrasa.attrib['CodStaOrigine'].isnumeric():
						cod_sta_orig = int(el_elementtrasa.attrib['CodStaOrigine'])
						if cod_sta_orig not in station_ids:
							station_ids.add(cod_sta_orig)
							insert(
								con,
								'Statii',
								cod_sta_orig,
								el_elementtrasa.attrib['DenStaOrigine'],
								_commit=False,
							)
					if el_elementtrasa.attrib['CodStaDest'].isnumeric():
						cod_sta_orig = int(el_elementtrasa.attrib['CodStaDest'])
						if cod_sta_orig not in station_ids:
							station_ids.add(cod_sta_orig)
							insert(
								con,
								'Statii',
								cod_sta_orig,
								el_elementtrasa.attrib['DenStaDestinatie'],
								_commit=False,
							)
		con.commit()

	con.commit()

if __name__ == '__main__':
	main()
