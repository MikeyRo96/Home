"""Test: chiar merge ONNX pe GPU? Compara CUDA vs CPU."""
import sys
import time

import numpy as np
import onnxruntime as ort
from onnx import TensorProto, helper

# Windows: onnxruntime NU vede singur DLL-urile CUDA venite ca pachete pip
import glob
import os

dlls = []
for baza in sys.path:
    if baza:
        for d in glob.glob(os.path.join(baza, "nvidia", "*", "bin")):
            if d not in dlls:
                dlls.append(d)
if dlls:
    os.environ["PATH"] = os.pathsep.join(dlls) + os.pathsep + os.environ.get("PATH", "")
    for d in dlls:
        try:
            os.add_dll_directory(d)
        except Exception:
            pass
print("DLL-uri CUDA gasite:", len(dlls))
for d in dlls:
    print("   ", d)

print("versiune onnxruntime:", ort.__version__)
print("provideri disponibili:", ort.get_available_providers())

X = helper.make_tensor_value_info("X", TensorProto.FLOAT, [1, 512, 512])
Y = helper.make_tensor_value_info("Y", TensorProto.FLOAT, [1, 512, 512])
n = helper.make_node("MatMul", ["X", "X"], ["Y"])
g = helper.make_graph([n], "t", [X], [Y])
m = helper.make_model(g, opset_imports=[helper.make_opsetid("", 13)])
m.ir_version = 9  # ONNX nou scrie ir_version prea mare -> ORT 1.24 nu-l poate citi
import onnx
onnx.save(m, "t.onnx")

x = np.random.rand(1, 512, 512).astype(np.float32)
rezultate = []
for nume, prov in (
    ("CPU", ["CPUExecutionProvider"]),
    ("CUDA", [("CUDAExecutionProvider", {"device_id": 0}), "CPUExecutionProvider"]),
):
    try:
        s = ort.InferenceSession("t.onnx", providers=prov)
        activ = s.get_providers()
        t0 = time.time()
        for _ in range(5):
            s.run(None, {"X": x})
        dt = (time.time() - t0) * 1000
        rezultate.append((nume, activ[0], dt))
        print(f"  {nume:6s} cerut -> activ {activ[0]:26s}  {dt:8.0f} ms")
    except Exception as e:
        print(f"  {nume:6s} -> EROARE: {str(e)[:120]}")

if len(rezultate) == 2 and "CUDA" in rezultate[1][1]:
    cpu, gpu = rezultate[0][2], rezultate[1][2]
    print(f"\n  REZULTAT: GPU merge! CPU {cpu:.0f} ms vs GPU {gpu:.0f} ms = {cpu/gpu:.1f}x")
else:
    print("\n  REZULTAT: GPU NU e disponibil pe acest runner (normal - nu are placa NVIDIA)")
