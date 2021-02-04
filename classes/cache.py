import math
import random
import sys
class Memory:
    #memory type:
    # 0 : byte addressable
    # 1 : word addressable
    def __init__(self,address_bit,mem_type):
        self.address_bit = address_bit
        self.mem_type = mem_type
    def mem_info(self):
        memory_type = {
            0 : 'Byte Addressable',
            1 : 'Word Addressable'
        }
        return "Memory With %dbyte Capacity and %s" % (2**self.address_bit,memory_type.get(self.mem_type))
class Block:
    def __init__(self,block_size):
        self.valid = False
        self.tag = ''
        self.counter = 0
class Cache:
    ###############  HELP FOR TYPES #######################
    ## Structure:
    # 0 : direct_map
    # 1 : fully_associative
    # 2 : n_way_associative
    ## replace methods:
    # 0 : RND
    # 1 : FIFO
    # 2 : LRU
    # 3 : LFU
    def __init__(self,capacity,structure,block_size,word_size,replace_method,memory,n=2):
        self.capacity = capacity
        self.structure = structure
        self.block_size = block_size
        self.word_size = word_size
        self.replace_method = replace_method
        if( structure == 2 ):
            self.n = n
        self.block_len = int( capacity / block_size )
        self.memory = memory
        self.blocks = []
        for i in range(0,self.block_len):
            block = Block(self.block_size)
            self.blocks.append(Block(self.block_size))
        self.byte_offset_len = int( math.log(block_size,2) )
        self.address_bit = int( math.log(capacity,2) )
        self.queue = []
        self.number_of_sets = self.block_len / n
        self.set_bits_len = int(math.log(self.number_of_sets,2))
        if(structure == 0):
            self.replace_method = 4
        self.__log_sys_info()
    def _to_binary(self,num):
        res = ''
        while(num != 0):
            res += str(num % 2)
            num=num/2
        return res[::-1]
    def _to_decimal(self,binary):
        binary = binary[::-1]
        num = 0
        i = 0
        for b in binary:
            num += int(b)*2**i
            i+=1
        return num
    def _sign_extend(self,address,bit):
        if(len(address) < bit):
            address = address[::-1]
            for i in range(0,bit-len(address)):
                address += '0'
            address = address[::-1]
        return address
    def _find_range(self,block):
        if(block.tag == ''):
            return 0
        address = block.tag
        # direct map
        if(self.structure == 0):
            middle = self._sign_extend(self._to_binary(self.blocks.index(block)),self.memory.address_bit - self.byte_offset_len - len(block.tag))
            address += middle
        # n-way associative
        if(self.structure == 2):
            index = self.blocks.index(block)
            address += self._sign_extend(self._to_binary(index/self.n),self.set_bits_len)
        for i in range(0,self.memory.address_bit-len(address)):
            address += '0'
        start = self._to_decimal(address)
        return (start,start+self.block_size)
    # if hit return 1
    # if miss return 0
    def query(self,address):
        # convert word address to byte address
        if( self.memory.mem_type == 1 ):
            address = address * self.word_size
        address = self._to_binary(address)
        # sign extend if needed
        address = self._sign_extend(address,self.memory.address_bit)
        # partition address
        first_part = self.memory.address_bit - self.address_bit
        byte_offset = address[-1*self.byte_offset_len:]
        middle_part = address[first_part:-1*self.byte_offset_len]
        tag = address[:first_part]
        # direct map structure
        if(self.structure == 0):
            block_index = self._to_decimal(middle_part)
            if(self.blocks[block_index].valid and self.blocks[block_index].tag == tag):
                self.__log_hit(address,block_index)
                return 1
            else:
                if(self.blocks[block_index].tag != ''):
                    self.__log__replace(address,block_index,'SIMPLE')
                else:
                    self.__log_miss(address,block_index)
                self.blocks[block_index].valid = True
                self.blocks[block_index].tag = tag
                return 0
        # fully associative structure
        if(self.structure == 1):
            tag = tag + middle_part
            free_index = -1
            c=-1
            for block in self.blocks :
                c+=1
                if(block.valid == False):
                    # find free one in loop
                    free_index = c
                if(block.valid and block.tag == tag):
                    block.counter = 0
                    if(self.replace_method == 2 or self.replace_method == 3):
                        for blck in self.blocks:
                            if(blck != block and blck.valid):
                                blck.counter += 1
                    self.__log_hit(address,self.blocks.index(block))
                    return 1
            # now i should add this block to my blocks
            if(free_index == -1):
                # random replacement method
                if(self.replace_method == 0):
                    index = self._random_replacment((0,self.block_len-1))
                    self.blocks[index].valid = True
                    self.blocks[index].tag = tag
                    self.__log__replace(address,index,'RND')
                    return 0
                # FIFO replacment method
                if(self.replace_method == 1):
                    index = self._FIFO((0,self.block_len-1))
                    self.blocks[index].valid = True
                    self.blocks[index].tag = tag
                    self.__log__replace(address,index,'FIFO')
                    return 0
                # LRU replacment method and LFU replacement method
                if(self.replace_method == 2 or self.replace_method == 3):
                     index = self._LRU((0,self.block_len-1))
                     self.blocks[index].valid = True
                     self.blocks[index].tag = tag
                     self.blocks[index].counter = 0
                     self.__log__replace(address,index,'LFU | LRU')
                     return 0
            else:
                self.blocks[free_index].valid = True
                self.blocks[free_index].tag = tag
                self.blocks[free_index].counter = 0
                self.queue.append(self.blocks[free_index])
                self.__log_miss(address,free_index)
                return 0
        # n-way associative
        if(self.structure == 2):  
            set_index = middle_part[-1*self.set_bits_len:]
            tag = tag+middle_part[:len(middle_part)-self.set_bits_len]
            set_index = self._to_decimal(set_index)
            base = set_index*self.n
            free_index = -1
            for i in range(0,self.n):
                if(self.blocks[base+i].valid == False):
                    free_index = base+i
                if(self.blocks[base+i].valid and self.blocks[base+i].tag == tag):
                    if(self.replace_method == 2 or self.replace_method == 3):
                        for blck in self.blocks:
                            if(self.blocks[base+i] != blck and blck.valid):
                                blck.counter +=1
                    self.__log_hit(address,base+i)
                    return 1
            if(free_index == -1):
                # Random replace method
                if(self.replace_method == 0):
                    index = self._random_replacment((base,base+self.n-1))
                    self.blocks[index].valid = True
                    self.blocks[index].tag = tag
                    self.blocks[index].counter = 0 
                    self.__log__replace(address,index,'RND')
                    return 0
                # FIFO replace method
                if(self.replace_method == 1):
                    index = self.replace_method((base,base+self.n-1))
                    self.blocks[index].valid = True
                    self.blocks[index].tag = tag
                    self.blocks[index].counter = 0 
                    self.__log__replace(address,index,'FIFO')
                    return 0
                # LRU or LFU replace method
                if(self.replace_method == 2 or self.replace_method == 3):
                    index = self._LRU((base,base+self.n-1))
                    self.blocks[index].valid = True
                    self.blocks[index].tag = tag
                    self.blocks[index].counter = 0 
                    self.__log__replace(address,index,'LFU | LRU')
                    return 0
            else:
                self.blocks[free_index].valid = True
                self.blocks[free_index].tag = tag
                self.blocks[free_index].counter = 0
                self.__log_miss(address,free_index)
                return 0
    def _random_replacment(self,block_range):
        return random.randint(block_range[0],block_range[1])
    def _FIFO(self,block_range):
        minimum = -1
        for i in range(block_range[0],block_range[1]+1):
            r = self.queue.index(self.blocks[i])
            if(r<minimum):
                r = minimum
        self.queue.pop(r)
        return r
    def _LRU(self,block_range):
        max_age = -1;
        index=0
        print(block_range)
        for i in range(block_range[0],block_range[1]+1):
            if(self.blocks[i].counter > max_age):
                max_age = self.blocks[i].counter
                index = i
        return index
    def __log_hit(self,address,block_index):
        print("Address %d founded on block %d | Hit" % (self._to_decimal(address),block_index))
    def __log_miss(self,address,block_index):
        print("Address %d not founded in cache \nAdded to block %d | Miss" % (self._to_decimal(address),block_index))
    def __log__replace(self,address,block_index,method):
        print("Replacement address %d in block %d | method : %s | Miss" % (self._to_decimal(address),block_index,method))

    def __log_sys_info(self):
        struct = {
            0 : "Direct Map",
            1 : "Fully Associative",
            2 : "%d-way Associative" % self.n
        }
        replace = {
            0 : "RND",
            1 : "FIFO",
            2 : "LRU",
            3 : "FRU",
            4 : "SIMPLE"
        }
        print('A Cache With %dbyte Capacity %dbyte Block Size %dbyte Word Size and %s Structure and %s Replacement Mothod Initalized' % (self.capacity,self.block_size,self.word_size,struct.get(self.structure),replace.get(self.replace_method)))
        print('Connect To A %s' % (self.memory.mem_info()))
    def show_cache(self):
        c = 0
        for block in self.blocks:
            print "blck ",c," :",
            rng = self._find_range(block)
            if(rng == 0):
                for i in range(0,self.block_size):
                    print 'EMP',
            else:
                for i in range(rng[0],rng[1]):
                    print i,
            if(self.replace_method == 2 or self.replace_method == 3):
                print block.counter
            print 
            c+=1

                            