import torch

# PyTorch'un Intel oneDNN'i kullanıp kullanmadığını kontrol etme
print(f"PyTorch sürümü: {torch.__version__}")
print(f"oneDNN kullanılıyor mu: {torch.backends.mkldnn.is_available()}")

# Hesaplama cihazını ayarlama
device = torch.device("cpu")  # Intel GPU, CPU üzerinden kullanılır

# Basit bir tensör işlemi
x = torch.randn(1000, 1000, device=device)
y = torch.randn(1000, 1000, device=device)
z = torch.matmul(x, y)

print("İşlem tamamlandı!")