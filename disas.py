#!/usr/bin/env python3

import argparse
import re
import subprocess
import xml.etree.ElementTree as ET
from collections import defaultdict, namedtuple

InstrDisas = namedtuple('InstrDisas', ['addr', 'opcode', 'asm', 'iform', 'extension', 'category', 'isaSet', 'regOperands', 'memOperands', 'rw', 'attributes'])
allXmlAttributes = ['agen', 'bcast', 'eosz', 'high8', 'immzero', 'mask', 'rep', 'rm', 'sae', 'zeroing']

# Returns a list of InstrDisas tuples
def parseXedOutput(output, useIACAMarkers=False):
   output = re.sub('#.*\n', '', output)
   output = re.sub('Setting chip.*\n', '', output)
   output = re.sub('Mapped.*\n', '', output)
   output = re.sub('RESETTING STATS', '', output)

   retList = []
   iacaStartMarkerFound = False
   prevOpcode = ''
   for instrOutput in re.findall(r'([\s\S]*?XDIS.*\n)', output):
      instrOutput = instrOutput.strip()
      lines = instrOutput.splitlines()

      lastLine = lines[-1].split()
      addr = lastLine[1].replace(':', '')
      category = lastLine[2]
      extension = lastLine[3]
      isaSet = lastLine[4]
      opcode = lastLine[5]

      if useIACAMarkers:
         lastTwoOpcodes = prevOpcode + opcode
         prevOpcode = opcode

         if iacaStartMarkerFound:
            if lastTwoOpcodes == 'BBDE000000646790':
               retList.pop()
               break
            elif opcode == '65C60425DE000000DE':
               break
         else:
            if (lastTwoOpcodes == 'BB6F000000646790') or (opcode == '65C604256F0000006F'):
               iacaStartMarkerFound = True
            continue

      tokensList = lines[0][re.match(r'\S* \S* ', lines[0]).end():].split(', ')
      tokens = {s[0]:(s[1] if len(s)>1 else '1') for x in tokensList for s in [x.split(':')]}

      memOperands = {k:v for k, v in tokens.items() if re.match(r'MEM\d|AGEN', k)}
      regOperands = {k:v for k, v in tokens.items() if re.match(r'REG\d', k)}

      attributes = dict(tokens)
      if 'MASK' in attributes and attributes['MASK'] != '0':
         attributes['MASK'] = '1'

      if 'AGEN' in tokens:
         v = tokens['AGEN']
         agen = []
         first = v.split('+')[0]
         if (not '*' in first) and (not '0x' in first) and (not 'RIP' in first): agen.append('B')
         if 'RIP' in v: agen.append('R')
         if '*1' in v: agen.append('I')
         elif '*' in v: agen.append('IS')
         if 'DISP_WIDTH' in attributes: agen.append('D' + attributes['DISP_WIDTH'])
         attributes['AGEN'] = '_'.join(agen)

      attributes['HIGH8'] = ','.join(n for n, r in sorted(regOperands.items()) if r in ['AH', 'BH', 'CH', 'DH'])

      if 'IMM0' in tokens:
         attributes['IMMZERO'] = str(int(tokens['IMM0'] == '0x0'))

      asm = lines[-2][6:]
      iform = lines[0].split()[1]

      rw = {}
      for line in lines[1:-2]:
         sp = line[3:].split('/')
         n, a = (sp[0], sp[-1])
         if n in memOperands or n in regOperands:
            rw[n] = a

      retList.append(InstrDisas(addr, opcode, asm, iform, extension, category, isaSet, regOperands, memOperands, rw, attributes))

   return retList


def matchAttributes(disasAttr, xmlAttr):
   for k, v in xmlAttr.items():
      if not k.lower() in allXmlAttributes: continue
      if k.lower() == 'rm':
         if disasAttr.get(k.upper(), '') not in v:
            return False
      else:
         if disasAttr.get(k.upper(), '0') != v:
            return False
   return True


# Disassembles a binary and finds for each instruction the corresponding entry in the XML file.
# With the -iacaMarkers option, only the parts of the code that are between the IACA markers are considered.
def main():
   parser = argparse.ArgumentParser(description='Disassembler')
   parser.add_argument('xmlfile', help='XML file')
   parser.add_argument('filename', help='File to be disassembled')
   parser.add_argument('-iacaMarkers', help='Use IACA markers', action='store_true')
   args = parser.parse_args()

   output = subprocess.check_output(['obj/wkit/bin/xed', '-v', '4', '-isa-set', '-i',  args.filename]).decode()
   disas = parseXedOutput(output, args.iacaMarkers)

   root = ET.parse(args.xmlfile)

   iformToXML = defaultdict(list)
   for XMLInstr in root.iter('instruction'):
      iformToXML[XMLInstr.attrib['iform']].append(XMLInstr)

   for instrD in disas:
      matchingEntries = [XMLInstr.attrib['string'] for XMLInstr in iformToXML[instrD.iform] if matchAttributes(instrD.attributes, XMLInstr.attrib)]
      if not matchingEntries:
         print('No XML entry found for ' + str(tuple(instrD)))
      elif len(matchingEntries) > 1:
         print('Multiple XML entries found for ' + str(tuple(instrD)) + ': ' + str(matchingEntries))
      else:
         print(str(tuple(instrD)) + ': ' + matchingEntries[0])

if __name__ == "__main__":
    main()
