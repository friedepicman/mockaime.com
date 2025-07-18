#!/usr/bin/env python3
"""
Check TensorFlow GPU support
"""

print("=== Installing TensorFlow (if needed) ===")
import subprocess
import sys

try:
    import tensorflow as tf
    print(f"✅ TensorFlow already installed: {tf.__version__}")
except ImportError:
    print("Installing TensorFlow...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "tensorflow[and-cuda]"])
    import tensorflow as tf
    print(f"✅ TensorFlow installed: {tf.__version__}")

print("\n=== GPU Check ===")
print(f"TensorFlow version: {tf.__version__}")
print(f"Built with CUDA: {tf.test.is_built_with_cuda()}")

physical_devices = tf.config.list_physical_devices('GPU')
print(f"GPUs available: {len(physical_devices)}")

for i, device in enumerate(physical_devices):
    print(f"  GPU {i}: {device}")

if len(physical_devices) > 0:
    print("✅ GPU detected!")
    
    # Test GPU computation
    print("\n=== Testing GPU computation ===")
    with tf.device('/GPU:0'):
        a = tf.random.normal([1000, 1000])
        b = tf.random.normal([1000, 1000])
        c = tf.matmul(a, b)
    print("✅ GPU computation test passed!")
    
else:
    print("❌ No GPU detected")
    print("Falling back to CPU (will be slower)")

print("\n=== CUDA/cuDNN Info ===")
print(f"CUDA version: {tf.sysconfig.get_build_info().get('cuda_version', 'Not found')}")
print(f"cuDNN version: {tf.sysconfig.get_build_info().get('cudnn_version', 'Not found')}")