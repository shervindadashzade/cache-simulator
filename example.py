###############  HELP FOR TYPES #######################
## Memory Type:
# 0 : byte addressable
# 1 : word addressable 
## Structure:
# 0 : direct_map
# 1 : fully_associative
# 2 : n_way_associative
## replace_method:
# 0 : RND
# 1 : FIFO
# 2 : LRU
# 3 : LFU

from classes.cache import *
# Memory(address_bit,mem_type)
mem = Memory(8,0)
# Cache(capacity,structure,block_size,word_size,replace_method,memory,n=2)
cache = Cache(32,2,4,4,0,mem)

cache.query(45)
cache.show_cache()
#cache.show_cache()
#cache.query(47)
#cache.show_cache()
cache.query(0)
cache.show_cache()
cache.query(2)
cache.show_cache()
cache.query(109)
cache.show_cache()
cache.query(125)
cache.show_cache()