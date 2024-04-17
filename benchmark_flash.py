import sys
import torch
import time
from hydragen_algo import hydragen_attention, attention_prefix

torch.set_default_device("cuda")
torch.manual_seed(1337)

b = 256
nq = 1
prefix_len = 512
suffix_len = 1
hq = 32
hkv = 32
d = 128

GENERATION_LEN = 100

prefix_k = torch.randn(prefix_len, hkv, d, dtype=torch.bfloat16)
prefix_v = torch.randn(prefix_len, hkv, d, dtype=torch.bfloat16)
suffix_k = torch.randn(b, suffix_len, hkv, d, dtype=torch.bfloat16)
suffix_v = torch.randn(b, suffix_len, hkv, d, dtype=torch.bfloat16)

prefix_k_expanded = prefix_k.unsqueeze(0).expand(suffix_k.size(0), -1, -1, -1)
k = torch.cat((prefix_k_expanded, suffix_k), 1)

prefix_v_expanded = prefix_v.unsqueeze(0).expand(suffix_v.size(0), -1, -1, -1)
v = torch.cat((prefix_v_expanded, suffix_v), 1)

timing = []

for _ in range(GENERATION_LEN):
    print(_)
    
    q = torch.randn(b, nq, hq, d, dtype=torch.bfloat16)
    new_k = torch.randn(b, nq, hkv, d, dtype=torch.bfloat16)
    new_v = torch.randn(b, nq, hkv, d, dtype=torch.bfloat16)

    k = torch.cat((k, new_k), dim=1)
    v = torch.cat((v, new_v), dim=1)

    s = time.time_ns()
    flash_out, lse = attention_prefix(q, k, v)
    e = time.time_ns()

    if _ >= 10:
        timing.append((e-s)/1_000_000)

    print("Flash out shape:", flash_out.shape)

print(flash_out)
torch.save(flash_out.to('cpu'), 'artifacts/flash_out.pt')
print(f"Average time: {sum(timing)/len(timing)} ms")