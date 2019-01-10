#!/usr/bin/python
import xml.etree.ElementTree as ET

def main():
   root = ET.parse('instructions.xml')
   
   print '.intel_syntax noprefix'      
   for instrNode in root.iter('instruction'):
      extension = instrNode.attrib['extension']
      isa_set = instrNode.attrib['isa-set']
      
      # Future instruction set extensions
      if extension in ['CLDEMOTE', 'MOVDIR', 'PCONFIG', 'WAITPKG', 'WBNOINVD']:
         continue
      
      asm = instrNode.attrib['asm']
      
      first = True
      for operandNode in instrNode.iter('operand'):
         operandIdx = int(operandNode.attrib['idx'])
         
         if operandNode.attrib.get('suppressed', '0') == '1': 
            continue;
         
         if not first and not operandNode.attrib.get('opmask', '') == '1':
            asm += ', '
         else:
            asm += ' '
            first = False
         
         if operandNode.attrib['type'] == 'reg':
            registers = operandNode.text.split(',')
            if 'DH' in registers:
               register = 'DH'
            else:
               scale = (4 if 'MM' in operandNode.text else 1)
               register = registers[min(operandIdx*scale, len(registers)-1)]
            if not operandNode.attrib.get('opmask', '') == '1':
               asm += register
            else:
               asm += '{' + register + '}'
               if instrNode.attrib.get('zeroing', '') == '1':
                  asm += '{z}'
         elif operandNode.attrib['type'] == 'mem' or operandNode.attrib['type'] == 'agen':
            memoryPrefix = operandNode.attrib.get('memory-prefix', '')            
            if memoryPrefix:
               asm += memoryPrefix + ' '
               
            if operandNode.attrib.get('VSIB', '0') != '0':
               asm += '[' + operandNode.attrib.get('VSIB') + '0]'
            else: 
               asm += '[RAX]'
               
            memorySuffix = operandNode.attrib.get('memory-suffix', '')
            if memorySuffix:
               asm += ' ' + memorySuffix
         elif operandNode.attrib['type'] == 'imm':
            if instrNode.attrib.get('roundc', '') == '1':
               asm += '{rn-sae}, '
            elif instrNode.attrib.get('sae', '') == '1':
               asm += '{sae}, '
            width = int(operandNode.attrib['width'])
            if operandNode.attrib.get('implicit', '') == '1':
               imm = operandNode.text
            else:
               imm = (1 << (width-8)) + 1
            asm += str(imm)
         elif operandNode.attrib['type'] == 'relbr':
            asm = '1: ' + asm + '1b'
      
      if not 'sae' in asm:
         if instrNode.attrib.get('roundc', '') == '1':
            asm += ', {rn-sae}'
         elif instrNode.attrib.get('sae', '') == '1':
            asm += ', {sae}' 
      
      print asm

if __name__ == "__main__":
    main()
