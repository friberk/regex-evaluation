import glob
import sys
import re
import os
import argparse
import numpy

parser = argparse.ArgumentParser(description='Optional app description')
parser.add_argument('input_folder', type=str,
                    help='A required string positional argument')

args = parser.parse_args()
input_dir = args.input_folder


num = []
length = []

files = glob.glob(input_dir + "*")
files.sort()

for filename in files:
	#print filename
	examples = 0
	with open(filename, 'r') as f:
		content = f.readlines()
		count = 0
		index = 0
		for line in content:
			index += 1
			if index == 1:
				length.append(len(line))
			if count == 0:
				if line.startswith('+++'):
					count = 1
					continue
				else:
					continue
			if count == 1:
				if line.startswith('---'):
					count = 2
					continue
				elif len(line.strip()) > 0:
					examples += 1
					continue
				else:
					continue
			if count == 2:
				if len(line.strip()) > 0:
					examples += 1
					continue
	#print examples
	num.append(examples)

#print 'num' + str(num)
print max(num)
print min(num)
#print 'length' + str(length)
#print max(length)
#print min(length)
#print 1.0*sum(length)/len(length)

